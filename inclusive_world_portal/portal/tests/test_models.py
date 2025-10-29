import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from inclusive_world_portal.portal.models import (
    UserProfile, UserRole, UserRoleType, Program, Enrollment, UserNotification
)

User = get_user_model()

@pytest.mark.django_db
def test_profile_and_default_role_created():
    u = User.objects.create(username="alice", email="a@example.com")
    assert UserProfile.objects.filter(user=u).exists()
    assert UserRole.objects.filter(user=u, role=UserRoleType.MEMBER).exists()

@pytest.mark.django_db
def test_enrollment_bumps_program_enrolled():
    u = User.objects.create(username="bob", email="b@example.com")
    p = Program.objects.create(name="P1", capacity=10)
    assert p.enrolled == 0
    Enrollment.objects.create(user=u, program=p, status="approved")
    p.refresh_from_db()
    assert p.enrolled == 1

@pytest.mark.django_db
def test_user_notification_read_timestamp():
    u = User.objects.create(username="c", email="c@example.com")
    from inclusive_world_portal.portal.models import Notification, UserNotification
    n = Notification.objects.create(message="hi")
    link = UserNotification.objects.create(user=u, notification=n, is_read=False)
    assert link.read_at is None
    link.is_read = True
    link.save()
    assert link.read_at is not None
    ts = link.read_at
    # flipping back to unread clears read_at
    link.is_read = False
    link.save()
    assert link.read_at is None
