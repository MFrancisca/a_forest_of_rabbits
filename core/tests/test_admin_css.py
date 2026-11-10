import pytest
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders


@pytest.mark.django_db
def test_admin_pages_load_the_site_admin_stylesheet(client):
    """core/wagtail_hooks.py adds css/admin.css (wider listing filter panel) to the admin."""
    # Production uses manifest static storage, where a missing file breaks every admin page.
    assert finders.find('css/admin.css')
    user = get_user_model().objects.create_superuser('admin', 'admin@example.com', 'pw')
    client.force_login(user)
    response = client.get('/cms/images/')
    assert response.status_code == 200
    assert 'css/admin.css' in response.content.decode()
