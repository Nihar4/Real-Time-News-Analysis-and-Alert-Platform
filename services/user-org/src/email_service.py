import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
import os
from src.config import settings

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "futurefeedalerts@gmail.com")
        # Remove spaces from app password (Gmail app passwords have spaces for readability)
        self.smtp_password = os.getenv("SMTP_PASSWORD", "").replace(" ", "")
        self.smtp_from = os.getenv("SMTP_FROM", "futurefeedalerts@gmail.com")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.logo_dev_token = os.getenv("LOGO_DEV_TOKEN", "")

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        """Send an email using Gmail SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_from
            msg['To'] = to_email
            msg['Subject'] = subject

            # Add text version if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)

            # Add HTML version
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Try SSL first (port 465), then STARTTLS (port 587)
            try:
                # Method 1: SMTP_SSL (port 465)
                with smtplib.SMTP_SSL(self.smtp_host, 465, timeout=30) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
                return True
            except Exception as ssl_error:
                print(f"SMTP_SSL failed: {ssl_error}, trying STARTTLS...")
                # Method 2: STARTTLS (port 587)
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
                return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False

    def send_invitation_email(self, to_email: str, to_name: str, org_name: str, token: str):
        """Send invitation email with password setup link"""
        setup_link = f"{self.frontend_url}/invite/{token}"
        
        subject = f"You're invited to join {org_name} on FutureFeed"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #334155; margin: 0; padding: 0; background-color: #f1f5f9; }}
                .container {{ max-width: 600px; margin: 40px auto; background-color: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
                .header {{ background: linear-gradient(to right, #4f46e5, #7c3aed); color: white; padding: 32px; text-align: center; }}
                .content {{ padding: 40px; }}
                .button {{ display: inline-block; background-color: #4f46e5; color: white !important; padding: 14px 28px; text-decoration: none; border-radius: 12px; margin: 24px 0; font-weight: 600; text-align: center; }}
                .footer {{ text-align: center; padding: 24px; background-color: #f8fafc; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
                .logo {{ font-size: 24px; font-weight: bold; margin-bottom: 8px; display: block; }}
                .link-box {{ background-color: #f1f5f9; padding: 12px; border-radius: 8px; word-break: break-all; font-family: monospace; font-size: 12px; color: #64748b; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <span class="logo">FutureFeed</span>
                    <div style="font-size: 16px; opacity: 0.9;">Competitor Intelligence Platform</div>
                </div>
                <div class="content">
                    <h2 style="color: #1e293b; margin-top: 0;">Welcome Aboard!</h2>
                    <p>Hi {to_name},</p>
                    <p>You've been invited to join <strong>{org_name}</strong> on FutureFeed. We help teams stay ahead by tracking competitor moves and market shifts in real-time.</p>
                    <p>To activate your account and set up your password, please click the button below:</p>
                    <center>
                        <a href="{setup_link}" class="button">Accept Invitation</a>
                    </center>
                    <p style="margin-bottom: 8px;">Or copy this link into your browser:</p>
                    <div class="link-box">{setup_link}</div>
                    <p style="font-size: 13px; color: #64748b; margin-top: 24px;"><strong>Note:</strong> This invitation link will expire in 48 hours for security reasons.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 FutureFeed. All rights reserved.</p>
                    <p>If you didn't expect this invitation, you can safely ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to FutureFeed!

        Hi {to_name},

        You've been invited to join {org_name} on FutureFeed.

        To get started, please set up your password by visiting:
        {setup_link}

        This invitation link will expire in 48 hours.

        If you didn't expect this invitation, you can safely ignore this email.
        """
        
        return self.send_email(to_email, subject, html_content, text_content)

    def send_event_alert_email(self, to_email: str, to_name: str, event_title: str, 
                               event_description: str, company_name: str, event_date: str, event_id: str):
        """Send event alert email to organization members"""
        event_link = f"{self.frontend_url}/events/{event_id}"
        
        # Heuristic for logo: assume slug is company name lowercased and stripped of spaces
        # In a real app, we should pass the slug. For now, we'll try to guess it or use a generic one.
        # Since we don't have the slug here easily without changing the signature, let's try a best effort
        # or just use the company name for the alt text.
        # Wait, we can try to generate a slug from the name for the logo API.
        slug = company_name.lower().replace(" ", "").replace(".", "").replace(",", "")
        if self.logo_dev_token:
            logo_url = f"https://img.logo.dev/{slug}.com?token={self.logo_dev_token}"
        else:
            logo_url = f"https://ui-avatars.com/api/?name={slug}&background=random"
        
        subject = f"Alert: {event_title} - {company_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #334155; margin: 0; padding: 0; background-color: #f1f5f9; }}
                .container {{ max-width: 600px; margin: 40px auto; background-color: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
                .header {{ background: linear-gradient(to right, #4f46e5, #7c3aed); color: white; padding: 24px; text-align: center; }}
                .content {{ padding: 32px; }}
                .event-card {{ background-color: #f8fafc; padding: 24px; border-left: 4px solid #4f46e5; border-radius: 0 8px 8px 0; margin: 24px 0; }}
                .button {{ display: inline-block; background-color: #4f46e5; color: white !important; padding: 12px 24px; text-decoration: none; border-radius: 10px; margin: 20px 0; font-weight: 600; }}
                .footer {{ text-align: center; padding: 24px; background-color: #f8fafc; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
                .tag {{ display: inline-block; background-color: #e0e7ff; color: #4338ca; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; text-transform: uppercase; }}
                .company-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }}
                .company-logo {{ width: 48px; height: 48px; border-radius: 8px; object-fit: contain; background-color: white; border: 1px solid #e2e8f0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin:0; font-size: 20px;">FutureFeed Alert</h1>
                </div>
                <div class="content">
                    <p>Hi {to_name},</p>
                    <p>We detected a new strategic event for <strong>{company_name}</strong>:</p>
                    
                    <div class="event-card">
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                            <img src="{logo_url}" alt="{company_name}" class="company-logo" onerror="this.style.display='none'">
                            <div>
                                <h2 style="margin: 0; color: #1e293b; font-size: 18px;">{event_title}</h2>
                                <p style="margin: 0; color: #64748b; font-size: 14px;">{company_name}</p>
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 12px;">
                            <span class="tag">New Insight</span>
                        </div>
                        
                        <p style="margin-bottom: 4px;"><strong>Date:</strong> {event_date}</p>
                        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 16px 0;">
                        <p style="color: #475569;">{event_description}</p>
                    </div>
                    
                    <center>
                        <a href="{event_link}" class="button">View Full Analysis</a>
                    </center>
                </div>
                <div class="footer">
                    <p>You received this alert because your organization tracks {company_name}.</p>
                    <p>&copy; 2024 FutureFeed. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        FutureFeed Alert

        Hi {to_name},

        We detected a new strategic event for {company_name}:

        Event: {event_title}
        Company: {company_name}
        Date: {event_date}

        Description:
        {event_description}

        View full analysis: {event_link}

        You received this alert because your organization tracks {company_name}.
        """
        
        return self.send_email(to_email, subject, html_content, text_content)

# Singleton instance
email_service = EmailService()
