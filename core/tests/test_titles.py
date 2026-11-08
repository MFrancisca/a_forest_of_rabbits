"""The site is branded "A Forest of Rabbits" in every <title> and the footer."""
import re

import pytest
from django.urls import reverse
from wagtail.models import Page, Site

from blog.factories import HomePageFactory, ProjectPageFactory, ProjectsIndexPageFactory
from pigments.factories import PigmentFactory

SITE = 'A Forest of Rabbits'


def _title(response):
    return re.search(r'<title>(.*?)</title>', response.content.decode(), re.S).group(1).strip()


@pytest.fixture
def home(db):
    home = HomePageFactory(parent=Page.objects.get(depth=1), title=SITE)
    Site.objects.update_or_create(
        is_default_site=True, defaults={'hostname': 'localhost', 'port': 80, 'root_page': home},
    )
    return home


def test_home_title_is_site_name_once(client, home):
    response = client.get('/')
    assert _title(response) == SITE
    assert f'{SITE}\n' in response.content.decode().split('&copy;')[1]
    assert 'Esperanza' not in response.content.decode()


def test_wagtail_page_title_is_prefixed_with_page_title(client, home):
    index = ProjectsIndexPageFactory(parent=home, title='Projects', slug='projects')
    project = ProjectPageFactory(parent=index, title='Gilded Armor')

    assert _title(client.get(index.url)) == f'Projects — {SITE}'
    assert _title(client.get(project.url)) == f'Gilded Armor — {SITE}'


def test_seo_title_overrides_page_title(client, home):
    index = ProjectsIndexPageFactory(parent=home, title='Projects', slug='projects',
                                     seo_title='All my projects')
    assert _title(client.get(index.url)) == f'All my projects — {SITE}'


@pytest.mark.django_db
def test_pigment_titles(client):
    pigment = PigmentFactory(with_formula=True, name='Vermilion')

    assert _title(client.get(reverse('pigments:list'))) == f'Pigments — {SITE}'
    assert _title(client.get(reverse('pigments:detail', args=[pigment.pk]))) == f'Vermilion — {SITE}'
