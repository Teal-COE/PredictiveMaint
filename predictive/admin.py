from django.contrib import admin
from predictive.models import *

admin.register(SensorDataLog)(admin.ModelAdmin)
admin.register(SettingsElement)(admin.ModelAdmin)
admin.register(SettingsOrg)(admin.ModelAdmin)
admin.register(ErrorLog)(admin.ModelAdmin)
admin.register(ModelLog)(admin.ModelAdmin)
admin.register(AnomalyDataLog)(admin.ModelAdmin)
admin.register(SettingsEmailRecipients)(admin.ModelAdmin)