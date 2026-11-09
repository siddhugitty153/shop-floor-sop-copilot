import sys
import json
from app.retriever import retriever
from app.llm_service import generate_grounded_answer

SAMPLE_QUESTIONS = [
    {"num": 1, "q": "What is the recommended coolant concentration for the TX-200 CNC turning centre?"},
    {"num": 2, "q": "The machine is showing alarm AL-104. What does it mean and what should the operator do?"},
    {"num": 3, "q": "Who is allowed to remove a lockout lock from a machine?"},
    {"num": 4, "q": "What is the outer diameter tolerance for the BH-220 bearing housing?"},
    {"num": 5, "q": "How often should spindle runout be checked, and who does it?"}
]

def run():
    print("# Official Google Drive Sample Questions Evaluation\n")
    for item in SAMPLE_QUESTIONS:
        q = item["q"]
        sources = retriever.retrieve(q)
        ans = generate_grounded_answer(q, sources)
        cites = ", ".join([f"`{s.source_file} (Page {s.page_number})`" for s in sources]) if ans["is_answerable"] else "None"
        print(f"### Sample Q{item['num']}: {q}")
        print(f"- **Answerable:** `{ans['is_answerable']}`")
        print(f"- **Engine:** `{ans['llm_used']}`")
        if ans.get("safety_warning"):
            print(f"- **Safety Alert:** ⚠️ *{ans['safety_warning']}*")
        print(f"- **Copilot Answer:**\n{ans['answer']}")
        print(f"- **Cited Sources:** {cites}\n")

if __name__ == "__main__":
    run()

