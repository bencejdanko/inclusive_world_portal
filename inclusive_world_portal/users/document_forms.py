"""
Forms for user document management with Quill editor.
"""
from django import forms
from django_quill.forms import QuillFormField
from inclusive_world_portal.portal.models import DocumentState


class DocumentForm(forms.Form):
    """
    Form for editing documents with Quill rich text editor.
    Configured to use brand fonts (Montserrat) for WYSIWYG consistency with PDF export.
    """
    title = forms.CharField(
        max_length=255,
        required=False,
        initial="One Page Description",
        widget=forms.HiddenInput()
    )
    content = QuillFormField(
        # Quill configuration uses settings.QUILL_CONFIGS['default']
        # which includes brand colors in the toolbar
    )
    state = forms.ChoiceField(
        choices=DocumentState.choices,
        initial=DocumentState.DRAFT,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm state-selector'
        })
    )
