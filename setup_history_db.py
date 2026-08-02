import sqlite3

def init_db():
    conn = sqlite3.connect("advertiser_history.db")
    cursor = conn.cursor()
    
    # Create an infrastructure tracking table mimicking internal trust logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS advertiser_profiles (
            Account_ID TEXT PRIMARY KEY,
            Account_Age_Days INTEGER,
            Past_Violations_Count INTEGER,
            Risk_Tier TEXT
        )
    """)
    
    # Seed the database with mock historical data to trace against our ad ids
    mock_profiles = [
        ("ACC-88101", 3, 4, "High Risk"),     # New account, lots of deletes
        ("ACC-00302", 720, 0, "Trusted"),     # Old established account
        ("ACC-44903", 45, 1, "Medium Risk")    # Mid-age account, one past violation
    ]
    
    cursor.executemany("INSERT OR REPLACE INTO advertiser_profiles VALUES (?, ?, ?, ?)", mock_profiles)
    conn.commit()
    conn.close()
    print("Relational database initialized securely as advertiser_history.db!")

if __name__ == "__main__":
    init_db()