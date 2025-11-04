"""
Views for user document management with Quill editor.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from weasyprint import HTML, CSS

from inclusive_world_portal.portal.models import Document
from inclusive_world_portal.users.document_forms import DocumentForm


class DocumentEditorView(LoginRequiredMixin, FormView):
    """
    Document editor view with Quill rich text editor.
    Allows users to create and edit their documents (e.g., One Page Description).
    """
    template_name = "users/document_editor.html"
    form_class = DocumentForm
    
    def get_initial(self):
        """Pre-populate form with existing document content."""
        initial = super().get_initial()
        
        # Get or create the user's primary document (for One Page Description)
        document, created = Document.objects.get_or_create(
            user=self.request.user,
            title="One Page Description",
            defaults={'content': '', 'state': 'draft'}
        )
        
        initial['title'] = document.title
        initial['content'] = document.content
        initial['state'] = document.state
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the document for context
        document, created = Document.objects.get_or_create(
            user=self.request.user,
            title="One Page Description",
            defaults={'content': '', 'state': 'draft'}
        )
        
        context['document'] = document
        context['document_title'] = document.title
        return context
    
    def form_valid(self, form):
        """Save the document when form is submitted."""
        title = form.cleaned_data.get('title', 'One Page Description')
        content = form.cleaned_data.get('content', '')
        state = form.cleaned_data.get('state', 'draft')
        
        # Get or create the document
        document, created = Document.objects.get_or_create(
            user=self.request.user,
            title=title,
            defaults={'content': content, 'state': state}
        )
        
        if not created:
            document.content = content
            document.state = state
            document.save()
        
        messages.success(self.request, _('Document saved successfully!'))
        return redirect('users:document_editor')
    
    def get_success_url(self):
        return reverse('users:document_editor')


document_editor_view = DocumentEditorView.as_view()


@login_required
def export_document_pdf(request):
    """
    Export the user's One Page Description document as a PDF.
    """
    import json
    
    # Get the user's document
    document = get_object_or_404(
        Document,
        user=request.user,
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
    
    # Create HTML for PDF - WYSIWYG style (what you see is what you get)
    pdf_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{document.title}</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: Arial, Helvetica, sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                color: #000;
            }}
            /* Quill editor default styles for PDF */
            h1 {{ font-size: 2em; margin: 0.67em 0; }}
            h2 {{ font-size: 1.5em; margin: 0.75em 0; }}
            h3 {{ font-size: 1.17em; margin: 0.83em 0; }}
            p {{ margin: 1em 0; }}
            strong {{ font-weight: bold; }}
            em {{ font-style: italic; }}
            u {{ text-decoration: underline; }}
            a {{ color: #06c; text-decoration: underline; }}
            ul, ol {{ margin: 1em 0; padding-left: 2em; }}
            blockquote {{
                border-left: 4px solid #ccc;
                margin: 1em 0;
                padding-left: 1em;
                color: #666;
            }}
        </style>
    </head>
    <body>
        {html_content_only}
    </body>
    </html>
    """
    
    # Generate PDF
    pdf = HTML(string=pdf_html).write_pdf()
    
    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="one_page_description_{request.user.username}.pdf"'
    
    return response
