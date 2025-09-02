# Import the necessary module from Django REST Framework
from rest_framework import serializers

# Import all models from the current module
from .models import *
# from .models import SensorDataLog, ErrorLog, SettingsElement, AnomalyDataLog


# Serializer for the SensorDataLog model
class SensorDataLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorDataLog
        # Exclude the 'id' field from serialization
        exclude = ['id']


# Serializer for the ErrorLog model
class ErrorLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErrorLog
        # Exclude the 'id' field from serialization
        exclude = ['id']


# Serializer for the SettingsElement model
class SettingsElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = SettingsElement
        # Fix the typo here: '__all_' → '__all__'
        fields = '__all__'  # Include all fields in the model


# Serializer for the AnomalyDataLog model
class AnomalyDataLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnomalyDataLog
        # Exclude the 'id' field from serialization
        exclude = ['id']
