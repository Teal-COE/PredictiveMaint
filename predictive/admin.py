from django.contrib import admin
from predictive.models import (
    SensorDataLog,
    SettingsElement,
    SettingsOrg,
    ErrorLog,
    ModelLog,
    AnomalyDataLog,
    SettingsEmailRecipients
)

# Register your models here.
admin.site.register(SensorDataLog)
admin.site.register(SettingsElement)
admin.site.register(SettingsOrg)
admin.site.register(ErrorLog)
admin.site.register(ModelLog)
admin.site.register(AnomalyDataLog)
admin.site.register(SettingsEmailRecipients)
