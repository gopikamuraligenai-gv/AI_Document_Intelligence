
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.grammar.document_grammar import DocumentGrammarAnalyzer


app = FastAPI(
    title="AI Document Intelligence API",
    description="Document grammar checking and AI correction using Llama 3.2",
    version="1.0.0"
)


UPLOAD_DIR = Path("documents/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
def home():
    return {
        "message": "AI Document Intelligence API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


def convert_grammar_errors(errors):
    """
    Convert LanguageTool error objects or dictionaries
    into JSON-compatible dictionaries.
    """

    converted_errors = []

    for error in errors:

        if isinstance(error, dict):
            get_value = error.get
        else:
            get_value = lambda key, default=None: getattr(
                error, key, default
            )

        converted_errors.append({
            "rule_id": get_value("ruleId"),
            "message": get_value("message"),
            "offset": get_value("offset"),
            "error_length": get_value(
                "error_length",
                get_value("errorLength")
            ),
            "replacements": get_value("replacements", []),
            "context": get_value("context")
        })

    return converted_errors


@app.post("/analyze-document")
async def analyze_document(file: UploadFile = File(...)):

    if not file.filename or Path(file.filename).suffix.lower() != ".docx":
        raise HTTPException(
            status_code=400,
            detail="Only DOCX files are supported."
        )

    file_path = UPLOAD_DIR / f"{uuid4().hex}.docx"

    try:
        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded document is empty."
            )

        file_path.write_bytes(content)

        analyzer = DocumentGrammarAnalyzer()

        try:
            result = analyzer.analyze_document(file_path)

            return {
                "file_name": file.filename,
                "total_errors": result["total_errors"],
                "grammar_errors": convert_grammar_errors(
                    result["grammar_errors"]
                ),
                "ai_corrected_text": result["ai_corrected_text"]
            }

        finally:
            analyzer.close()

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Document analysis failed: {str(error)}"
        ) from error

    finally:
        if file_path.exists():
            file_path.unlink()
