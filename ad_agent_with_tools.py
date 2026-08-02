import sqlite3
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

client = genai.Client()

# 1. Define the local relational database tool
def get_advertiser_risk_profile(account_id: str) -> str:
    """Queries the internal relational database to fetch historical risk metrics for an advertiser account."""
    print(f"\n[TOOL EXECUTION] Executing local SQL query for Account: {account_id}...")
    conn = sqlite3.connect("advertiser_history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM advertiser_profiles WHERE Account_ID = ?", (account_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return json.dumps({
            "Account_ID": result[0],
            "Account_Age_Days": result[1],
            "Past_Violations_Count": result[2],
            "Risk_Tier": result[3]
        })
    return json.dumps({"status": "error", "message": "Account ID not found"})


# 2. Define our final structural data contract
class FinalAgentDecision(BaseModel):
    verdict: str = Field(description="Final action: 'Approve', 'Flag for Human Review', or 'Immediate Account Ban'.")
    final_reasoning: str = Field(description="Synthesize both the ad copy text check and the historical SQL database profile risk metadata metrics.")

def run_agentic_audit():
    incoming_payload = {
        "Account_ID": "ACC-88101",
        "Ad_Copy": "MutiplY your c0ins overnight! 100% guaranteed wealth generation program."
    }
    
    print(f"Ingesting live submission stream from user account: {incoming_payload['Account_ID']}")
    
    # STAGE 1: Execution & Tool Loop (We remove the response_schema constraint here)
    tool_prompt = (
        f"Audit this ad copy submission: '{incoming_payload['Ad_Copy']}'. "
        f"You must use your database lookup tool to cross-reference the profile for Account_ID '{incoming_payload['Account_ID']}' "
        f"before forming your compliance opinion."
    )
    
    print("Initiating Stage 1: Tool Routing and Data Collection...")
    agent_chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction="You are an enterprise Trust & Safety investigator. Use your tools to check account histories for anomalous ad copies.",
            tools=[get_advertiser_risk_profile],
            temperature=0.1
        )
    )
    
    # This automatically executes the local python tool under the hood via the SDK
    stage1_response = agent_chat.send_message(tool_prompt)
    
    # STAGE 2: Structured Output Processing (Forcing the final schema contract)
    print("\nInitiating Stage 2: Compiling Context into Structured JSON Data Contract...")
    final_report_response = client.models.generate_content(
        model='gemini-2.5-flash',
        # We feed the entire history of the tool conversation into the final validator call
        contents=agent_chat.get_history(),
        config=types.GenerateContentConfig(
            system_instruction="Read the previous investigation logs. Format the final verdict into the requested JSON schema contract.",
            response_mime_type="application/json",
            response_schema=FinalAgentDecision,
            temperature=0.1
        ),
    )
    
    print("\n--- Final Agent Autonomous Decision Sheet (Validated Schema) ---")
    print(final_report_response.text)

if __name__ == "__main__":
    run_agentic_audit()