
from predictive.models import SettingsElement, AnomalyDataLog

def get_sidebar_counts(request):
    org_id = request.session.get('ORG_ID')

    if not org_id:
        return {'sensor_count': 0, 'anomaly_count': 0}
    return {
        'sensor_count': SettingsElement.objects.filter(org_id=org_id, active=True).count(),
        'anomaly_count': AnomalyDataLog.objects.filter(org_id=org_id).count(),
    }
