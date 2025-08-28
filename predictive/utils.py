from predictive.models import SettingsElement, AnomalyDataLog

def get_sidebar_counts(request):
    # Get org_id from the current session
    org_id = request.session.get('ORG_ID')

    # If no org_id is found in session, return default counts
    if not org_id:
        return {'sensor_count': 0, 'anomaly_count': 0}

    # Count number of active sensors linked to this org
    sensor_count = SettingsElement.objects.filter(
        org_id=org_id, active=True
    ).count()

    # Count number of anomalies logged for this org
    anomaly_count = AnomalyDataLog.objects.filter(
        org_id=org_id
    ).count()

    # Return both counts as a dictionary (useful in templates/sidebar)
    return {
        'sensor_count': sensor_count,
        'anomaly_count': anomaly_count,
    }
