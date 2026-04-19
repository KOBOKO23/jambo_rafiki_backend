"""
Email service utilities
"""
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.conf import settings
from typing import List, Optional


class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def send_simple_email(
        subject: str,
        message: str,
        recipient_list: List[str],
        from_email: Optional[str] = None,
        fail_silently: bool = True
    ) -> int:
        """
        Send a simple text email
        
        Args:
            subject: Email subject
            message: Email body (plain text)
            recipient_list: List of recipient email addresses
            from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
            fail_silently: If False, raise exception on failure
        
        Returns:
            Number of emails sent
        """
        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL
        
        return send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=fail_silently,
        )
    
    @staticmethod
    def send_html_email(
        subject: str,
        html_content: str,
        recipient_list: List[str],
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        fail_silently: bool = True
    ) -> int:
        """
        Send an HTML email with optional plain text fallback
        
        Args:
            subject: Email subject
            html_content: HTML email body
            recipient_list: List of recipient email addresses
            text_content: Plain text fallback (optional)
            from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
            fail_silently: If False, raise exception on failure
        
        Returns:
            Number of emails sent
        """
        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL
        
        if text_content is None:
            # Strip HTML tags for text version
            import re
            text_content = re.sub('<[^<]+?>', '', html_content)
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipient_list
        )
        msg.attach_alternative(html_content, "text/html")
        
        try:
            msg.send()
            return 1
        except Exception as e:
            if not fail_silently:
                raise
            print(f"Failed to send email: {e}")
            return 0
    
    @staticmethod
    def send_bulk_email(
        subject: str,
        message: str,
        recipient_list: List[str],
        from_email: Optional[str] = None,
        batch_size: int = 100
    ) -> int:
        """
        Send bulk emails in batches
        
        Args:
            subject: Email subject
            message: Email body
            recipient_list: List of recipient email addresses
            from_email: Sender email
            batch_size: Number of emails per batch
        
        Returns:
            Total number of emails sent
        """
        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL
        
        total_sent = 0
        
        # Send in batches
        for i in range(0, len(recipient_list), batch_size):
            batch = recipient_list[i:i + batch_size]
            sent = EmailService.send_simple_email(
                subject=subject,
                message=message,
                recipient_list=batch,
                from_email=from_email,
                fail_silently=True
            )
            total_sent += sent
        
        return total_sent
    
    @staticmethod
    def send_admin_notification(subject: str, message: str) -> int:
        """
        Send notification to admin email
        
        Args:
            subject: Email subject
            message: Email body
        
        Returns:
            Number of emails sent
        """
        return EmailService.send_simple_email(
            subject=f"[Admin] {subject}",
            message=message,
            recipient_list=list(settings.ADMIN_NOTIFICATION_EMAILS),
        )


# Convenience functions
def send_email(subject: str, message: str, recipient_list: List[str]) -> int:
    """Shortcut to send simple email"""
    return EmailService.send_simple_email(subject, message, recipient_list)


def send_admin_email(subject: str, message: str) -> int:
    """Shortcut to send admin notification"""
    return EmailService.send_admin_notification(subject, message)
