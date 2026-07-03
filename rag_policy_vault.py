import os
import numpy as np
from google import genai

client = genai.Client()

def get_embedding(text: str) -> list:
    """Generates a text embedding vector using Gemini's native model."""
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text
    )
    # Extract the mathematical float list from the response object
    return response.embeddings[0].values

def compute_cosine_similarity(v1, v2) -> float:
    """Calculates semantic similarity between two vectors (1.0 is identical)."""
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    return dot_product / (norm_v1 * norm_v2)

class PolicyVaultRAG:
    def __init__(self, policies_dir="policies"):
        self.policies_dir = policies_dir
        self.knowledge_base = []
        self.load_and_embed_policies()

    def load_and_embed_policies(self):
        print("Indexing policy vault documents into vector arrays...")
        if not os.path.exists(self.policies_dir):
            print(f"Error: Directory '{self.policies_dir}' does not exist.")
            return

        for filename in os.listdir(self.policies_dir):
            if filename.endswith(".txt"):
                file_path = os.path.join(self.policies_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    
                print(f"-> Generating embeddings for {filename}...")
                embedding = get_embedding(content)
                
                self.knowledge_base.append({
                    "source": filename,
                    "text": content,
                    "vector": embedding
                })
        print("Vector database indexing complete!\n")

    def query_relevant_policy(self, flagged_ad_text: str) -> dict:
        """Finds the single most semantically relevant compliance clause."""
        if not self.knowledge_base:
            return {"text": "No policy indexed.", "similarity": 0.0}

        query_vector = get_embedding(flagged_ad_text)
        best_match = None
        highest_score = -1.0

        for item in self.knowledge_base:
            score = compute_cosine_similarity(query_vector, item["vector"])
            if score > highest_score:
                highest_score = score
                best_match = item

        return {
            "source": best_match["source"],
            "policy_text": best_match["text"],
            "similarity_score": highest_score
        }

if __name__ == "__main__":
    # Test our local vector lookup independently
    test_ad = "Melt 20lbs in two days using our secret capsule!"
    vault = PolicyVaultRAG()
    result = vault.query_relevant_policy(test_ad)
    
    print(f"Test Query: '{test_ad}'")
    print(f"Matched Source: {result['source']} (Score: {result['similarity_score']:.4f})")
    print(f"Extracted Rule Context:\n{result['policy_text']}")