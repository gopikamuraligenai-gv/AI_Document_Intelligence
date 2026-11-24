
from pathlib import Path

from app.document.loader import load_document
from app.document.splitter import create_document_chunks
from app.rag.embeddings import EmbeddingGenerator
from app.rag.vector_store import FaissVectorStore


# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# DOCX document path
DOCUMENT_PATH = BASE_DIR / "documents" / "reference_project.docx"

# FAISS storage directory
FAISS_PATH = BASE_DIR / "faiss_index"


def run_retrieval_pipeline():

    print("\n========== DOCUMENT RETRIEVAL PIPELINE ==========\n")

    # STEP 1: Load DOCX document
    print("Step 1: Loading DOCX document...")

    if not DOCUMENT_PATH.exists():
        raise FileNotFoundError(
            f"Document not found: {DOCUMENT_PATH}"
        )

    document = load_document(str(DOCUMENT_PATH))

    print("Document loaded successfully!")

    # STEP 2: Split document into chunks
    print("\nStep 2: Creating document chunks...")

    chunks = create_document_chunks(document)

    if not chunks:
        raise ValueError("No document chunks generated.")

    print("Total chunks:", len(chunks))

    # STEP 3: Extract chunk text
    print("\nStep 3: Extracting chunk text...")

    chunk_texts = [
        chunk["chunk_text"]
        for chunk in chunks
    ]

    print("Total text chunks:", len(chunk_texts))

    # STEP 4: Generate embeddings
    print("\nStep 4: Generating embeddings...")

    embedding_generator = EmbeddingGenerator()

    embeddings = embedding_generator.generate_embeddings(
        chunk_texts
    )

    print("Embeddings generated successfully!")
    print("Embedding shape:", embeddings.shape)

    # STEP 5: Initialize FAISS
    print("\nStep 5: Initializing FAISS vector store...")

    vector_store = FaissVectorStore(
        dimension=embedding_generator.dimension
    )

    # STEP 6: Store embeddings and metadata
    print("\nStep 6: Adding embeddings to FAISS...")

    vector_store.add_embeddings(
        embeddings=embeddings,
        chunks=chunks
    )

    print("Vectors stored:", vector_store.index.ntotal)

    # STEP 7: Save FAISS index
    print("\nStep 7: Saving FAISS index...")

    vector_store.save(str(FAISS_PATH))

    # STEP 8: User query
    print("\nStep 8: Performing similarity search...")

    query = "What is the main purpose of this document?"

    print("User Query:", query)

    query_embedding = (
        embedding_generator.generate_single_embedding(query)
    )

    # STEP 9: Retrieve relevant chunks
    results = vector_store.search(
        query_embedding=query_embedding,
        top_k=3
    )

    # STEP 10: Display results
    print("\n========== RETRIEVED DOCUMENT CHUNKS ==========\n")

    for index, result in enumerate(results, start=1):

        print(f"\nResult {index}")

        print("Chunk ID:", result.get("chunk_id"))

        print("File Name:", result.get("file_name"))

        print(
            "Similarity Score:",
            round(result["similarity_score"], 4)
        )

        print("\nRetrieved Text:")

        print(result["chunk_text"])

        print("-" * 60)

    # STEP 11: Load saved FAISS index
    print("\nStep 11: Testing saved FAISS index...")

    loaded_store = FaissVectorStore.load(str(FAISS_PATH))

    print("FAISS index loaded successfully!")

    print("Total stored vectors:", loaded_store.index.ntotal)

    print("\n========== PIPELINE COMPLETED ==========\n")


if __name__ == "__main__":
    run_retrieval_pipeline()
