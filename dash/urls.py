from django.conf.urls import url
from django.views.generic import TemplateView

from .views import ReleaseListView, releases_data


urlpatterns = [
    url(r"^$", TemplateView.as_view(template_name="homepage.html"), name="home"),
    url(r"^releases/$", ReleaseListView.as_view(), name="releases"),
    url(r"^releases.json$", releases_data, name="releases_data")
]
