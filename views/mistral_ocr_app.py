import streamlit as st
from util import *
from datetime import datetime
from streamlit_pdf_viewer import pdf_viewer


if "mistral_api_key" not in st.session_state:
    st.session_state.mistral_api_key = ''

if "markdown_mistral" not in st.session_state:
    st.session_state.markdown_mistral = None

page_title = "Mistral OCR 📄🔍✨"
page_icon = "📄"
st.set_page_config(page_title=page_title, page_icon=page_icon, layout="wide")

st.title(page_title)
st.write(':blue[***Transforming PDFs into Markdown Magic! 🌟📄***]')
st.write("""
This app takes your PDFs and performs lightning-fast OCR 🖹✨, extracting text with precision and delivering it 
in clean, structured Markdown format🖋️💡. Whether it’s scanned documents or complex layouts, this app simplifies 
your workflow, making document management effortless and accessible.🚀
""")
st.info("This application is powered by [Mistral OCR](https://mistral.ai/en/news/mistral-ocr). "
        "Popular model for document OCR'ing.", icon=':material/info:')

# Check if API key is set or not
api_key_status, api_key = check_api_key_status()

# File uploader
st.subheader("Upload a PDF file:", divider='gray')
uploaded_pdf = st.file_uploader("Upload a PDF file", type=["pdf"], label_visibility="collapsed", disabled=not api_key_status)

# If pdf file is not none then read the file contents and pass it on to Mistral OCR
if uploaded_pdf is not None:

    # Reset the variables if new PDF is loaded.
    st.session_state.markdown_mistral = None

    col1, col2 = st.columns([1, 1], vertical_alignment="top")

    # OCR with Mistral API
    with (col1):
        st.subheader('OCR with Mistral:', divider='gray')
        run_ocr_mistral = st.button("Run OCR", type="primary", key="run_ocr_mistral", disabled=not uploaded_pdf, icon=':material/document_scanner:')
        if run_ocr_mistral:
            with st.spinner('Processing ...'):
                st.session_state.markdown_mistral = mistral_ocr(uploaded_pdf, api_key)

        # Display the markdown response
        if st.session_state.markdown_mistral is not None:
            st.subheader('Response:', divider='gray')

            with st.expander('Markdown Response', expanded=True, icon=':material/markdown:'):
                mistral_container = st.container(height=1000, key='mistral-container')
                mistral_container.markdown(st.session_state.markdown_mistral, unsafe_allow_html=True)

                # Create a unique file name based on current date & time for download
                file_name = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                left, right = st.columns(2)
                left.download_button("Download MD", data=st.session_state.markdown_mistral,file_name=f"{file_name}_mistral.md",
                                   type='primary', icon=':material/markdown:', help='Download the Markdown Response',
                                   on_click="ignore")
                pdf_data = convert_md_to_pdf(st.session_state.markdown_mistral)
                right.download_button("Download PDF", data=pdf_data,file_name=f"{file_name}_mistral.pdf",
                                   type='primary', icon=':material/picture_as_pdf:', help='Download in PDF Format',
                                   on_click="ignore")

    # Display PDF Previewer
    with col2:
        st.subheader('PDF Previewer:', divider='gray')
        with st.expander(':blue[***Preview PDF***]', expanded=False, icon=':material/preview:'):
            pdf_viewer(uploaded_pdf.getvalue(), height=1000, render_text=True)

# Display footer on the sidebar
display_footer()
