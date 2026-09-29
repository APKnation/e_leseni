import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from businesses.models import Business, BusinessDocument

print("Total businesses:", Business.objects.count())
print("Total documents:", BusinessDocument.objects.count())
for doc in BusinessDocument.objects.all():
    print(f"- {doc.kind}: {doc.file.name}")
