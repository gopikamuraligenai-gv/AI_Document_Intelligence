
from pathlib import Path

from app.grammar.document_grammar import DocumentGrammarAnalyzer
from app.grammar.docx_corrector import DocxCorrector


def main():

    analyzer = DocumentGrammarAnalyzer()
    corrector = DocxCorrector()

    try:

        project_root = Path(__file__).resolve().parent.parent

        original_file = (
            project_root
            / "documents"
            / "reference_project.docx"
        )

        print("\n========== DOCX CORRECTION TEST ==========\n")

        # Step 1: Analyze document
        result = analyzer.analyze_document(
            str(original_file)
        )

        print("Original Document:", result["file_name"])

        print("Total Grammar Errors:", result["total_errors"])

        # Step 2: Save corrected document
        output_path = corrector.save_corrected_document(
            result["corrected_text"],
            original_file
        )

        print("\nCorrected DOCX generated successfully!")

        print("Output Path:", output_path)

        # Step 3: Verify generated document
        if Path(output_path).exists():

            verification = Document(output_path)

            print("\nVerification: PASSED")

            print(
                "Generated Paragraphs:",
                len(verification.paragraphs)
            )

    except Exception as error:

        print("\nError:", error)

    finally:

        analyzer.close()


if __name__ == "__main__":
    from docx import Document
    main()
