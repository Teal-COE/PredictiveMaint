from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# Utility function
def org_details():
    org_data = SettingsOrg.objects.all().values('org_id', 'line_code', 'plant_code')
    return [(org['org_id'], f"{org['plant_code']} | {org['line_code']}") for org in org_data]


class SensorDataLog(models.Model):
    id = models.AutoField(primary_key=True)
    element_id = models.CharField(max_length=255)
    max = models.DecimalField(max_digits=8, decimal_places=4)
    min = models.DecimalField(max_digits=8, decimal_places=4)
    avg = models.DecimalField(max_digits=8, decimal_places=4)
    rec_train_data = models.BooleanField(default=False)
    no_of_records = models.IntegerField()
    timestamp = models.DateTimeField()
    org_id = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.element_id} | Max: {self.max} | Min: {self.min} | Avg: {self.avg} | {self.timestamp}"


class SettingsOrg(models.Model):
    company_code = models.CharField(max_length=255)
    plant_code = models.CharField(max_length=255)
    line_code = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    org_id = models.AutoField(primary_key=True)

    def __str__(self):
        return f"{self.timestamp} | {self.plant_code} | {self.line_code} | ID: {self.org_id}"


class SettingsElement(models.Model):
    element_id = models.CharField(max_length=255)
    element_name = models.CharField(max_length=255)
    tag = models.CharField(max_length=255)
    server_ip = models.CharField(max_length=255)
    machine_code = models.CharField(max_length=255)
    element_type = models.CharField(max_length=255)
    model_path = models.CharField(max_length=255, default='model not created')
    upper_anamoly_limit = models.CharField(max_length=255, default='model not created')
    lower_anamoly_limit = models.CharField(max_length=255, default='model not created')
    aggregation_type = models.CharField(max_length=255, default='model not created')
    rec_train_data = models.BooleanField(default=False)
    remarks = models.TextField()
    org_id = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    prediction = models.BooleanField(default=False)
    train_dataset_size = models.IntegerField(default=0)
    possible_prediction_nos = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.element_id} | {self.element_name} | Type: {self.element_type} | Active: {self.active}"


class ErrorLog(models.Model):
    id = models.AutoField(primary_key=True)
    service = models.CharField(max_length=255)
    error_category = models.CharField(max_length=255)
    error_text = models.TextField()
    severity = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Severity must be between 1 and 10"
    )
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.service} | {self.error_category} | Severity: {self.severity} | {self.timestamp}"


class ModelLog(models.Model):
    id = models.AutoField(primary_key=True)
    start_time = models.DateTimeField()
    model_path = models.CharField(max_length=255)
    model_created = models.BooleanField()
    remarks = models.TextField()
    log_time = models.DateTimeField()

    def __str__(self):
        return f"ModelLog #{self.id} | Created: {self.model_created} | Time: {self.log_time}"


class AnomalyDataLog(models.Model):
    id = models.AutoField(primary_key=True)
    element_id = models.CharField(max_length=255)
    element_name = models.CharField(max_length=255)
    current_value = models.DecimalField(max_digits=8, decimal_places=4)
    aggregation_type = models.CharField(max_length=255)
    no_of_records = models.CharField(max_length=255)
    anomaly_ranges = models.CharField(max_length=255)
    machine = models.CharField(max_length=255)
    org_id = models.CharField(max_length=255)
    time_stamp = models.CharField(max_length=255)
    new_anamoly = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.element_name} | Time: {self.time_stamp} | Org: {self.org_id}"

    @property
    def lsl(self):
        try:
            return float(self.anomaly_ranges.split("to")[0].strip())
        except Exception:
            return None

    @property
    def hsl(self):
        try:
            return float(self.anomaly_ranges.split("to")[1].strip())
        except Exception:
            return None


class SettingsEmailRecipients(models.Model):
    recipient_options = [
        ('1', 'To'),
        ('2', 'CC'),
        ('3', 'Bcc'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    org_id = models.CharField(max_length=255)
    recipient_type = models.CharField(max_length=255, choices=recipient_options, default='1')
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    org_name = models.CharField(max_length=255, default='Default Org')

    def __str__(self):
        return f"{self.name} | {self.email} | Type: {self.get_recipient_type_display()}"
