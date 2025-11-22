"""
Enhanced views for user document management with multi-document support.
Supports creating multiple documents per user with survey-based auto-generation.
"""
import base64
import json
import logging
import os
from datetime import datetime
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, ListView
from pdf2image import convert_from_bytes
from PIL import Image
from weasyprint import HTML

from inclusive_world_portal.portal.models import Document
from inclusive_world_portal.users.document_forms import DocumentForm
from inclusive_world_portal.users.models import User

logger = logging.getLogger(__name__)


class DocumentListView(LoginRequiredMixin, ListView):
    """
    List all documents for a user.
    Managers can view documents for other users by passing ?user=username.
    """
    model = Document
    template_name = "users/document_list.html"
    context_object_name = "documents"
    paginate_by = 20
    
    def get_target_user(self):
        """Get the user whose documents are being viewed."""
        target_username = self.request.GET.get('user')
        if target_username:
            # Only managers/PCMs can view other users' documents
            if self.request.user.role not in ['manager', 'person_centered_manager']:
                messages.error(self.request, _('You do not have permission to view other users\' documents.'))
                return self.request.user
            
            try:
                return User.objects.get(username=target_username)
            except User.DoesNotExist:
                messages.error(self.request, _('User not found.'))
                return self.request.user
        
        return self.request.user
    
    def get_queryset(self):
        target_user = self.get_target_user()
        queryset = Document.objects.filter(user=target_user).select_related('created_by', 'source_survey')
        
        # Non-managers/PCMs can only see published documents
        if self.request.user.role not in ['manager', 'person_centered_manager']:
            queryset = queryset.filter(published=True)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target_user = self.get_target_user()
        context['target_user'] = target_user
        context['viewing_own_documents'] = target_user.id == self.request.user.id
        return context


document_list_view = DocumentListView.as_view()


