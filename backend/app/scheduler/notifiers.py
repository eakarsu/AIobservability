import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from app.config import settings

logger = logging.getLogger("ai_observability.notifiers")


def send_webhook(webhook_url: str, alert_info: dict):
    """Send alert notification via webhook."""
    try:
        response = httpx.post(
            webhook_url,
            json={"text": f"Alert: {alert_info['rule_name']}", "alert": alert_info},
            timeout=10.0,
        )
        logger.info(f"Webhook sent to {webhook_url}: {response.status_code}")
    except Exception as e:
        logger.error(f"Webhook failed: {e}")


def send_email_alert(to_email: str, alert_info: dict):
    """Send alert notification via email."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[AI Observability] Alert: {alert_info['rule_name']}"
        msg["From"] = settings.from_email
        msg["To"] = to_email

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #e53e3e;">Alert Triggered</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Rule</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{alert_info['rule_name']}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Metric</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{alert_info['metric_type']}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Value</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{alert_info['metric_value']:.4f}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Threshold</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{alert_info['condition']} {alert_info['threshold']}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Time</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{alert_info['triggered_at']}</td></tr>
            </table>
            <p style="margin-top: 20px; color: #666;">AI Observability Platform</p>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))

        if settings.smtp_user:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_pass)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.send_message(msg)

        logger.info(f"Email sent to {to_email}")
    except Exception as e:
        logger.error(f"Email failed: {e}")
