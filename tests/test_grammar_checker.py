
from pathlib import Path

from app.grammar.document_grammar import DocumentGrammarAnalyzer


def test_document_grammar():

    project_root = Path(__file__).resolve().parent.parent

    file_path = (
        project_root
        / "documents"
        / "reference_project.docx"
    )

    analyzer = DocumentGrammarAnalyzer()

    try:
        result = analyzer.analyze_document(file_path)

        print("\n========== DOCUMENT GRAMMAR ANALYSIS ==========")

        print("\nFile Name:")
        print(result["file_name"])

        print("\nTotal Grammar Errors:")
        print(result["total_errors"])

        print("\nAI Corrected Document:")
        print(result["ai_corrected_text"])

        assert result["ai_corrected_text"].strip()

        print("\nDOCUMENT GRAMMAR TEST: PASSED")

    finally:
        analyzer.close()


if __name__ == "__main__":
    test_document_grammar()
