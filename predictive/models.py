from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# Create your models here.
def org_details():
    org_data = list(SettingsOrg.objects.all().values('org_id', 'line_code', 'plant_code'))
    return [(id['org_id'], str(id['plant_code']) + " | " + str(id['line_code'])) for id in org_data]


class SensorDataLog(models.Model):
    id = models.AutoField(primary_key=True)
    element_id = models.CharField(max_length=255, null=False)
    max = models.DecimalField(max_digits=8, decimal_places=4)
    min = models.DecimalField(max_digits=8, decimal_places=4)
    avg = models.DecimalField(max_digits=8, decimal_places=4)
    rec_train_data = models.BooleanField(default=False)
    no_of_records = models.IntegerField()
    timestamp = models.DateTimeField()
    org_id = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.element_id}-{self.max}-{self.min} - {self.avg} - {self.timestamp}"


class SettingsOrg(models.Model):
    company_code = models.CharField(max_length=255, null=False)
    plant_code = models.CharField(max_length=255, null=False)
    line_code = models.CharField(max_length=255, null=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    org_id = models.AutoField(primary_key=True)

    def __str__(self):
        return f"{self.timestamp} - {self.plant_code} - {self.line_code} - {self.org_id}"


class SettingsElement(models.Model):
    element_id = models.CharField(max_length=255, null=False)
    element_name = models.CharField(max_length=255, null=False)
    tag = models.CharField(max_length=255, null=False)
    server_ip = models.CharField(max_length=255, null=False)
    machine_code = models.CharField(max_length=255, null=False)
    element_type = models.CharField(max_length=255, null=False)
    model_path = models.CharField(max_length=255, default='model not created')
    upper_anamoly_limit = models.CharField(max_length=255, default='model not created')
    lower_anamoly_limit = models.CharField(max_length=255, default='model not created')
    aggregation_type = models.CharField(max_length=255, default='model not created')
    rec_train_data = models.BooleanField(default=False)
    remarks = models.TextField()
    org_id = models.CharField(max_length=255, null=False)
    active = models.BooleanField(default=True)
    prediction = models.BooleanField(default=False)
    train_dataset_size = models.IntegerField(default=0)
    possible_prediction_nos = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.element_id}-{self.element_id}-{self.element_name} - {self.element_type} - {self.active}"





class ErrorLog(models.Model):
    id = models.AutoField(primary_key=True)
    service = models.CharField(max_length=255, null=False)
    error_category = models.CharField(max_length=255, null=False)
    error_text = models.TextField()
    severity = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)],
                                   help_text="severity must be between 1 to 10 ( integer ) ")
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.service}-{self.error_category} - {self.severity} - {self.timestamp}"


class ModelLog(models.Model):
    id = models.AutoField(primary_key=True)
    start_time = models.DateTimeField()
    model_path = models.CharField(max_length=255, null=False)
    model_created = models.BooleanField()
    remarks = models.TextField()
    log_time = models.DateTimeField()

    def __str__(self):
        return f"{self.id}-{self.start_time} - {self.model_created} - {self.log_time}"


class AnomalyDataLog(models.Model):
    id = models.AutoField(primary_key=True)
    element_id = models.CharField(max_length=255, null=False)
    element_name = models.CharField(max_length=255, null=False)
    current_value = models.DecimalField(max_digits=8, decimal_places=4)
    aggregation_type = models.CharField(max_length=255, null=False)
    no_of_records = models.CharField(max_length=255, null=False)
    anomaly_ranges = models.CharField(max_length=255, null=False)
    machine = models.CharField(max_length=255, null=False)
    org_id = models.CharField(max_length=255, null=False)
    time_stamp = models.CharField(max_length=255, null=False)
    new_anamoly = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id}-{self.element_name} - {self.time_stamp} - {self.org_id}"

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
    name = models.CharField(max_length=255, null=False)
    email = models.EmailField(max_length=255, null=False)
    org_id = models.CharField(max_length=255, null=False)
    recipient_type = models.CharField(max_length=255, choices=recipient_options, default='To')
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    org_name = models.CharField(max_length=255, null=False, blank=False, default='Default Org')


    def __str__(self):
        return f"{self.id}-{self.email} - {self.recipient_type} - {self.org_id}"
