
from pathlib import Path
from typing import List, Dict, Any
import json

import faiss
import numpy as np


class FaissVectorStore:
    """
    Store and retrieve document embeddings using FAISS.

    Embeddings are normalized, so IndexFlatIP performs
    cosine-similarity search.
    """

    def __init__(self, dimension: int):
        if dimension <= 0:
            raise ValueError("Embedding dimension must be positive.")

        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.metadata: List[Dict[str, Any]] = []

    def add_embeddings(
        self,
        embeddings: np.ndarray,
        chunks: List[Dict[str, Any]]
    ) -> None:

        if len(chunks) == 0:
            raise ValueError("No document chunks provided.")

        embeddings = np.asarray(embeddings, dtype="float32")

        if embeddings.ndim != 2:
            raise ValueError("Embeddings must be a 2D array.")

        if embeddings.shape[1] != self.dimension:
            raise ValueError("Embedding dimension mismatch.")

        if embeddings.shape[0] != len(chunks):
            raise ValueError(
                "Number of embeddings must match number of chunks."
            )

        if not np.isfinite(embeddings).all():
            raise ValueError("Embeddings contain invalid values.")

        embeddings = np.ascontiguousarray(embeddings)

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)

        # Add embeddings to FAISS index
        self.index.add(embeddings)

        # Store corresponding metadata
        self.metadata.extend(chunks)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:

        if self.index.ntotal == 0:
            raise ValueError("FAISS index is empty.")

        if top_k <= 0:
            raise ValueError("top_k must be positive.")

        query_embedding = np.asarray(
            query_embedding,
            dtype="float32"
        )

        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        if query_embedding.ndim != 2:
            raise ValueError("Query embedding must be a 2D array.")

        if query_embedding.shape[0] != 1:
            raise ValueError("Only one query embedding is supported.")

        if query_embedding.shape[1] != self.dimension:
            raise ValueError("Query embedding dimension mismatch.")

        if not np.isfinite(query_embedding).all():
            raise ValueError("Query embedding contains invalid values.")

        query_embedding = np.ascontiguousarray(query_embedding)

        faiss.normalize_L2(query_embedding)

        # Search relevant document chunks
        scores, indices = self.index.search(
            query_embedding,
            min(top_k, self.index.ntotal)
        )

        results = []

        for score, index_id in zip(scores[0], indices[0]):

            if index_id == -1:
                continue

            result = self.metadata[index_id].copy()

            result["similarity_score"] = float(score)

            results.append(result)

        return results

    def save(self, directory: str = "faiss_index") -> None:

        save_path = Path(directory)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(
            self.index,
            str(save_path / "index.faiss")
        )

        # Save metadata
        with open(
            save_path / "metadata.json",
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.metadata,
                file,
                ensure_ascii=False,
                indent=4
            )

        print(f"FAISS index saved successfully: {save_path}")

    @classmethod
    def load(cls, directory: str = "faiss_index"):

        load_path = Path(directory)

        index_file = load_path / "index.faiss"
        metadata_file = load_path / "metadata.json"

        if not index_file.exists():
            raise FileNotFoundError(index_file)

        if not metadata_file.exists():
            raise FileNotFoundError(metadata_file)

        # Load FAISS index
        index = faiss.read_index(str(index_file))

        # Create vector store
        store = cls(index.d)

        store.index = index

        # Load metadata
        with open(
            metadata_file,
            "r",
            encoding="utf-8"
        ) as file:

            store.metadata = json.load(file)

        if store.index.ntotal != len(store.metadata):
            raise ValueError(
                "FAISS index and metadata count mismatch."
            )

        return store
