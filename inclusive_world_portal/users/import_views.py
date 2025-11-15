"""
Views for bulk user import functionality.
Allows managers to import multiple users via a spreadsheet-like interface.
"""
import json
import logging
from typing import Dict, List, Tuple

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from inclusive_world_portal.users.models import User

logger = logging.getLogger(__name__)


class UserImportView(LoginRequiredMixin, TemplateView):
    """
    View for importing multiple users via spreadsheet interface.
    Only accessible to managers.
    """
    template_name = "users/user_import.html"
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user has permission to access the import feature."""
        if request.user.role not in ['manager', 'person_centered_manager']:
            messages.error(request, _('Only managers can access the user import feature.'))
            return redirect('users:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        import json as json_module
        context = super().get_context_data(**kwargs)
        
        # Define the fields that will be imported
        import_fields = [
            {'key': 'username', 'label': 'Username', 'required': True, 'type': 'text'},
            {'key': 'email', 'label': 'Email', 'required': True, 'type': 'email'},
            {'key': 'name', 'label': 'Full Name', 'required': True, 'type': 'text'},
            {'key': 'role', 'label': 'Role', 'required': True, 'type': 'select', 
             'choices': ['member', 'volunteer', 'person_centered_manager', 'manager']},
            {'key': 'phone_no', 'label': 'Phone Number', 'required': False, 'type': 'text'},
            {'key': 'age', 'label': 'Age', 'required': False, 'type': 'number'},
            {'key': 'grade', 'label': 'Grade', 'required': False, 'type': 'text'},
            {'key': 'bio', 'label': 'Bio', 'required': False, 'type': 'text'},
            {'key': 'support_needs', 'label': 'Support Needs', 'required': False, 'type': 'text'},
            {'key': 'parent_guardian_name', 'label': 'Parent/Guardian Name', 'required': False, 'type': 'text'},
            {'key': 'parent_guardian_phone', 'label': 'Parent/Guardian Phone', 'required': False, 'type': 'text'},
            {'key': 'parent_guardian_email', 'label': 'Parent/Guardian Email', 'required': False, 'type': 'email'},
            {'key': 'emergency_contact_first_name', 'label': 'Emergency Contact First Name', 'required': False, 'type': 'text'},
            {'key': 'emergency_contact_last_name', 'label': 'Emergency Contact Last Name', 'required': False, 'type': 'text'},
            {'key': 'emergency_contact_relationship', 'label': 'Emergency Contact Relationship', 'required': False, 'type': 'text'},
            {'key': 'emergency_contact_phone', 'label': 'Emergency Contact Phone', 'required': False, 'type': 'text'},
            {'key': 'emergency_contact_email', 'label': 'Emergency Contact Email', 'required': False, 'type': 'email'},
        ]
        
        # Role choices for display
        role_choices = [
            {'value': 'member', 'label': 'Member'},
            {'value': 'volunteer', 'label': 'Volunteer'},
            {'value': 'person_centered_manager', 'label': 'Person Centered Manager'},
            {'value': 'manager', 'label': 'Manager'},
        ]
        
        # Convert to JSON strings to avoid Python boolean issues
        context['import_fields_json'] = json_module.dumps(import_fields)
        context['role_choices_json'] = json_module.dumps(role_choices)
        
        return context


user_import_view = UserImportView.as_view()


@login_required
def process_user_import(request):
    """
    Process the bulk user import from the spreadsheet interface.
    Validates data and creates users in a transaction.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST request required'}, status=405)
    
    # Check permissions
    if request.user.role not in ['manager', 'person_centered_manager']:
        return JsonResponse({
            'success': False,
            'error': 'Only managers can import users.'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        users_data = data.get('users', [])
        
        if not users_data:
            return JsonResponse({
                'success': False,
                'error': 'No user data provided.'
            }, status=400)
        
        # Validate all users first
        validation_errors = []
        for idx, user_data in enumerate(users_data):
            row_errors = validate_user_data(user_data, idx + 1)
            if row_errors:
                validation_errors.extend(row_errors)
        
        if validation_errors:
            return JsonResponse({
                'success': False,
                'error': 'Validation failed',
                'validation_errors': validation_errors
            }, status=400)
        
        # Create users in a transaction
        created_users = []
        with transaction.atomic():
            for user_data in users_data:
                user = create_user_from_data(user_data)
                created_users.append({
                    'username': user.username,
                    'email': user.email,
                    'name': user.name
                })
        
        logger.info(f"Successfully imported {len(created_users)} users by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully imported {len(created_users)} user(s).',
            'created_users': created_users
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        logger.error(f"Error processing user import: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred while importing users: {str(e)}'
        }, status=500)


def validate_user_data(user_data: Dict, row_number: int) -> List[str]:
    """
    Validate a single user's data.
    Returns a list of error messages.
    """
    errors = []
    
    # Required fields
    username = user_data.get('username', '').strip()
    email = user_data.get('email', '').strip()
    name = user_data.get('name', '').strip()
    role = user_data.get('role', '').strip()
    
    if not username:
        errors.append(f"Row {row_number}: Username is required")
    elif len(username) < 3:
        errors.append(f"Row {row_number}: Username must be at least 3 characters")
    elif User.objects.filter(username=username).exists():
        errors.append(f"Row {row_number}: Username '{username}' already exists")
    
    if not email:
        errors.append(f"Row {row_number}: Email is required")
    elif '@' not in email:
        errors.append(f"Row {row_number}: Invalid email format")
    elif User.objects.filter(email=email).exists():
        errors.append(f"Row {row_number}: Email '{email}' already exists")
    
    if not name:
        errors.append(f"Row {row_number}: Full name is required")
    
    if not role:
        errors.append(f"Row {row_number}: Role is required")
    elif role not in ['member', 'volunteer', 'person_centered_manager', 'manager']:
        errors.append(f"Row {row_number}: Invalid role '{role}'")
    
    # Validate age if provided
    age = user_data.get('age')
    if age:
        try:
            age_int = int(age)
            if age_int < 0 or age_int > 150:
                errors.append(f"Row {row_number}: Age must be between 0 and 150")
        except (ValueError, TypeError):
            errors.append(f"Row {row_number}: Age must be a number")
    
    return errors


def create_user_from_data(user_data: Dict) -> User:
    """
    Create a user from validated data.
    Sets a temporary password (email + age) that must be changed on first login.
    """
    # Extract required fields
    username = user_data.get('username', '').strip()
    email = user_data.get('email', '').strip()
    name = user_data.get('name', '').strip()
    role = user_data.get('role', '').strip()
    
    # Create temporary password from email + age
    age = user_data.get('age', '0')
    temp_password = f"{email}{age}"
    
    # Create user with temporary password
    user = User.objects.create_user(
        username=username,
        email=email,
        password=temp_password,
    )
    
    # Set basic fields
    user.name = name
    user.role = role
    user.status = User.Status.PENDING_VERIFICATION  # Require verification
    
    # Set optional fields
    if user_data.get('phone_no'):
        user.phone_no = user_data['phone_no'].strip()
    
    if user_data.get('age'):
        try:
            user.age = int(user_data['age'])
        except (ValueError, TypeError):
            pass
    
    if user_data.get('grade'):
        user.grade = user_data['grade'].strip()
    
    if user_data.get('bio'):
        user.bio = user_data['bio'].strip()
    
    if user_data.get('support_needs'):
        user.support_needs = user_data['support_needs'].strip()
    
    # Parent/Guardian info
    if user_data.get('parent_guardian_name'):
        user.parent_guardian_name = user_data['parent_guardian_name'].strip()
    
    if user_data.get('parent_guardian_phone'):
        user.parent_guardian_phone = user_data['parent_guardian_phone'].strip()
    
    if user_data.get('parent_guardian_email'):
        user.parent_guardian_email = user_data['parent_guardian_email'].strip()
    
    # Emergency contact info
    if user_data.get('emergency_contact_first_name'):
        user.emergency_contact_first_name = user_data['emergency_contact_first_name'].strip()
    
    if user_data.get('emergency_contact_last_name'):
        user.emergency_contact_last_name = user_data['emergency_contact_last_name'].strip()
    
    if user_data.get('emergency_contact_relationship'):
        user.emergency_contact_relationship = user_data['emergency_contact_relationship'].strip()
    
    if user_data.get('emergency_contact_phone'):
        user.emergency_contact_phone = user_data['emergency_contact_phone'].strip()
    
    if user_data.get('emergency_contact_email'):
        user.emergency_contact_email = user_data['emergency_contact_email'].strip()
    
    user.save()
    
    logger.info(f"Created user {username} via import")
    
    return user
