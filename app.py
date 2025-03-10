# Import libraries
import streamlit as st

# --- PAGE SETUP ---
main_page = st.Page(
    "views/mistral_ocr_app.py",
    title="Mistral OCR",
    icon=":material/article:",
    default=True,
)

config_page = st.Page(
    "views/configuration.py",
    title="Configuration",
    icon=":material/toggle_on:",
)


faq_page = st.Page(
    "views/faqs.py",
    title="FAQs",
    icon=":material/help:",
)

contact_us = st.Page(
    "views/contact.py",
    title="Contact Us",
    icon=":material/contact_page:",
)

pg = st.navigation({
    "Admin": [config_page],
    "Home": [main_page],
    "Support": [faq_page, contact_us],
                    })

pg.run()