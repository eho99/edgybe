import os
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import logging

logger = logging.getLogger(__name__)

# Get the templates directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Setup Jinja2 environment
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True
)


def generate_referral_pdf(referral, organization, student, author, interventions=None) -> bytes:
    """
    Generate a PDF for a referral using WeasyPrint and Jinja2.
    
    Args:
        referral: Referral model instance
        organization: Organization model instance
        student: Profile model instance (student)
        author: Profile model instance (author)
        interventions: List of Intervention model instances (optional)
    
    Returns:
        bytes: PDF file content as bytes
    """
    try:
        # Import WeasyPrint here to allow startup without it installed
        from weasyprint import HTML, CSS
    except ImportError:
        logger.error("WeasyPrint is not installed. Install with: pip install weasyprint")
        raise ImportError("WeasyPrint is required for PDF generation")
    
    # Prepare template context
    context = {
        'organization_name': organization.name,
        'organization_phone': organization.phone_number,
        'referral_id': str(referral.id),
        'status': referral.status,
        'type': referral.type,
        'location': referral.location,
        'time_of_day': referral.time_of_day,
        'behaviors': referral.behaviors or [],
        'description': referral.description,
        'created_at': referral.created_at.strftime('%B %d, %Y at %I:%M %p') if referral.created_at else 'N/A',
        'student_name': student.full_name if student else 'N/A',
        'student_id': student.student_id if student else None,
        'grade_level': student.grade_level if student else None,
        'author_name': author.full_name if author else 'Unknown',
        'generated_at': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
        'interventions': []
    }
    
    # Add interventions if provided
    if interventions:
        for intervention in interventions:
            context['interventions'].append({
                'title': intervention.title,
                'status': intervention.status,
                'description': intervention.description,
                'creator_name': None,  # Will be populated by caller if needed
                'created_at': intervention.created_at.strftime('%B %d, %Y') if intervention.created_at else 'N/A'
            })
    
    # Load and render template
    template = jinja_env.get_template('referral_report.html')
    html_content = template.render(**context)
    
    # Generate PDF
    pdf_bytes = HTML(string=html_content).write_pdf()
    
    logger.info(f"Successfully generated PDF for referral {referral.id}")
    return pdf_bytes


def generate_html_preview(referral, organization, student, author, interventions=None) -> str:
    """
    Generate HTML preview of a referral report (for debugging/testing).
    
    Args:
        referral: Referral model instance
        organization: Organization model instance
        student: Profile model instance (student)
        author: Profile model instance (author)
        interventions: List of Intervention model instances (optional)
    
    Returns:
        str: HTML content
    """
    # Prepare template context (same as PDF generation)
    context = {
        'organization_name': organization.name,
        'organization_phone': organization.phone_number,
        'referral_id': str(referral.id),
        'status': referral.status,
        'type': referral.type,
        'location': referral.location,
        'time_of_day': referral.time_of_day,
        'behaviors': referral.behaviors or [],
        'description': referral.description,
        'created_at': referral.created_at.strftime('%B %d, %Y at %I:%M %p') if referral.created_at else 'N/A',
        'student_name': student.full_name if student else 'N/A',
        'student_id': student.student_id if student else None,
        'grade_level': student.grade_level if student else None,
        'author_name': author.full_name if author else 'Unknown',
        'generated_at': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
        'interventions': []
    }
    
    # Add interventions if provided
    if interventions:
        for intervention in interventions:
            context['interventions'].append({
                'title': intervention.title,
                'status': intervention.status,
                'description': intervention.description,
                'creator_name': None,
                'created_at': intervention.created_at.strftime('%B %d, %Y') if intervention.created_at else 'N/A'
            })
    
    # Load and render template
    template = jinja_env.get_template('referral_report.html')
    html_content = template.render(**context)
    
    return html_content

