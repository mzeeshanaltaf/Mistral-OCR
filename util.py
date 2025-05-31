import streamlit as st
from mistralai import Mistral
from mistralai import DocumentURLChunk, ImageURLChunk, TextChunk
from mistralai.models import OCRResponse
from markdown_pdf import MarkdownPdf, Section
from pdf2image import convert_from_bytes
from PIL import Image
import base64
import io
import json
import time
import pandas as pd

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

def encode_image_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_image}"

def convert_pdf_to_base64_images(pdf_bytes: bytes) -> list:
    images = convert_from_bytes(pdf_bytes)
    base64_images = [encode_image_to_base64(img) for img in images]
    return base64_images

def create_jsonl_batch_file(pdfs: list):
    """
    pdfs: list of tuples → [(file_name, file_bytes), ...]
    """
    output_path = "ocr_batch_input.jsonl"
    with open(output_path, "w") as f:
        idx = 0
        for pdf_name, pdf_bytes in pdfs:
            base64_images = convert_pdf_to_base64_images(pdf_bytes)
            for image_str in base64_images:
                entry = {
                    "custom_id": f"{pdf_name}_page_{idx}",
                    "body": {
                        "document": {
                            "type": "image_url",
                            "image_url": image_str
                        },
                        "include_image_base64": True
                    }
                }
                f.write(json.dumps(entry) + "\n")
                idx += 1

def create_jsonl_batch(pdfs: list) -> str:
    """
    pdfs: list of tuples → [(file_name, file_bytes), ...]
    Returns a JSONL string.
    """
    output_lines = []
    idx = 0
    for pdf_name, pdf_bytes in pdfs:
        base64_images = convert_pdf_to_base64_images(pdf_bytes)
        for image_str in base64_images:
            entry = {
                "custom_id": f"{pdf_name}_page_{idx}",
                "body": {
                    "document": {
                        "type": "image_url",
                        "image_url": image_str
                    },
                    "include_image_base64": True
                }
            }
            output_lines.append(json.dumps(entry) + "\n")
            idx += 1

    output_jsonl = "\n".join(output_lines)
    return output_jsonl

def mistral_ocr_batch(uploaded_pdfs, api_key):
    client = Mistral(api_key=api_key)

    pdf_contents = []
    for pdf in uploaded_pdfs:
        pdf_contents.append((pdf.name, pdf.getvalue()))

    with st.spinner('Processing ...'):
        # Create the batch file
        output_jsonl = create_jsonl_batch(pdf_contents)

        # Upload the batch file to the API
        batch_data = client.files.upload(
            file={
                "file_name": "batch_file.jsonl",
                "content": output_jsonl},
            purpose="batch"
        )

        # Create a Batch Job
        created_job = client.batch.jobs.create(
            input_files=[batch_data.id],
            model='mistral-ocr-latest',
            endpoint="/v1/ocr",
            metadata={"job_type": "insuragi_ocr"}
        )

        # Retrieve the job information
        retrieved_job = client.batch.jobs.get(job_id=created_job.id)

        # Display OCR progress
        retrieved_job = display_ocr_progress(client, retrieved_job, created_job)

    st.session_state.retrieved_job = retrieved_job

def display_ocr_progress(client, retrieved_job, created_job):
    # Display OCR progress
    ocr_bar = st.progress(0, text='OCR in progress. Please wait.')

    while retrieved_job.status in ["QUEUED", "RUNNING"]:
        retrieved_job = client.batch.jobs.get(job_id=created_job.id)
        percent_done = round(
            (retrieved_job.succeeded_requests + retrieved_job.failed_requests) / retrieved_job.total_requests, 4)
        ocr_bar.progress(percent_done, text='OCR in progress...')
        time.sleep(1)

    ocr_bar.empty()

    return retrieved_job

def display_ocr_statistics(retrieved_job, uploaded_pdfs):
    st.subheader('OCR Statistics:', divider='gray')
    # Display statistics
    col1, col2, col3 = st.columns(3)
    col1.metric('Status', f'{retrieved_job.status}', border=True)
    col2.metric('PDF(s) Processed', f'{len(uploaded_pdfs)}', border=True)
    col3.metric('Total Number of Pages OCRed', f'{retrieved_job.total_requests}', border=True)

    col4, col5, col6 = st.columns(3)
    col4.metric('Pages OCRed Successfully', f'{retrieved_job.succeeded_requests}', border=True)
    col5.metric('Pages Unable to OCRed', f'{retrieved_job.failed_requests}', border=True)
    col6.metric('Total Cost', f'${retrieved_job.total_requests / 1000}', border=True)

def download_markdown_files(client, retrieved_job, uploaded_pdfs):

    response = client.files.download(file_id=retrieved_job.output_file)

    file_content = response.read()
    decoded_string = file_content.decode('utf-8')
    lines = decoded_string.strip().split('\n')
    parsed_objects = [json.loads(line) for line in lines]

    file_names = [pdf.name.split('.')[0] for pdf in uploaded_pdfs]
    st.session_state.markdown_mistral = {file_name: [] for file_name in file_names}

    for obj in parsed_objects:
        file_name = obj['custom_id'].split('.')[0]
        if file_name in file_names:
            st.session_state.markdown_mistral[file_name].append(obj['response']['body']['pages'][0]['markdown'])

def display_download_table(uploaded_pdfs):
    st.subheader('Download Markdown File(s):', divider='gray')

    client = Mistral(api_key=st.session_state.mistral_api_key)

    with st.spinner('Downloading ...'):
        # Download Markdown Files
        download_markdown_files(client, st.session_state.retrieved_job, uploaded_pdfs)

    file_names = [pdf.name.split('.')[0] for pdf in uploaded_pdfs]

    for i in range(len(file_names)):
        col1, col2 = st.columns([3, 1], border=True)
        col1.write(f'{file_names[i]}.md')
        col2.download_button(
            label="Download MD",
            type='primary',
            data=st.session_state.markdown_mistral[file_names[i]][0],
            file_name=f'{file_names[i]}.md',
            mime="text/markdown",
            key=f"download_btn_{i}",
            icon=":material/markdown:",
            on_click="ignore"
        )

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