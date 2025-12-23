import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

class EmailService:
    @staticmethod
    def generate_assignment_email_html(student_name: str, assignment_title: str, due_date: str, link: str) -> str:
        """
        Generate an HTML email body for a new assignment.
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .header {{ color: #4a90e2; border-bottom: 2px solid #4a90e2; padding-bottom: 10px; margin-bottom: 20px; }}
                .details {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .button {{ display: inline-block; background-color: #4a90e2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #888; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2 class="header">New Assignment Posted</h2>
                <p>Hello <strong>{student_name}</strong>,</p>
                <p>Your teacher has posted a new assignment for your class.</p>
                
                <div class="details">
                    <p><strong>Assignment:</strong> {assignment_title}</p>
                    <p><strong>Due Date:</strong> {due_date}</p>
                </div>
                
                <p>Please log in to your dashboard to view the full details and start working.</p>
                
                <div style="text-align: center;">
                    <a href="{link}" class="button">View Assignment</a>
                </div>
                
                <div class="footer">
                    <p>This is an automated notification from your Learning Platform.</p>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    async def send_email(to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """
        Send an email to a single recipient.
        """
        # Get credentials from environment variables
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        sender_email = os.getenv("SMTP_EMAIL")
        sender_password = os.getenv("SMTP_PASSWORD")

        # Mock sending if credentials are not configured
        if not sender_email or not sender_password:
            print(f"\n[Mock Email Service]")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Body Preview: {body[:100]}...")
            if html_body:
                print(f"HTML Body Present: Yes")
            print("-" * 30 + "\n")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender_email
            msg["To"] = to_email

            # Attach plain text version
            part1 = MIMEText(body, "plain")
            msg.attach(part1)

            # Attach HTML version if provided
            if html_body:
                part2 = MIMEText(html_body, "html")
                msg.attach(part2)

            # Connect to server and send
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, to_email, msg.as_string())
            
            print(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False