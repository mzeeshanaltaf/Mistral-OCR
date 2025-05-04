import streamlit as st
from mistralai import Mistral
from mistralai import DocumentURLChunk, ImageURLChunk, TextChunk
from mistralai.models import OCRResponse
from markdown_pdf import MarkdownPdf, Section
import io

# Function for selecting LLM Model
def check_api_key_status():
    api_key_status = False  # Variable to disable PDF uploading if key is none

    if st.session_state.mistral_api_key == '':
        st.warning('API Key not set. Configure the Mistral API key from Configuration page.👈', icon=':material/warning:')
    else:
        api_key_status = True

    return api_key_status, st.session_state.mistral_api_key

def replace_images_in_markdown(markdown_str: str, images_dict: dict) -> str:
    for img_name, base64_str in images_dict.items():
        markdown_str = markdown_str.replace(f"![{img_name}]({img_name})", f"![{img_name}]({base64_str})")
    return markdown_str

def get_combined_markdown(ocr_response: OCRResponse) -> str:
  markdowns: list[str] = []
  for page in ocr_response.pages:
    image_data = {}
    for img in page.images:
      image_data[img.id] = img.image_base64
    markdowns.append(replace_images_in_markdown(page.markdown, image_data))

  return "\n\n".join(markdowns)

def convert_md_to_pdf(md_contents):
    # Generate PDF from markdown content
    pdf = MarkdownPdf(toc_level=2, optimize=True)
    pdf.add_section(Section(md_contents))

    # Save PDF to bytes buffer
    pdf_buffer = io.BytesIO()
    pdf.save(pdf_buffer)
    pdf_bytes = pdf_buffer.getvalue()

    return pdf_bytes


# Function to perform OCR using Mistral model
def mistral_ocr(uploaded_pdf, api_key):

    client = Mistral(api_key=api_key)

    uploaded_file = client.files.upload(
        file={
            "file_name": uploaded_pdf.name,
            "content": uploaded_pdf.getvalue(),
        },
        purpose="ocr",
    )
    signed_url = client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)
    pdf_response = client.ocr.process(document=DocumentURLChunk(document_url=signed_url.url),
                                      model="mistral-ocr-latest", include_image_base64=True)

    return get_combined_markdown(pdf_response)

def display_footer():
    footer = """
    <style>
    /* Ensures the footer stays at the bottom of the sidebar */
    [data-testid="stSidebar"] > div: nth-child(3) {
        position: fixed;
        bottom: 0;
        width: 100%;
        text-align: center;
    }

    .footer {
        color: grey;
        font-size: 15px;
        text-align: center;
        background-color: transparent;
    }
    </style>
    <div class="footer">
    Made with ❤️ by <a href="mailto:zeeshan.altaf@gmail.com">Zeeshan</a>.
    </div>
    """
    st.sidebar.markdown(footer, unsafe_allow_html=True)