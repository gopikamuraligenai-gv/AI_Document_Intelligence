from __future__ import annotations

import csv
import io
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

# Optional document libraries
try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    from docx import Document
except Exception:
    Document = None

try:
    from pptx import Presentation
except Exception:
    Presentation = None

try:
    from openpyxl import load_workbook
except Exception:
    load_workbook = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
except Exception:
    A4 = SimpleDocTemplate = Paragraph = Spacer = getSampleStyleSheet = None

try:
    import language_tool_python
except Exception:
    language_tool_python = None


# ----------------------------- Paths / settings -----------------------------

APP_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = APP_DIR / "uploads"
DB_PATH = APP_DIR / "documind.db"
UPLOAD_DIR.mkdir(exist_ok=True)

SUPPORTED_TYPES = ["pdf", "docx", "txt", "md", "csv", "xlsx", "pptx"]


# ----------------------------- Database -------------------------------------

@contextmanager
def db_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create the current schema and safely add columns to older databases."""
    with db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_type TEXT,
                stored_path TEXT,
                original_text TEXT,
                corrected_text TEXT,
                issue_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Completed',
                created_at TEXT NOT NULL
            )
        """)

        existing_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(documents)").fetchall()
        }

        migrations = {
            "file_type": "ALTER TABLE documents ADD COLUMN file_type TEXT",
            "stored_path": "ALTER TABLE documents ADD COLUMN stored_path TEXT",
            "original_text": "ALTER TABLE documents ADD COLUMN original_text TEXT",
            "corrected_text": "ALTER TABLE documents ADD COLUMN corrected_text TEXT",
            "issue_count": "ALTER TABLE documents ADD COLUMN issue_count INTEGER DEFAULT 0",
            "status": "ALTER TABLE documents ADD COLUMN status TEXT DEFAULT 'Completed'",
            "created_at": "ALTER TABLE documents ADD COLUMN created_at TEXT",
        }

        for column, sql in migrations.items():
            if column not in existing_columns:
                conn.execute(sql)

        conn.execute("""
            UPDATE documents
            SET issue_count = 0
            WHERE issue_count IS NULL
        """)
        conn.execute("""
            UPDATE documents
            SET created_at = ?
            WHERE created_at IS NULL OR created_at = ''
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))


def save_document(filename, file_type, stored_path, original_text,
                  corrected_text, issue_count, status="Completed"):
    with db_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO documents
            (filename, file_type, stored_path, original_text, corrected_text,
             issue_count, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            filename, file_type, str(stored_path), original_text,
            corrected_text, int(issue_count), status,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        return cursor.lastrowid


def get_documents():
    with db_connection() as conn:
        return conn.execute(
            "SELECT * FROM documents ORDER BY id DESC"
        ).fetchall()


def get_document(document_id):
    with db_connection() as conn:
        return conn.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()


def delete_document(document_id):
    record = get_document(document_id)
    with db_connection() as conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))

    if record and record["stored_path"]:
        try:
            path = Path(record["stored_path"])
            if path.exists() and path.is_file():
                path.unlink()
        except OSError:
            pass


def clear_history():
    records = get_documents()
    with db_connection() as conn:
        conn.execute("DELETE FROM documents")

    for record in records:
        if record["stored_path"]:
            try:
                path = Path(record["stored_path"])
                if path.exists() and path.is_file():
                    path.unlink()
            except OSError:
                pass


# ----------------------------- Document extraction -------------------------

def extract_text(uploaded_file, extension):
    raw = uploaded_file.getvalue()

    if extension == "txt" or extension == "md":
        return raw.decode("utf-8", errors="replace")

    if extension == "pdf":
        if PdfReader is None:
            raise RuntimeError("PDF support is unavailable. Install pypdf.")
        reader = PdfReader(io.BytesIO(raw))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)

    if extension == "docx":
        if Document is None:
            raise RuntimeError("DOCX support is unavailable. Install python-docx.")
        doc = Document(io.BytesIO(raw))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                paragraphs.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(paragraphs)

    if extension == "pptx":
        if Presentation is None:
            raise RuntimeError("PPTX support is unavailable. Install python-pptx.")
        presentation = Presentation(io.BytesIO(raw))
        parts = []
        for slide_number, slide in enumerate(presentation.slides, start=1):
            parts.append(f"Slide {slide_number}")
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    parts.append(shape.text)
        return "\n".join(parts)

    if extension == "xlsx":
        if load_workbook is None:
            raise RuntimeError("Excel support is unavailable. Install openpyxl.")
        workbook = load_workbook(io.BytesIO(raw), data_only=True, read_only=True)
        parts = []
        for sheet in workbook.worksheets:
            parts.append(f"Sheet: {sheet.title}")
            for row in sheet.iter_rows(values_only=True):
                values = [str(value) for value in row if value is not None]
                if values:
                    parts.append(" | ".join(values))
        workbook.close()
        return "\n".join(parts)

    if extension == "csv":
        decoded = raw.decode("utf-8-sig", errors="replace")
        rows = csv.reader(io.StringIO(decoded))
        return "\n".join(" | ".join(row) for row in rows)

    raise ValueError(f"Unsupported file format: .{extension}")


# ----------------------------- Proofreading ---------------------------------

def proofread_text(text):
    if language_tool_python is None:
        raise RuntimeError(
            "language-tool-python is not installed. Run: "
            "python -m pip install language-tool-python"
        )

    tool = None
    try:
        tool = language_tool_python.LanguageTool("en-US")
        matches = tool.check(text)
        corrected_text = language_tool_python.utils.correct(text, matches)

        issues = []
        for match in matches:
            offset = int(getattr(match, "offset", 0) or 0)
            error_length = int(
                getattr(match, "errorLength",
                        getattr(match, "error_length", 0)) or 0
            )
            suggestions = getattr(match, "replacements", []) or []
            category_obj = getattr(match, "category", None)
            category = getattr(category_obj, "name", None) or str(category_obj or "Grammar")

            issues.append({
                "offset": offset,
                "length": error_length,
                "message": getattr(match, "message", "") or "",
                "original": text[offset:offset + error_length],
                "suggestions": list(suggestions),
                "category": category,
                "rule": getattr(getattr(match, "rule", None), "id", "") or ""
            })

        return corrected_text, issues
    finally:
        if tool is not None:
            try:
                tool.close()
            except Exception:
                pass


# ----------------------------- Export helpers -------------------------------

def safe_stem(filename):
    return Path(filename).stem or "proofread_document"


def download_section(corrected_text, filename, key_prefix):
    st.markdown("**Download corrected document**")
    txt_name = f"{safe_stem(filename)}_corrected.txt"
    st.download_button(
        "Download TXT",
        data=corrected_text.encode("utf-8"),
        file_name=txt_name,
        mime="text/plain",
        key=f"{key_prefix}_txt"
    )

    if Document is not None:
        doc = Document()
        for paragraph in corrected_text.splitlines():
            doc.add_paragraph(paragraph)
        buffer = io.BytesIO()
        doc.save(buffer)
        st.download_button(
            "Download DOCX",
            data=buffer.getvalue(),
            file_name=f"{safe_stem(filename)}_corrected.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"{key_prefix}_docx"
        )

    if all(item is not None for item in
           [SimpleDocTemplate, Paragraph, Spacer, getSampleStyleSheet, A4]):
        buffer = io.BytesIO()
        pdf = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        for paragraph in corrected_text.splitlines():
            story.append(Paragraph(paragraph.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") or " ", styles["BodyText"]))
            story.append(Spacer(1, 6))
        pdf.build(story)
        st.download_button(
            "Download PDF",
            data=buffer.getvalue(),
            file_name=f"{safe_stem(filename)}_corrected.pdf",
            mime="application/pdf",
            key=f"{key_prefix}_pdf"
        )


# ----------------------------- UI helpers -----------------------------------

def apply_styles():
    st.markdown("""
    <style>
    :root {
        --dm-accent: #5267df;
        --dm-accent-soft: rgba(82, 103, 223, .10);
        --dm-border: rgba(128, 128, 128, .22);
    }
    .stApp { background: #f6f8fc; }
    [data-testid="stHeader"] { background: rgba(246,248,252,.88); }
    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 3rem;
        max-width: 1320px;
    }
    [data-testid="stSidebar"] {
        background: #101a32;
    }
    [data-testid="stSidebar"] * {
        color: #f4f6ff;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        padding: .35rem .45rem;
        border-radius: 8px;
    }
    .section-title {
        font-size: 1.85rem;
        line-height: 1.2;
        font-weight: 750;
        letter-spacing: -.035em;
        color: #17233f;
        margin-bottom: .35rem;

    }
    
    .dashboard-heading {
    display: block;
    width: 100%;
    box-sizing: border-box;
    background: linear-gradient(120deg, #17264a, #405bb5);
    color: #ffffff !important;
    padding: 22px 28px;
    border-radius: 14px;
    font-size: 30px;
    font-weight: 750;
    line-height: 1.3;
    margin-bottom: 20px;
    text-align: left;
}

    .hero {
        background: linear-gradient(120deg, #17264a 0%, #354e9c 100%);
        color: white;
        padding: 1.55rem 1.7rem;
        border-radius: 18px;
        margin: .7rem 0 1.25rem 0;
        box-shadow: 0 12px 28px rgba(30, 48, 100, .13);
    }
    .hero h3 { color: white; margin: 0 0 .4rem 0; }
    .hero p { color: #e7ebff; margin: 0; font-size: .98rem; }
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid var(--dm-border);
        border-radius: 14px;
        padding: 1rem 1.1rem;
        box-shadow: 0 3px 12px rgba(20,35,70,.035);
    }
    [data-testid="stMetricLabel"] { color: #65718a; }
    [data-testid="stMetricValue"] { color: #182746; }
    .stButton > button, .stDownloadButton > button {
        border-radius: 9px;
        min-height: 2.65rem;
        font-weight: 600;
    }
    .stButton > button[kind="primary"] {
        background: var(--dm-accent);
        border-color: var(--dm-accent);
    }
    [data-testid="stFileUploader"] {
        background: white;
        border: 1px dashed #aab5d0;
        border-radius: 14px;
        padding: .6rem;
    }
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        border: 1px solid var(--dm-border);
        border-radius: 12px;
        overflow: hidden;
    }
    div[data-testid="stExpander"] {
        background: white;
        border: 1px solid var(--dm-border);
        border-radius: 12px;
    }
    .small-muted { color: #69758c; font-size: .88rem; }
    @media (prefers-color-scheme: dark) {
        .section-title { color: inherit; }
        .hero { box-shadow: none; }
    }
    </style>
    """, unsafe_allow_html=True)


def render_issue_list(issues):
    if not issues:
        st.success("No grammar or spelling issues were found.")
        return

    st.markdown("#### Detected issues")
    for index, issue in enumerate(issues, start=1):
        with st.expander(
            f"{index}. {issue['category']} — {issue['message'][:100] or 'Review suggestion'}"
        ):
            st.write("**Original:**", issue["original"] or "(No text captured)")
            st.write("**Explanation:**", issue["message"] or "No explanation provided.")
            suggestions = issue["suggestions"]
            if suggestions:
                st.write("**Suggestions:**", ", ".join(str(s) for s in suggestions[:8]))
            else:
                st.write("**Suggestions:** No automatic suggestion provided.")


# ----------------------------- App start ------------------------------------

st.set_page_config(
    page_title="DocuMind AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)
apply_styles()
init_db()

if "page" not in st.session_state:
    st.session_state.page = "Overview"
if "result" not in st.session_state:
    st.session_state.result = None

with st.sidebar:
    st.markdown("## 📄 DocuMind AI")
    st.caption("Document proofreading workspace")
    page = st.radio(
        "Navigation",
        ["Overview", "Proofread Document", "Document Library", "Settings"],
        key="navigation",
        index=["Overview", "Proofread Document", "Document Library", "Settings"].index(
            st.session_state.page
        ) if st.session_state.page in
        ["Overview", "Proofread Document", "Document Library", "Settings"] else 0
    )
    st.session_state.page = page
    st.divider()
    st.caption("Supported: PDF · DOCX · TXT · MD · CSV · XLSX · PPTX")


# ----------------------------- Overview -------------------------------------

# ----------------------------- Overview -------------------------------------

if page == "Overview":

    st.markdown(
        '<div class="dashboard-heading">'
        'Document Intelligence Dashboard'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="hero">'
        '<h3>Make every document clearer and more professional.</h3>'
        '<p>Proofread files, review writing suggestions, compare versions, '
        'and manage all your documents in one simple workspace.</p>'
        '</div>',
        unsafe_allow_html=True
    )

    records = get_documents()
    total_docs = len(records)
    total_issues = sum(int(r["issue_count"] or 0) for r in records)

    c1, c2, c3 = st.columns(3)

    c1.metric("Documents reviewed", total_docs)
    c2.metric("Issues identified", total_issues)
    c3.metric(
        "Proofreading engine",
        "LanguageTool" if language_tool_python else "Unavailable"
    )

    st.markdown("### Recent Documents")

    if records:
        recent = [{
            "Document": r["filename"],
            "Type": (r["file_type"] or "").upper(),
            "Issues": r["issue_count"] or 0,
            "Reviewed": r["created_at"]
        } for r in records[:5]]

        st.dataframe(
            pd.DataFrame(recent),
            use_container_width=True,
            hide_index=False

        )
    else:
        st.info(
            "Your document history is empty. "
            "Open Proofread Document to get started."
        )

    def go_to_proofread():
        st.session_state["navigation"] = "Proofread Document"

    st.button(
        "Go to Proofread Document",
        type="primary",
        on_click=go_to_proofread
    )


# ----------------------------- Proofread Document ---------------------------

elif page == "Proofread Document":

    st.markdown(
        '<div class="dashboard-heading">Proofread a Document</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Upload your document to check grammar, spelling, "
        "punctuation and writing quality."
    )

    st.markdown(
        """
        <div class="upload-card">
            <h3 style="color:#17233f;">Upload your document</h3>
            <p style="color:#66738c;">
                Select a file from your computer or drag and drop it below.
            </p>
            <p style="color:#66738c;font-size:13px;">
                Supported formats: PDF, DOCX, TXT, MD, CSV, XLSX and PPTX
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(
        "Choose your document",
        type=SUPPORTED_TYPES,
        key="document_uploader"
    )

    if uploaded_file is not None:

        extension = Path(uploaded_file.name).suffix.lower().lstrip(".")
        file_size = len(uploaded_file.getvalue())

        st.success("Document uploaded successfully!")

        st.markdown("### Selected Document")

        file_col1, file_col2, file_col3 = st.columns(3)

        file_col1.markdown("**File name**")
        file_col1.write(uploaded_file.name)

        file_col2.markdown("**File type**")
        file_col2.write(extension.upper())

        file_col3.markdown("**File size**")
        file_col3.write(f"{file_size / 1024:.2f} KB")

        st.divider()

        # Document preview
        with st.expander("Preview Uploaded Document", expanded=True):

            try:
                preview_text = extract_text(uploaded_file, extension)

                if preview_text.strip():

                    st.text_area(
                        "Extracted document content",
                        value=preview_text[:5000],
                        height=250,
                        disabled=True,
                        key=f"preview_{uploaded_file.name}"
                    )

                    if len(preview_text) > 5000:
                        st.caption(
                            "Showing the first 5,000 characters only."
                        )

                else:
                    st.warning(
                        "No readable text found. "
                        "Scanned PDFs require OCR."
                    )

            except Exception as error:
                st.error(f"Document preview failed: {error}")

        st.markdown("### Start Proofreading")

        if st.button(
            "Check Grammar & Proofread",
            type="primary",
            use_container_width=True,
            key="start_proofreading"
        ):

            try:
                with st.spinner(
                    "Extracting text and checking grammar..."
                ):

                    original_text = extract_text(uploaded_file, extension)

                    if not original_text.strip():

                        st.warning(
                            "No readable text was found in this document."
                        )

                    else:

                        corrected_text, issues = proofread_text(
                            original_text
                        )

                        safe_name = Path(uploaded_file.name).name

                        stored_path = UPLOAD_DIR / (
                            datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                            + "_" + safe_name
                        )

                        stored_path.write_bytes(
                            uploaded_file.getvalue()
                        )

                        document_id = save_document(
                            safe_name,
                            extension,
                            stored_path,
                            original_text,
                            corrected_text,
                            len(issues)
                        )

                        st.session_state.result = {
                            "id": document_id,
                            "filename": safe_name,
                            "original": original_text,
                            "corrected": corrected_text,
                            "issues": issues
                        }

                        st.success(
                            "Proofreading completed successfully! "
                            "Your document has been saved."
                        )

            except Exception as error:
                st.error(
                    f"Proofreading could not be completed: {error}"
                )

    # Display proofreading results

    result = st.session_state.get("result")

    if result:

        st.divider()
        st.markdown("### Proofreading Results")

        result_col1, result_col2 = st.columns(2)

        result_col1.metric(
            "Grammar Issues Found",
            len(result["issues"])
        )

        result_col2.metric(
            "Characters Checked",
            len(result["original"])
        )

        tab1, tab2, tab3 = st.tabs([
            "Detected Issues",
            "Original vs Corrected",
            "Corrected Document"
        ])

        with tab1:

            render_issue_list(result["issues"])

        with tab2:

            x, y = st.columns(2)

            with x:
                st.text_area(
                    "Original Document",
                    result["original"],
                    height=350,
                    disabled=True,
                    key=f"original_{result['id']}"
                )

            with y:
                st.text_area(
                    "Corrected Document",
                    result["corrected"],
                    height=350,
                    disabled=True,
                    key=f"corrected_{result['id']}"
                )

        with tab3:

            st.text_area(
                "Corrected Document Text",
                result["corrected"],
                height=350,
                key=f"corrected_output_{result['id']}"
            )

            download_section(
                result["corrected"],
                result["filename"],
                f"result_{result['id']}"
            )


# ----------------------------- Document Library ----------------------------

elif page == "Document Library":

    st.markdown(
        '<div class="dashboard-heading">Document Library</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Browse your saved documents, review proofreading results, "
        "download corrected files or remove documents."
    )

    records = get_documents()

    if not records:

        st.info(
            "Your document library is empty. "
            "Upload a document from the Proofread Document page."
        )

    else:

        total_issues = sum(
            int(r["issue_count"] or 0) for r in records
        )

        m1, m2 = st.columns(2)

        m1.metric("Saved Documents", len(records))
        m2.metric("Total Issues Identified", total_issues)

        st.markdown("### Saved Documents")

        for record in records:

            doc_id = record["id"]
            filename = record["filename"] or "Untitled document"
            file_type = (record["file_type"] or "FILE").upper()
            issue_count = int(record["issue_count"] or 0)
            created_at = record["created_at"] or "Date unavailable"

            with st.container(border=True):

                left, middle, right = st.columns([5, 1.5, 1.5])

                with left:
                    st.markdown(f"**{filename}**")
                    st.caption(
                        f"{file_type} · Reviewed {created_at}"
                    )

                with middle:
                    st.metric("Issues", issue_count)

                with right:
                    if st.button(
                        "Remove",
                        key=f"remove_doc_{doc_id}"
                    ):
                        st.session_state[
                            f"confirm_remove_{doc_id}"
                        ] = True
                        st.rerun()

                # Remove confirmation

                if st.session_state.get(
                    f"confirm_remove_{doc_id}", False
                ):

                    st.warning(
                        f"Are you sure you want to remove {filename}?"
                    )

                    confirm_col, cancel_col = st.columns(2)

                    with confirm_col:

                        if st.button(
                            "Yes, Remove Document",
                            key=f"confirm_yes_{doc_id}",
                            type="primary"
                        ):

                            delete_document(doc_id)

                            st.session_state.pop(
                                f"confirm_remove_{doc_id}", None
                            )

                            current_result = st.session_state.get("result")

                            if (
                                current_result
                                and current_result.get("id") == doc_id
                            ):
                                st.session_state.result = None

                            st.success("Document removed successfully.")
                            st.rerun()

                    with cancel_col:

                        if st.button(
                            "Cancel",
                            key=f"confirm_cancel_{doc_id}"
                        ):

                            st.session_state.pop(
                                f"confirm_remove_{doc_id}", None
                            )
                            st.rerun()

                # View saved document

                with st.expander("View Document Details"):

                    selected = get_document(doc_id)

                    if selected:

                        t1, t2 = st.tabs([
                            "Corrected Text",
                            "Original Text"
                        ])

                        with t1:

                            corrected = selected["corrected_text"] or ""

                            st.text_area(
                                "Corrected Version",
                                corrected,
                                height=240,
                                key=f"lib_corrected_{doc_id}"
                            )

                            download_section(
                                corrected,
                                selected["filename"],
                                f"library_{doc_id}"
                            )

                        with t2:

                            st.text_area(
                                "Original Version",
                                selected["original_text"] or "",
                                height=240,
                                key=f"lib_original_{doc_id}"
                            )

        # Clear entire library

        st.divider()

        with st.expander("Library Maintenance"):

            st.warning(
                "Clearing the library permanently deletes all "
                "saved document records and stored uploaded originals."
            )

            clear_confirm = st.checkbox(
                "I understand and want to clear the entire document library.",
                key="confirm_clear_library"
            )

            if st.button(
                "Clear Entire Library",
                disabled=not clear_confirm,
                key="clear_all_documents"
            ):

                clear_history()
                st.session_state.result = None

                for key in list(st.session_state.keys()):

                    if str(key).startswith("confirm_remove_"):
                        st.session_state.pop(key, None)

                st.success("Document library cleared.")
                st.rerun()


# ----------------------------- Settings -------------------------------------

elif page == "Settings":

    st.markdown(
        '<div class="dashboard-heading">Settings & System Status</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Check the document readers and proofreading engine "
        "available in your environment."
    )

    components = {
        "LanguageTool Grammar Checker": language_tool_python,
        "PDF Reader": PdfReader,
        "DOCX Reader / Exporter": Document,
        "PowerPoint Reader": Presentation,
        "Excel Reader": load_workbook,
        "PDF Exporter": SimpleDocTemplate,
    }

    st.markdown("### System Components")

    for label, package in components.items():

        status = (
            "Available"
            if package is not None
            else "Not installed"
        )

        if package is not None:
            st.success(f"{label}: {status}")
        else:
            st.warning(f"{label}: {status}")

    st.divider()

    st.markdown("### Supported File Formats")

    st.write(
        ", ".join(f".{ext}" for ext in SUPPORTED_TYPES)
    )

    st.markdown("### Data Storage")

    st.code(str(DB_PATH), language="text")

    st.caption(
        "Uploaded originals are stored in the project's uploads folder. "
        "The SQLite database stores extracted and corrected text."
    )

    st.info(
        "LanguageTool may require Java and an internet connection "
        "on its first launch. Scanned PDFs require OCR."
    )
