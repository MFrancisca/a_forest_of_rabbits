"""0014_carousel_block_with_title converts stored carousel values from a bare
list of slides to {'title', 'images'}. It rewrites live pages *and* their
revisions, so the conversion helpers are pinned down here."""
import importlib

migration = importlib.import_module('blog.migrations.0014_carousel_block_with_title')


def test_convert_carousel_wraps_list_and_strips_slide_titles():
    old = [
        {'type': 'item', 'value': {'image': 1, 'caption': 'a', 'title': 'gone'}, 'id': 'x'},
        {'image': 2, 'caption': 'b', 'title': 'gone'},  # older un-wrapped shape
    ]
    assert migration._convert_carousel(old) == {
        'title': '',
        'images': [
            {'type': 'item', 'value': {'image': 1, 'caption': 'a'}, 'id': 'x'},
            {'image': 2, 'caption': 'b'},
        ],
    }
    # Input left untouched (items are copied before editing).
    assert old[0]['value']['title'] == 'gone'


def test_convert_carousel_is_idempotent():
    new = {'title': 'T', 'images': []}
    assert migration._convert_carousel(new) is new


def test_convert_body_only_reports_changes():
    untouched = [{'type': 'rich_text', 'value': {'title': '', 'text': '<p/>'}}]
    assert migration._convert_body(untouched) is None

    raw = untouched + [{'type': 'carousel', 'value': [{'image': 1, 'caption': ''}]}]
    converted = migration._convert_body(raw)
    assert converted[1]['value'] == {'title': '', 'images': [{'image': 1, 'caption': ''}]}
    assert migration._convert_body(converted) is None
