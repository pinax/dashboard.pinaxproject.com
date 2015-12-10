from django.db import connection
from django.db.models import Count
from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import ListView

from .models import Release


class ReleaseListView(ListView):
    model = Release
    ordering = ["-date"]
    paginate_by = 25

    def get_context_data(self, *args, **kwargs):
        context = super(ReleaseListView, self).get_context_data(*args, **kwargs)
        return context


def date_list(start):
    year, month, day = map(lambda x: int(x), start.split("-"))
    current_year = timezone.now().year
    current_month = timezone.now().month
    dates = [start]
    while year <= current_year and month <= current_month:
        month += 1
        if month == 13:
            month = 1
            year += 1
        if year <= current_year and month <= current_month:
            dates.append("{}-{}-01".format(year, str(month).zfill(2)))
    return dates


def releases_data(request):
    truncate_date = connection.ops.date_trunc_sql("month", "date")
    qs = Release.objects.extra({"month": truncate_date})
    report = qs.values("month").annotate(Count("pk")).order_by("month")
    first = report[0]
    dates = {
        m: {"pk__count": 0}
        for m in date_list(first["month"])
    }
    for r in report:
        dates[r["month"]]["pk__count"] = r["pk__count"]
    months = dates.keys()
    months.sort()
    report = [
        {"month": k, "pk__count": dates[k]["pk__count"]}
        for k in months
    ]
    data = {
        "labels": [x["month"] for x in report],
        "datasets": [
            {
                "label": "Releases",
                "fillColor": "rgba(151,187,205,0.5)",
                "strokeColor": "rgba(151,187,205,0.8)",
                "highlightFill": "rgba(151,187,205,0.75)",
                "highlightStroke": "rgba(151,187,205,1)",
                "data": [x["pk__count"] for x in report]
            }
        ]
    }
    return JsonResponse(data)
