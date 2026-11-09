import json
import re
import httpx
from typing import Optional
from app.config import settings
from app.schemas import SourceCitation

SYSTEM_PROMPT = """You are a strict Manufacturing Shop-Floor SOP Copilot.
Answer the supervisor's question ONLY using the provided SOP excerpts.

CRITICAL RULES:
1. If the provided excerpts do NOT explicitly contain the answer to the question, you MUST set "is_answerable" to false, set "answer" to "This information is not found in the provided plant SOPs and manuals. Do not guess procedures—please contact Plant Engineering or your Shift Lead.", and set "safety_warning" to null.
2. NEVER invent numbers, temperatures, pressures, torque specs, or steps not present in the excerpts.
3. Format the "answer" using concise, direct bullet points so a supervisor on a phone can read it in 5 seconds. Always mention the source document and page number inline.
4. SHOP-FLOOR SAFETY IMPROVEMENT: If the excerpts mention Lockout/Tagout (LOTO), PPE (gloves, goggles, ear protection), high voltage, pressure bleed, chemical hazards, or thermal hazards, extract a 1-sentence urgent alert into "safety_warning". Otherwise, set "safety_warning" to null.

Respond ONLY in valid JSON with this exact structure:
{
  "is_answerable": true,
  "safety_warning": "Optional urgent safety/PPE/LOTO string or null",
  "answer": "Clear bulleted answer citing document and page"
}
"""

def extract_heuristic_safety_warning(sources: list[SourceCitation]) -> Optional[str]:
    hazard_keywords = {
        "loto": "Mandatory Lockout/Tagout (LOTO) required before servicing.",
        "lockout": "Verify Lockout/Tagout (LOTO) isolation before touching equipment.",
        "ppe": "Required PPE must be worn as specified in the SOP before proceeding.",
        "goggles": "Eye protection / safety goggles and gloves required for this procedure.",
        "pressure": "Ensure hydraulic/pneumatic pressure is fully bled to zero before opening lines.",
        "voltage": "High-voltage hazard: De-energize main breaker and verify zero energy state."
    }
    combined = " ".join([s.snippet.lower() for s in sources])
    triggered = [msg for kw, msg in hazard_keywords.items() if kw in combined]
    return triggered[0] if triggered else None

def generate_grounded_answer(question: str, sources: list[SourceCitation]) -> dict:
    if not sources:
        return {
            "is_answerable": False,
            "safety_warning": None,
            "answer": "This information is not found in the provided plant SOPs and manuals. Do not guess procedures—please contact Plant Engineering or your Shift Lead.",
            "llm_used": "vector-guardrail"
        }

    context_blocks = []
    for i, s in enumerate(sources, 1):
        context_blocks.append(f"[Excerpt {i} | Source: {s.source_file} - Page {s.page_number}]\n{s.snippet}")
    context_text = "\n\n".join(context_blocks)
    user_prompt = f"Supervisor Question: {question}\n\nSOP Excerpts:\n{context_text}"

    # 1. Try Ollama Local LLM if configured
    if settings.LLM_PROVIDER.lower() == "ollama":
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "format": "json",
                        "stream": False,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ]
                    }
                )
                if resp.status_code == 200:
                    content = resp.json()["message"]["content"]
                    parsed = json.loads(content)
                    return {
                        "is_answerable": bool(parsed.get("is_answerable", True)),
                        "safety_warning": parsed.get("safety_warning") or extract_heuristic_safety_warning(sources),
                        "answer": parsed.get("answer", ""),
                        "llm_used": f"ollama/{settings.OLLAMA_MODEL}"
                    }
        except Exception as e:
            print(f"[LLM Warning] Ollama call failed ({e}), falling back...")

    # 2. Try Groq Hosted API if configured
    if settings.GROQ_API_KEY:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json={
                        "model": settings.GROQ_MODEL,
                        "response_format": {"type": "json_object"},
                        "temperature": 0.0,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ]
                    }
                )
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    return {
                        "is_answerable": bool(parsed.get("is_answerable", True)),
                        "safety_warning": parsed.get("safety_warning") or extract_heuristic_safety_warning(sources),
                        "answer": parsed.get("answer", ""),
                        "llm_used": f"groq/{settings.GROQ_MODEL}"
                    }
        except Exception as e:
            print(f"[LLM Warning] Groq call failed ({e}), falling back to extractive synthesis...")

    # 3. Try Gemini Hosted API if configured
    if settings.GEMINI_API_KEY:
        try:
            with httpx.Client(timeout=10.0) as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}"
                payload = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {"text": f"{SYSTEM_PROMPT}\n\n{user_prompt}"}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "temperature": 0.0
                    }
                }
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(content)
                    return {
                        "is_answerable": bool(parsed.get("is_answerable", True)),
                        "safety_warning": parsed.get("safety_warning") or extract_heuristic_safety_warning(sources),
                        "answer": parsed.get("answer", ""),
                        "llm_used": "gemini/gemini-2.0-flash"
                    }
        except Exception as e:
            print(f"[LLM Warning] Gemini call failed ({e}), falling back to extractive synthesis...")

    # 4. Deterministic Extractive Fallback (Guarantees app works offline even without Ollama/API keys)
    top = sources[0]
    bullet_points = [s.strip() for s in re.split(r'(?<=[.!?])\s+', top.snippet) if len(s.strip()) > 15]
    formatted_bullets = "\n".join([f"• {b}" for b in bullet_points[:4]])
    answer_text = (
        f"According to **{top.source_file} (Page {top.page_number})**:\n\n"
        f"{formatted_bullets}"
    )
    return {
        "is_answerable": True,
        "safety_warning": extract_heuristic_safety_warning(sources),
        "answer": answer_text,
        "llm_used": "extractive-fallback"
    }
