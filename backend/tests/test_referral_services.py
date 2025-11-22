"""
Unit tests for referral services (PDF and Email) using arrange-act-assert pattern.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid
import sys
from datetime import datetime, timezone

from app.models import Organization, Profile, Referral, Intervention
from app.services import pdf_service, email_service


# ============================================================================
# ARRANGE: Reusable Test Fixtures
# ============================================================================

@pytest.fixture
def mock_organization():
    """Mock organization for testing."""
    org = Mock(spec=Organization)
    org.id = uuid.uuid4()
    org.name = "Test High School"
    org.phone_number = "+14155551234"
    return org


@pytest.fixture
def mock_student():
    """Mock student profile for testing."""
    student = Mock(spec=Profile)
    student.id = uuid.uuid4()
    student.full_name = "Jane Smith"
    student.student_id = "STU12345"
    student.grade_level = "10"
    return student


@pytest.fixture
def mock_author():
    """Mock author profile for testing."""
    author = Mock(spec=Profile)
    author.id = uuid.uuid4()
    author.full_name = "Mr. Johnson"
    return author


@pytest.fixture
def mock_referral(mock_organization, mock_student, mock_author):
    """Mock referral for testing."""
    referral = Mock(spec=Referral)
    referral.id = uuid.uuid4()
    referral.organization_id = mock_organization.id
    referral.student_id = mock_student.id
    referral.author_id = mock_author.id
    referral.status = "SUBMITTED"
    referral.type = "Behavior"
    referral.location = "Classroom 101"
    referral.time_of_day = "Morning"
    referral.behaviors = ["Disruption", "Defiance"]
    referral.description = "Student refused to follow instructions and disrupted class"
    referral.created_at = datetime.now(timezone.utc)
    referral.updated_at = datetime.now(timezone.utc)
    return referral


@pytest.fixture
def mock_intervention(mock_author):
    """Mock intervention for testing."""
    intervention = Mock(spec=Intervention)
    intervention.id = uuid.uuid4()
    intervention.title = "Parent Contact"
    intervention.description = "Called parent to discuss behavior"
    intervention.status = "COMPLETED"
    intervention.created_by = mock_author.id
    intervention.created_at = datetime.now(timezone.utc)
    intervention.updated_at = datetime.now(timezone.utc)
    intervention.completed_at = datetime.now(timezone.utc)
    return intervention


# ============================================================================
# TESTS: PDF Service
# ============================================================================

class TestPDFService:
    """Tests for PDF generation service."""
    
    def test_generate_pdf_success(
        self,
        mock_organization,
        mock_student,
        mock_author,
        mock_referral
    ):
        """
        ARRANGE: Valid referral data, mocked WeasyPrint
        ACT: generate_referral_pdf()
        ASSERT: PDF generated with correct content
        """
        # Arrange
        mock_html_instance = Mock()
        mock_html_instance.write_pdf.return_value = b'PDF_CONTENT'
        
        # Create mock weasyprint module
        mock_weasyprint = MagicMock()
        mock_weasyprint.HTML = Mock(return_value=mock_html_instance)
        mock_weasyprint.CSS = Mock()
        
        # Patch sys.modules to inject mock weasyprint before the function imports it
        with patch.dict('sys.modules', {'weasyprint': mock_weasyprint}):
            # Act
            result = pdf_service.generate_referral_pdf(
                referral=mock_referral,
                organization=mock_organization,
                student=mock_student,
                author=mock_author,
                interventions=None
            )
        
        # Assert
        assert result == b'PDF_CONTENT'
        mock_weasyprint.HTML.assert_called_once()
        # Verify HTML was generated with string parameter
        call_args = mock_weasyprint.HTML.call_args
        assert call_args[1]['string'] is not None
        assert 'Test High School' in call_args[1]['string']
        assert 'Jane Smith' in call_args[1]['string']
    
    def test_generate_pdf_with_interventions(
        self,
        mock_organization,
        mock_student,
        mock_author,
        mock_referral,
        mock_intervention
    ):
        """
        ARRANGE: Referral with interventions
        ACT: generate_referral_pdf()
        ASSERT: PDF includes intervention data
        """
        # Arrange
        mock_html_instance = Mock()
        mock_html_instance.write_pdf.return_value = b'PDF_WITH_INTERVENTIONS'
        
        # Create mock weasyprint module
        mock_weasyprint = MagicMock()
        mock_weasyprint.HTML = Mock(return_value=mock_html_instance)
        mock_weasyprint.CSS = Mock()
        
        # Patch sys.modules to inject mock weasyprint before the function imports it
        with patch.dict('sys.modules', {'weasyprint': mock_weasyprint}):
            # Act
            result = pdf_service.generate_referral_pdf(
                referral=mock_referral,
                organization=mock_organization,
                student=mock_student,
                author=mock_author,
                interventions=[mock_intervention]
            )
        
        # Assert
        assert result == b'PDF_WITH_INTERVENTIONS'
        # Verify intervention data in HTML
        call_args = mock_weasyprint.HTML.call_args
        html_content = call_args[1]['string']
        assert 'Parent Contact' in html_content
    
    def test_generate_html_preview(
        self,
        mock_organization,
        mock_student,
        mock_author,
        mock_referral
    ):
        """
        ARRANGE: Valid referral data
        ACT: generate_html_preview()
        ASSERT: HTML string generated correctly
        """
        # Act
        result = pdf_service.generate_html_preview(
            referral=mock_referral,
            organization=mock_organization,
            student=mock_student,
            author=mock_author
        )
        
        # Assert
        assert isinstance(result, str)
        assert 'Test High School' in result
        assert 'Jane Smith' in result
        assert 'Mr. Johnson' in result
        assert 'Behavior' in result
        assert 'Classroom 101' in result
    
    def test_generate_pdf_missing_weasyprint(
        self,
        mock_organization,
        mock_student,
        mock_author,
        mock_referral
    ):
        """
        ARRANGE: WeasyPrint not installed
        ACT: generate_referral_pdf()
        ASSERT: Raises ImportError
        """
        # Arrange - make weasyprint import fail
        import builtins
        original_import = builtins.__import__
        
        def import_side_effect(name, *args, **kwargs):
            if name == 'weasyprint':
                raise ImportError("WeasyPrint not found")
            return original_import(name, *args, **kwargs)
        
        # Remove weasyprint from sys.modules if it exists
        if 'weasyprint' in sys.modules:
            del sys.modules['weasyprint']
        
        with patch('builtins.__import__', side_effect=import_side_effect):
            # Act & Assert
            with pytest.raises(ImportError, match="WeasyPrint is required"):
                pdf_service.generate_referral_pdf(
                    referral=mock_referral,
                    organization=mock_organization,
                    student=mock_student,
                    author=mock_author
                )


# ============================================================================
# TESTS: Email Service
# ============================================================================

def create_test_referral(db_session):
    """Helper function to create a referral in the database for testing."""
    from app.models import Organization, Profile, Referral
    
    # Create organization
    org = Organization(
        name="Test School",
        phone_number="+14155551234",
        preset_config={}
    )
    db_session.add(org)
    db_session.flush()
    
    # Create student profile
    student = Profile(
        id=uuid.uuid4(),
        full_name="Test Student",
        student_id="STU001",
        is_active=True
    )
    db_session.add(student)
    db_session.flush()
    
    # Create author profile
    author = Profile(
        id=uuid.uuid4(),
        full_name="Test Author",
        is_active=True
    )
    db_session.add(author)
    db_session.flush()
    
    # Create referral
    referral = Referral(
        organization_id=org.id,
        student_id=student.id,
        author_id=author.id,
        status="DRAFT",
        type="Behavior",
        description="Test referral"
    )
    db_session.add(referral)
    db_session.commit()
    return referral


class TestEmailService:
    """Tests for email sending service."""
    
    def test_send_email_success(
        self,
        db_session
    ):
        """
        ARRANGE: Valid email data, mocked Resend
        ACT: send_referral_email()
        ASSERT: Email sent successfully
        """
        # Arrange - create referral in database
        referral = create_test_referral(db_session)
        referral_id = referral.id
        
        # Create mock resend module
        mock_resend = MagicMock()
        mock_resend.api_key = "test_key"
        mock_resend.Emails.send.return_value = {"id": "email_123"}
        
        # Patch sys.modules to inject mock resend before the function imports it
        with patch.dict('sys.modules', {'resend': mock_resend}):
            with patch.dict('os.environ', {'RESEND_API_KEY': 'test_key'}):
                # Act
                success, message, log_id = email_service.send_referral_email(
                    db=db_session,
                    referral_id=referral_id,
                    recipient_emails=["parent@example.com"],
                    subject="Test Subject",
                    message="Test Message",
                    pdf_bytes=b'PDF_CONTENT'
                )
        
        # Assert
        assert success is True
        assert "successfully" in message.lower()
        assert log_id is not None
        mock_resend.Emails.send.assert_called_once()
    
    def test_send_email_multiple_recipients(
        self,
        db_session
    ):
        """
        ARRANGE: Multiple recipients
        ACT: send_referral_email()
        ASSERT: Emails sent to all recipients
        """
        # Arrange - create referral in database
        referral = create_test_referral(db_session)
        referral_id = referral.id
        
        # Create mock resend module
        mock_resend = MagicMock()
        mock_resend.api_key = "test_key"
        mock_resend.Emails.send.return_value = {"id": "email_123"}
        
        recipients = [
            "parent1@example.com",
            "parent2@example.com",
            "counselor@example.com"
        ]
        
        with patch.dict('sys.modules', {'resend': mock_resend}):
            with patch.dict('os.environ', {'RESEND_API_KEY': 'test_key'}):
                # Act
                success, message, log_id = email_service.send_referral_email(
                    db=db_session,
                    referral_id=referral_id,
                    recipient_emails=recipients,
                    subject="Test Subject",
                    message="Test Message"
                )
        
        # Assert
        assert success is True
        # Should be called once per recipient
        assert mock_resend.Emails.send.call_count == 3
    
    def test_send_email_with_attachment(
        self,
        db_session
    ):
        """
        ARRANGE: Email with PDF attachment
        ACT: send_referral_email()
        ASSERT: PDF attached to email
        """
        # Arrange - create referral in database
        referral = create_test_referral(db_session)
        referral_id = referral.id
        
        # Create mock resend module
        mock_resend = MagicMock()
        mock_resend.api_key = "test_key"
        mock_resend.Emails.send.return_value = {"id": "email_123"}
        
        pdf_content = b'FAKE_PDF_CONTENT'
        
        with patch.dict('sys.modules', {'resend': mock_resend}):
            with patch.dict('os.environ', {'RESEND_API_KEY': 'test_key'}):
                # Act
                success, message, log_id = email_service.send_referral_email(
                    db=db_session,
                    referral_id=referral_id,
                    recipient_emails=["parent@example.com"],
                    subject="Test Subject",
                    message="Test Message",
                    pdf_bytes=pdf_content
                )
        
        # Assert
        assert success is True
        # Verify attachment was included in call
        call_args = mock_resend.Emails.send.call_args[0][0]
        assert 'attachments' in call_args
        assert len(call_args['attachments']) == 1
        assert 'referral_' in call_args['attachments'][0]['filename']
    
    def test_send_email_failure(
        self,
        db_session
    ):
        """
        ARRANGE: Resend API fails
        ACT: send_referral_email()
        ASSERT: Returns failure status and logs error
        """
        # Arrange - create referral in database
        referral = create_test_referral(db_session)
        referral_id = referral.id
        
        # Create mock resend module
        mock_resend = MagicMock()
        mock_resend.api_key = "test_key"
        mock_resend.Emails.send.side_effect = Exception("API Error")
        
        with patch.dict('sys.modules', {'resend': mock_resend}):
            with patch.dict('os.environ', {'RESEND_API_KEY': 'test_key'}):
                # Act
                success, message, log_id = email_service.send_referral_email(
                    db=db_session,
                    referral_id=referral_id,
                    recipient_emails=["parent@example.com"],
                    subject="Test Subject",
                    message="Test Message"
                )
        
        # Assert
        assert success is False
        assert "failed" in message.lower() or "api error" in message.lower()
        # Should still have a log entry
        assert log_id is not None
    
    def test_send_email_missing_api_key(
        self,
        db_session
    ):
        """
        ARRANGE: RESEND_API_KEY not set
        ACT: send_referral_email()
        ASSERT: Returns failure status
        """
        # Arrange - create referral in database
        referral = create_test_referral(db_session)
        referral_id = referral.id
        
        # Patch RESEND_API_KEY directly (it's set at module import time)
        with patch.object(email_service, 'RESEND_API_KEY', None):
            # Act
            success, message, log_id = email_service.send_referral_email(
                db=db_session,
                referral_id=referral_id,
                recipient_emails=["parent@example.com"],
                subject="Test",
                message="Test"
            )
        
        # Assert
        assert success is False
        assert "not configured" in message.lower()
        assert log_id is None
    
    def test_render_email_template(self):
        """
        ARRANGE: Email template with variables
        ACT: render_email_template()
        ASSERT: Template rendered with values
        """
        # Arrange
        template = "Dear {{student_name}}, your referral type is {{type}}."
        context = {
            "student_name": "John Doe",
            "type": "Behavior"
        }
        
        # Act
        result = email_service.render_email_template(template, context)
        
        # Assert
        assert "Dear John Doe" in result
        assert "Behavior" in result
    
    def test_get_email_context_for_referral(
        self,
        mock_referral,
        mock_organization,
        mock_student,
        mock_author
    ):
        """
        ARRANGE: Referral with all data
        ACT: get_email_context_for_referral()
        ASSERT: Context dictionary created correctly
        """
        # Act
        context = email_service.get_email_context_for_referral(
            referral=mock_referral,
            organization=mock_organization,
            student=mock_student,
            author=mock_author
        )
        
        # Assert
        assert context["organization_name"] == "Test High School"
        assert context["student_name"] == "Jane Smith"
        assert context["author_name"] == "Mr. Johnson"
        assert context["type"] == "Behavior"
        assert context["location"] == "Classroom 101"
        assert "Disruption" in context["behaviors"]


# ============================================================================
# TESTS: Template Rendering
# ============================================================================

class TestTemplateRendering:
    """Tests for Jinja2 template rendering."""
    
    def test_render_referral_template(
        self,
        mock_referral,
        mock_organization,
        mock_student,
        mock_author
    ):
        """
        ARRANGE: Referral template with variables
        ACT: Render using get_email_context_for_referral
        ASSERT: All variables replaced correctly
        """
        # Arrange
        template_body = """
        Dear Parent,
        
        Student: {{student_name}}
        Type: {{type}}
        Location: {{location}}
        Behaviors: {{behaviors}}
        
        Sincerely,
        {{organization_name}}
        """
        
        # Act
        context = email_service.get_email_context_for_referral(
            referral=mock_referral,
            organization=mock_organization,
            student=mock_student,
            author=mock_author
        )
        result = email_service.render_email_template(template_body, context)
        
        # Assert
        assert "Jane Smith" in result
        assert "Behavior" in result
        assert "Classroom 101" in result
        assert "Test High School" in result
    
    def test_render_template_missing_variable(self):
        """
        ARRANGE: Template with undefined variable
        ACT: render_email_template()
        ASSERT: Template renders without error (variable shows as empty)
        """
        # Arrange
        template = "Hello {{undefined_variable}}, welcome!"
        context = {"name": "John"}
        
        # Act
        result = email_service.render_email_template(template, context)
        
        # Assert
        # Jinja2 renders undefined variables as empty strings
        assert "Hello" in result
        assert "welcome" in result


# ============================================================================
# TESTS: Integration Tests for Services
# ============================================================================

class TestServiceIntegration:
    """Integration tests combining PDF and Email services."""
    
    def test_complete_workflow_pdf_and_email(
        self,
        db_session,
        mock_referral,
        mock_organization,
        mock_student,
        mock_author
    ):
        """
        ARRANGE: Generate PDF and send email
        ACT: Complete workflow
        ASSERT: Both services work together
        """
        # Arrange
        mock_html_instance = Mock()
        mock_html_instance.write_pdf.return_value = b'GENERATED_PDF'
        
        # Create mock weasyprint module
        mock_weasyprint = MagicMock()
        mock_weasyprint.HTML = Mock(return_value=mock_html_instance)
        mock_weasyprint.CSS = Mock()
        
        # Create real referral in database for email service
        real_referral = create_test_referral(db_session)
        
        # Create mock resend module
        mock_resend = MagicMock()
        mock_resend.api_key = "test_key"
        mock_resend.Emails.send.return_value = {"id": "email_123"}
        
        # Act - Generate PDF (uses mock objects)
        with patch.dict('sys.modules', {'weasyprint': mock_weasyprint}):
            pdf_bytes = pdf_service.generate_referral_pdf(
                referral=mock_referral,
                organization=mock_organization,
                student=mock_student,
                author=mock_author
            )
        
        # Act - Send Email with PDF (uses real referral ID)
        with patch.dict('sys.modules', {'resend': mock_resend}):
            with patch.dict('os.environ', {'RESEND_API_KEY': 'test_key'}):
                success, message, log_id = email_service.send_referral_email(
                    db=db_session,
                    referral_id=real_referral.id,
                    recipient_emails=["parent@example.com"],
                    subject="Referral Report",
                    message="Please find attached",
                    pdf_bytes=pdf_bytes
                )
        
        # Assert
        assert pdf_bytes == b'GENERATED_PDF'
        assert success is True
        assert log_id is not None

