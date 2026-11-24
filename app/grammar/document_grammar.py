
from pathlib import Path

from app.grammar.grammar_checker import GrammarChecker
from app.document_processing.docx_extractor import extract_docx
from app.llm.ollama_client import OllamaClient


class DocumentGrammarAnalyzer:

    def __init__(self):
        self.grammar_checker = GrammarChecker()
        self.ollama_client = OllamaClient(
            model="llama3.2:latest"
        )

    def analyze_document(self, file_path):

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Document not found: {file_path}"
            )

        if file_path.suffix.lower() != ".docx":
            raise ValueError("Only DOCX documents are supported.")

        # Extract document text
        extracted_text = extract_docx(str(file_path))

        if not extracted_text.strip():
            raise ValueError("The document contains no readable text.")

        # LanguageTool grammar analysis
        grammar_errors = self.grammar_checker.check_grammar(
            extracted_text
        )

        # Llama AI grammar correction
        ai_corrected_text = self.ollama_client.correct_grammar(
            extracted_text
        )

        return {
            "file_name": file_path.name,
            "extracted_text": extracted_text,
            "total_errors": len(grammar_errors),
            "grammar_errors": grammar_errors,
            "ai_corrected_text": ai_corrected_text
        }

    def close(self):
        self.grammar_checker.close()
