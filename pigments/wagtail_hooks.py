# pigments/wagtail_hooks.py
from wagtail.snippets.models import register_snippet  # noqa: F401
# Models are registered via @register_snippet decorator in models.py.
# This file confirms the hooks module loads correctly.
# Phase 2+ will add SnippetViewSet customisations for list columns and search.
