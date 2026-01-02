import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ================= CONFIGURATION =================
# Use your verified Gmail credentials here
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "devadasmanu4@gmail.com"
SENDER_PASSWORD = "hbreraxiazbzhldg" # Your 16-character App Password
# =================================================

def send_alert(receiver_email, subject, body):
    """
    Sends a secure Email alert using Gmail SMTP.
    This replaces the SMS option to keep the project cost-free.
    """
    try:
        # Create the email container
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = subject
        
        # Attach the plain-text body
        msg.attach(MIMEText(body, 'plain'))

        # Connect to the server and send
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection with TLS encryption
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Success: Email sent to {receiver_email}")
        return True
    except Exception as e:
        # Log the error to the terminal for debugging
        print(f"❌ Email Failed: {str(e)}")
        return False

# --- SELF-TEST BLOCK ---
# Run 'python notifications.py' to test your Gmail connection directly
if __name__ == "__main__":
    print("🚀 Testing Free Email Notification System...")
    test_subject = "Portal Connection Test"
    test_body = "Your Blood and Bone Marrow Portal is successfully sending email alerts!"
    
    send_alert(SENDER_EMAIL, test_subject, test_body)
    print("🏁 Test sequence complete.")