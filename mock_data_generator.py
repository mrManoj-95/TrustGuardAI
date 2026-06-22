import csv
import random

# Core configuration for synthetic ad generation
NUM_RECORDS = 1000
OUTPUT_FILE = "mock_ad_logs.csv"

# Mock datasets mimicking real-world ad compliance issues
AD_SAMPLES = [
    {"text": "Get rich quick! Earn $5000/day from home with zero risk. Register now!", "category": "Misleading Claims", "algo_id": 101},
    {"text": "Buy high-quality weight loss pills. Melt 20lbs in 48 hours guaranteed!", "category": "Restricted Goods", "algo_id": 102},
    {"text": "Standard household kitchen blender. 3 speeds, stainless steel blades.", "category": "None", "algo_id": 0},
    {"text": "Click here to see a shocking viral video! WARNING: explicit details inside.", "category": "Malicious/Adult", "algo_id": 103},
    {"text": "Affordable life insurance policies for families. Get a free quote today.", "category": "None", "algo_id": 0},
    {"text": "Earn standard rewards points back on everyday grocery purchases with our card.", "category": "None", "algo_id": 0}
]

def generate_dataset():
    print(GEN_MSG := f"Generating {NUM_RECORDS} synthetic ad records...")
    
    with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Writing header schema matching our data analyst track requirements
        writer.writerow(["Ad_ID", "Ad_Copy", "Account_Age_Days", "Historical_Flags", "FailedAdGroupFraudRule"])
        
        for i in range(1, NUM_RECORDS + 1):
            ad_id = f"AD-{2026}{i:05d}"
            # Randomly pick a sample but weight it to have more clean ads (None)
            sample = random.choices(AD_SAMPLES, weights=[15, 15, 50, 10, 30, 30], k=1)[0]
            
            account_age = random.randint(1, 730)
            # Newer accounts have a slightly higher tendency for fraud edge-cases
            hist_flags = random.randint(0, 5) if sample["algo_id"] != 0 else random.randint(0, 1)
            
            writer.writerow([ad_id, sample["text"], account_age, hist_flags, sample["algo_id"]])
            
    print(f"Success! Synthetic data successfully saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_dataset()