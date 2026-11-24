
import streamlit as st
import tempfile
import hashlib
import difflib

from pathlib import Path
from datetime import datetime

from app.document_processing.docx_extractor import extract_docx
from app.grammar.grammar_checker import GrammarChecker
from app.grammar.docx_corrector import DocxCorrector
from app.llm.ollama_client import OllamaClient


# ==========================================================
# 1. PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="DocuMind AI | AI TECH ZONE",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ASSETS_FOLDER = PROJECT_ROOT / "assets"

LOGO_PATH = ASSETS_FOLDER / "ai_tech_zone_logo.png"


# ==========================================================
# 2. PROFESSIONAL SAAS THEME
# ==========================================================

st.markdown("""
<style>

/* APPLICATION BACKGROUND */

.stApp {
    background-color: #F3F6FB;
    color: #172B45;
    font-family: "Segoe UI", sans-serif;
}

.block-container {
    max-width: 1450px;
    padding-top: 1.8rem;
    padding-bottom: 3rem;
}

/* SIDEBAR */

[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #10243A 0%,
        #183B5B 100%
    );
    border-right: 1px solid #24496C;
}

[data-testid="stSidebar"] * {
    color: #FFFFFF;
}

[data-testid="stSidebar"] .stRadio label {
    color: #FFFFFF;
    font-weight: 500;
}

/* HEADINGS */

h1 {
    color: #10243A !important;
    font-weight: 800 !important;
    letter-spacing: -0.7px;
}

h2, h3 {
    color: #173D63 !important;
    font-weight: 700 !important;
}

/* TEXT */

p {
    color: #60748A;
    line-height: 1.65;
}

/* BUTTONS */

.stButton > button {
    background: linear-gradient(
        100deg,
        #0755A7,
        #087DC2
    );
    color: #FFFFFF !important;
    border: none;
    border-radius: 9px;
    padding: 0.65rem 1.1rem;
    font-weight: 650;
    transition: 0.2s;
}

.stButton > button:hover {
    background: #063D7A;
    color: #FFFFFF !important;
    box-shadow: 0 4px 14px rgba(7, 85, 167, 0.2);
}

/* DOWNLOAD BUTTONS */

.stDownloadButton > button {
    background: #E5F2FF;
    color: #0755A7 !important;
    border: 1px solid #B8D7F5;
    border-radius: 9px;
    font-weight: 650;
}

.stDownloadButton > button:hover {
    background: #D5EAFE;
    border-color: #0755A7;
}

/* CARDS */

[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border: 1px solid #DFE7F0;
    border-radius: 13px;
}

/* METRICS */

[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #DFE7F0;
    border-radius: 12px;
    padding: 17px;
    box-shadow: 0 3px 10px rgba(20, 50, 80, 0.03);
}

[data-testid="stMetricLabel"] {
    color: #64788E;
    font-weight: 600;
}

[data-testid="stMetricValue"] {
    color: #0755A7;
    font-weight: 800;
}

/* FILE UPLOADER */

[data-testid="stFileUploader"] {
    background: #FFFFFF;
    border: 2px dashed #9CC5E8;
    border-radius: 13px;
    padding: 16px;
}

/* TABS */

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid #DCE5F0;
}

.stTabs [data-baseweb="tab"] {
    background: #E8EFF8;
    color: #294968;
    border-radius: 8px 8px 0 0;
    padding: 12px 16px;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background: #0755A7 !important;
    color: white !important;
}

/* INPUT FIELDS */

.stTextArea textarea,
.stTextInput input {
    background: #FFFFFF;
    border: 1px solid #D1DFEC;
    border-radius: 8px;
}

/* DATAFRAME */

[data-testid="stDataFrame"] {
    border: 1px solid #DFE7F0;
    border-radius: 10px;
}

/* FOOTER */

.footer {
    color: #718096;
    font-size: 12px;
    text-align: center;
    padding: 20px;
    border-top: 1px solid #DCE5F0;
    margin-top: 35px;
}

/* HIDE DEFAULT STREAMLIT BRANDING */

#MainMenu {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


# ==========================================================
# 3. SESSION STATE
# ==========================================================

DEFAULT_STATE = {
    "analysis_result": None,
    "original_bytes": None,
    "original_name": None,
    "corrected_bytes": None,
    "corrected_name": None,
    "file_hash": None,
    "history": [],
    "selected_page": "Dashboard"
}

for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================================
# 4. AI COMPONENT INITIALIZATION
# ==========================================================

@st.cache_resource
def get_grammar_checker():

    return GrammarChecker()


@st.cache_resource
def get_ollama_client():

    return OllamaClient()


@st.cache_resource
def get_docx_corrector():

    return DocxCorrector()


# ==========================================================
# 5. TEXT CHUNKING
# ==========================================================

def split_text_into_chunks(text, max_chars=2500):

    paragraphs = [
        paragraph.strip()
        for paragraph in text.splitlines()
        if paragraph.strip()
    ]

    chunks = []

    current_chunk = ""

    for paragraph in paragraphs:

        if len(current_chunk) + len(paragraph) <= max_chars:

            current_chunk += paragraph + "\n"

        else:

            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            current_chunk = paragraph + "\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


# ==========================================================
# 6. AI DOCUMENT CORRECTION
# ==========================================================

def correct_document_with_ai(
    original_text,
    progress_bar,
    status
):

    client = get_ollama_client()

    chunks = split_text_into_chunks(original_text)

    if not chunks:
        return original_text

    corrected_chunks = []

    total_chunks = len(chunks)

    for index, chunk in enumerate(chunks):

        status.info(
            f"AI is correcting section {index + 1} "
            f"of {total_chunks}..."
        )

        prompt = f"""
You are a professional English grammar correction assistant.

Correct the following document text.

Instructions:

1. Correct grammar and spelling.
2. Correct punctuation.
3. Improve sentence structure.
4. Preserve the original meaning.
5. Do not summarize the document.
6. Do not add new information.
7. Use professional business English.
8. Return only corrected text.

DOCUMENT:

{chunk}
"""

        corrected = client.correct_grammar(prompt)

        if not corrected:
            corrected = chunk

        corrected_chunks.append(corrected.strip())

        progress = 0.30 + (
            0.55 * (index + 1) / total_chunks
        )

        progress_bar.progress(progress)

    return "\n\n".join(corrected_chunks)


# ==========================================================
# 7. GRAMMAR ERROR DETAILS
# ==========================================================

def get_error_details(matches):

    errors = []

    for match in matches:

        errors.append({

            "Context": getattr(
                match, "context", ""
            ),

            "Position": getattr(
                match, "offset", 0
            ),

            "Error Length": getattr(
                match, "error_length", 0
            ),

            "Message": getattr(
                match, "message", ""
            ),

            "Suggestions": ", ".join(
                getattr(match, "replacements", [])[:5]
            ),

            "Rule": getattr(
                match, "rule_id", ""
            )
        })

    return errors


# ==========================================================
# 8. DOCUMENT COMPARISON
# ==========================================================

def compare_texts(original_text, corrected_text):

    original_words = original_text.split()

    corrected_words = corrected_text.split()

    matcher = difflib.SequenceMatcher(
        None,
        original_words,
        corrected_words
    )

    changes = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag != "equal":

            changes.append({

                "Change Type": tag.capitalize(),

                "Original Text": " ".join(
                    original_words[i1:i2]
                ),

                "Corrected Text": " ".join(
                    corrected_words[j1:j2]
                )
            })

    return changes


# ==========================================================
# 9. DOCUMENT PROCESSING PIPELINE
# ==========================================================

def analyze_document(uploaded_file):

    progress_bar = st.progress(0)

    status = st.empty()

    temp_path = None

    try:

        file_bytes = uploaded_file.getvalue()

        # STEP 1: TEMPORARY FILE

        status.info("Step 1/4: Extracting document...")

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".docx"
        ) as temp_file:

            temp_file.write(file_bytes)

            temp_path = Path(temp_file.name)

        original_text = extract_docx(
            str(temp_path)
        )

        if not original_text or not original_text.strip():

            raise ValueError(
                "No readable text found in the document."
            )

        progress_bar.progress(0.20)

        # STEP 2: GRAMMAR CHECKING

        status.info("Step 2/4: Checking grammar...")

        grammar_checker = get_grammar_checker()

        grammar_matches = grammar_checker.check_grammar(
            original_text
        )

        progress_bar.progress(0.30)

        # STEP 3: AI CORRECTION

        status.info("Step 3/4: AI grammar correction...")

        corrected_text = correct_document_with_ai(
            original_text,
            progress_bar,
            status
        )

        # STEP 4: CREATE CORRECTED DOCX

        status.info("Step 4/4: Generating corrected document...")

        docx_corrector = get_docx_corrector()

        output_path = docx_corrector.save_corrected_document(
            corrected_text,
            str(temp_path)
        )

        output_path = Path(output_path)

        if not output_path.exists():

            raise FileNotFoundError(
                "Corrected DOCX was not generated."
            )

        corrected_bytes = output_path.read_bytes()

        # STORE RESULTS

        errors = get_error_details(grammar_matches)

        comparison = compare_texts(
            original_text,
            corrected_text
        )

        st.session_state["analysis_result"] = {

            "original_text": original_text,

            "corrected_text": corrected_text,

            "grammar_matches": grammar_matches,

            "error_details": errors,

            "comparison": comparison
        }

        st.session_state["original_bytes"] = file_bytes

        st.session_state["original_name"] = uploaded_file.name

        st.session_state["corrected_bytes"] = corrected_bytes

        st.session_state["corrected_name"] = (
            f"{Path(uploaded_file.name).stem}_corrected.docx"
        )

        st.session_state["file_hash"] = hashlib.md5(
            file_bytes
        ).hexdigest()

        # DOCUMENT HISTORY

        st.session_state["history"].insert(
            0,
            {
                "Document": uploaded_file.name,
                "Date": datetime.now().strftime(
                    "%d-%m-%Y %I:%M %p"
                ),
                "Grammar Errors": len(errors),
                "Status": "Completed"
            }
        )

        progress_bar.progress(1.0)

        status.success(
            "Document successfully analyzed!"
        )

        return True

    except Exception as error:

        status.error(
            f"Processing failed: {error}"
        )

        st.exception(error)

        return False

    finally:

        if temp_path and temp_path.exists():

            temp_path.unlink()


# ==========================================================
# 10. SIDEBAR
# ==========================================================

with st.sidebar:

    st.markdown(" ")

    if LOGO_PATH.exists():

        st.image(
            str(LOGO_PATH),
            width=190
        )

    else:

        st.title("🤖 AI TECH ZONE")

        st.caption(
            "Add your logo to assets/ai_tech_zone_logo.png"
        )

    st.divider()

    st.subheader("DocuMind AI")

    st.caption("Your intelligent document workspace")

    st.divider()

    st.markdown("### WORKSPACE")

    page = st.radio(

        "Navigation",

        [
            "Dashboard",
            "Upload Document",
            "Document History",
            "About"
        ],

        label_visibility="collapsed"

    )

    st.divider()

    st.markdown("### AI ENGINE")

    st.success("Llama 3.2 configured")

    st.caption("Local inference powered by Ollama")

    st.divider()

    st.caption("INNOVATE • AUTOMATE • EXCEL")


# ==========================================================
# 11. DASHBOARD
# ==========================================================

if page == "Dashboard":

    st.title("Welcome to DocuMind AI")

    st.caption(
        "AI TECH ZONE | Intelligent Document Processing Platform"
    )

    st.write(
        "Your intelligent workspace for document analysis, "
        "grammar checking and AI-powered writing improvement."
    )

    st.divider()

    # DASHBOARD METRICS

    st.subheader("Workspace Overview")

    total_documents = len(
        st.session_state["history"]
    )

    total_errors = sum(
        item["Grammar Errors"]
        for item in st.session_state["history"]
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Documents Processed",
            total_documents
        )

    with col2:

        st.metric(
            "Grammar Issues",
            total_errors
        )

    with col3:

        st.metric(
            "AI Model",
            "Llama 3.2"
        )

    with col4:

        st.metric(
            "Platform Status",
            "Ready"
        )

    st.divider()

    # FEATURE CARDS

    st.subheader("Platform Features")

    col1, col2, col3 = st.columns(3)

    with col1:

        with st.container(border=True):

            st.subheader("📄 Document Upload")

            st.write(
                "Upload and extract content from Word documents."
            )

            st.caption("DOCX processing")

    with col2:

        with st.container(border=True):

            st.subheader("🔍 Grammar Intelligence")

            st.write(
                "Identify spelling, grammar and punctuation mistakes."
            )

            st.caption("LanguageTool engine")

    with col3:

        with st.container(border=True):

            st.subheader("✨ AI Correction")

            st.write(
                "Improve writing using local artificial intelligence."
            )

            st.caption("Ollama Llama 3.2")

    st.divider()

    # GET STARTED

    st.subheader("Get Started")

    with st.container(border=True):

        st.write(
            "Start by uploading a Word document for analysis."
        )

        st.write(
            "The AI engine will check grammar, correct text "
            "and generate a downloadable DOCX document."
        )

        if st.button(
            "Start Document Analysis",
            type="primary",
            use_container_width=True
        ):

            st.session_state["selected_page"] = (
                "Upload Document"
            )

            st.session_state["navigate_to_upload"] = True

            st.rerun()


# ==========================================================
# 12. UPLOAD DOCUMENT
# ==========================================================

elif page == "Upload Document":

    st.title("Document Analysis")

    st.caption(
        "Upload, analyze and improve your Word documents."
    )

    st.divider()

    st.subheader("Upload Your Document")

    st.write(
        "Choose a DOCX file to start the intelligent "
        "document processing workflow."
    )

    uploaded_file = st.file_uploader(
        "Choose a Word document",
        type=["docx"],
        help="Supported format: Microsoft Word DOCX"
    )

    if uploaded_file:

        current_hash = hashlib.md5(
            uploaded_file.getvalue()
        ).hexdigest()

        st.success(
            f"Selected: {uploaded_file.name}"
        )

        st.caption(
            f"File size: {uploaded_file.size / 1024:.2f} KB"
        )

        if current_hash != st.session_state["file_hash"]:

            if st.button(
                "🚀 Start AI Document Analysis",
                type="primary",
                use_container_width=True
            ):

                analyze_document(uploaded_file)

        else:

            st.info(
                "This document has already been processed."
            )

    # ANALYSIS RESULTS

    result = st.session_state["analysis_result"]

    if result:

        st.divider()

        st.header("Document Analysis Results")

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Grammar Issues",
                len(result["grammar_matches"])
            )

        with col2:

            st.metric(
                "Original Words",
                len(result["original_text"].split())
            )

        with col3:

            st.metric(
                "Corrected Words",
                len(result["corrected_text"].split())
            )

        st.divider()

        # RESULT TABS

        tab1, tab2, tab3, tab4 = st.tabs([

            "Original Document",

            "Grammar Mistakes",

            "AI Corrected Document",

            "Text Comparison"

        ])

        # ORIGINAL DOCUMENT

        with tab1:

            st.subheader("Original Document")

            st.text_area(
                "Original Content",
                value=result["original_text"],
                height=400,
                disabled=True
            )

            st.download_button(

                "Download Original DOCX",

                data=st.session_state["original_bytes"],

                file_name=st.session_state["original_name"],

                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                )
            )

        # GRAMMAR MISTAKES

        with tab2:

            st.subheader("Grammar Analysis")

            if result["error_details"]:

                st.dataframe(
                    result["error_details"],
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.success(
                    "No grammar issues detected by LanguageTool."
                )

        # CORRECTED DOCUMENT

        with tab3:

            st.subheader("AI Corrected Content")

            st.text_area(
                "Corrected Text",
                value=result["corrected_text"],
                height=400,
                disabled=True
            )

            st.download_button(

                "Download Corrected DOCX",

                data=st.session_state["corrected_bytes"],

                file_name=st.session_state["corrected_name"],

                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),

                type="primary"
            )

        # COMPARISON

        with tab4:

            st.subheader("Original vs Corrected")

            changes = result["comparison"]

            if changes:

                st.dataframe(
                    changes,
                    use_container_width=True,
                    hide_index=True
                )

                st.info(
                    f"{len(changes)} text changes identified."
                )

            else:

                st.success(
                    "No text differences identified."
                )

        st.divider()

        if st.button("Clear Current Analysis"):

            for key, value in DEFAULT_STATE.items():

                st.session_state[key] = value

            st.rerun()


# ==========================================================
# 13. DOCUMENT HISTORY
# ==========================================================

elif page == "Document History":

    st.title("Document History")

    st.caption(
        "View documents processed during this application session."
    )

    st.divider()

    history = st.session_state["history"]

    if history:

        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True
        )

        st.info(
            "History is currently stored in Streamlit session state. "
            "It is not yet persisted in a database."
        )

    else:

        with st.container(border=True):

            st.subheader("No Documents Yet")

            st.write(
                "Your processed documents will appear here."
            )

            st.info(
                "Go to Upload Document to process your first file."
            )


# ==========================================================
# 14. ABOUT PAGE
# ==========================================================

elif page == "About":

    st.title("About DocuMind AI")

    st.caption(
        "AI TECH ZONE | Intelligent Document Processing Platform"
    )

    st.divider()

    if LOGO_PATH.exists():

        st.image(
            str(LOGO_PATH),
            width=200
        )

    st.subheader("Our Platform")

    st.write(
        "DocuMind AI is an intelligent document processing "
        "application designed to analyze Word documents, "
        "identify grammar mistakes and improve writing "
        "using artificial intelligence."
    )

    st.divider()

    st.subheader("Technology Stack")

    col1, col2 = st.columns(2)

    with col1:

        with st.container(border=True):

            st.write("🐍 Python")

            st.write("🎨 Streamlit")

            st.write("📝 LanguageTool")

    with col2:

        with st.container(border=True):

            st.write("🤖 Ollama")

            st.write("🧠 Llama 3.2")

            st.write("📄 Python DOCX")

    st.divider()

    st.subheader("Platform Capabilities")

    st.write("✓ DOCX document upload")

    st.write("✓ Document text extraction")

    st.write("✓ Grammar and spelling analysis")

    st.write("✓ AI-powered text correction")

    st.write("✓ Original and corrected comparison")

    st.write("✓ Corrected document download")


# ==========================================================
# 15. FOOTER
# ==========================================================

st.markdown("---")

st.markdown(
    """
    <div class="footer">
        <b>AI TECH ZONE | DocuMind AI</b><br>
        INNOVATE • AUTOMATE • EXCEL<br>
        Powered by Python, Streamlit, LanguageTool and Ollama<br>
        © 2026 AI TECH ZONE. All Rights Reserved.
    </div>
    """,
    unsafe_allow_html=True
)
