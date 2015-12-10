from django.db import models
from django.utils import timezone


class Release(models.Model):
    name = models.CharField(max_length=150)
    version = models.CharField(max_length=50)
    commits = models.IntegerField(default=0)
    changeset_url = models.TextField()
    pypi_url = models.TextField()
    date = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("name", "version")]

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super(Release, self).save(*args, **kwargs)
