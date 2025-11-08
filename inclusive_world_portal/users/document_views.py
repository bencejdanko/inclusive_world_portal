"""
Views for user document management with Quill editor.
"""
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from weasyprint import HTML, CSS

from inclusive_world_portal.portal.models import Document
from inclusive_world_portal.users.document_forms import DocumentForm
from inclusive_world_portal.users.models import DiscoverySurvey


class DocumentEditorView(LoginRequiredMixin, FormView):
    """
    Document editor view with Quill rich text editor.
    Allows users to create and edit their documents (e.g., One Page Description).
    Person-centered managers can also edit other users' documents by passing ?user=username.
    """
    template_name = "users/document_editor.html"
    form_class = DocumentForm
    
    def get_target_user(self):
        """Get the user whose document is being edited."""
        from inclusive_world_portal.users.models import User
        
        # Check if PCM is editing another user's document
        target_username = self.request.GET.get('user')
        if target_username:
            # Only PCMs can edit other users' documents
            if self.request.user.role != 'person_centered_manager':
                messages.error(self.request, _('You do not have permission to edit other users\' documents.'))
                return self.request.user
            
            # Get the target user
            try:
                return User.objects.get(username=target_username)
            except User.DoesNotExist:
                messages.error(self.request, _('User not found.'))
                return self.request.user
        
        return self.request.user
    
    def get_initial(self):
        """Pre-populate form with existing document content."""
        initial = super().get_initial()
        
        target_user = self.get_target_user()
        
        # Get or create the user's primary document (for One Page Description)
        document, created = Document.objects.get_or_create(
            user=target_user,
            title="One Page Description",
            defaults={'content': '', 'state': 'draft'}
        )
        
        initial['title'] = document.title
        initial['content'] = document.content
        initial['state'] = document.state
        return initial
    
    def get_context_data(self, **kwargs):
        from inclusive_world_portal.portal.models import DocumentExport
        
        context = super().get_context_data(**kwargs)
        
        target_user = self.get_target_user()
        
        # Get the document for context
        document, created = Document.objects.get_or_create(
            user=target_user,
            title="One Page Description",
            defaults={'content': '', 'state': 'draft'}
        )
        
        # Get all exports for this document, ordered by creation date (newest first)
        exports = DocumentExport.objects.filter(
            user=target_user,
            document=document
        ).order_by('-created_at')
        
        # Get the active export
        active_export = exports.filter(is_active=True).first()
        
        context['document'] = document
        context['document_title'] = document.title
        context['document_exports'] = exports
        context['active_export'] = active_export
        context['target_user'] = target_user
        context['editing_own_document'] = target_user.id == self.request.user.id
        return context
    
    def form_valid(self, form):
        """Save the document when form is submitted."""
        target_user = self.get_target_user()
        
        title = form.cleaned_data.get('title', 'One Page Description')
        content = form.cleaned_data.get('content', '')
        state = form.cleaned_data.get('state', 'draft')
        
        # Get or create the document
        document, created = Document.objects.get_or_create(
            user=target_user,
            title=title,
            defaults={'content': content, 'state': state}
        )
        
        if not created:
            document.content = content
            document.state = state
            document.save()
        
        if target_user.id == self.request.user.id:
            messages.success(self.request, _('Document saved successfully!'))
        else:
            messages.success(self.request, _(f'Document saved successfully for {target_user.name or target_user.username}!'))
        
        # Redirect back with the user parameter if editing another user's document
        if target_user.id != self.request.user.id:
            return redirect(f"{reverse('users:document_editor')}?user={target_user.username}")
        
        return redirect('users:document_editor')
    
    def get_success_url(self):
        return reverse('users:document_editor')


document_editor_view = DocumentEditorView.as_view()


