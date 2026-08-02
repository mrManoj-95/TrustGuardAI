import os
import numpy as np
from google import genai
from rank_bm25 import BM25Okapi

client = genai.Client()

def get_embedding(text: str) -> list:
    """Generates a text embedding vector using Gemini's native model."""
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text
    )
    return response.embeddings[0].values

def compute_cosine_similarity(v1, v2) -> float:
    """Calculates semantic similarity between two vectors."""
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    return dot_product / (norm_v1 * norm_v2)

class PolicyVaultRAG:
    def __init__(self, policies_dir="policies"):
        self.policies_dir = policies_dir
        self.knowledge_base = []
        self.bm25 = None
        self.load_and_embed_policies()

    def load_and_embed_policies(self):
        print("Indexing policy vault documents into Dense (Vector) and Sparse (BM25) arrays...")
        if not os.path.exists(self.policies_dir):
            print(f"Error: Directory '{self.policies_dir}' does not exist.")
            return

        corpus_tokens = []
        for filename in os.listdir(self.policies_dir):
            if filename.endswith(".txt"):
                file_path = os.path.join(self.policies_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    
                print(f"-> Indexing {filename}...")
                embedding = get_embedding(content)
                
                # Tokenize text for BM25 Sparse Search
                tokens = content.lower().split()
                corpus_tokens.append(tokens)
                
                self.knowledge_base.append({
                    "source": filename,
                    "text": content,
                    "vector": embedding
                })

        # Initialize Sparse BM25 Index
        self.bm25 = BM25Okapi(corpus_tokens)
        print("Hybrid Search Indexing complete!\n")

    def query_relevant_policy(self, flagged_ad_text: str, alpha: float = 0.5) -> dict:
        """
        Executes HYBRID SEARCH combining Dense Vector Search + Sparse BM25 Search.
        alpha = weight factor (0.5 means equal weight to Vector and BM25 scores).
        """
        if not self.knowledge_base:
            return {"text": "No policy indexed.", "similarity": 0.0}

        # 1. DENSE SEARCH (Vector Cosine Similarity)
        query_vector = get_embedding(flagged_ad_text)
        vector_scores = []
        for item in self.knowledge_base:
            score = compute_cosine_similarity(query_vector, item["vector"])
            vector_scores.append(score)

        # Normalize vector scores (0 to 1 range)
        max_v = max(vector_scores) if max(vector_scores) > 0 else 1
        norm_vector_scores = [v / max_v for v in vector_scores]

        # 2. SPARSE SEARCH (BM25 Keyword Matching)
        query_tokens = flagged_ad_text.lower().split()
        bm25_scores = self.bm25.get_scores(query_tokens)
        
        # Normalize BM25 scores (0 to 1 range)
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
        norm_bm25_scores = [b / max_bm25 for b in bm25_scores]

        # 3. HYBRID FUSION (Reciprocal Score Combination)
        hybrid_results = []
        for idx, item in enumerate(self.knowledge_base):
            # Combine scores using alpha weighting
            final_score = (alpha * norm_vector_scores[idx]) + ((1 - alpha) * norm_bm25_scores[idx])
            hybrid_results.append({
                "source": item["source"],
                "policy_text": item["text"],
                "dense_score": norm_vector_scores[idx],
                "sparse_score": norm_bm25_scores[idx],
                "hybrid_score": final_score
            })

        # Sort by final hybrid score descending
        hybrid_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        best_match = hybrid_results[0]

        return {
            "source": best_match["source"],
            "policy_text": best_match["policy_text"],
            "similarity_score": best_match["hybrid_score"]
        }

if __name__ == "__main__":
    # Test query containing an exact policy code (BM25 will catch this) + semantic meaning
    test_ad = "POL-FIN-101: Get rich quick with our trading bot!"
    vault = PolicyVaultRAG()
    result = vault.query_relevant_policy(test_ad)
    
    print(f"Test Query: '{test_ad}'")
    print(f"Matched Source: {result['source']} (Hybrid Score: {result['similarity_score']:.4f})")
    print(f"Extracted Rule Context:\n{result['policy_text']}")