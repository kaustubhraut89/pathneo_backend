import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, Optional
from app.core.config import settings

def send_email(
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"SMTP not configured. Email to {email_to} with subject '{subject}' not sent.")
        print(f"Content: {html_content}")
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    message["To"] = email_to

    part = MIMEText(html_content, "html")
    message.attach(part)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM_EMAIL, email_to, message.as_string())
    except Exception as e:
        print(f"Error sending email to {email_to}: {e}")

def send_otp_email(email: str, otp: str) -> None:
    subject = f"{otp} is your Pathneo verification code"
    html_content = f"""
      <html><body style="margin:0;padding:0;background:#f4f6fb;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
        <tr><td align="center">
          <table width="520" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #e0e0e0;">
            <tr>
             <td style="background:#1a1a2e;padding:28px 32px;text-align:center;">
    <span style="font-size:28px;font-weight:700;color:#ffffff;letter-spacing:-1px;">Path</span>&thinsp;<span style="font-size:28px;font-weight:300;color:#00FFB2;letter-spacing:-1px;">neo</span>
             </td>
            </tr>
            <tr>
              <td style="padding:36px 32px 24px;text-align:center;">
                <h2 style="margin:0 0 8px;font-size:22px;color:#1a1a2e;">Verify your email</h2>
                <p style="margin:0;font-size:14px;color:#6b7280;line-height:1.7;">
                  Use the code below to complete your Pathneo signup.<br>It expires in <strong>10 minutes</strong>.
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:0 32px 24px;">
                <div style="background:#EEEDFE;border-radius:12px;padding:24px;text-align:center;">
                  <p style="margin:0 0 12px;font-size:11px;color:#534AB7;letter-spacing:2px;text-transform:uppercase;font-weight:bold;">Your verification code</p>
                  <div style="font-size:36px;font-weight:bold;color:#3C3489;letter-spacing:10px;margin-top:4px;">{otp}</div>
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:0 32px 28px;">
                <div style="background:#f9fafb;border-radius:8px;padding:14px 16px;">
                  <p style="margin:0;font-size:13px;color:#6b7280;line-height:1.6;">
                    If you did not request this code, you can safely ignore this email.
                  </p>
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:16px 32px;border-top:1px solid #e0e0e0;text-align:center;">
                <p style="margin:0;font-size:12px;color:#9ca3af;">© 2026 Pathneo. All rights reserved.</p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body></html>
    """
    send_email(email_to=email, subject=subject, html_content=html_content)