@login_required
def export_document_pdf(request):
    """
    Export the user's One Page Description document as a PDF.
    Saves the PDF to MinIO/S3 storage and creates a DocumentExport record.
    Person-centered managers can export for other users by passing ?user=username.
    """
    import json
    import logging
    from django.core.files.base import ContentFile
    from inclusive_world_portal.portal.models import DocumentExport
    from datetime import datetime
    from inclusive_world_portal.users.models import User
    
    logger = logging.getLogger(__name__)
    
    try:
        # Determine which user's document to export
        target_username = request.GET.get('user')
        if target_username:
            # Only PCMs can export other users' documents
            if request.user.role != 'person_centered_manager':
                messages.error(request, _('You do not have permission to export other users\' documents.'))
                return redirect('users:document_editor')
            
            try:
                target_user = User.objects.get(username=target_username)
            except User.DoesNotExist:
                messages.error(request, _('User not found.'))
                return redirect('users:document_editor')
        else:
            target_user = request.user
        
        # Get the user's document
        document = get_object_or_404(
            Document,
            user=target_user,
            title="One Page Description"
        )
        
        # Extract HTML content from django-quill-editor format
        # The content is stored as JSON: {"delta": {...}, "html": "..."}
        try:
            content_data = json.loads(document.content)
            html_content_only = content_data.get('html', '')
        except (json.JSONDecodeError, TypeError):
            # If it's not JSON, use as-is (fallback)
            html_content_only = document.content
        
        # Check if document has content
        if not html_content_only or html_content_only.strip() == '':
            if target_user.id == request.user.id:
                messages.warning(request, _('Your document is empty. Please add some content before exporting.'))
            else:
                messages.warning(request, _(f'The document for {target_user.name or target_user.username} is empty. Please add some content before exporting.'))
            
            if target_user.id != request.user.id:
                return redirect(f"{reverse('users:document_editor')}?user={target_user.username}")
            return redirect('users:document_editor')
        
        # Get the logo path and font paths for embedding in PDF
        from django.conf import settings
        import base64
        import os
        
        logo_path = os.path.join(settings.BASE_DIR, 'inclusive_world_portal', 'static', 'images', 'inclusive-world-logo.png')
        logo_data_uri = ''
        
        try:
            with open(logo_path, 'rb') as logo_file:
                logo_base64 = base64.b64encode(logo_file.read()).decode('utf-8')
                logo_data_uri = f'data:image/png;base64,{logo_base64}'
        except Exception as e:
            logger.warning(f"Could not load logo for PDF: {e}")
        
        # Get user's profile picture for PDF header
        profile_picture_data_uri = ''
        if target_user.profile_picture:
            try:
                # Open profile picture file and convert to base64
                with target_user.profile_picture.open('rb') as profile_file:
                    profile_base64 = base64.b64encode(profile_file.read()).decode('utf-8')
                    # Detect image type (png, jpg, etc.)
                    file_ext = target_user.profile_picture.name.split('.')[-1].lower()
                    mime_type = 'image/jpeg' if file_ext in ['jpg', 'jpeg'] else f'image/{file_ext}'
                    profile_picture_data_uri = f'data:{mime_type};base64,{profile_base64}'
            except Exception as e:
                logger.warning(f"Could not load profile picture for PDF: {e}")
        
        # Get font paths for Montserrat (brand font)
        montserrat_font_path = os.path.join(settings.BASE_DIR, 'inclusive_world_portal', 'static', 'fonts', 'Montserrat-VariableFont_wght.ttf')
        
        # Load shared document styles (single source of truth for editor and PDF)
        shared_styles_path = os.path.join(settings.BASE_DIR, 'inclusive_world_portal', 'templates', 'users', '_document_shared_styles.css')
        try:
            with open(shared_styles_path, 'r') as f:
                shared_styles = f.read()
                # Replace template variable with actual font path for PDF
                shared_styles = shared_styles.replace('{{ montserrat_font_url }}', f'file://{montserrat_font_path}')
        except Exception as e:
            logger.warning(f"Could not load shared styles: {e}")
            # Fallback to basic styles if shared styles file is missing
            shared_styles = f"""
                @font-face {{
                    font-family: 'Montserrat';
                    src: url('file://{montserrat_font_path}') format('truetype');
                    font-weight: 100 900;
                }}
                body {{ font-family: 'Montserrat', sans-serif; font-size: 11pt; line-height: 1.6; }}
            """
        
        # Create HTML for PDF with shared styles and running header on every page
        pdf_html = f"""        <!DOCTYPE html>        <html>        <head>            <meta charset="utf-8">            <title>{document.title}</title>            <style>                /* PDF-specific page setup with running header */                @page {{                    size: A4;                    margin-top: 1.5cm;
                    margin-bottom: 0.5cm;
                    margin-left: 0.5cm;
                    margin-right: 0.5cm;
                    margin-top: 3cm;
                    
                    /* Display the header on every page */
                    @top-left {{
                        content: element(header);
                        width: 100%;
                    }}
                }}
                
                /* Running header element - positioned at top of every page */
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
                    width: auto;
                    height: auto;
                    border-radius: 4px;
                    object-fit: cover;
                }}
                                
                /* Shared document styles - single source of truth */                {shared_styles}            </style>        </head>        <body>            <!-- Running header that appears on every page -->            <div class="running-header">                <div class="logo-container">                    {'<img class="logo" src="' + logo_data_uri + '" alt="Inclusive World">' if logo_data_uri else '<div style="width:100px;"></div>'}                </div>                <div class="profile-container">                    {'<img class="profile-picture" src="' + profile_picture_data_uri + '" alt="Profile Picture">' if profile_picture_data_uri else '<div style="width:80px;"></div>'}                </div>            </div>                        <div class="pdf-content document-content">                {html_content_only}            </div>        </body>        </html>        """
        
        # Configure WeasyPrint with font configuration
        try:
            # Create font configuration for WeasyPrint
            font_config = None
            if os.path.exists(montserrat_font_path):
                from weasyprint.text.fonts import FontConfiguration
                font_config = FontConfiguration()
            
            # Generate PDF with explicit font configuration and presentational hints
            # CRITICAL: presentational_hints=True preserves ALL inline styles from the editor,
            # including colors, font sizes, and other formatting applied by users in Quill.
            # This ensures true WYSIWYG - the PDF matches exactly what users see in the editor.
            pdf_bytes = HTML(string=pdf_html).write_pdf(
                presentational_hints=True,
                font_config=font_config,
            )
        except Exception as pdf_error:
            logger.error(f"PDF generation error: {pdf_error}", exc_info=True)
            messages.error(
                request, 
                _('An error occurred while generating the PDF. Please try again or contact support if the problem persists.')
            )
            return redirect('users:document_editor')
        
        # Save PDF to storage (MinIO/S3 or filesystem)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'one_page_description_{target_user.username}_{timestamp}.pdf'
        
        # Create new export record (NOT automatically active)
        export = DocumentExport.objects.create(
            user=target_user,
            document=document,
            is_active=False
        )
        
        # Save the PDF file
        export.file.save(filename, ContentFile(pdf_bytes), save=True)
        
        logger.info(f"Successfully created PDF export {export.export_id} for user {target_user.username} by {request.user.username}")
        
        if target_user.id == request.user.id:
            messages.success(
                request,
                _('Document exported successfully! Select the radio button to set it as your active OPD.')
            )
        else:
            messages.success(
                request,
                _(f'Document exported successfully for {target_user.name or target_user.username}! Select the radio button to set it as the active OPD.')
            )
        
        # Redirect back with the user parameter if editing another user's document
        if target_user.id != request.user.id:
            return redirect(f"{reverse('users:document_editor')}?user={target_user.username}")
        
        return redirect('users:document_editor')
        
    except Exception as e:
        logger.error(f"Unexpected error in PDF export: {e}", exc_info=True)
        messages.error(
            request,
            _('An unexpected error occurred. Please try again later.')
        )
        
        # Redirect back with the user parameter if editing another user's document
        target_username = request.GET.get('user')
        if target_username and request.user.role == 'person_centered_manager':
            return redirect(f"{reverse('users:document_editor')}?user={target_username}")
        
        return redirect('users:document_editor')


