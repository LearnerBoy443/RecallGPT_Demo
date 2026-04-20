import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = get_wsgi_application()

# Run migrations automatically
from django.core.management import call_command
try:
    call_command('migrate', interactive=False)
except Exception as e:
    print("Migration error:", e)

app = application
