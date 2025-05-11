"""
Notification service for sending SMS and other notifications
"""
import logging
from typing import List, Optional
from twilio.rest import Client

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class NotificationService:
    """
    NotificationService handles sending notifications to supervisors and customers
    """
    
    def __init__(self):
        """Initialize notification service"""
        self.twilio_enabled = (
            settings.NOTIFICATION_ENABLED and
            settings.TWILIO_ACCOUNT_SID and
            settings.TWILIO_AUTH_TOKEN
        )
        
        if self.twilio_enabled:
            try:
                self.twilio_client = Client(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
                self.twilio_phone = settings.TWILIO_PHONE_NUMBER
                logger.info("Twilio SMS notifications initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.twilio_enabled = False
        else:
            logger.info("Twilio not configured, using console for notifications")
    
    async def notify_supervisor(self, message: str, supervisors: Optional[List[str]] = None) -> bool:
        """
        Notify a supervisor about a help request
        
        Args:
            message: The notification message
            supervisors: Optional list of supervisor phone numbers
        
        Returns:
            bool: Success status
        """
        try:
            # Use provided supervisors or get from settings
            phone_numbers = supervisors or settings.SUPERVISOR_PHONE_NUMBERS
            
            if self.twilio_enabled and phone_numbers:
                # Send SMS to each supervisor
                for phone in phone_numbers:
                    if phone:  # Skip empty phone numbers
                        try:
                            message_instance = self.twilio_client.messages.create(
                                body=message,
                                from_=self.twilio_phone,
                                to=phone
                            )
                            logger.info(f"Sent supervisor notification to {phone}, SID: {message_instance.sid}")
                        except Exception as e:
                            logger.error(f"Failed to send SMS to {phone}: {e}")
                
                return True
            else:
                # Fall back to console notification
                logger.info(f"SUPERVISOR NOTIFICATION: {message}")
                print(f"\n===== SUPERVISOR NOTIFICATION =====\n{message}\n=============================\n")
                return True
        
        except Exception as e:
            logger.error(f"Error sending supervisor notification: {e}")
            return False
    
    async def notify_customer(self, phone_number: str, message: str) -> bool:
        """
        Notify a customer with an answer
        
        Args:
            phone_number: Customer's phone number
            message: The notification message
        
        Returns:
            bool: Success status
        """
        try:
            if self.twilio_enabled:
                # Send SMS via Twilio
                message_instance = self.twilio_client.messages.create(
                    body=message,
                    from_=self.twilio_phone,
                    to=phone_number
                )
                logger.info(f"Sent customer notification to {phone_number}, SID: {message_instance.sid}")
                return True
            else:
                # Fall back to console notification
                logger.info(f"CUSTOMER NOTIFICATION to {phone_number}: {message}")
                print(f"\n===== CUSTOMER NOTIFICATION to {phone_number} =====\n{message}\n=============================\n")
                return True
        
        except Exception as e:
            logger.error(f"Error sending customer notification to {phone_number}: {e}")
            return False
    
    async def send_email(self, to: str, subject: str, body: str) -> bool:
        """
        Send an email notification (placeholder for future implementation)
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
        
        Returns:
            bool: Success status
        """
        # This would integrate with an email service like SendGrid, SES, etc.
        logger.info(f"EMAIL NOTIFICATION to {to}: Subject: {subject}")
        print(f"\n===== EMAIL NOTIFICATION to {to} =====\nSubject: {subject}\n{body}\n=============================\n")
        return True
    
    async def send_dashboard_notification(self, message: str, type: str = "info") -> bool:
        """
        Send a dashboard notification (placeholder for WebSocket implementation)
        
        Args:
            message: Notification message
            type: Notification type (info, warning, error)
        
        Returns:
            bool: Success status
        """
        # In a real implementation, this would emit an event to connected dashboard clients
        logger.info(f"DASHBOARD NOTIFICATION [{type}]: {message}")
        print(f"\n===== DASHBOARD NOTIFICATION [{type}] =====\n{message}\n=============================\n")
        return True

# Create singleton instance
notification_service = NotificationService()