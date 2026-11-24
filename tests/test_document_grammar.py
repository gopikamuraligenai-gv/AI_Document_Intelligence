
from pathlib import Path

from app.grammar.document_grammar import DocumentGrammarAnalyzer


def main():

    analyzer = DocumentGrammarAnalyzer()

    try:
        # Exact DOCX file path
        project_root = Path(__file__).resolve().parent.parent

        file_path = project_root / "documents" / "reference_project.docx"

        print("\n========== DOCUMENT GRAMMAR ANALYSIS ==========\n")

        print("Document:", file_path.name)

        result = analyzer.analyze_document(str(file_path))

        print("\nFile Name:", result["file_name"])

        print("\nTotal Grammar Errors:", result["total_errors"])

        print("\n========== GRAMMAR ERRORS ==========\n")

        for index, error in enumerate(
            result["grammar_errors"], start=1
        ):
            print(f"\nError {index}")
            print("Incorrect Text:", error["wrong_text"])
            print("Message:", error["message"])
            print("Suggestions:", error["suggestions"])

        print("\n========== CORRECTED DOCUMENT ==========\n")

        print(result["corrected_text"])

    except Exception as error:
        print("\nError:", error)

    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
