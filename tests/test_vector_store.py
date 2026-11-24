
import numpy as np

from app.rag.vector_store import FaissVectorStore


def test_vector_store():

    # Sample embeddings (3 documents, 3 dimensions)
    embeddings = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ], dtype="float32")

    chunks = [
        {"text": "Loan agreement document"},
        {"text": "Financial risk assessment"},
        {"text": "Investment banking report"}
    ]

    # Initialize FAISS
    store = FaissVectorStore(dimension=3)

    # Add embeddings
    store.add_embeddings(embeddings, chunks)

    # Search
    query = np.array([1.0, 0.0, 0.0], dtype="float32")

    results = store.search(query, top_k=2)

    print("\nSearch Results:")

    for result in results:
        print(result)

    # Save index
    store.save("faiss_index")

    # Load index
    loaded_store = FaissVectorStore.load("faiss_index")

    print("\nLoaded index successfully!")
    print("Total vectors:", loaded_store.index.ntotal)


if __name__ == "__main__":
    test_vector_store()