class DocumentEditorView(LoginRequiredMixin, FormView):
    """
    Document editor view with Quill rich text editor.
    Supports creating and editing multiple documents per user.
    Only managers and Person Centered Managers can create/edit documents.
    """
    template_name = "users/document_editor.html"
    form_class = DocumentForm
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user has permission to access the editor."""
        if request.user.role not in ['manager', 'person_centered_manager']:
            messages.error(request, _('Only managers and Person Centered Managers can edit documents.'))
            return redirect('users:document_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_target_user(self):
        """Get the user whose document is being edited."""
        target_username = self.request.GET.get('user')
        if target_username:
            try:
                return User.objects.get(username=target_username)
            except User.DoesNotExist:
                messages.error(self.request, _('User not found.'))
                return self.request.user
        
        return self.request.user
    
    def get_document(self):
        """Get the document being edited, or None for new document."""
        document_id = self.request.GET.get('document_id')
        if document_id:
            target_user = self.get_target_user()
            try:
                return Document.objects.get(document_id=document_id, user=target_user)
            except Document.DoesNotExist:
                messages.error(self.request, _('Document not found.'))
                return None
        return None
    
    def get_initial(self):
        """Pre-populate form with existing document content."""
        initial = super().get_initial()
        document = self.get_document()
        
        if document:
            initial['title'] = document.title
            initial['content'] = document.content
            initial['state'] = document.state
        else:
            # Default for new documents
            initial['title'] = 'Untitled Document'
            initial['state'] = 'draft'
        
        return initial
    
    def get_context_data(self, **kwargs):
        from inclusive_world_portal.survey.models import Survey
        
        context = super().get_context_data(**kwargs)
        target_user = self.get_target_user()
        document = self.get_document()
        
        # Get available surveys for auto-generation
        available_surveys = Survey.objects.filter(is_published=True).order_by('name')
        
        
        context.update({
            'document': document,
            'document_title': document.title if document else 'New Document',
            'target_user': target_user,
            'editing_own_document': False,  # Managers/PCMs are always editing for others
            'available_surveys': available_surveys,
            'is_new_document': document is None,
        })
        return context
    
    def form_valid(self, form):
        """Save the document when form is submitted."""
        target_user = self.get_target_user()
        document = self.get_document()
        
        title = form.cleaned_data.get('title', 'Untitled Document')
        content = form.cleaned_data.get('content', '')
        state = form.cleaned_data.get('state', 'draft')
        
        if document:
            # Update existing document
            document.title = title
            document.content = content
            document.state = state
            document.save()
            messages.success(self.request, _('Document updated successfully!'))
        else:
            # Create new document - always set created_by since only managers/PCMs can create
            document = Document.objects.create(
                user=target_user,
                created_by=self.request.user,
                title=title,
                content=content,
                state=state
            )
            messages.success(self.request, _('Document created successfully!'))
        
        # Redirect to edit the document
        redirect_url = reverse('users:document_editor') + f'?document_id={document.document_id}'
        if target_user.id != self.request.user.id:
            redirect_url += f'&user={target_user.username}'
        
        return redirect(redirect_url)
    
    def get_success_url(self):
        return reverse('users:document_list')


document_editor_view = DocumentEditorView.as_view()


@login_required
def autogenerate_document_from_survey(request):
    """
    Generate document content from survey responses.
    Returns JSON with the generated HTML content.
    Only managers and Person Centered Managers can generate documents.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Check permissions
    if request.user.role not in ['manager', 'person_centered_manager']:
        return JsonResponse({
            'success': False,
            'error': 'Only managers and Person Centered Managers can generate documents.'
        }, status=403)
    
    try:
        # Get survey ID from request
        data = json.loads(request.body)
        survey_id = data.get('survey_id')
        
        if not survey_id:
            return JsonResponse({
                'success': False,
                'error': 'Survey ID is required.'
            }, status=400)
        
        # Determine which user's survey to use
        target_username = request.GET.get('user')
        if target_username:
            try:
                target_user = User.objects.get(username=target_username)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'User not found.'
                }, status=404)
        else:
            target_user = request.user
        
        # Get the survey and user's responses
        from inclusive_world_portal.survey.models import Survey, Response, Answer
        
        try:
            survey = Survey.objects.get(id=survey_id)
        except Survey.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Survey not found.'
            }, status=404)
        
        # Get user's responses to this survey
        responses = Response.objects.filter(user=target_user, survey=survey)
        
        if not responses.exists():
            user_display = target_user.name or target_user.username
            if target_user.id == request.user.id:
                error_msg = f'Please complete the survey "{survey.name}" first before generating your document.'
            else:
                error_msg = f'{user_display} has not completed the survey "{survey.name}" yet.'
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=400)
        
        # Build context from survey responses
        context = {
            'user_name': target_user.name or target_user.username,
            'survey_name': survey.name,
        }
        
        # Get all answers for this user's responses
        for response in responses:
            answers = Answer.objects.filter(response=response).select_related('question')
            for answer in answers:
                question_text = answer.question.text
                # Create a safe key from question text
                key = question_text.lower().replace(' ', '_').replace('?', '').replace("'", '')[:50]
                context[key] = answer.body
        
        # Generate HTML content
        html_content = generate_document_html_from_context(context, survey.name)
        
        return JsonResponse({
            'success': True,
            'html': html_content,
            'message': f'Document template generated from "{survey.name}"!',
            'survey_id': survey_id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        logger.error(f"Error generating document from survey: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while generating the document. Please try again.'
        }, status=500)


def generate_document_html_from_context(context, survey_name):
    """
    Generate HTML content for a document from survey response context.
    This is a generic template that can be customized per survey type.
    """
    html_parts = [
        f'<h1>{context.get("user_name", "User")}</h1>',
    ]
    
    # Add all context items as sections
    for key, value in context.items():
        if key not in ['user_name', 'survey_name'] and value:
            # Convert key to readable title
            title = key.replace('_', ' ').title()
            html_parts.append(f'<h2>{title}</h2><p>{value}</p>')
    
    return '\n'.join(html_parts)


@login_required
def toggle_document_publish(request, document_id):
    """
    Toggle the published status of a document.
    When publishing, generates a PDF and saves it to S3/MinIO.
    When unpublishing, deletes the PDF.
    Only managers and Person Centered Managers can publish/unpublish documents.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST request required'}, status=405)
    
    # Check permissions
    if request.user.role not in ['manager', 'person_centered_manager']:
        return JsonResponse({
            'success': False,
            'error': 'Only managers and Person Centered Managers can publish documents.'
        }, status=403)
    
    try:
        # Get the document
        document = get_object_or_404(Document, document_id=document_id)
        
        # Toggle published status
        if document.published:
            # Unpublish - delete PDF and thumbnail
            if document.pdf_file:
                document.pdf_file.delete(save=False)
            if document.thumbnail:
                document.thumbnail.delete(save=False)
            document.published = False
            document.published_at = None
            document.save()
            
            action = 'unpublished'
            message = f'"{document.title}" has been unpublished.'
        else:
            # Publish - generate PDF
            # Extract HTML content
            try:
                content_data = json.loads(document.content)
                html_content_only = content_data.get('html', '')
            except (json.JSONDecodeError, TypeError):
                html_content_only = document.content
            
            if not html_content_only or html_content_only.strip() == '':
                return JsonResponse({
                    'success': False,
                    'error': 'Document is empty. Please add content before publishing.'
                }, status=400)
            
            # Get logo for PDF header
            logo_path = os.path.join(settings.BASE_DIR, 'inclusive_world_portal', 'static', 'images', 'inclusive-world-logo.png')
            logo_data_uri = ''
            try:
                with open(logo_path, 'rb') as logo_file:
                    logo_base64 = base64.b64encode(logo_file.read()).decode('utf-8')
                    logo_data_uri = f'data:image/png;base64,{logo_base64}'
            except Exception as e:
                logger.warning(f"Could not load logo for PDF: {e}")
            
            # Get user's profile picture
            profile_picture_data_uri = ''
            if document.user.profile_picture:
                try:
                    with document.user.profile_picture.open('rb') as profile_file:
                        profile_base64 = base64.b64encode(profile_file.read()).decode('utf-8')
                        file_ext = document.user.profile_picture.name.split('.')[-1].lower()
                        mime_type = 'image/jpeg' if file_ext in ['jpg', 'jpeg'] else f'image/{file_ext}'
                        profile_picture_data_uri = f'data:{mime_type};base64,{profile_base64}'
                except Exception as e:
                    logger.warning(f"Could not load profile picture for PDF: {e}")
            
            # Get font path
            montserrat_font_path = os.path.join(settings.BASE_DIR, 'inclusive_world_portal', 'static', 'fonts', 'Montserrat-VariableFont_wght.ttf')
            
            # Create PDF HTML
            pdf_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{document.title}</title>
    <style>
        @page {{
            size: A4;
            margin: 3cm 0.5cm 0.5cm 0.5cm;
            @top-left {{
                content: element(header);
                width: 100%;
            }}
        }}
        
        .running-header {{
            position: running(header);
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 0.3cm;
            border-bottom: 1px solid #ddd;
            width: 100%;
        }}
        
        .running-header .logo {{
            max-width: 60px;
            height: auto;
        }}
        
        .running-header .profile-picture {{
            max-width: 80px;
            max-height: 80px;
            border-radius: 4px;
            object-fit: cover;
        }}
        
        @font-face {{
            font-family: 'Montserrat';
            src: url('file://{montserrat_font_path}') format('truetype');
            font-weight: 100 900;
        }}
        
        body {{
            font-family: 'Montserrat', sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #404040;
        }}
        
        /* Quill editor styles - matching document_editor.html */
        h1 {{
            font-family: 'Montserrat', sans-serif;
            font-size: 2em;
            margin: 0.67em 0;
            font-weight: 700;
            line-height: 1.2;
        }}
        
        h2 {{
            font-family: 'Montserrat', sans-serif;
            font-size: 1.5em;
            margin: 0.75em 0;
            font-weight: 700;
            line-height: 1.3;
        }}
        
        h3 {{
            font-family: 'Montserrat', sans-serif;
            font-size: 1.25em;
            margin: 0.83em 0;
            font-weight: 600;
            line-height: 1.4;
        }}
        
        h4 {{
            font-family: 'Montserrat', sans-serif;
            font-size: 1.1em;
            margin: 1em 0;
            font-weight: 600;
            line-height: 1.4;
        }}
        
        h5 {{
            font-family: 'Montserrat', sans-serif;
            font-size: 1em;
            margin: 1.33em 0;
            font-weight: 600;
            line-height: 1.5;
        }}
        
        h6 {{
            font-family: 'Montserrat', sans-serif;
            font-size: 0.875em;
            margin: 1.67em 0;
            font-weight: 600;
            line-height: 1.5;
        }}
        
        p {{
            font-family: 'Montserrat', sans-serif;
            margin: 1em 0;
            line-height: 1.6;
        }}
        
        strong, b {{
            font-weight: 700;
        }}
        
        em, i {{
            font-style: italic;
        }}
        
        u {{
            text-decoration: underline;
        }}
        
        s, strike {{
            text-decoration: line-through;
        }}
        
        a {{
            color: #008B9C;
            text-decoration: underline;
        }}
        
        a:hover {{
            color: #006A78;
        }}
        
        ul, ol {{
            font-family: 'Montserrat', sans-serif;
            margin: 1em 0;
            padding-left: 2em;
        }}
        
        li {{
            font-family: 'Montserrat', sans-serif;
            margin: 0.5em 0;
            line-height: 1.6;
        }}
        
        blockquote {{
            font-family: 'Montserrat', sans-serif;
            border-left: 4px solid #008B9C;
            margin: 1.5em 0;
            padding-left: 1em;
            padding-top: 0.5em;
            padding-bottom: 0.5em;
            color: #595959;
            font-style: italic;
        }}
        
        code {{
            font-family: 'Courier New', monospace;
            background-color: #F2F2F2;
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        
        pre {{
            font-family: 'Courier New', monospace;
            background-color: #F2F2F2;
            padding: 1em;
            border-radius: 4px;
            overflow-x: auto;
            margin: 1em 0;
        }}
        
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        
        sub {{
            vertical-align: sub;
            font-size: 0.75em;
        }}
        
        sup {{
            vertical-align: super;
            font-size: 0.75em;
        }}
        
        hr {{
            border: none;
            border-top: 2px solid #E5E7EB;
            margin: 2em 0;
        }}
    </style>
</head>
<body>
    <div class="running-header">
        <div class="logo-container">
            {'<img class="logo" src="' + logo_data_uri + '" alt="Inclusive World">' if logo_data_uri else '<div style="width:100px;"></div>'}
        </div>
        <div class="profile-container">
            {'<img class="profile-picture" src="' + profile_picture_data_uri + '" alt="Profile Picture">' if profile_picture_data_uri else '<div style="width:80px;"></div>'}
        </div>
    </div>
    <div class="pdf-content">
        {html_content_only}
    </div>
</body>
</html>"""
            
            # Generate PDF
            try:
                from weasyprint.text.fonts import FontConfiguration
                font_config = FontConfiguration() if os.path.exists(montserrat_font_path) else None
                pdf_bytes = HTML(string=pdf_html).write_pdf(
                    presentational_hints=True,
                    font_config=font_config,
                )
            except Exception as pdf_error:
                logger.error(f"PDF generation error: {pdf_error}", exc_info=True)
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to generate PDF. Please try again.'
                }, status=500)
            
            # Save PDF to storage
            filename = document.get_pdf_filename()
            
            # Delete old PDF and thumbnail if exists
            if document.pdf_file:
                document.pdf_file.delete(save=False)
            if document.thumbnail:
                document.thumbnail.delete(save=False)
            
            # Save new PDF
            document.pdf_file.save(filename, ContentFile(pdf_bytes), save=False)
            
            # Generate thumbnail from first page of PDF
            try:
                # Convert first page of PDF to image at lower DPI for thumbnail
                # dpi=100 gives us a decent quality thumbnail
                # use_cropbox=False ensures we capture the entire page including margins
                images = convert_from_bytes(
                    pdf_bytes, 
                    dpi=100, 
                    first_page=1, 
                    last_page=1,
                    use_cropbox=False,
                    use_pdftocairo=True  # Better rendering quality
                )
                
                if images:
                    img = images[0]
                    
                    # Resize to a consistent thumbnail size (e.g., 400px wide)
                    # Maintain aspect ratio
                    max_width = 400
                    if img.width > max_width:
                        ratio = max_width / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Convert to RGB if necessary (for JPEG)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    
                    # Save thumbnail to BytesIO
                    thumbnail_io = BytesIO()
                    img.save(thumbnail_io, format='JPEG', quality=85, optimize=True)
                    thumbnail_io.seek(0)
                    
                    # Save thumbnail to storage
                    thumbnail_filename = f"thumb_{filename.replace('.pdf', '.jpg')}"
                    document.thumbnail.save(thumbnail_filename, ContentFile(thumbnail_io.read()), save=False)
                
            except Exception as thumb_error:
                logger.warning(f"Failed to generate thumbnail: {thumb_error}", exc_info=True)
                # Continue without thumbnail - it's not critical
            
            document.published = True
            document.published_at = timezone.now()
            document.save()
            
            action = 'published'
            message = f'"{document.title}" has been published as a PDF.'
        
        return JsonResponse({
            'success': True,
            'action': action,
            'message': message,
            'published': document.published,
        })
        
    except Exception as e:
        logger.error(f"Error toggling document publish status: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)


@login_required
def view_published_document(request, document_id):
    """
    View a published document's PDF in a framed view with navigation.
    Requires login - accessible to document owner and managers/PCMs.
    Shows the PDF in an iframe similar to the old OPD view.
    """
    try:
        # Get the document - must be published
        document = get_object_or_404(Document, document_id=document_id, published=True)
        
        # Check permissions
        can_view = (
            document.user == request.user or
            request.user.role in ['manager', 'person_centered_manager']
        )
        
        if not can_view:
            messages.error(request, _('You do not have permission to view this document.'))
            return redirect('users:document_list')
        
        context = {
            'document': document,
            'target_user': document.user,
            'viewing_own_document': document.user == request.user,
        }
        
        return render(request, 'users/view_published_document.html', context)
        
    except Exception as e:
        logger.error(f"Error viewing published document: {e}", exc_info=True)
        messages.error(request, _('Document not found or not published.'))
        return redirect('users:document_list')


@login_required
def serve_document_pdf(request, document_id):
    """
    Serve the PDF file for a published document.
    Used for embedding in iframe.
    """
    from django.http import HttpResponse
    from django.views.decorators.clickjacking import xframe_options_sameorigin
    
    try:
        # Get the document
        document = get_object_or_404(Document, document_id=document_id, published=True)
        
        # Check permissions
        can_view = (
            document.user == request.user or
            request.user.role in ['manager', 'person_centered_manager']
        )
        
        if not can_view:
            return HttpResponse('Permission denied', status=403)
        
        # Serve the PDF
        if not document.pdf_file:
            return HttpResponse('PDF not found', status=404)
        
        response = HttpResponse(document.pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{document.get_pdf_filename()}"'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving PDF: {e}", exc_info=True)
        return HttpResponse('Error loading PDF', status=500)


@login_required
def delete_document(request, document_id):
    """
    Delete a document and its associated files (PDF and thumbnail).
    Only managers and Person Centered Managers can delete documents.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST request required'}, status=405)
    
    # Check permissions
    if request.user.role not in ['manager', 'person_centered_manager']:
        return JsonResponse({
            'success': False,
            'error': 'Only managers and Person Centered Managers can delete documents.'
        }, status=403)
    
    try:
        # Get the document
        document = get_object_or_404(Document, document_id=document_id)
        
        document_title = document.title
        
        # Delete associated files if they exist
        if document.pdf_file:
            document.pdf_file.delete(save=False)
        if document.thumbnail:
            document.thumbnail.delete(save=False)
        
        # Delete the document
        document.delete()
        
        logger.info(f"Document '{document_title}' (ID: {document_id}) deleted by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': f'"{document_title}" has been deleted successfully.'
        })
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while deleting the document. Please try again.'
        }, status=500)
