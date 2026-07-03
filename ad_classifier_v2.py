import csv
import json
import time
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
# Import our custom RAG class from our previous milestone file
from rag_policy_vault import PolicyVaultRAG

# 1. Initialize our GenAI Client and the RAG Policy Vault
client = genai.Client()
policy_vault = PolicyVaultRAG()

# 2. Define our complete, multi-stage data contract schema
class IntegratedAuditReport(BaseModel):
    is_violation: bool = Field(description="True if the text violates standard platform safety guidelines.")
    violation_category: str = Field(description="Must be exactly one of: 'None', 'Misleading Claims', 'Restricted Goods', 'Malicious/Adult'.")
    confidence_score: float = Field(description="Confidence from 0.0 to 1.0.")
    audit_reasoning: str = Field(description="A short one-sentence justification detailing the semantic flag.")
    policy_citation_summary: str = Field(description="Synthesize how the ad directly breaks the specific rules cited in the policy context text.")

def run_integrated_pipeline(input_csv="mock_ad_logs.csv", num_records=3):
    print(f"--- Launching Integrated TrustGuard AI Pipeline ---")
    
    try:
        with open(input_csv, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            
            for index, row in enumerate(reader):
                if index >= num_records:
                    break
                    
                ad_id = row["Ad_ID"]
                ad_copy = row["Ad_Copy"]
                
                print(f"\n[RECORD {index + 1}] Processing: {ad_id}")
                print(f"Ad Text: '{ad_copy}'")
                
                # STEP 1: Query the RAG Vector Base to find the most relevant policy document
                rag_result = policy_vault.query_relevant_policy(ad_copy)
                context_policy = rag_result["policy_text"]
                
                # STEP 2: Feed the raw ad copy AND the retrieved rule context to Gemini
                combined_prompt = f"""
                Ad Copy to Inspect: "{ad_copy}"
                
                Retrieved Reference Policy Context:
                \"\"\"
                {context_policy}
                \"\"\"
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=combined_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            "You are an enterprise Trust & Safety auditor. Analyze the input ad copy against "
                            "the provided policy context. Evaluate if it violates the rules, calculate confidence, "
                            "and synthesize a clean compliance citation summary based strictly on the policy text."
                        ),
                        response_mime_type="application/json",
                        response_schema=IntegratedAuditReport,
                        temperature=0.1
                    ),
                )
                
                # STEP 3: Parse and Display the final multi-agent report
                report = json.loads(response.text)
                print(f"-> Violation Detected: {report['is_violation']} ({report['violation_category']})")
                print(f"-> Confidence Score  : {report['confidence_score'] * 100}%")
                print(f"-> Auditor Justification: {report['audit_reasoning']}")
                print(f"-> Automated Citation   : {report['policy_citation_summary']}")
                print("-" * 60)
                
                time.sleep(2) # Free tier pacing buffer
                
    except FileNotFoundError:
        print("Please ensure your CSV dataset is generated first.")

if __name__ == "__main__":
    run_integrated_pipeline()