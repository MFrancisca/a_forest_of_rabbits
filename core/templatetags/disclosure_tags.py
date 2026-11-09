"""{% disclosure %} — the site's expand/collapse section (native <details>).

    {% load disclosure_tags %}
    {% disclosure label="Notes" class="mt-4" %}
      <p>…content…</p>
    {% enddisclosure %}

Arguments:
    label    (required) text in the always-visible summary row
    heading  truthy → the label is an <h2> (use when the content has h3s)
    class    extra classes for the <details> element (spacing)

Markup lives in core/templates/includes/disclosure.html.
"""
from django import template
from django.template.base import token_kwargs

register = template.Library()

ALLOWED = {'label', 'heading', 'class'}


class DisclosureNode(template.Node):
    def __init__(self, nodelist, kwargs):
        self.nodelist = nodelist
        self.kwargs = kwargs

    def render(self, context):
        values = {key: value.resolve(context) for key, value in self.kwargs.items()}
        content = self.nodelist.render(context)  # SafeString: already rendered and escaped
        tpl = context.template.engine.get_template('includes/disclosure.html')
        with context.push(
            label=values['label'],
            heading=values.get('heading', False),
            extra_class=values.get('class', ''),
            content=content,
        ):
            return tpl.render(context)


@register.tag
def disclosure(parser, token):
    bits = token.split_contents()
    tag_name, remaining = bits[0], bits[1:]
    kwargs = token_kwargs(remaining, parser)
    if remaining:
        raise template.TemplateSyntaxError(f'{tag_name} only takes keyword arguments, got {remaining!r}')
    unknown = set(kwargs) - ALLOWED
    if unknown:
        raise template.TemplateSyntaxError(f'{tag_name} got unknown arguments: {", ".join(sorted(unknown))}')
    if 'label' not in kwargs:
        raise template.TemplateSyntaxError(f'{tag_name} requires label="…"')
    nodelist = parser.parse(('enddisclosure',))
    parser.delete_first_token()
    return DisclosureNode(nodelist, kwargs)
