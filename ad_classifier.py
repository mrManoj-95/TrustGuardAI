import csv
import json
import time
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. Initialize the GenAI Client (reads $env:GEMINI_API_KEY from RAM memory)
client = genai.Client()

# 2. Define the Pydantic structured output validation contract
class AdAuditVerdict(BaseModel):
    is_violation: bool = Field(description="True if the text violates standard policies like fraud, explicit content, or dangerous goods.")
    violation_category: str = Field(description="Must be exactly one of: 'None', 'Misleading Claims', 'Restricted Goods', 'Malicious/Adult'.")
    confidence_score: float = Field(description="A confidence value grading from 0.0 (low confidence) to 1.0 (absolute certainty).")
    audit_reasoning: str = Field(description="A short, professional one-sentence justification detailing the policy decision.")

def process_ad_stream(input_csv="mock_ad_logs.csv", num_records_to_test=5):
    print(f"Opening data stream from {input_csv}...")
    print(f"Evaluating the first {num_records_to_test} records via Gemini API...\n")
    
    try:
        with open(input_csv, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            
            for index, row in enumerate(reader):
                if index >= num_records_to_test:
                    break
                    
                ad_id = row["Ad_ID"]
                ad_copy = row["Ad_Copy"]
                ground_truth_algo = row["FailedAdGroupFraudRule"]
                
                print(f"--- Processing Record {index + 1}: {ad_id} ---")
                print(f"Raw Ad Copy: '{ad_copy}'")
                
                # 3. Request strict schema validation from Gemini
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=ad_copy,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            "You are an advanced automated Trust & Safety content auditor. "
                            "Analyze the input ad copy text for platform policy violations. "
                            "Output your judgment strictly inside the provided structural schema parameters."
                        ),
                        response_mime_type="application/json",
                        response_schema=AdAuditVerdict,
                        temperature=0.1  # Low temperature guarantees deterministic accuracy
                    ),
                )
                
                # 4. Parse the structured output
                verdict_data = json.loads(response.text)
                
                print(f"AI Verdict  : Violation={verdict_data['is_violation']} | Category={verdict_data['violation_category']}")
                print(f"AI Confidence: {verdict_data['confidence_score'] * 100}%")
                print(f"AI Reasoning : {verdict_data['audit_reasoning']}")
                print(f"Ground Truth AlgoId Flag: {ground_truth_algo}")
                print("-" * 50 + "\n")
                
                # Polite rate-limiting buffer for the free tier process
                time.sleep(2)
                
    except FileNotFoundError:
        print(f"Error: {input_csv} not found. Please run mock_data_generator.py first.")

if __name__ == "__main__":
    process_ad_stream()