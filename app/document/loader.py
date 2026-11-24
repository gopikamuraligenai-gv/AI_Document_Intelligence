
from pathlib import Path
from typing import Dict, Any

import pymupdf
from docx import Document


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def load_document(file_path: str) -> Dict[str, Any]:
    """
    Load PDF, DOCX, or TXT documents and extract their text.
    """

    path = Path(file_path)

    # Check whether file exists
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    # Check supported file format
    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format: {extension}. "
            "Supported formats: PDF, DOCX, TXT"
        )

    # Extract text based on file format
    if extension == ".pdf":
        text = extract_pdf(path)

    elif extension == ".docx":
        text = extract_docx(path)

    elif extension == ".txt":
        text = extract_txt(path)

    # Validate extracted content
    if not text.strip():
        raise ValueError("The document contains no extractable text.")

    # Return document information
    return {
        "file_name": path.name,
        "file_type": extension,
        "file_path": str(path.resolve()),
        "text": text,
        "word_count": len(text.split()),
        "character_count": len(text)
    }


def extract_pdf(path: Path) -> str:
    """
    Extract text from PDF files using PyMuPDF.
    """

    text = ""

    with pymupdf.open(path) as pdf:

        for page_number, page in enumerate(pdf, start=1):

            page_text = page.get_text()

            text += f"\n--- Page {page_number} ---\n"
            text += page_text

    return text


def extract_docx(path: Path) -> str:
    """
    Extract text from DOCX files, including tables.
    """

    document = Document(path)

    extracted_text = []

    # Extract paragraphs
    for paragraph in document.paragraphs:

        if paragraph.text.strip():
            extracted_text.append(paragraph.text)

    # Extract tables
    for table in document.tables:

        for row in table.rows:

            row_text = " | ".join(
                cell.text.strip() for cell in row.cells
            )

            if row_text.strip():
                extracted_text.append(row_text)

    return "\n".join(extracted_text)


def extract_txt(path: Path) -> str:
    """
    Extract text from TXT files.
    """

    return path.read_text(encoding="utf-8-sig")


if __name__ == "__main__":

    print("Document Loader Module")
    print("----------------------")

    sample_path = Path("documents/reference_project.docx")

    if sample_path.exists():

        result = load_document(str(sample_path))

        print("File name:", result["file_name"])
        print("File type:", result["file_type"])
        print("Word count:", result["word_count"])
        print("Character count:", result["character_count"])

        print("\nExtracted Text Preview:")
        print(result["text"][:1000])

    else:

        print("Sample document not found.")
        print("Place a PDF, DOCX, or TXT file inside the documents folder.")
