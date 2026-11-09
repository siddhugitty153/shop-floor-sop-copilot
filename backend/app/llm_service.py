import json
import re
import httpx
from typing import Optional
from app.config import settings
from app.schemas import SourceCitation

SYSTEM_PROMPT = """You are an expert Manufacturing Shop-Floor SOP Copilot for plant supervisors.
Answer the supervisor's question using the provided SOP excerpts.

CRITICAL INSTRUCTIONS:
1. Grounding: Answer based on the provided excerpts. Synthesize clear, direct bullet points (2 to 4 bullets max) so a supervisor on a mobile device can read it in 5 seconds. Cite the source document and page number inline (e.g., "[SAF-SOP-003, Page 1]").
2. Answerability: If the excerpts provide relevant rules, specifications, steps, or procedures that address the question, set "is_answerable" to true. Only set "is_answerable" to false if the excerpts are completely unrelated or completely silent on the topic.
3. Safety Alerts: If the excerpts mention Lockout/Tagout (LOTO), electrical disconnects, PPE (safety glasses, gloves, boots), pressure bleed, or chemical hazards, include a 1-sentence urgent reminder in "safety_warning". Otherwise set "safety_warning" to null.
4. Accuracy: Never hallucinate or invent steps or numbers not supported by the excerpts.

Format response strictly in JSON:
{
  "is_answerable": true,
  "safety_warning": "Urgent safety alert or null",
  "answer": "Concise bulleted answer citing document and page inline"
}
"""

def extract_heuristic_safety_warning(sources: list[SourceCitation]) -> Optional[str]:
    hazard_keywords = {
        "loto": "Mandatory Lockout/Tagout (LOTO) required before servicing.",
        "lockout": "Verify Lockout/Tagout (LOTO) isolation before touching equipment.",
        "ppe": "Required PPE (gloves, safety glasses, steel-toe boots) must be worn as specified in the SOP.",
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

    # 1. Try Gemini Hosted API if configured
    if settings.GEMINI_API_KEY:
        try:
            with httpx.Client(timeout=12.0) as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
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
                    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.MULTILINE)
                    parsed = json.loads(cleaned)
                    is_ans = bool(parsed.get("is_answerable", True))
                    if is_ans and parsed.get("answer"):
                        return {
                            "is_answerable": True,
                            "safety_warning": parsed.get("safety_warning") or extract_heuristic_safety_warning(sources),
                            "answer": parsed.get("answer", ""),
                            "llm_used": "gemini/gemini-2.5-flash"
                        }
                    elif sources[0].score >= 0.10:
                        print(f"[LLM Note] Gemini returned unanswerable but top match score is {sources[0].score}. Using grounded fallback.")
                    else:
                        return {
                            "is_answerable": False,
                            "safety_warning": None,
                            "answer": parsed.get("answer") or "This information is not found in the provided plant SOPs and manuals. Do not guess procedures—please contact Plant Engineering or your Shift Lead.",
                            "llm_used": "gemini/gemini-2.5-flash"
                        }
                else:
                    print(f"[LLM Warning] Gemini returned status {resp.status_code}: {resp.text[:150]}")
        except Exception as e:
            print(f"[LLM Warning] Gemini call failed ({e}), falling back...")

    # 2. Try LM Studio Local LLM if configured or running
    if settings.LLM_PROVIDER.lower() == "lmstudio":
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    f"{settings.LM_STUDIO_BASE_URL}/chat/completions",
                    json={
                        "temperature": 0.0,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ]
                    }
                )
                if resp.status_code == 200:
                    raw_content = resp.json()["choices"][0]["message"]["content"]
                    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_content.strip(), flags=re.MULTILINE)
                    parsed = json.loads(cleaned)
                    return {
                        "is_answerable": bool(parsed.get("is_answerable", True)),
                        "safety_warning": parsed.get("safety_warning") or extract_heuristic_safety_warning(sources),
                        "answer": parsed.get("answer", ""),
                        "llm_used": "lm-studio/local"
                    }
        except Exception as e:
            print(f"[LLM Warning] LM Studio call failed ({e}), falling back...")

    # 3. Try Ollama Local LLM if configured
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

    # 4. Try Groq Hosted API if configured
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

    # 5. Deterministic Extractive Fallback (Guarantees app works 100% reliably even offline or during API outage)
    top_sources = sources[:3]
    answer_parts = []
    for s in top_sources:
        bullet_points = [b.strip() for b in re.split(r'(?<=[.!?])\s+', s.snippet) if len(b.strip()) > 15]
        if bullet_points:
            formatted_bullets = "\n".join([f"• {b}" for b in bullet_points[:3]])
            answer_parts.append(f"**From {s.source_file} (Page {s.page_number}):**\n{formatted_bullets}")

    answer_text = "\n\n".join(answer_parts) if answer_parts else f"According to **{sources[0].source_file} (Page {sources[0].page_number})**:\n\n{sources[0].snippet}"
    return {
        "is_answerable": True,
        "safety_warning": extract_heuristic_safety_warning(sources),
        "answer": answer_text,
        "llm_used": "extractive-fallback"
    }
