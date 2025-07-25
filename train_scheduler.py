from apscheduler.schedulers.blocking import BlockingScheduler
import os
import django

# Set environment variable and setup Django BEFORE importing Django app code
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AIMaintenance.settings")
django.setup()

# Now import Django view function
from predictive.views import train_model1

# Initialize the scheduler
scheduler = BlockingScheduler()

# Add the job to run at 14:40 daily
scheduler.add_job(train_model1, trigger='cron', hour=14, minute=40)

print("APScheduler started...")
scheduler.start()
# Note: This script will run indefinitely, executing the train_model1 function at the specified time daily.
# Make sure to run this script in an environment where Django can access the database and other settings