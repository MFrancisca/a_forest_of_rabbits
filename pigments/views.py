from django.shortcuts import render
from django.db.models import Q

from pigments.models import (
    ColorFamily,
    Country,
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


def get_century_buckets():
    """
    Return a list of century bucket dicts for the filter UI.
    Only includes centuries that have at least one manuscript overlapping that range.
    Example: [{"start": 800, "label": "9th century"}, ...]
    """
    manuscripts = Manuscript.objects.exclude(
        date_start__isnull=True, date_end__isnull=True
    ).values_list("date_start", "date_end")

    occupied = set()
    for start, end in manuscripts:
        if start is None or end is None:
            continue
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


def build_filtered_queryset(params):
    """
    Build a filtered and deduplicated Pigment queryset from GET params.
    Filtering logic: OR within a dimension, AND across dimensions.
    Always returns .distinct() to prevent M2M join duplicates.
    """
    qs = Pigment.objects.select_related("color_family", "pigment_family").all()

    # Color family — OR within dimension via __in
    color_ids = params.getlist("color")
    if color_ids:
        qs = qs.filter(color_family__id__in=color_ids)

    # Pigment family — OR within dimension via __in
    pfam_ids = params.getlist("pfam")
    if pfam_ids:
        qs = qs.filter(pigment_family__id__in=pfam_ids)

    # Country — joins through manuscript_links → manuscript → country
    country_ids = params.getlist("country")
    if country_ids:
        qs = qs.filter(manuscript_links__manuscript__country__id__in=country_ids)

    # Manuscript — joins through manuscript_links → manuscript
    manuscript_ids = params.getlist("manuscript")
    if manuscript_ids:
        qs = qs.filter(manuscript_links__manuscript__id__in=manuscript_ids)

    # Century — range overlap: manuscript overlaps [c_start, c_start+99]
    # A manuscript overlaps if date_start <= c_end AND date_end >= c_start
    centuries = params.getlist("century")
    if centuries:
        century_q = Q()
        for c_start in centuries:
            c_start_int = int(c_start)
            c_end_int = c_start_int + 99
            century_q |= Q(
                manuscript_links__manuscript__date_start__lte=c_end_int,
                manuscript_links__manuscript__date_end__gte=c_start_int,
            )
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
        for val in params.getlist(param):
            try:
                obj = queryset.get(id=int(val))
                pills.append({"label": str(obj), "param": param, "value": val})
            except (ValueError, queryset.model.DoesNotExist):
                pass

    # Century pills with consecutive merge
    raw_centuries = params.getlist("century")
    if raw_centuries:
        try:
            centuries = sorted(int(c) for c in raw_centuries)
        except ValueError:
            centuries = []

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

    # Determine which filter params are active
    color_ids = params.getlist("color")
    pfam_ids = params.getlist("pfam")
    country_ids = params.getlist("country")
    manuscript_ids = params.getlist("manuscript")
    centuries = params.getlist("century")

    qs = build_filtered_queryset(params)

    context = {
        "pigments": qs,
        "filtered_count": qs.count(),
        "total_count": Pigment.objects.count(),
        "is_filtered": bool(color_ids or pfam_ids or country_ids or manuscript_ids or centuries),
        "color_families": ColorFamily.objects.all(),
        "pigment_families": PigmentFamily.objects.all(),
        "countries": Country.objects.all(),
        "manuscripts": Manuscript.objects.all(),
        "century_buckets": get_century_buckets(),
        "active_pills": build_active_pills(params),
        "active_filters": params,
    }

    if is_htmx and not is_history_restore:
        return render(request, "pigments/pigment_list_partial.html", context)

    return render(request, "pigments/pigment_list.html", context)
