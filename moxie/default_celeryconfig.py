## Broker settings.
BROKER_URL = 'redis://localhost:6379/1'

## Results backend
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'

# List of modules to import when celery starts.
CELERY_IMPORTS = ("moxie.places.tasks", )
