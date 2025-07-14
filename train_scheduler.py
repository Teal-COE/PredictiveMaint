from apscheduler.schedulers.blocking import BlockingScheduler
import os
import django

# Set environment variable and setup Django BEFORE importing Django code
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AIMaintenance.settings")
django.setup()

# Now import Django app code
from predictive.views import train_model1

scheduler = BlockingScheduler()
scheduler.add_job(train_model1, trigger='cron', hour=14, minute=40)


print("APScheduler started...")
scheduler.start()

