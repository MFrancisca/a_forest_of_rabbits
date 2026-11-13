"""Image collections the site creates for itself, such as "Projects" and "Manuscripts"."""
from wagtail.models import Collection


def top_level_collection(name):
    """The collection named `name` directly under Root, created if missing."""
    root = Collection.get_first_root_node()
    return root.get_children().filter(name=name).first() or root.add_child(name=name)
