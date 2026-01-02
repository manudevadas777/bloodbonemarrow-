import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ================= CONFIGURATION =================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  # Changed to SSL port for cloud compatibility
SENDER_EMAIL = "devadasmanu4@gmail.com"
SENDER_PASSWORD = "hbreraxiazbzhldg" 
# =================================================

def send_alert(receiver_email, subject, body):
    """
    Sends a secure Email alert using Gmail SMTP over SSL.
    Port 465 is more reliable on cloud hosting like Render.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))

        # Use SMTP_SSL for Port 465
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Success: Email sent to {receiver_email}")
        return True
    except Exception as e:
        print(f"❌ Email Failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_subject = "Cloud SMTP Test"
    test_body = "Testing the permanent SSL fix for Render deployment."
    send_alert(SENDER_EMAIL, test_subject, test_body)
