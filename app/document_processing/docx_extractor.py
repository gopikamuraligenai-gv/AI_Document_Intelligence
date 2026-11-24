
from docx import Document


def extract_docx(file_path):

    document = Document(file_path)

    extracted_text = []

    # Extract paragraphs
    for paragraph in document.paragraphs:

        if paragraph.text.strip():
            extracted_text.append(paragraph.text)

    # Extract tables
    for table in document.tables:

        for row in table.rows:

            row_text = []

            for cell in row.cells:
                row_text.append(cell.text.strip())

            extracted_text.append(" | ".join(row_text))

    return "\n".join(extracted_text)
