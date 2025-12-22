import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from inclusive_world_portal.portal.models import (
    Program, Enrollment
)

User = get_user_model()

@pytest.mark.django_db
def test_user_has_default_role():
    """Test that new users get the default 'member' role set on the User model."""
    u = User.objects.create(username="alice", email="a@example.com")
    # The User model has a 'role' field with default='member'
    assert u.role == 'member'

@pytest.mark.django_db
def test_enrollment_bumps_program_enrolled():
    u = User.objects.create(username="bob", email="b@example.com")
    p = Program.objects.create(name="P1", capacity=10)
    assert p.enrolled == 0
    Enrollment.objects.create(user=u, program=p, status="approved")
    p.refresh_from_db()
    assert p.enrolled == 1

@pytest.mark.django_db
def test_notification_system():
    """Test that django-notifications-hq is working correctly."""
    from notifications.signals import notify
    
    sender = User.objects.create(username="sender", email="sender@example.com")
    recipient = User.objects.create(username="recipient", email="recipient@example.com")
    
    # Send a notification
    notify.send(
        sender=sender,
        recipient=recipient,
        verb="test notification",
        description="This is a test"
    )
    
    # Check that the notification was created
    notifications = recipient.notifications.all()  # type: ignore[attr-defined]
    assert notifications.count() == 1
    
    notification = notifications.first()
    assert notification.verb == "test notification"
    assert notification.unread is True
    
    # Mark as read
    notification.mark_as_read()
    assert notification.unread is False
