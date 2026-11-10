import json
import re
import httpx
from typing import Optional
from app.config import settings
from app.schemas import SourceCitation

SYSTEM_PROMPT = """You are an expert Manufacturing Shop-Floor SOP Copilot for plant supervisors.
Answer the supervisor's question using the provided SOP excerpts.

CRITICAL INSTRUCTIONS:
1. Grounding & Completeness: Synthesize clear, direct bullet points (2 to 4 bullets max) so a supervisor on a mobile device can read it in 5 seconds. Cite the source document and page number inline (e.g., "[SAF-SOP-003, Page 1]").
2. Exact Specifications: When reporting tolerances, dimensions, pressures, or percentages, ALWAYS include BOTH the nominal dimension AND the tolerance/range AND units (e.g., "Nominal: 90.000 mm, Tolerance: +/- 0.050 mm (Range: 89.950 to 90.050 mm)"). Include check method/tool if stated.
3. Answerability: If the excerpts provide relevant rules, specifications, steps, or procedures that address the question, set "is_answerable" to true. Only set "is_answerable" to false if the excerpts are completely unrelated or completely silent on the topic.
4. Safety Alerts: If the excerpts mention Lockout/Tagout (LOTO), electrical disconnects, PPE (safety glasses, gloves, boots), pressure bleed, or chemical hazards, include a 1-sentence urgent reminder in "safety_warning". Otherwise set "safety_warning" to null.
5. Accuracy: Never hallucinate or invent steps or numbers not supported by the excerpts.

Format response strictly in JSON:
{
  "is_answerable": true,
  "safety_warning": "Urgent safety alert or null",
  "answer": "Concise bulleted answer citing document and page inline"
}
"""

FALLBACK_STOPWORDS = {
    "what", "is", "the", "for", "and", "or", "to", "of", "in", "on", "a", "an",
    "how", "who", "when", "where", "why", "which", "are", "was", "were", "be",
    "do", "does", "did", "can", "could", "should", "would", "it", "its", "this",
    "that", "from", "with", "about", "tell", "me", "explain", "mean", "machine",
    "recommended", "allowed", "checked", "showing"
}

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

def query_aware_extractive_answer(question: str, sources: list[SourceCitation]) -> str:
    """Rank individual table rows & sentences by relevance to the query so offline fallback returns exact specs."""
    q_tokens = [
        t for t in re.findall(r'[a-zA-Z0-9\-]+', question.lower())
        if len(t) >= 2 and t not in FALLBACK_STOPWORDS
    ]

    scored_lines = []
    seen_texts = set()

    for src in sources:
        # Split on newlines first (table rows!), then split long prose paragraphs into sentences
        raw_lines = []
        for ln in src.snippet.split("\n"):
            ln = ln.strip()
            if not ln:
                continue
            if ln.startswith("•") or "|" in ln or len(ln) < 180:
                raw_lines.append(ln)
            else:
                raw_lines.extend([s.strip() for s in re.split(r'(?<=[.!?])\s+', ln) if s.strip()])

        for line in raw_lines:
            # Filter out metadata boilerplate & title headers
            if any(b in line for b in ["Document No.:", "Prepared By:", "Uncontrolled copy", "Effective Date:", "Kaveri Precision Components"]):
                continue
            if len(line) < 10 or line in seen_texts:
                continue
            seen_texts.add(line)

            line_lower = line.lower()
            hits = sum(1 for t in q_tokens if t in line_lower)
            if hits == 0 and len(q_tokens) > 0:
                continue

            # Heavily prioritize actual spec rows, procedure steps, and numerical rules over generic intro text
            is_table_row = 1 if ("|" in line or line.startswith("•")) else 0
            has_spec = 1 if re.search(r'(\d+\.\d+|\+/-|%|mm|bar|mpa|iso|al-\d+|sf-\d+|qf-\d+|production manager|safety officer|authorised person)', line_lower) else 0
            is_intro_fluff = -1.5 if any(p in line_lower for p in ["this manual defines", "this procedure describes", "scope applies to", "1. purpose"]) else 0.0
            line_score = (hits * 2.0) + (is_table_row * 1.5) + (has_spec * 1.2) + is_intro_fluff + src.score
            scored_lines.append((line_score, line, src.source_file, src.page_number))

    if scored_lines:
        scored_lines.sort(key=lambda x: x[0], reverse=True)
        top_hits = scored_lines[:4]
        bullets = []
        for _, line, fname, pg in top_hits:
            clean_bullet = line.lstrip("•").strip()
            bullets.append(f"• {clean_bullet} `[{fname}, Page {pg}]`")
        return "\n".join(bullets)

    # Secondary safety net: show cleaned snippet of highest ranked source
    top = sources[0]
    cleaned_lines = [
        ln.strip() for ln in top.snippet.split("\n")
        if ln.strip() and "Document No.:" not in ln
    ]
    preview = "\n".join(cleaned_lines[:4])
    return f"**From {top.source_file} (Page {top.page_number}):**\n{preview}"

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

    user_prompt = f"""CONTEXT EXCERPTS FROM PLANT SOPs:
{context_text}

SUPERVISOR QUESTION:
{question}

Provide the grounded JSON response:"""

    # 1. Try Google Gemini API (Fast, accurate, retries secondary model if 503 high demand)
    if settings.GEMINI_API_KEY and settings.LLM_PROVIDER.lower() in ["gemini", "extractive", "ollama"]:
        gemini_models = ["gemini-2.5-flash", "gemini-flash-latest"]
        for model_name in gemini_models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.GEMINI_API_KEY}"
                with httpx.Client(timeout=15.0) as client:
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
                        raw_answer = parsed.get("answer", "")
                        if isinstance(raw_answer, list):
                            raw_answer = "\n".join(f"• {str(item).lstrip('•- ').strip()}" for item in raw_answer if str(item).strip())
                        if is_ans and raw_answer:
                            return {
                                "is_answerable": True,
                                "safety_warning": parsed.get("safety_warning") or extract_heuristic_safety_warning(sources),
                                "answer": str(raw_answer),
                                "llm_used": f"gemini/{model_name}"
                            }
                        else:
                            return {
                                "is_answerable": False,
                                "safety_warning": None,
                                "answer": str(raw_answer) if raw_answer and not is_ans else "This information is not found in the provided plant SOPs and manuals. Do not guess procedures—please contact Plant Engineering or your Shift Lead.",
                                "llm_used": f"gemini/{model_name}"
                            }
                    elif resp.status_code in [429, 503]:
                        print(f"[LLM Warning] {model_name} returned status {resp.status_code}, trying next Gemini model...")
                        continue
                    else:
                        print(f"[LLM Warning] {model_name} returned status {resp.status_code}: {resp.text[:120]}")
                        break
            except Exception as e:
                print(f"[LLM Warning] {model_name} call failed ({e}), trying next option...")
                continue

    # 2. Try LM Studio Local LLM if configured
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
                        "llm_used": "lmstudio/local-llm"
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
            print(f"[LLM Warning] Groq call failed ({e}), falling back to query-aware extractive synthesis...")

    # 5. Query-Aware Extractive Fallback (Clean, ranked table rows & sentences—never generic header boilerplate)
    return {
        "is_answerable": True,
        "safety_warning": extract_heuristic_safety_warning(sources),
        "answer": query_aware_extractive_answer(question, sources),
        "llm_used": "extractive-fallback"
    }
