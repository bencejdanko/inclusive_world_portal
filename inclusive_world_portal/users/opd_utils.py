"""
Utilities for generating One Page Description (OPD) editor links.
This module handles JWT token generation and integration with the OPD collaborative editor.
"""
import time
from typing import Dict, Optional
from urllib.parse import urlencode

import jwt
from django.conf import settings


def get_opd_role_mapping(django_role: str) -> str:
    """
    Map Django user roles to OPD editor roles.
    
    OPD Role Permissions:
    - member: read-only access
    - volunteer: read-only access
    - volunteer-lead: can edit Draft and Review states
    - pcm (Person Centered Manager): full access
    - manager: full access
    - admin: full access
    
    Args:
        django_role: The Django user's role (e.g., 'member', 'person_centered_manager')
    
    Returns:
        The corresponding OPD editor role
    """
    role_mapping = {
        'member': 'member',
        'volunteer': 'volunteer',
        'person_centered_manager': 'pcm',  # Map to PCM role
        'manager': 'manager',
        'admin': 'admin',
    }
    
    # Default to member (read-only) if role not found
    return role_mapping.get(django_role, 'member')


def generate_opd_token(
    username: str,
    doc_id: str,
    role: str,
    expires_in: int = 1800  # 30 minutes default
) -> str:
    """
    Generate a JWT token for accessing the OPD editor.
    
    Args:
        username: The user's username
        doc_id: The document ID to access
        role: The user's role in the OPD system
        expires_in: Token expiration time in seconds (default: 30 minutes)
    
    Returns:
        A signed JWT token
    
    Raises:
        ValueError: If OPD_SECRET is not configured
    """
    opd_secret = getattr(settings, 'INCLUSIVE_WORLD_OPD_SECRET', None)
    
    if not opd_secret:
        raise ValueError(
            "INCLUSIVE_WORLD_OPD_SECRET is not configured in settings. "
            "Please set it in your .env file."
        )
    
    # Create JWT payload matching the OPD server's expected format
    payload = {
        'username': username,
        'doc': doc_id,
        'role': role,
        'exp': int(time.time()) + expires_in,  # Expiration timestamp
    }
    
    # Sign the token with the shared secret
    token = jwt.encode(payload, opd_secret, algorithm='HS256')
    
    return token


def generate_opd_editor_url(
    user,
    doc_id: Optional[str] = None,
    expires_in: int = 1800
) -> str:
    """
    Generate a complete URL to the OPD editor frontend with authentication token.
    
    Args:
        user: Django User instance
        doc_id: Document ID (defaults to user's username if not provided)
        expires_in: Token expiration time in seconds (default: 30 minutes)
    
    Returns:
        A complete URL to the OPD editor with authentication token
    
    Raises:
        ValueError: If OPD_SERVER is not configured
    """
    opd_server = getattr(settings, 'INCLUSIVE_WORLD_OPD_SERVER', None)
    
    if not opd_server:
        raise ValueError(
            "INCLUSIVE_WORLD_OPD_SERVER is not configured in settings. "
            "Please set it in your .env file."
        )
    
    # Use username as doc_id if not provided (each user gets their own document)
    if not doc_id:
        doc_id = user.username
    
    # Map the Django role to OPD role
    opd_role = get_opd_role_mapping(user.role)
    
    # Generate the JWT token
    token = generate_opd_token(
        username=user.username,
        doc_id=doc_id,
        role=opd_role,
        expires_in=expires_in
    )
    
    # Construct the frontend URL with token as query parameter.
    # Prefer an explicit client URL from settings. If not provided, fall back
    # to a best-effort derivation from the OPD server URL (useful for
    # local development where backend runs on :4000 and frontend on :5173).
    client_url = getattr(settings, 'INCLUSIVE_WORLD_OPD_CLIENT_URL', None)

    if not client_url:
        # Fallback: if OPD server looks like localhost:4000, map it to :5173
        if opd_server.startswith('http://localhost:') or opd_server.startswith('http://127.0.0.1:'):
            client_url = opd_server.replace(':4000', ':5173')
        else:
            # Last resort default (same as OPD server's client default)
            client_url = 'http://localhost:5173'

    params = urlencode({'token': token})

    return f"{client_url}/?{params}"


def get_opd_document_id_for_user(user) -> str:
    """
    Get the OPD document ID for a user.
    By default, each user has their own document based on their username.
    
    Args:
        user: Django User instance
    
    Returns:
        The document ID to use for this user
    """
    # For now, use username as the document ID
    # In the future, this could be customized per user or linked to specific programs
    return user.username
