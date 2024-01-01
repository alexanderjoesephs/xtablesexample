from django.apps import AppConfig


class TimestablesappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'timestablesapp'




class MyAppConfig(AppConfig):
    name = 'timestablesapp'

    def ready(self):
        # Importing the middleware ensures it gets registered when Django starts.
        from . import middleware