@login_required
def autogenerate_document_from_survey(request):
    """
    Generate One Page Profile document from Discovery Questions responses.
    Returns JSON with the generated HTML content.
    Person-centered managers can generate for other users by passing ?user=username.
    """
    from inclusive_world_portal.users.models import User
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Determine which user's survey to use
        target_username = request.GET.get('user')
        if target_username:
            # Only PCMs can generate for other users
            if request.user.role != 'person_centered_manager':
                return JsonResponse({
                    'success': False,
                    'error': 'You do not have permission to generate documents for other users.'
                }, status=403)
            
            try:
                target_user = User.objects.get(username=target_username)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'User not found.'
                }, status=404)
        else:
            target_user = request.user
        
        # Get the target user's discovery survey
        try:
            survey = DiscoverySurvey.objects.get(user=target_user)
        except DiscoverySurvey.DoesNotExist:
            user_display = target_user.name or target_user.username
            if target_user.id == request.user.id:
                error_msg = 'Please complete the Discovery Questions first before generating your profile.'
            else:
                error_msg = f'{user_display} has not completed the Discovery Questions yet. Please complete it first.'
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=400)
        
        # Get template context from survey
        context = survey.get_template_context()
        
        # Generate HTML content for One Page Profile
        html_content = generate_one_page_profile_html(context)
        
        return JsonResponse({
            'success': True,
            'html': html_content,
            'message': 'Document template generated successfully!'
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating document from survey: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while generating the document. Please try again.'
        }, status=500)


