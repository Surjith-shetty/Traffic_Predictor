from app import app, mail
from flask_mail import Message

def test_email():
    with app.app_context():
        try:
            print("Testing email configuration...")
            print(f"SMTP Server: {app.config['MAIL_SERVER']}")
            print(f"SMTP Port: {app.config['MAIL_PORT']}")
            print(f"Username: {app.config['MAIL_USERNAME']}")
            print(f"TLS: {app.config['MAIL_USE_TLS']}")
            
            # Test email
            msg = Message(
                subject='🕉️ Test Email from Divine Darshan',
                recipients=['srikharsri.j@gmail.com'],  # Send to yourself
                body='This is a test email to verify email configuration is working.'
            )
            
            mail.send(msg)
            print("✅ Test email sent successfully!")
            
        except Exception as e:
            print(f"❌ Email test failed: {e}")
            print("\n📋 To fix email issues:")
            print("1. Go to https://myaccount.google.com/security")
            print("2. Enable 2-Step Verification")
            print("3. Generate App Password for 'Mail'")
            print("4. Update MAIL_PASSWORD in config.py with the 16-character app password")

if __name__ == "__main__":
    test_email()