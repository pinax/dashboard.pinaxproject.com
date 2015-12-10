from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

import pytz
import requests

from dash.models import Release


RENAMES = [
    ("biblion", "pinax-blog"),
    ("agon", "pinax-points"),
    ("agon-ratings", "pinax-ratings"),
    ("django-stripe-payments", "pinax-stripe")
]


class Command(BaseCommand):
    help = "store release information in database"

    def add_arguments(self, parser):
        parser.add_argument("--auth-token", action="store", dest="token", help="your github auth token")
        parser.add_argument("--org", action="store", dest="org", help="github org")
        parser.add_argument("--package", action="store", dest="pkg", help="PyPI Package")

    def _next_url(self, headers):
        if headers.get("Link"):
            link = headers.get("Link")
            next_link = [l.split("; ") for l in link.split(", ") if "next" in l]
            if next_link:
                return next_link[0][0].replace("<", "").replace(">", "")

    def _fetch_url(self, url, params=None):
        r = self.session.get(url, params=params)
        print "Rate Limits {} / {}: {} with {}".format(
            r.headers.get("X-RateLimit-Limit"),
            r.headers.get("X-RateLimit-Remaining"),
            url,
            params
        )
        data = r.json()
        next_url = self._next_url(r.headers)
        if next_url:
            data.extend(
                self._fetch_url(next_url)
            )
        return data

    def _fetch(self, path, **kwargs):
        kwargs.update(dict(per_page=100))
        return self._fetch_url(
            "https://api.github.com{}".format(path),
            params=kwargs
        )

    def fetch_repos(self, org):
        return self._fetch("/orgs/{}/repos".format(org), type="sources")

    def fetch_commits(self, org, repo, until, since=None):
        commits = []
        url = "/repos/{}/{}/commits".format(org, repo)
        if since:
            commits = self._fetch(url, since=since, until=until)
        else:
            commits = self._fetch(url, until=until)
        return commits

    def changeset_url(self, commits):
        if commits[-1]["parents"]:
            begin_sha = commits[-1]["parents"][0]["sha"]
        else:
            begin_sha = commits[-1]["sha"]
        return commits[0]["html_url"].replace(
            "commit/",
            "compare/{}...".format(begin_sha)
        )

    def create_release(self, name, release_url, version, date, commits):
        release, _ = Release.objects.get_or_create(
            name=name,
            version=version,
            defaults=dict(
                commits=len(commits),
                changeset_url=self.changeset_url(commits),
                pypi_url=release_url,
                date=date,
            )
        )
        return release

    def get_releases(self, name, pypi_name=None):
        if pypi_name is None:
            pypi_name = name
        releases = []
        if name in ["pinax"]:
            releases
        print "Processing {}".format(pypi_name)
        try:
            pypi_data = self.pypi_session.get(
                "http://pypi.python.org/pypi/{}/json".format(pypi_name)
            ).json()
            for release in pypi_data["releases"]:
                if pypi_data["releases"][release]:
                    rdata = pypi_data["releases"][release][0]
                    url = rdata["url"]
                    date = pytz.timezone("UTC").localize(
                        parse_datetime(rdata["upload_time"])
                    )
                    releases.append(
                        (date, release, url, rdata["upload_time"] + "Z")
                    )
        except Exception:
            pass
        releases.sort()
        return releases

    def create_releases(self, org, name, pypi_name=None):
        releases = self.get_releases(name, pypi_name)
        prev = None
        for release in releases:
            commits = self.fetch_commits(org, name, release[3], prev)
            commits = [
                c
                for c in commits
                if not c["commit"]["message"].startswith("Merge pull")
            ]
            if len(commits) == 0:
                continue
            prev = release[3]
            self.create_release(pypi_name or name, release[2], release[1], release[0], commits)

    def handle(self, *args, **options):
        auth_token = options["token"]
        org = options["org"]
        pkg = options["pkg"]
        if auth_token is None and org is not None:
            print "You must supply an auth token and GitHub org"
            return
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "token {}".format(auth_token)
        })
        self.pypi_session = requests.Session()
        if pkg is None:
            public_repos = [r for r in self.fetch_repos(org) if not r["private"]]
            for repo in public_repos:
                self.create_releases(org, repo["name"])
            if org == "pinax":
                for rename in RENAMES:
                    self.create_releases(org, rename[1], rename[0])
        else:
            self.create_releases(org, pkg)