def generate_one_page_profile_html(context):
    """
    Generate HTML content for One Page Profile based on survey data.
    Applies brand colors: Berry (#7F4857) for H1/H2, Blue Peacock (#00494F) for H3.
    Note: No blank lines between elements to prevent Quill from creating empty paragraphs.
    
    This template has been simplified to only use fields from the current Discovery Questions survey.
    """
    # Extract data from context with fallbacks for empty values
    fname = context.get('fname', '')
    lname = context.get('lname', '')
    
    # Brand colors: Berry for primary headers, Blue Peacock for secondary
    # IMPORTANT: No blank lines between HTML elements to avoid extra spacing in Quill editor
    html = f"""<h1><span style="color: #7F4857;">Name: {fname} {lname}</span></h1><h2><span style="color: #7F4857;">One Page Profile</span></h2><h3><span style="color: #00494F;">What people appreciate about me</span></h3><p>{context.get('about_you_great_things') or '<em>Not provided</em>'}</p><h3><span style="color: #00494F;">Who is on my team</span></h3><p>{context.get('about_you_who_is_on_your_team') or '<em>Not provided</em>'}</p><h3><span style="color: #00494F;">Things I like to do</span></h3><p>{context.get('about_you_things_you_like_to_do') or '<em>Not provided</em>'}</p><h3><span style="color: #00494F;">What I want to learn</span></h3><p>{context.get('about_you_things_you_want_to_learn') or '<em>Not provided</em>'}</p><h3><span style="color: #00494F;">What makes me happy and how I communicate it</span></h3><p>{context.get('about_you_happy') or '<em>Not provided</em>'}</p><h3><span style="color: #00494F;">What makes me sad/mad/frustrated and how I communicate it</span></h3><p>{context.get('about_you_sad') or '<em>Not provided</em>'}</p><h3><span style="color: #00494F;">School Experience</span></h3><h4>What I learned at school that I liked:</h4><p>{context.get('about_you_learned_at_school_liked') or '<em>Not provided</em>'}</p><h4>What I learned at school that I didn't like:</h4><p>{context.get('about_you_learned_at_school_didnt_like') or '<em>Not provided</em>'}</p><h3><span style="color: #00494F;">Employment Experience</span></h3><p>{context.get('about_you_jobs') or '<em>Not provided</em>'}</p><h3><span style="color: #00494F;">My IEP (Individualized Education Program)</span></h3><h4>What's working for me:</h4><p>{context.get('about_you_iep_working') or '<em>Not provided</em>'}</p><h4>What's not working for me:</h4><p>{context.get('about_you_iep_not_working') or '<em>Not provided</em>'}</p><h3><span style="color: #00494F;">How I learn best</span></h3><p>I am a <strong>{context.get('about_you_how_to_learn') or '<em>___</em>'}</strong> learner</p><h4>Supportive devices I use:</h4><p>{context.get('supportive_devices') or '<em>Not provided</em>'}</p><h4>My environment preferences:</h4><p>{context.get('about_your_working_environment') or '<em>Not provided</em>'}</p>"""
    
    # Return without calling strip() to preserve the exact HTML structure
    return html


