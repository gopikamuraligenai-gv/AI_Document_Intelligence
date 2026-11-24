
from pathlib import Path

from app.document.loader import load_document
from app.document.splitter import create_document_chunks
from app.rag.embeddings import EmbeddingGenerator


BASE_DIR = Path(__file__).resolve().parents[1]
DOCUMENT_DIR = BASE_DIR / "documents"


def main():

    files = []

    for extension in ["*.pdf", "*.docx", "*.txt"]:
        files.extend(DOCUMENT_DIR.glob(extension))

    if not files:
        print("No documents found in documents folder.")
        return

    # Load first available document
    document = load_document(str(files[0]))

    print("\nDocument:", document["file_name"])

    # Split document
    chunks = create_document_chunks(
        document=document,
        chunk_size=800,
        chunk_overlap=100
    )

    print("Total chunks:", len(chunks))

    # Extract chunk text
    chunk_texts = [
        chunk["chunk_text"]
        for chunk in chunks
    ]

    # Generate embeddings
    generator = EmbeddingGenerator()

    embeddings = generator.generate_embeddings(chunk_texts)

    print("\nEmbedding Evaluation")
    print("--------------------")

    print("Number of chunks:", len(chunk_texts))
    print("Embedding shape:", embeddings.shape)
    print("Embedding dimensions:", embeddings.shape[1])
    print("Data type:", embeddings.dtype)

    print("\nFirst embedding preview:")
    print(embeddings[0][:10])


if __name__ == "__main__":
    main()
