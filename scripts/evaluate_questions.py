import httpx

API_URL = "http://localhost:8000/ask"

# 5 Custom Evaluation Questions covering Safety, Maintenance, Quality, Troubleshooting, and Out-of-Scope
TEST_QUESTIONS = [
    {"type": "Custom 1 (Safety)", "q": "What are the mandatory Lockout/Tagout (LOTO) and PPE requirements before performing maintenance?"},
    {"type": "Custom 2 (Maintenance)", "q": "What is the standard preventive maintenance and lubrication schedule for the shop-floor equipment?"},
    {"type": "Custom 3 (Quality)", "q": "What are the quality inspection criteria and actions required when an out-of-tolerance defect is detected?"},
    {"type": "Custom 4 (Troubleshooting)", "q": "What steps should a supervisor follow when an abnormal pressure, temperature, or machine fault occurs?"},
    {"type": "Custom 5 (Unanswerable / Out-of-Scope)", "q": "What is the corporate reimbursement policy for international business class flights and hotel stays?"}
]

def run_eval():
    print("# Evaluation Output for README.md\n")
    with httpx.Client(timeout=30.0) as client:
        for idx, item in enumerate(TEST_QUESTIONS, 1):
            resp = client.post(API_URL, json={"question": item["q"], "category_filter": "All"})
            data = resp.json()
            cites = ", ".join([f"`{s['source_file']} (Page {s['page_number']})`" for s in data.get("sources", [])]) or "None (Refused - Out of Scope)"
            print(f"### {idx}. [{item['type']}] {item['q']}")
            print(f"- **Answerable from SOPs:** `{data['is_answerable']}`")
            if data.get("safety_warning"):
                print(f"- **Safety Banner Triggered:** ⚠️ *{data['safety_warning']}*")
            print(f"- **Copilot Answer:**\n  > {data['answer'].replace(chr(10), chr(10) + '  > ')}")
            print(f"- **Cited Sources:** {cites}")
            print(f"- **Engine:** `{data.get('llm_used')}` | **Latency:** `{data.get('latency_ms')}ms`\n")

if __name__ == "__main__":
    run_eval()
