import csv
import json
import random
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

client = genai.Client()

# 1. Define the Pydantic Output Contract for the LLM
class EvasiveAd(BaseModel):
    manipulated_text: str = Field(description="Ad text that promotes a banned category but uses typos, symbols, or soft context to disguise it.")
    true_intended_violation: str = Field(description="The underlying violation category (e.g., Crypto Scams, Counterfeit Goods, Pharma Fraud).")

# 2. Trigger the Live API
adversarial_prompt = "Generate an example of a deceptive ad copy that attempts to mask a pharmaceutical or financial scam using characters updates or semantic phrasing."

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=adversarial_prompt,
    config=types.GenerateContentConfig(
        system_instruction="You are a red-team security engineer simulating evasive ad behavior for Trust & Safety benchmarking.",
        response_mime_type="application/json",
        response_schema=EvasiveAd,
        temperature=0.8 
    )
)

# 3. Parse the Structured JSON Output
ai_data = json.loads(response.text)

# 4. Data Transformation Layer (Mapping to our Data Contract)
# Read the current file to calculate the next dynamic Ad_ID sequence index
try:
    with open("mock_ad_logs.csv", "r", encoding="utf-8") as f:
        row_count = sum(1 for line in f)
except FileNotFoundError:
    row_count = 1

next_id = f"AD-2026{row_count:05d}"

# Map the string categories to our technical tracking Algorithm IDs
algo_mapping = {
    "Crypto Scams": 101,
    "Pharma Fraud": 102,
    "Counterfeit Goods": 103
}
# Fallback to 101 if the AI creates a new text string category dynamically
assigned_algo_id = algo_mapping.get(ai_data["true_intended_violation"], 101)

# Package it up cleanly matching the base header definitions
transformed_row = [
    next_id,
    ai_data["manipulated_text"],
    random.randint(1, 15), # New accounts are typical for targeted adversarial attacks
    random.randint(0, 2),  # Historical violations flag
    assigned_algo_id       # The explicit numerical AlgoId rule assignment
]

# 5. Append directly to the CSV Data Stream
with open("mock_ad_logs.csv", mode="a", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(transformed_row)

print(f"Success! Transformed adversarial ad injected into mock_ad_logs.csv as {next_id}.")