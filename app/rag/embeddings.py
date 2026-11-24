
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingGenerator:

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        print(f"Loading embedding model: {model_name}")

        self.model = SentenceTransformer(model_name)

        self.dimension = self.model.get_sentence_embedding_dimension()

        print("Embedding model loaded successfully.")
        print(f"Embedding dimension: {self.dimension}")

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:

        if not texts:
            raise ValueError("Text list cannot be empty.")

        if not all(isinstance(text, str) and text.strip() for text in texts):
            raise ValueError("All texts must be non-empty strings.")

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        return embeddings.astype("float32")

    def generate_single_embedding(self, text: str) -> np.ndarray:

        if not isinstance(text, str) or not text.strip():
            raise ValueError("Text cannot be empty.")

        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        return embedding.astype("float32")


if __name__ == "__main__":

    generator = EmbeddingGenerator()

    sample_texts = [
        "Artificial intelligence helps automate document processing.",
        "Grammar checking identifies spelling and sentence errors.",
        "Retrieval augmented generation retrieves relevant document information."
    ]

    vectors = generator.generate_embeddings(sample_texts)

    print("\nEmbedding Results")
    print("-----------------")
    print("Number of texts:", len(sample_texts))
    print("Embedding shape:", vectors.shape)
    print("Embedding dimension:", generator.dimension)
    print("Data type:", vectors.dtype)
