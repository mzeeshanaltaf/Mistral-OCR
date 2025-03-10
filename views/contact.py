import streamlit as st
import smtplib
import random
import time
from util import display_footer

from email_validator import validate_email, EmailNotValidError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from captcha.image import ImageCaptcha

options = st.secrets['OPTIONS']
server = st.secrets["SERVER"]
port = st.secrets["PORT"]
user_name = st.secrets["USERNAME"]
password = st.secrets["PASSWORD"]
recipient = st.secrets["RECIPIENT"]


def generate_captcha():
    captcha_text = "".join(random.choices(options,
                                          k=6))  # options is a string of characters that can be included in the CAPTCHA. It may be as simple or as complex as you wish.
    image = ImageCaptcha(width=400, height=100).generate(captcha_text)
    return captcha_text, image


## Generate CAPTCHA
if 'captcha_text' not in st.session_state:
    st.session_state.captcha_text = generate_captcha()

captcha_text, captcha_image = st.session_state.captcha_text

## Contact Form
app_name = 'Mistral OCR'
# Page configuration options
page_title = "Contact Us"
page_icon = ":email:"
st.set_page_config(page_title=page_title, page_icon=page_icon, layout="wide", initial_sidebar_state="expanded")

# Show the title of the app
st.header("📫 Contact Us")
st.write(":blue[*Contact for any feedback/suggestions/bug reports/features etc.*]")
st.write("")

col1, col2 = st.columns([2, 1], gap="large")  # Make Contact form column to be twice as big as CAPTCHA column

captcha_input = None  # initiate CAPTCHA

## CAPTCHA
with col2:  # right side of the layout
    st.info(' CAPTCHAs are in place to block automated submissions.', icon="ℹ️")

    if st.button("Refresh", type="secondary", use_container_width=True):  # option to refresh CAPTCHA without refreshing the page
        st.session_state.captcha_text = generate_captcha()
        captcha_text, captcha_image = st.session_state.captcha_text

    captcha_placeholder = st.empty()
    captcha_placeholder.image(captcha_image, use_container_width=True)

    captcha_input = st.text_input("Enter the CAPTCHA")  # box to insert CAPTCHA

## Contact form
with col1:  # left side of the layout
    email = st.text_input("Email: :red[*]", key='email',
                          help='Enter your email address')  # input widget for contact email
    message = st.text_area("Message: :red[*]", key='message', help='Enter your message')  # input widget for message

    st.write(':red[*] Required fields')  # indication to user that both fields must be filled

    if st.button("Send", type="primary"):
        if not email or not message:
            st.error("Please fill out all required fields.")  # error for any blank field
        else:
            try:
                # Robust email validation
                valid = validate_email(email, check_deliverability=True)

                # Check CAPTCHA
                if captcha_input.upper() == captcha_text:
                    smtp_server = server
                    smtp_port = port
                    smtp_username = user_name
                    smtp_password = password
                    recipient_email = recipient

                    ## Create an SMTP connection
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                    server.login(smtp_username, smtp_password)

                    ## Compose the email message
                    from_name = "Streamlit App"
                    subject = f"{app_name} App Feedback"  # subject of the email you will receive upon contact.
                    body = f"Email: {email}\nMessage: {message}"
                    msg = MIMEMultipart()
                    msg['From'] = f"{from_name} <{smtp_username}>"
                    msg['To'] = recipient_email
                    msg['Subject'] = subject
                    msg.attach(MIMEText(body, 'plain'))

                    ## Send the email
                    server.sendmail(smtp_username, recipient_email, msg.as_string())

                    ## Send the confirmation email to the message sender # If you do not want to send a confirmation email leave this section commented
                    # current_datetime = datetime.datetime.now()
                    # formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    # confirmation_subject = f"Confirmation of Contact Form Submission ({formatted_datetime})"
                    # confirmation_body = f"Thank you for contacting us! Your message has been received.\n\nYour message:\n {message}"
                    # confirmation_msg = MIMEMultipart()
                    # confirmation_msg['From'] = smtp_username
                    # confirmation_msg['To'] = email  # Use the sender's email address here
                    # confirmation_msg['Subject'] = confirmation_subject
                    # confirmation_msg.attach(MIMEText(confirmation_body, 'plain'))
                    # server.sendmail(smtp_username, email, confirmation_msg.as_string())

                    ## Close the SMTP server connection
                    server.quit()

                    # Acknowledgment message to the user.
                    st.success(
                        "Thank you for contacting us! Your message has been received, and we’ll respond as soon as possible.")

                    # Generate a new captcha to prevent button spamming.
                    st.session_state.captcha_text = generate_captcha()
                    captcha_text, captcha_image = st.session_state.captcha_text
                    # Update the displayed captcha image
                    captcha_placeholder.image(captcha_image, use_container_width=True)

                    time.sleep(3)
                else:
                    st.error(
                        "Text does not match the CAPTCHA.")  # error to the user in case CAPTCHA does not match input

            except EmailNotValidError as e:
                st.error(
                    f"Invalid email address. {e}")  # error in case any of the email validation checks have not passed
display_footer()