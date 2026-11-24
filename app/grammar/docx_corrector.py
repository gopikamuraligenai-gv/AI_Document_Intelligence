
from pathlib import Path
from docx import Document


class DocxCorrector:

    def save_corrected_document(
        self,
        corrected_text,
        original_file_path
    ):

        original_path = Path(original_file_path)

        if not original_path.exists():
            raise FileNotFoundError(
                f"Document not found: {original_path}"
            )

        if not corrected_text.strip():
            raise ValueError("Corrected text is empty.")

        output_folder = (
            original_path.parent / "corrected_documents"
        )

        output_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        output_path = output_folder / (
            f"{original_path.stem}_corrected.docx"
        )

        document = Document()

        document.add_heading(
            "Corrected Document",
            level=1
        )

        document.add_paragraph(
            f"Original File: {original_path.name}"
        )

        for paragraph in corrected_text.splitlines():

            document.add_paragraph(paragraph)

        document.save(output_path)

        return str(output_path)
