import base64
import html
import os

import requests
import streamlit as st

from dotenv import load_dotenv


load_dotenv()


def get_backend_url() -> str:
    # Streamlit Cloud: set BACKEND_URL in App Settings -> Secrets.
    # Local development: use BACKEND_URL from .env when available.
    secret_url = ""
    try:
        secret_url = str(st.secrets.get("BACKEND_URL", "")).strip()
    except Exception:
        pass

    env_url = os.getenv("BACKEND_URL", "").strip()

    return (
        secret_url
        or env_url
        or "http://127.0.0.1:8000"
    ).rstrip("/")


BACKEND_URL = get_backend_url()


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="LegalEase",
    page_icon="⚖️",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .subtitle {
        text-align: center;
        color: #777;
        margin-bottom: 25px;
    }

    .preview {
        background: #17191c;
        color: #f3f3f3;
        border-radius: 12px;
        padding: 24px;
        max-height: 620px;
        overflow-y: auto;
        white-space: pre-wrap;
        font-family: Georgia, serif;
        line-height: 1.55;
    }

    .notice {
        padding: 12px;
        border-radius: 8px;
        background: #fff7df;
        border: 1px solid #ead69a;
        color: #5c4b14;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">⚖️ LegalEase</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-powered legal document drafting and export'
    '</div>',
    unsafe_allow_html=True
)


