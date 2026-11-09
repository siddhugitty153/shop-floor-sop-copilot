import time
from app.retriever import retriever
from app.llm_service import generate_grounded_answer

TEST_QUESTIONS = [
    {"type": "Custom 1 (Safety)", "q": "What are the mandatory Lockout/Tagout (LOTO) and PPE requirements before performing maintenance?"},
    {"type": "Custom 2 (Maintenance)", "q": "What is the standard preventive maintenance and lubrication schedule for the shop-floor equipment?"},
    {"type": "Custom 3 (Quality)", "q": "What are the quality inspection criteria and actions required when an out-of-tolerance defect is detected?"},
    {"type": "Custom 4 (Troubleshooting)", "q": "What steps should a supervisor follow when an abnormal pressure, temperature, or machine fault occurs?"},
    {"type": "Custom 5 (Unanswerable / Out-of-Scope)", "q": "What is the corporate reimbursement policy for international business class flights and hotel stays?"}
]

def run_eval():
    print("# Evaluation Output for README.md\n")
    for idx, item in enumerate(TEST_QUESTIONS, 1):
        start = time.perf_counter()
        sources = retriever.retrieve(item["q"], "All")
        data = generate_grounded_answer(item["q"], sources)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        final_sources = sources if data["is_answerable"] else []
        cites = ", ".join([f"`{s.source_file} (Page {s.page_number})`" for s in final_sources]) or "None (Refused - Out of Scope)"
        
        print(f"### {idx}. [{item['type']}] {item['q']}")
        print(f"- **Answerable from SOPs:** `{data['is_answerable']}`")
        if data.get("safety_warning"):
            print(f"- **Safety Banner Triggered:** ⚠️ *{data['safety_warning']}*")
        print(f"- **Copilot Answer:**\n  > {data['answer'].replace(chr(10), chr(10) + '  > ')}")
        print(f"- **Cited Sources:** {cites}")
        print(f"- **Engine:** `{data.get('llm_used')}` | **Latency:** `{elapsed_ms}ms`\n")

if __name__ == "__main__":
    run_eval()

