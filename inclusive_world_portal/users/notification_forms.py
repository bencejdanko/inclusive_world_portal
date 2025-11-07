"""
Forms for notification management.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe

from inclusive_world_portal.users.models import User
from inclusive_world_portal.portal.models import Program

User = get_user_model()


class LinkedModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """ModelMultipleChoiceField that renders labels as HTML links to object.get_absolute_url().

    Used for the users field so user choices include links to their profile.
    """
    def label_from_instance(self, obj):
        try:
            url = obj.get_absolute_url()
        except Exception:
            url = '#'
        label = obj.name or getattr(obj, 'username', str(obj))
        return mark_safe(f'<a href="{url}">{label}</a>')


class BulkNotificationForm(forms.Form):
    """
    Form for managers to create bulk notifications.
    Supports targeting by role, program, or specific users.
    """
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    
    verb = forms.CharField(
        max_length=255,
        label='Title',
        help_text='Short title for the notification (e.g., "New Program Available")',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter notification title'})
    )
    
    description = forms.CharField(
        label='Message',
        help_text='Detailed message content',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter notification message'})
    )
    
    level = forms.ChoiceField(
        choices=LEVEL_CHOICES,
        initial='info',
        label='Type',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Targeting options
    target_roles = forms.MultipleChoiceField(
        choices=User.Role.choices,
        required=False,
        label='Target Roles',
        help_text='Send to all users with these roles',
        widget=forms.CheckboxSelectMultiple()
    )

    # Render programs as checkboxes; Program.__str__ returns the name
    target_programs = forms.ModelMultipleChoiceField(
        queryset=Program.objects.filter(archived=False),
        required=False,
        label='Target Programs',
        help_text='Send to all users enrolled in these programs',
        widget=forms.CheckboxSelectMultiple()
    )

    # Render specific users as checkboxes with linked labels
    target_users = LinkedModelMultipleChoiceField(
        queryset=User.objects.filter(status=User.Status.ACTIVE).order_by('username'),
        required=False,
        label='Specific Users',
        help_text='Send to specific individual users',
        widget=forms.CheckboxSelectMultiple()
    )
    
    def clean(self):
        cleaned_data = super().clean()
        target_roles = cleaned_data.get('target_roles')
        target_programs = cleaned_data.get('target_programs')
        target_users = cleaned_data.get('target_users')
        
        # At least one targeting option must be selected
        if not any([target_roles, target_programs, target_users]):
            raise forms.ValidationError(
                'Please select at least one targeting option: roles, programs, or specific users.'
            )
        
        return cleaned_data
