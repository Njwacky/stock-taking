"""Feedback: submit, view, manager review."""
import pytest
from django.contrib.auth import get_user_model

from stockT.models import UserComment

User = get_user_model()

pytestmark = pytest.mark.django_db


def submit_comment(client, **overrides):
    payload = {'category': 'bug', 'subject': 'Broken thing', 'message': 'It is broken'}
    payload.update(overrides)
    return client.post('/comments/submit/', payload)


class TestSubmission:
    def test_member_submits(self, as_member, member):
        response = submit_comment(as_member)
        assert response.status_code == 302
        assert UserComment.objects.filter(user=member, status='pending').exists()

    def test_my_comments_lists_own(self, as_member):
        submit_comment(as_member)
        response = as_member.get('/comments/my/')
        assert 'Broken thing' in response.content.decode()

    def test_ajax_submit_returns_json(self, as_member):
        response = as_member.post(
            '/comments/submit/',
            {'category': 'bug', 'subject': 'S', 'message': 'M'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        assert response.status_code == 200
        assert response.json()['success'] is True


class TestReview:
    def test_manager_updates_status(self, as_manager, member):
        comment = UserComment.objects.create(
            user=member, category='bug', subject='S', message='M',
        )
        response = as_manager.post(f'/comments/update/{comment.id}/', {
            'status': 'resolved', 'admin_response': 'Fixed it',
        })
        assert response.status_code == 302
        comment.refresh_from_db()
        assert comment.status == 'resolved'
        assert comment.admin_response == 'Fixed it'
        assert comment.reviewed_by is not None

    def test_invalid_status_rejected(self, as_manager, member):
        comment = UserComment.objects.create(
            user=member, category='bug', subject='S', message='M',
        )
        as_manager.post(f'/comments/update/{comment.id}/', {'status': 'bogus'})
        comment.refresh_from_db()
        assert comment.status == 'pending'

    def test_plain_member_cannot_review(self, as_member, member):
        comment = UserComment.objects.create(
            user=member, category='bug', subject='S', message='M',
        )
        response = as_member.post(f'/comments/update/{comment.id}/', {'status': 'resolved'})
        assert response.status_code == 302
        comment.refresh_from_db()
        assert comment.status == 'pending'

    def test_manage_page_gated(self, as_member):
        assert as_member.get('/comments/manage/').status_code == 302
        assert as_member.get('/comments/my/').status_code == 200
