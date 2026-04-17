from django.apps import AppConfig


class SponsorshipsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sponsorships'

    def ready(self):
        import sponsorships.signals  # noqa: F401
