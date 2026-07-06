"""Notification Service

Handles notifications for alerts, anomalies, budget thresholds, etc.
Supports multiple channels: email, webhooks, Slack, Discord.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)


class NotificationType(Enum):
    """Types of notifications."""
    ANOMALY_DETECTED = "anomaly_detected"
    BUDGET_THRESHOLD = "budget_threshold"
    COST_SPIKE = "cost_spike"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SAFETY_VIOLATION = "safety_violation"
    SYSTEM_ALERT = "system_alert"
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_REPORT = "weekly_report"


class NotificationChannel(Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    IN_APP = "in_app"


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationService:
    """Service for sending notifications through various channels."""
    
    def __init__(self):
        """Initialize notification service."""
        self.smtp_enabled = bool(settings.SMTP_HOST)
        self.webhook_timeout = 10  # seconds
        
    async def send_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        recipients: Optional[List[str]] = None,
        channels: Optional[List[NotificationChannel]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send notification through specified channels.
        
        Args:
            notification_type: Type of notification
            title: Notification title
            message: Notification message body
            priority: Priority level
            recipients: List of recipient emails/IDs
            channels: Delivery channels to use
            metadata: Additional metadata
        
        Returns:
            Status of notification delivery
        """
        if channels is None:
            channels = [NotificationChannel.EMAIL]
        
        results = {}
        
        # Send through each channel
        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    if recipients:
                        result = await self._send_email(
                            recipients, title, message, priority, metadata
                        )
                        results['email'] = result
                
                elif channel == NotificationChannel.WEBHOOK:
                    result = await self._send_webhook(
                        notification_type, title, message, priority, metadata
                    )
                    results['webhook'] = result
                
                elif channel == NotificationChannel.SLACK:
                    result = await self._send_slack(
                        title, message, priority, metadata
                    )
                    results['slack'] = result
                
                elif channel == NotificationChannel.DISCORD:
                    result = await self._send_discord(
                        title, message, priority, metadata
                    )
                    results['discord'] = result
                
            except Exception as e:
                logger.error(f"Error sending notification via {channel.value}: {e}")
                results[channel.value] = {"success": False, "error": str(e)}
        
        return {
            "notification_type": notification_type.value,
            "title": title,
            "priority": priority.value,
            "timestamp": datetime.utcnow().isoformat(),
            "channels": results
        }
    
    async def _send_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        priority: NotificationPriority,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send email notification."""
        if not self.smtp_enabled:
            logger.warning("SMTP not configured, skipping email notification")
            return {"success": False, "error": "SMTP not configured"}
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{priority.value.upper()}] {subject}"
            msg['From'] = settings.SMTP_FROM_EMAIL
            msg['To'] = ", ".join(recipients)
            
            # Create HTML body
            html_body = self._create_email_html(subject, body, priority, metadata)
            
            # Attach parts
            text_part = MIMEText(body, 'plain')
            html_part = MIMEText(html_body, 'html')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email sent to {len(recipients)} recipients: {subject}")
            return {
                "success": True,
                "recipients_count": len(recipients),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_webhook(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send webhook notification."""
        if not settings.WEBHOOK_URL:
            logger.warning("Webhook URL not configured")
            return {"success": False, "error": "Webhook URL not configured"}
        
        try:
            payload = {
                "type": notification_type.value,
                "title": title,
                "message": message,
                "priority": priority.value,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            async with httpx.AsyncClient(timeout=self.webhook_timeout) as client:
                response = await client.post(
                    settings.WEBHOOK_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
            
            logger.info(f"Webhook sent: {title}")
            return {
                "success": True,
                "status_code": response.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_slack(
        self,
        title: str,
        message: str,
        priority: NotificationPriority,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send Slack notification."""
        if not settings.SLACK_WEBHOOK_URL:
            logger.warning("Slack webhook URL not configured")
            return {"success": False, "error": "Slack webhook not configured"}
        
        try:
            # Color based on priority
            color_map = {
                NotificationPriority.LOW: "#36a64f",
                NotificationPriority.MEDIUM: "#ff9900",
                NotificationPriority.HIGH: "#ff6600",
                NotificationPriority.CRITICAL: "#ff0000"
            }
            
            payload = {
                "attachments": [
                    {
                        "fallback": f"{title}: {message}",
                        "color": color_map.get(priority, "#36a64f"),
                        "title": title,
                        "text": message,
                        "footer": "AI Gateway Monitoring",
                        "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            # Add metadata fields if present
            if metadata:
                fields = []
                for key, value in metadata.items():
                    fields.append({
                        "title": key.replace("_", " ").title(),
                        "value": str(value),
                        "short": True
                    })
                payload["attachments"][0]["fields"] = fields
            
            async with httpx.AsyncClient(timeout=self.webhook_timeout) as client:
                response = await client.post(
                    settings.SLACK_WEBHOOK_URL,
                    json=payload
                )
                response.raise_for_status()
            
            logger.info(f"Slack notification sent: {title}")
            return {"success": True, "timestamp": datetime.utcnow().isoformat()}
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_discord(
        self,
        title: str,
        message: str,
        priority: NotificationPriority,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send Discord notification."""
        if not settings.DISCORD_WEBHOOK_URL:
            logger.warning("Discord webhook URL not configured")
            return {"success": False, "error": "Discord webhook not configured"}
        
        try:
            # Color based on priority (Discord uses decimal colors)
            color_map = {
                NotificationPriority.LOW: 3066993,      # Green
                NotificationPriority.MEDIUM: 16776960,  # Yellow
                NotificationPriority.HIGH: 16744448,    # Orange
                NotificationPriority.CRITICAL: 15158332 # Red
            }
            
            embed = {
                "title": title,
                "description": message,
                "color": color_map.get(priority, 3066993),
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "AI Gateway Monitoring"
                }
            }
            
            # Add metadata fields
            if metadata:
                fields = []
                for key, value in metadata.items():
                    fields.append({
                        "name": key.replace("_", " ").title(),
                        "value": str(value),
                        "inline": True
                    })
                embed["fields"] = fields
            
            payload = {"embeds": [embed]}
            
            async with httpx.AsyncClient(timeout=self.webhook_timeout) as client:
                response = await client.post(
                    settings.DISCORD_WEBHOOK_URL,
                    json=payload
                )
                response.raise_for_status()
            
            logger.info(f"Discord notification sent: {title}")
            return {"success": True, "timestamp": datetime.utcnow().isoformat()}
            
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_email_html(
        self,
        subject: str,
        body: str,
        priority: NotificationPriority,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create HTML email body."""
        # Priority color
        priority_colors = {
            NotificationPriority.LOW: "#28a745",
            NotificationPriority.MEDIUM: "#ffc107",
            NotificationPriority.HIGH: "#fd7e14",
            NotificationPriority.CRITICAL: "#dc3545"
        }
        color = priority_colors.get(priority, "#007bff")
        
        # Build metadata HTML
        metadata_html = ""
        if metadata:
            metadata_html = "<h3>Details</h3><ul>"
            for key, value in metadata.items():
                metadata_html += f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>"
            metadata_html += "</ul>"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }}
                .priority {{ display: inline-block; padding: 5px 10px; background-color: {color}; color: white; border-radius: 3px; font-weight: bold; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
                ul {{ padding-left: 20px; }}
                li {{ margin-bottom: 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>AI Gateway Alert</h2>
                </div>
                <div class="content">
                    <p><span class="priority">{priority.value.upper()}</span></p>
                    <h2>{subject}</h2>
                    <p>{body}</p>
                    {metadata_html}
                    <div class="footer">
                        <p>Sent by AI Gateway Monitoring Platform</p>
                        <p>Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    async def send_anomaly_alert(
        self,
        anomaly_type: str,
        severity: str,
        description: str,
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send anomaly detection alert."""
        priority_map = {
            "low": NotificationPriority.LOW,
            "medium": NotificationPriority.MEDIUM,
            "high": NotificationPriority.HIGH,
            "critical": NotificationPriority.CRITICAL
        }
        
        priority = priority_map.get(severity.lower(), NotificationPriority.MEDIUM)
        
        return await self.send_notification(
            notification_type=NotificationType.ANOMALY_DETECTED,
            title=f"Anomaly Detected: {anomaly_type}",
            message=description,
            priority=priority,
            metadata=metadata,
            channels=[NotificationChannel.WEBHOOK, NotificationChannel.SLACK]
        )
    
    async def send_budget_alert(
        self,
        department_name: str,
        current_usage: float,
        budget_limit: float,
        utilization_percent: float,
        recipients: List[str]
    ) -> Dict[str, Any]:
        """Send budget threshold alert."""
        priority = NotificationPriority.HIGH if utilization_percent >= 95 else NotificationPriority.MEDIUM
        
        message = (
            f"Department '{department_name}' has reached {utilization_percent:.1f}% "
            f"of monthly budget.\n\n"
            f"Current Usage: ${current_usage:.2f}\n"
            f"Budget Limit: ${budget_limit:.2f}\n"
            f"Remaining: ${budget_limit - current_usage:.2f}"
        )
        
        return await self.send_notification(
            notification_type=NotificationType.BUDGET_THRESHOLD,
            title=f"Budget Alert: {department_name}",
            message=message,
            priority=priority,
            recipients=recipients,
            channels=[NotificationChannel.EMAIL, NotificationChannel.WEBHOOK],
            metadata={
                "department": department_name,
                "utilization": f"{utilization_percent:.1f}%",
                "current_usage": f"${current_usage:.2f}",
                "budget_limit": f"${budget_limit:.2f}"
            }
        )
    
    async def send_cost_spike_alert(
        self,
        spike_amount: float,
        time_window: str,
        description: str,
        recipients: List[str]
    ) -> Dict[str, Any]:
        """Send cost spike alert."""
        return await self.send_notification(
            notification_type=NotificationType.COST_SPIKE,
            title="Unusual Cost Spike Detected",
            message=description,
            priority=NotificationPriority.HIGH,
            recipients=recipients,
            channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
            metadata={
                "spike_amount": f"${spike_amount:.2f}",
                "time_window": time_window
            }
        )
    
    async def send_daily_summary(
        self,
        db: Session,
        recipients: List[str],
        summary_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send daily usage summary."""
        message = (
            f"Daily AI Gateway Summary\n\n"
            f"Total Requests: {summary_data.get('total_requests', 0)}\n"
            f"Total Cost: ${summary_data.get('total_cost', 0):.2f}\n"
            f"Average Latency: {summary_data.get('avg_latency', 0):.0f}ms\n"
            f"Error Rate: {summary_data.get('error_rate', 0):.2f}%\n"
        )
        
        return await self.send_notification(
            notification_type=NotificationType.DAILY_SUMMARY,
            title="Daily AI Gateway Summary",
            message=message,
            priority=NotificationPriority.LOW,
            recipients=recipients,
            channels=[NotificationChannel.EMAIL],
            metadata=summary_data
        )


# Global notification service instance
notification_service = NotificationService()
