"""Light/dark theme (issue #17): tokens, contrast in both themes, toggle, no flash."""
import re
from pathlib import Path

import pytest
from django.conf import settings

CSS = Path(settings.BASE_DIR) / 'core' / 'css' / 'input.css'
TEMPLATE_DIRS = [Path(settings.BASE_DIR) / app / 'templates' for app in ('core', 'blog', 'pigments')]

# The lightbox is always a black overlay in both themes, so it keeps literal colors:
# backdrop, Close button, and the Close button's focus outline. Allowed only there.
ALLOWED_RAW = {
    Path('core/templates/includes/lightbox.html'): {'bg-black', 'bg-white', 'text-stone-900', 'outline-white'},
}
PALETTE = (
    'red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple'
    '|fuchsia|pink|rose|slate|gray|zinc|neutral|stone|mauve|olive|mist|taupe'
)
RAW_COLOR = re.compile(
    r'(?<![\w-])(?:[\w-]+:)*('
    r'(?:bg|text|border(?:-[trblxy])?|divide|decoration|ring|outline|fill|stroke|placeholder|caret|accent|shadow|from|via|to)'
    rf'-(?:white|black|(?:{PALETTE})-\d+))(?![\w-])'
)


def _tokens():
    """{name: (light, dark)} from the light-dark() values in input.css."""
    return {
        name: (light, dark)
        for name, light, dark in re.findall(r'--color-([\w-]+):\s*light-dark\((#[0-9a-f]{6}),\s*(#[0-9a-f]{6})\)', CSS.read_text())
    }


def _luminance(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(a, b):
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


# Every foreground/background pairing the templates use, with its WCAG AA minimum.
PAIRS = [
    *[(fg, bg, 4.5) for fg in ('ink', 'ink-muted', 'ink-subtle', 'accent') for bg in ('surface', 'surface-muted')],
    ('on-accent', 'accent', 4.5),   # hovered home pills, 404 button
    ('on-tag', 'tag', 4.5),         # category tags
    ('surface', 'ink', 4.5),        # no-JS "Apply filters" button
    ('ink-subtle', 'surface', 3.0),  # inactive carousel dot outline (UI part)
]


@pytest.mark.parametrize('theme', [0, 1], ids=['light', 'dark'])
@pytest.mark.parametrize('fg, bg, minimum', PAIRS, ids=[f'{fg}-on-{bg}' for fg, bg, _ in PAIRS])
def test_token_pairs_meet_wcag_aa_in_both_themes(theme, fg, bg, minimum):
    tokens = _tokens()
    ratio = _contrast(tokens[fg][theme], tokens[bg][theme])
    assert ratio >= minimum, f'{fg} on {bg}: {ratio:.2f} < {minimum}'


def test_fallback_for_browsers_without_light_dark_uses_the_light_values():
    css = CSS.read_text()
    fallback = css.split('@supports not (color: light-dark(', 1)[1].split('}', 1)[0]
    values = dict(re.findall(r'--color-([\w-]+):\s*(#[0-9a-f]{6})', fallback))
    assert values == {name: light for name, (light, _) in _tokens().items()}


def test_every_token_has_a_light_and_dark_value():
    assert set(_tokens()) >= {
        'surface', 'surface-muted', 'ink', 'ink-muted', 'ink-subtle',
        'line', 'line-strong', 'accent', 'on-accent', 'tag', 'on-tag',
    }


def test_templates_use_theme_tokens_not_raw_palette_colors():
    found = {}
    for directory in TEMPLATE_DIRS:
        for path in directory.rglob('*.html'):
            relative = path.relative_to(settings.BASE_DIR)
            raw = set(RAW_COLOR.findall(path.read_text())) - ALLOWED_RAW.get(relative, set())
            if raw:
                found[str(relative)] = sorted(raw)
    assert found == {}, f'raw palette colors would not switch with the theme: {found}'


# --- toggle and no-flash -----------------------------------------------------------------

@pytest.mark.django_db
def test_saved_theme_is_applied_before_the_stylesheet_loads(client):
    html = client.get('/pigments/').content.decode()
    head = html.split('</head>', 1)[0]
    script = head.index("localStorage.getItem('theme')")
    assert script < head.index('css/output.css')
    assert '<meta name="color-scheme" content="light dark">' in head


@pytest.mark.django_db
def test_toggle_button_is_accessible_and_hidden_without_js(client):
    html = client.get('/pigments/').content.decode()
    button = re.search(r'<button[^>]*id="theme-toggle"[^>]*>', html).group(0)
    assert ' hidden' in button                       # shown by the script
    assert 'aria-pressed="false"' in button and 'aria-label="Dark mode"' in button
    toggle = html.split('id="theme-toggle"', 1)[1].split('</button>', 1)[0]
    assert toggle.count('aria-hidden="true"') == 2   # moon + sun icons are decorative
    assert "localStorage.setItem('theme'" in html
    # Both scripts bail out where light-dark() is unsupported (those browsers get the
    # light palette, so a dark toggle could only darken scrollbars and form controls).
    assert html.count("CSS.supports('color', 'light-dark(#000, #fff)')") == 2


def test_color_scheme_follows_device_unless_pinned():
    css = CSS.read_text()
    assert ':root { color-scheme: light dark; }' in css
    assert ':root.light { color-scheme: light; }' in css
    assert ':root.dark { color-scheme: dark; }' in css
