import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart  # Note this should be the correct import as well
import os
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("SMTP_EMAIL")
        self.sender_password = os.getenv("SMTP_PASSWORD")
    
    async def send_verification_email(self, recipient_email: str, verification_code: str, user_pin: str):
        """Send verification email with OTP code"""
        try:
            # Skip if no email configuration
            if not self.sender_email or not self.sender_password:
                print(f"📧 [DEV MODE] Verification code for {recipient_email}: {verification_code}")
                print(f"📌 [DEV MODE] User PIN: {user_pin}")
                return True
            
            # Create message
            subject = "Secret Chat - Email Verification"
            
            body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background: #f9f9f9; }}
                    .code {{ font-size: 32px; font-weight: bold; color: #4F46E5; text-align: center; margin: 20px 0; }}
                    .pin {{ background: #e9ecef; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Secret Chat</h1>
                    </div>
                    <div class="content">
                        <h2>Email Verification</h2>
                        <p>Hello,</p>
                        <p>Thank you for registering with Secret Chat. Please use the verification code below to complete your registration:</p>
                        
                        <div class="code">{verification_code}</div>
                        
                        <p>This code will expire in 24 hours.</p>
                        
                        <div class="pin">
                            <strong>Your Unique PIN:</strong> {user_pin}
                            <br><small>Share this PIN with friends to start chatting securely!</small>
                        </div>
                        
                        <p>If you didn't create an account, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2024 Secret Chat. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = recipient_email
            message["Subject"] = subject
            
            message.attach(MIMEText(body, "html"))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            print(f"✅ Verification email sent to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {recipient_email}: {e}")
            # Fallback to console print
            print(f"📧 [FALLBACK] Verification code for {recipient_email}: {verification_code}")
            print(f"📌 [FALLBACK] User PIN: {user_pin}")
            return False

# Global instance
email_service = EmailService()