st.markdown(
    '<div class="notice">'
    '<b>Important:</b> Generated documents are drafts '
    'for review and are not legal advice.'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# SESSION STATE
# =========================================================

if "document_text" not in st.session_state:

    st.session_state.document_text = ""


if "terms" not in st.session_state:

    st.session_state.terms = []


# =========================================================
# TWO COLUMN LAYOUT
# =========================================================

left, right = st.columns(
    [0.95, 1.25],
    gap="large"
)


# =========================================================
# LEFT SIDE
# =========================================================

with left:

    st.subheader(
        "Document Details"
    )

    # -----------------------------------------------------
    # DOCUMENT TYPE
    # -----------------------------------------------------

    document_type = st.selectbox(
        "Document Type",
        [
            "Employment Contract",
            "Non-Disclosure Agreement",
            "Lease Agreement",
            "Employment Offer Letter",
            "Freelance Work Contract",
            "General Agreement",
            "Other"
        ]
    )


    if document_type == "Other":

        document_type = st.text_input(
            "Enter Document Type",
            placeholder=(
                "Example: Consulting Agreement"
            )
        )


    # -----------------------------------------------------
    # PARTIES
    # -----------------------------------------------------

    parties = st.text_area(
        "Parties Involved",

        placeholder=(
            "Jane Doe (Service Provider), "
            "TechNova Inc. (Client)"
        ),

        height=100
    )


    # -----------------------------------------------------
    # TERMS
    # -----------------------------------------------------

    terms_text = st.text_area(
        "Terms & Conditions",

        placeholder=(
            "Payment within 30 days of invoice;\n"
            "Confidentiality must be maintained;\n"
            "Either party may terminate with 15 days notice"
        ),

        height=150,

        help=(
            "Separate terms with semicolons "
            "or put one term per line."
        )
    )


    # -----------------------------------------------------
    # EFFECTIVE DATE
    # -----------------------------------------------------

    effective_date = st.text_input(
        "Effective Date",

        placeholder=(
            "April 15, 2026"
        )
    )


    # -----------------------------------------------------
    # LOGO
    # -----------------------------------------------------

    st.file_uploader(
        "Optional Logo",

        type=[
            "png",
            "jpg",
            "jpeg"
        ],

        help=(
            "Reserved for branding extensions. "
            "The current exporter uses a text header/footer."
        )
    )


    # =====================================================
    # GENERATE BUTTON
    # =====================================================

    if st.button(
        "✨ Generate Document",
        type="primary",
        use_container_width=True
    ):

        if not all(
            [
                document_type.strip(),
                parties.strip(),
                terms_text.strip(),
                effective_date.strip()
            ]
        ):

            st.error(
                "Please complete all required fields."
            )

        else:

            payload = {

                "document_type":
                    document_type,

                "parties":
                    parties,

                "terms":
                    terms_text,

                "effective_date":
                    effective_date
            }


            try:

                with st.spinner(
                    "Generating your legal draft..."
                ):

                    response = requests.post(

                        f"{BACKEND_URL}/generate",

                        json=payload,

                        timeout=120
                    )


                if response.ok:

                    data = response.json()

                    st.session_state.document_text = (
                        data["text"]
                    )


                    st.session_state.terms = [

                        item.strip()

                        for item in
                        terms_text.replace(
                            "\n",
                            ";"
                        ).split(";")

                        if item.strip()
                    ]


                    st.success(
                        "Document generated successfully."
                    )


                else:

                    try:

                        message = response.json().get(
                            "detail",
                            response.text
                        )

                    except Exception:

                        message = response.text


                    st.error(
                        f"Backend error: {message}"
                    )


            except requests.RequestException as exc:

                st.error(
                    "Could not connect to FastAPI. "
                    "Start the backend first.\n\n"
                    f"Details: {exc}"
                )


# =========================================================
# RIGHT SIDE
# =========================================================

with right:

    st.subheader(
        "Editable Preview"
    )


    edited = st.text_area(

        "Edit your document here",

        value=st.session_state.document_text,

        height=560,

        label_visibility="collapsed"
    )


    st.session_state.document_text = edited


    # -----------------------------------------------------
    # HTML PREVIEW
    # -----------------------------------------------------

    if st.session_state.document_text:

        safe_text = html.escape(
            st.session_state.document_text
        )


        st.markdown(

            f'<div class="preview">'
            f'{safe_text}'
            f'</div>',

            unsafe_allow_html=True
        )


# =========================================================
# DOWNLOAD SECTION
# =========================================================

st.divider()


if st.session_state.document_text:

    st.subheader(
        "Download"
    )


    cols = st.columns(3)


    formats = [
        ("txt", "Prepare TXT"),
        ("docx", "Prepare DOCX"),
        ("pdf", "Prepare PDF")
    ]


    # =====================================================
    # PREPARE FILE
    # =====================================================

    for col, (fmt, label) in zip(
        cols,
        formats
    ):

        with col:

            if st.button(
                label,
                use_container_width=True
            ):

                payload = {

                    "format":
                        fmt,

                    "document_type":
                        document_type
                        or "Legal Document",

                    "text":
                        st.session_state.document_text,

                    "terms":
                        st.session_state.terms
                }


                try:

                    with st.spinner(
                        f"Preparing {fmt.upper()}..."
                    ):

                        response = requests.post(

                            f"{BACKEND_URL}/export",

                            json=payload,

                            timeout=120
                        )


                    if response.ok:

                        result = (
                            response.json()
                        )


                        st.session_state[
                            f"download_{fmt}"
                        ] = result


                        st.success(
                            f"{fmt.upper()} is ready."
                        )


                    else:

                        try:

                            message = (
                                response.json()
                                .get(
                                    "detail",
                                    response.text
                                )
                            )

                        except Exception:

                            message = response.text


                        st.error(message)


                except requests.RequestException as exc:

                    st.error(
                        f"Export failed: {exc}"
                    )


    # =====================================================
    # SAVE FILE
    # =====================================================

    for fmt in [
        "txt",
        "docx",
        "pdf"
    ]:

        result = st.session_state.get(
            f"download_{fmt}"
        )


        if result:

            file_bytes = base64.b64decode(
                result["data_base64"]
            )


            st.download_button(

                label=(
                    f"⬇️ Save {fmt.upper()} File"
                ),

                data=file_bytes,

                file_name=result[
                    "filename"
                ],

                mime=result[
                    "media_type"
                ],

                key=f"save_{fmt}",

                use_container_width=True
            )


# =========================================================
# FOOTER
# =========================================================

st.caption(
    "LegalEase is an AI drafting prototype. "
    "Review generated content with a qualified "
    "legal professional before relying on it."
)