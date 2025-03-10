import streamlit as st
from util import display_footer

st.title("Configuration")

# API Key configuration for Mistral
with st.form('Mistral API Key Configuration'):
    api_key = st.text_input("Enter your Mistral API Key:", type="password",
                                                    value=st.session_state.mistral_api_key,
                                                    help='Get API Key from: https://console.mistral.ai/api-keys')
    submitted_mistral = st.form_submit_button('Submit', type='primary', icon=":material/check:")

    if len(api_key.strip()) < 25:
        st.warning('Please enter the valid API Key')
    else:
        st.session_state.mistral_api_key = api_key


# Display footer
display_footer()