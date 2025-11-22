import os
import base64
import logging
from typing import List, Optional
from pydantic import UUID4
from sqlalchemy.orm import Session

from .. import models

logger = logging.getLogger(__name__)

# Get Resend API key from environment
RESEND_API_KEY = os.getenv("RESEND_API_KEY")


# Available email variables
EMAIL_VARIABLES = [
    {"label": "Student Name", "value": "{{student_name}}", "description": "The student's full name"},
    {"label": "Student ID", "value": "{{student_id}}", "description": "The student's ID number"},
    {"label": "Grade Level", "value": "{{grade_level}}", "description": "The student's grade"},
    {"label": "Incident Type", "value": "{{type}}", "description": "Type of referral (Behavior, Academic, etc.)"},
    {"label": "Location", "value": "{{location}}", "description": "Where the incident occurred"},
    {"label": "Time", "value": "{{time_of_day}}", "description": "When the incident occurred"},
    {"label": "Behaviors", "value": "{{behaviors}}", "description": "Comma-separated list of behaviors"},
    {"label": "Description", "value": "{{description}}", "description": "Full incident description"},
    {"label": "Date Created", "value": "{{created_at}}", "description": "When the referral was created"},
    {"label": "Author Name", "value": "{{author_name}}", "description": "Name of staff member who created referral"},
    {"label": "Org Name", "value": "{{organization_name}}", "description": "Name of your organization"},
    {"label": "Org Phone", "value": "{{organization_phone}}", "description": "Phone number of your organization"},
]


def get_email_variables() -> List[dict]:
    """
    Get list of available email template variables.
    """
    return EMAIL_VARIABLES


def send_referral_email(
    db: Session,
    referral_id: UUID4,
    recipient_emails: List[str],
    subject: str,
    message: str,
    pdf_bytes: Optional[bytes] = None,
    sender_email: str = "noreply@edgybe.com"
) -> tuple[bool, str, Optional[UUID4]]:
    """
    Send a referral email via Resend with optional PDF attachment.
    
    Args:
        db: Database session
        referral_id: UUID of the referral
        recipient_emails: List of recipient email addresses
        subject: Email subject
        message: Email body (can include HTML)
        pdf_bytes: Optional PDF file content as bytes
        sender_email: Sender email address
    
    Returns:
        tuple: (success: bool, message: str, log_id: Optional[UUID4])
    """
    if not RESEND_API_KEY:
        logger.error("RESEND_API_KEY not set in environment variables")
        return (False, "Email service not configured", None)
    
    try:
        import resend
    except ImportError:
        logger.error("Resend SDK is not installed. Install with: pip install resend")
        return (False, "Email service not available", None)
    
    # Configure Resend
    resend.api_key = RESEND_API_KEY
    
    # Prepare attachments
    attachments = []
    if pdf_bytes:
        # Encode PDF as base64
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        attachments.append({
            "filename": f"referral_{referral_id}.pdf",
            "content": pdf_base64
        })
    
    # Send to each recipient and log
    all_succeeded = True
    failed_recipients = []
    log_ids = []
    
    for recipient_email in recipient_emails:
        try:
            # Send email
            email_params = {
                "from": sender_email,
                "to": [recipient_email],
                "subject": subject,
                "html": message,
            }
            
            if attachments:
                email_params["attachments"] = attachments
            
            response = resend.Emails.send(email_params)
            
            # Log successful send
            log = models.CommunicationLog(
                referral_id=referral_id,
                communication_type="email",
                recipient_email=recipient_email,
                subject=subject,
                status="sent",
                error_message=None
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            log_ids.append(log.id)
            
            logger.info(f"Successfully sent email to {recipient_email} for referral {referral_id}")
            
        except Exception as e:
            all_succeeded = False
            failed_recipients.append(recipient_email)
            error_msg = str(e)
            logger.error(f"Failed to send email to {recipient_email}: {error_msg}")
            
            # Log failed send
            log = models.CommunicationLog(
                referral_id=referral_id,
                communication_type="email",
                recipient_email=recipient_email,
                subject=subject,
                status="failed",
                error_message=error_msg
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            log_ids.append(log.id)
    
    # Prepare result message
    if all_succeeded:
        result_message = f"Email sent successfully to all {len(recipient_emails)} recipient(s)"
    else:
        result_message = f"Email sent to {len(recipient_emails) - len(failed_recipients)} recipient(s). Failed: {', '.join(failed_recipients)}"
    
    return (all_succeeded, result_message, log_ids[0] if log_ids else None)


def render_email_template(template_body: str, context: dict) -> str:
    """
    Render an email template with Jinja2.
    
    Args:
        template_body: Email template string with Jinja2 syntax
        context: Dictionary of variables to render
    
    Returns:
        str: Rendered email content
    """
    from jinja2 import Template
    
    try:
        template = Template(template_body)
        return template.render(**context)
    except Exception as e:
        logger.error(f"Failed to render email template: {str(e)}")
        return template_body  # Return original if rendering fails


def get_email_context_for_referral(referral, organization, student, author) -> dict:
    """
    Prepare email template context for a referral.
    
    Args:
        referral: Referral model instance
        organization: Organization model instance
        student: Profile model instance (student)
        author: Profile model instance (author)
    
    Returns:
        dict: Context dictionary for template rendering
    """
    return {
        'organization_name': organization.name,
        'organization_phone': organization.phone_number,
        'referral_id': str(referral.id),
        'status': referral.status,
        'type': referral.type,
        'location': referral.location or 'N/A',
        'time_of_day': referral.time_of_day or 'N/A',
        'behaviors': ', '.join(referral.behaviors) if referral.behaviors else 'N/A',
        'description': referral.description or 'N/A',
        'created_at': referral.created_at.strftime('%B %d, %Y at %I:%M %p') if referral.created_at else 'N/A',
        'student_name': student.full_name if student else 'N/A',
        'student_id': student.student_id if student else 'N/A',
        'grade_level': student.grade_level if student else 'N/A',
        'author_name': author.full_name if author else 'Unknown',
    }

