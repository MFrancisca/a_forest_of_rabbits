from django.shortcuts import render, get_object_or_404
from django.db.models import Exists, OuterRef, Q

from pigments.models import (
    ColorFamily,
    Country,
    Formula,
    Manuscript,
    Pigment,
    PigmentFamily,
)

ORDINALS = {
    1: "1st", 2: "2nd", 3: "3rd",
    **{n: f"{n}th" for n in range(4, 21)},
    21: "21st", 22: "22nd",
}


def century_label(c_start):
    """Convert a century start year (e.g. 800) to a human label (e.g. '9th century')."""
    century_num = (c_start // 100) + 1
    ordinal = ORDINALS.get(century_num, f"{century_num}th")
    return f"{ordinal} century"


def get_century_buckets(manuscripts=None):
    """
    Return a list of century bucket dicts for the filter UI.
    Only includes centuries that have at least one manuscript (from
    `manuscripts`, default all) overlapping that range.
    Example: [{"start": 800, "label": "9th century"}, ...]
    """
    if manuscripts is None:
        manuscripts = Manuscript.objects.all()
    manuscripts = manuscripts.exclude(
        date_start__isnull=True, date_end__isnull=True
    ).values_list("date_start", "date_end")

    occupied = set()
    for start, end in manuscripts:
        # A single known date ("c.800") is treated as that one year.
        start = start if start is not None else end
        end = end if end is not None else start
        first_century = (start // 100) * 100
        last_century = (end // 100) * 100
        c = first_century
        while c <= last_century:
            occupied.add(c)
            c += 100

    buckets = []
    for c_start in sorted(occupied):
        buckets.append({"start": c_start, "label": century_label(c_start)})

    return buckets


FILTER_PARAMS = ("color", "pfam", "country", "manuscript", "century")
MAX_DB_INT = 2**63 - 1  # BigAutoField range; larger values can't match any row


def int_values(params, key):
    """Values of a multi-valued GET param that parse as integers, as canonical
    strings (e.g. "007" -> "7").

    Anything else (``?color=abc``, an empty ``?color=``, a 30-digit number) is
    dropped rather than passed to the ORM, where it would raise ValueError /
    OverflowError and turn a mistyped or crawled URL into a 500.
    """
    values = []
    for raw in params.getlist(key):
        try:
            value = int(raw)
        except ValueError:
            continue
        if abs(value) <= MAX_DB_INT:
            values.append(str(value))
    return values


def listed_pigments():
    """Pigments shown on the list page: only those with at least one formula.

    Exists() rather than a join so pigments with several formulas aren't duplicated.
    Pigments without formulas stay reachable at their detail URL.
    """
    return Pigment.objects.filter(Exists(Formula.objects.filter(pigment=OuterRef("pk"))))


def filter_options():
    """Sidebar options, limited to those matching at least one listed pigment,
    so no option leads to an empty result."""
    listed = listed_pigments()
    manuscripts = Manuscript.objects.filter(pigment_links__pigment__in=listed).distinct()
    return {
        "color_families": ColorFamily.objects.filter(pigments__in=listed).distinct(),
        "pigment_families": PigmentFamily.objects.filter(pigments__in=listed).distinct(),
        "countries": Country.objects.filter(manuscripts__in=manuscripts).distinct(),
        "manuscripts": manuscripts,
        "century_buckets": get_century_buckets(manuscripts),
    }


def build_filtered_queryset(params):
    """
    Build a filtered and deduplicated Pigment queryset from GET params.
    Filtering logic: OR within a dimension, AND across dimensions.
    Always returns .distinct() to prevent M2M join duplicates.
    """
    qs = listed_pigments().select_related("color_family", "pigment_family")

    # Color family — OR within dimension via __in
    color_ids = int_values(params, "color")
    if color_ids:
        qs = qs.filter(color_family__id__in=color_ids)

    # Pigment family — OR within dimension via __in
    pfam_ids = int_values(params, "pfam")
    if pfam_ids:
        qs = qs.filter(pigment_family__id__in=pfam_ids)

    # Country — joins through manuscript_links → manuscript → country
    country_ids = int_values(params, "country")
    if country_ids:
        qs = qs.filter(manuscript_links__manuscript__country__id__in=country_ids)

    # Manuscript — joins through manuscript_links → manuscript
    manuscript_ids = int_values(params, "manuscript")
    if manuscript_ids:
        qs = qs.filter(manuscript_links__manuscript__id__in=manuscript_ids)

    # Century — range overlap: manuscript overlaps [c_start, c_start+99].
    # A dated range overlaps if date_start <= c_end AND date_end >= c_start;
    # a manuscript with only one of the two dates is treated as that one year.
    centuries = int_values(params, "century")
    if centuries:
        ms = "manuscript_links__manuscript__"
        century_q = Q()
        for c_start in centuries:
            c_start_int = int(c_start)
            c_end_int = min(c_start_int + 99, MAX_DB_INT)
            century_q |= Q(**{
                f"{ms}date_start__lte": c_end_int,
                f"{ms}date_end__gte": c_start_int,
            })
            century_q |= Q(**{
                f"{ms}date_end__isnull": True,
                f"{ms}date_start__range": (c_start_int, c_end_int),
            })
            century_q |= Q(**{
                f"{ms}date_start__isnull": True,
                f"{ms}date_end__range": (c_start_int, c_end_int),
            })
        qs = qs.filter(century_q)

    # Always deduplicate — M2M joins produce duplicate rows
    return qs.distinct()


def build_active_pills(params):
    """
    Convert active GET params into a list of pill dicts for the template.
    Consecutive century selections are merged into a single pill.
    """
    pills = []

    # Non-century filter pills
    for param, queryset in [
        ("color", ColorFamily.objects),
        ("pfam", PigmentFamily.objects),
        ("country", Country.objects),
        ("manuscript", Manuscript.objects),
    ]:
        for val in int_values(params, param):
            try:
                obj = queryset.get(id=val)
                pills.append({"label": str(obj), "param": param, "value": val})
            except queryset.model.DoesNotExist:
                pass

    # Century pills with consecutive merge
    centuries = sorted({int(c) for c in int_values(params, "century")})
    if centuries:
        groups = []
        current_group = [centuries[0]]
        for c in centuries[1:]:
            if c == current_group[-1] + 100:
                current_group.append(c)
            else:
                groups.append(current_group)
                current_group = [c]
        groups.append(current_group)

        for group in groups:
            if len(group) == 1:
                label = century_label(group[0])
            else:
                start_label = century_label(group[0])
                end_label = century_label(group[-1])
                label = f"{start_label}\u2013{end_label}"
            pills.append({
                "label": label,
                "param": "century",
                "values": [str(c) for c in group],
                "is_century": True,
            })

    return pills


def pigment_list(request):
    """
    Pigment list view at /pigments/.

    Handles three request scenarios:
    1. Direct GET (no HX-Request header) — returns full page (pigment_list.html)
    2. HTMX filter request (HX-Request: true) — returns fragment (pigment_list_partial.html)
    3. HTMX history restore (HX-Request: true + HX-History-Restore-Request: true) — returns full page
    """
    is_htmx = request.headers.get("HX-Request") == "true"
    is_history_restore = request.headers.get("HX-History-Restore-Request") == "true"

    params = request.GET

    # Active filter values, minus any that aren't integers (ignored by the
    # queryset too, so they shouldn't count as "filtered" either).
    selected = {key: int_values(params, key) for key in FILTER_PARAMS}

    qs = build_filtered_queryset(params)

    context = {
        "pigments": qs,
        "filtered_count": qs.count(),
        "total_count": listed_pigments().count(),
        "is_filtered": any(selected.values()),
        **filter_options(),
        "active_pills": build_active_pills(params),
        # Selected values per filter, so templates can tick the right checkboxes
        # (templates can't call params.getlist(key) themselves).
        "selected": selected,
    }

    if is_htmx and not is_history_restore:
        return render(request, "pigments/pigment_list_partial.html", context)

    return render(request, "pigments/pigment_list.html", context)


def pigment_detail(request, pk):
    pigment = get_object_or_404(Pigment, pk=pk)
    formulas = pigment.formulas.select_related('brand').prefetch_related(
        'parts__paint'
    ).all()
    images = list(pigment.images.select_related('image').all())
    manuscript_links = list(pigment.manuscript_links.select_related(
        'manuscript__country', 'source'
    ).all())

    # Bibliography: sources cited on manuscript links first (in table order),
    # then the pigment's general references, each listed once.
    references = []
    seen = set()
    for source in [l.source for l in manuscript_links if l.source] + list(pigment.sources.all()):
        if source.pk not in seen:
            seen.add(source.pk)
            references.append(source)
    context = {
        'pigment': pigment,
        'formulas': formulas,
        'images': images,
        'featured_image': images[0] if images else None,
        'additional_images': images[1:] if len(images) > 1 else [],
        'manuscript_links': manuscript_links,
        'references': references,
    }
    return render(request, 'pigments/pigment_detail.html', context)
