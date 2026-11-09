"""{% disclosure %}: the shared expand/collapse markup."""
import re

import pytest
from django.template import Context, Template, TemplateSyntaxError


def _render(source, **context):
    return Template('{% load disclosure_tags %}' + source).render(Context(context))


def test_renders_native_details_with_label_and_content():
    html = _render('{% disclosure label="Notes" class="mt-4" %}<p>Body {{ x }}</p>{% enddisclosure %}', x=1)

    assert '<details class="mt-4">' in html
    summary = html.split('<summary', 1)[1].split('</summary>', 1)[0]
    assert '<span class="font-display text-accent text-lg">Notes</span>' in summary
    assert 'aria-hidden="true"' in summary  # chevron is decorative
    assert '[[open]>summary>&]:rotate-180' in summary
    # Content comes after the summary, inside <details>, rendered in the caller's context.
    assert html.index('</summary>') < html.index('<p>Body 1</p>') < html.index('</details>')


def test_nested_disclosures_rotate_their_own_chevron_only():
    html = _render('{% disclosure label="Outer" %}{% disclosure label="Inner" %}x{% enddisclosure %}{% enddisclosure %}')
    # A shared group-open/* name would rotate the inner chevron whenever the outer one opened.
    assert 'group-open' not in html
    assert html.count('[[open]>summary>&]:rotate-180') == 2


def test_omits_class_attribute_when_no_class_given():
    assert '<details>' in _render('{% disclosure label="X" %}x{% enddisclosure %}')


def test_heading_variant_puts_an_h2_in_the_summary():
    html = _render('{% disclosure label=name heading=True %}x{% enddisclosure %}', name='Archive')
    summary = html.split('<summary', 1)[1].split('</summary>', 1)[0]
    assert re.search(r'<h2\b[^>]*>Archive</h2>', summary)
    assert '<span' not in summary


def test_label_is_escaped_but_content_is_not_double_escaped():
    html = _render(
        '{% disclosure label=name %}<em>{{ body }}</em>{% enddisclosure %}',
        name='<b>Tom & Jerry</b>', body='a < b',
    )
    assert '&lt;b&gt;Tom &amp; Jerry&lt;/b&gt;' in html
    assert '<em>a &lt; b</em>' in html


def test_does_not_leak_its_variables_into_the_caller():
    html = _render('{% disclosure label="X" %}{% enddisclosure %}[{{ label }}]')
    assert html.endswith('[]')


@pytest.mark.parametrize('source, message', [
    ('{% disclosure %}x{% enddisclosure %}', 'requires label'),
    ('{% disclosure label="X" colour="red" %}x{% enddisclosure %}', 'unknown arguments: colour'),
    ('{% disclosure "X" %}x{% enddisclosure %}', 'only takes keyword arguments'),
])
def test_bad_arguments_fail_at_compile_time(source, message):
    with pytest.raises(TemplateSyntaxError, match=message):
        _render(source)
