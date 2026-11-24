
from typing import List, Dict, Any

from app.rag.embeddings import EmbeddingGenerator
from app.rag.vector_store import FaissVectorStore


class DocumentRetriever:

    def __init__(self, vector_store: FaissVectorStore):

        self.vector_store = vector_store
        self.embedding_generator = EmbeddingGenerator()

    def retrieve(
        self,
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:

        if not query.strip():
            raise ValueError("Query cannot be empty.")

        # Generate query embedding
        query_embedding = (
            self.embedding_generator.generate_single_embedding(
                query
            )
        )

        # Search FAISS
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k
        )

        return results
