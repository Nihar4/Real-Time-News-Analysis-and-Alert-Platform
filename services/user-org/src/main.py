from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import auth, org, companies, events, tasks

from contextlib import asynccontextmanager
import asyncio
from src.notification_service import notification_service
from src.email_service import email_service
from datetime import datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Send test email on startup
    try:
        test_email_sent = email_service.send_email(
            to_email="niharpatel4444@gmail.com",
            subject="🚀 User-Org Service Started Successfully",
            html_content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #334155; margin: 0; padding: 0; background-color: #f1f5f9; }}
                    .container {{ max-width: 600px; margin: 40px auto; background-color: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
                    .header {{ background: linear-gradient(to right, #10b981, #059669); color: white; padding: 32px; text-align: center; }}
                    .content {{ padding: 40px; }}
                    .info-box {{ background-color: #f0fdf4; padding: 16px; border-left: 4px solid #10b981; border-radius: 0 8px 8px 0; margin: 20px 0; }}
                    .footer {{ text-align: center; padding: 24px; background-color: #f8fafc; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin:0; font-size: 24px;">✅ Service Status: Running</h1>
                    </div>
                    <div class="content">
                        <h2 style="color: #1e293b; margin-top: 0;">User-Org Service Restarted</h2>
                        <p>The <strong>user-org</strong> service has successfully restarted and the email service is working correctly.</p>
                        
                        <div class="info-box">
                            <p style="margin: 0;"><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            <p style="margin: 8px 0 0 0;"><strong>Service:</strong> user-org (NewsInsight)</p>
                        </div>
                        
                        <p>This is an automated test email to confirm:</p>
                        <ul>
                            <li>✅ SMTP configuration is correct</li>
                            <li>✅ Email service is operational</li>
                            <li>✅ Service startup completed successfully</li>
                        </ul>
                    </div>
                    <div class="footer">
                        <p>&copy; 2024 FutureFeed. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            text_content=f"""
            User-Org Service Restarted
            
            The user-org service has successfully restarted and the email service is working correctly.
            
            Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Service: user-org (NewsInsight)
            
            This is an automated test email to confirm:
            - SMTP configuration is correct
            - Email service is operational
            - Service startup completed successfully
            """
        )
        if test_email_sent:
            print("✅ Test email sent successfully to niharpatel4444@gmail.com")
        else:
            print("❌ Failed to send test email")
    except Exception as e:
        print(f"❌ Error sending test email: {str(e)}")
    
    # Start notification service in background
    task = asyncio.create_task(notification_service.run())
    yield
    # Cleanup
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="User & Organization Service", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(org.router)
app.include_router(companies.router)
app.include_router(events.router)
app.include_router(tasks.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