# -------------------------
# Document Export Management Views
# -------------------------

@login_required
def preview_document_export(request, export_id):
    """
    Preview a document export in HTML view (shows PDF in iframe).
    Person-centered managers can preview exports for users they're managing.
    """
    from inclusive_world_portal.portal.models import DocumentExport
    from django.shortcuts import render
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get the export first (without filtering by user)
        export = get_object_or_404(DocumentExport, export_id=export_id)
        
        # Check permissions: user can preview their own exports, or PCMs can preview any export
        if export.user.id != request.user.id and request.user.role != 'person_centered_manager':
            logger.warning(f"User {request.user.username} attempted to preview export {export_id} belonging to {export.user.username}")
            messages.error(request, _('Permission denied.'))
            return redirect('users:document_editor')
        
        logger.info(f"User {request.user.username} previewed export {export_id} for {export.user.username}")
        
        return render(request, 'users/document_preview.html', {
            'export': export,
        })
        
    except Exception as e:
        logger.error(f"Error previewing export {export_id}: {e}", exc_info=True)
        messages.error(request, _('Could not preview the file. Please try again.'))
        return redirect('users:document_editor')


@login_required
@xframe_options_sameorigin
def preview_document_export_pdf(request, export_id):
    """
    Serve the actual PDF file for embedding in the preview page.
    Uses Content-Disposition: inline to display in browser's PDF viewer.
    Allows embedding within same origin using X-Frame-Options: SAMEORIGIN.
    Person-centered managers can preview exports for users they're managing.
    """
    from inclusive_world_portal.portal.models import DocumentExport
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get the export first (without filtering by user)
        export = get_object_or_404(DocumentExport, export_id=export_id)
        
        # Check permissions: user can preview their own exports, or PCMs can preview any export
        if export.user.id != request.user.id and request.user.role != 'person_centered_manager':
            logger.warning(f"User {request.user.username} attempted to preview PDF {export_id} belonging to {export.user.username}")
            return HttpResponse('Permission denied', status=403)
        
        # Serve the file inline for browser preview
        response = HttpResponse(export.file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{export.get_filename()}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving PDF for preview {export_id}: {e}", exc_info=True)
        messages.error(request, _('Could not load the PDF. Please try again.'))
        return redirect('users:document_editor')


@login_required
def download_document_export(request, export_id):
    """
    Download a specific document export PDF.
    Person-centered managers can download exports for users they're managing.
    """
    from inclusive_world_portal.portal.models import DocumentExport
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get the export first (without filtering by user)
        export = get_object_or_404(DocumentExport, export_id=export_id)
        
        # Check permissions: user can download their own exports, or PCMs can download any export
        if export.user.id != request.user.id and request.user.role != 'person_centered_manager':
            logger.warning(f"User {request.user.username} attempted to download export {export_id} belonging to {export.user.username}")
            messages.error(request, _('Permission denied.'))
            return redirect('users:document_editor')
        
        # Serve the file
        response = HttpResponse(export.file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{export.get_filename()}"'
        
        logger.info(f"User {request.user.username} downloaded export {export_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error downloading export {export_id}: {e}", exc_info=True)
        messages.error(request, _('Could not download the file. Please try again.'))
        return redirect('users:document_editor')


@login_required
def delete_document_export(request, export_id):
    """
    Delete a document export record and file.
    Person-centered managers can delete exports for users they're managing.
    """
    from inclusive_world_portal.portal.models import DocumentExport
    import logging
    
    logger = logging.getLogger(__name__)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Get the export first (without filtering by user)
        export = get_object_or_404(DocumentExport, export_id=export_id)
        
        # Check permissions: user can delete their own exports, or PCMs can delete any export
        if export.user.id != request.user.id and request.user.role != 'person_centered_manager':
            logger.warning(f"User {request.user.username} attempted to delete export {export_id} belonging to {export.user.username}")
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Delete the file from storage
        if export.file:
            export.file.delete(save=False)
        
        # Delete the record
        export.delete()
        
        logger.info(f"User {request.user.username} deleted export {export_id} for {export.user.username}")
        messages.success(request, _('Export deleted successfully.'))
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting export {export_id}: {e}", exc_info=True)
        return JsonResponse({'error': 'Could not delete the export'}, status=500)


@login_required
def toggle_active_export(request, export_id):
    """
    Toggle which export is marked as active (current OPD).
    If the export is already active, deactivate it.
    If it's not active, activate it and deactivate all others.
    Person-centered managers can toggle exports for users they're managing.
    """
    from inclusive_world_portal.portal.models import DocumentExport
    import logging
    
    logger = logging.getLogger(__name__)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Get the export first (without filtering by user)
        export = get_object_or_404(DocumentExport, export_id=export_id)
        
        # Check permissions: user can toggle their own exports, or PCMs can toggle any export
        if export.user.id != request.user.id and request.user.role != 'person_centered_manager':
            logger.warning(f"User {request.user.username} attempted to toggle export {export_id} belonging to {export.user.username}")
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Check if this export is already active
        if export.is_active:
            # Deactivate it
            export.is_active = False
            export.save()
            logger.info(f"User {request.user.username} deactivated export {export_id} for {export.user.username}")
            messages.success(request, _('Active OPD cleared. No OPD is currently active.'))
            return JsonResponse({'success': True, 'action': 'deactivated'})
        else:
            # Deactivate all other exports for this user and document
            DocumentExport.objects.filter(
                user=export.user,
                document=export.document
            ).exclude(export_id=export_id).update(is_active=False)
            
            # Activate this one
            export.is_active = True
            export.save()
            
            logger.info(f"User {request.user.username} set export {export_id} as active for {export.user.username}")
            messages.success(request, _('Active OPD updated successfully.'))
            return JsonResponse({'success': True, 'action': 'activated'})
        
    except Exception as e:
        logger.error(f"Error toggling active export {export_id}: {e}", exc_info=True)
        return JsonResponse({'error': 'Could not update active status'}, status=500)


@login_required
def view_active_opd(request, username=None):
    """
    View the active OPD for a user.
    If username is provided and current user is a person_centered_manager, show that user's OPD.
    Otherwise, show the current user's OPD.
    Displays embedded PDF or a message if no active OPD exists.
    """
    from inclusive_world_portal.portal.models import DocumentExport
    from inclusive_world_portal.users.models import User
    
    # Determine which user's OPD to display
    if username:
        # Check if current user has permission to view other users' OPDs
        if request.user.role not in ['person_centered_manager', 'manager']:
            messages.error(request, _('You do not have permission to view other users\' OPDs.'))
            return redirect('users:view_active_opd')
        
        # Get the target user
        target_user = get_object_or_404(User, username=username)
    else:
        # View own OPD
        target_user = request.user
    
    # Get the active OPD export
    try:
        document = Document.objects.get(
            user=target_user,
            title="One Page Description"
        )
        active_export = DocumentExport.objects.filter(
            user=target_user,
            document=document,
            is_active=True
        ).first()
    except Document.DoesNotExist:
        document = None
        active_export = None
    
    context = {
        'target_user': target_user,
        'active_export': active_export,
        'viewing_own_opd': target_user.id == request.user.id,
    }
    
    return render(request, 'users/view_active_opd.html', context)
