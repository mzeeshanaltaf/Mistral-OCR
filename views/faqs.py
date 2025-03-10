import streamlit as st
from util import display_footer

# Page configuration options
page_title = "FAQs"
page_icon = "💬"
st.set_page_config(page_title=page_title, page_icon=page_icon, layout="wide", initial_sidebar_state="expanded")

st.title('FAQs')

# Toggle switch to expand all FAQs.
expand_all = st.toggle("Expand all", value=False)

# Dictionary to store FAQs
faq_data = {
        'What this Application is about?': '<p>This application takes a PDF document and extract text, tables, formulas from it with '
                                           'precision and deliver it in a clean and structured markdown format. '
                                           'This application makes use of Mistral OCR to perform lightning fast OCR.</p>',


        'Can I get the application source code?': '<p>Yes, Source code of this application is available at: <a href="https://github.com/mzeeshanaltaf/Mistral-OCR">GitHub</a></p>',

    }


# Display expandable boxes for each question-answer pair
for question, answer in faq_data.items():
    with st.expander(r"$\textbf{\textsf{" + question + r"}}$", expanded=expand_all):  # Use LaTeX for bold label
        st.markdown(f'<div style="text-align: justify;"> {answer} </div>', unsafe_allow_html=True)

display_footer()