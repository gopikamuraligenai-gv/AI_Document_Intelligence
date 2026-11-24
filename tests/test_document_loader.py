
from pathlib import Path

from app.document.loader import load_document


BASE_DIR = Path(__file__).resolve().parents[1]
DOCUMENT_DIR = BASE_DIR / "documents"


def main():
    files = list(DOCUMENT_DIR.glob("*.pdf"))
    files += list(DOCUMENT_DIR.glob("*.docx"))
    files += list(DOCUMENT_DIR.glob("*.txt"))

    if not files:
        print("No documents found in the documents folder.")
        return

    for file_path in files:
        print("\nProcessing:", file_path.name)

        result = load_document(str(file_path))

        print("File type:", result["file_type"])
        print("Word count:", result["word_count"])
        print("Character count:", result["character_count"])

        print("\nExtracted text preview:")
        print(result["text"][:1000])

        print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
