
from pathlib import Path

from app.document.loader import load_document
from app.document.splitter import create_document_chunks


BASE_DIR = Path(__file__).resolve().parents[1]
DOCUMENT_DIR = BASE_DIR / "documents"


def main():

    files = []

    for extension in ["*.pdf", "*.docx", "*.txt"]:
        files.extend(DOCUMENT_DIR.glob(extension))

    if not files:
        print("No documents found in documents folder.")
        return

    for file_path in files:

        print("\nProcessing:", file_path.name)

        document = load_document(str(file_path))

        chunks = create_document_chunks(
            document=document,
            chunk_size=800,
            chunk_overlap=100
        )

        print("Total chunks:", len(chunks))

        for chunk in chunks[:3]:
            print("\nChunk ID:", chunk["chunk_id"])
            print("Word count:", chunk["word_count"])
            print("Character count:", chunk["character_count"])
            print("Content:")
            print(chunk["chunk_text"])

        print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
