
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(
    receiver_email,
    subject,
    body
):

    sender_email = "tapandattapeketi7@gmail.com"

    app_password = "pgnqmwlwylqhlbvo"

    message = MIMEMultipart()

    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(
        MIMEText(body, "plain")
    )

    try:

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()

        server.login(
            sender_email,
            app_password
        )

        server.sendmail(
            sender_email,
            receiver_email,
            message.as_string()
        )

        server.quit()

        print("Email Sent Successfully")

    except Exception as e:

        print("Error:", e)
