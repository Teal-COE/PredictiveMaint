from django.contrib import admin
from django.urls import path, include
from predictive import views as pred
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('', pred.login_screen, name='login_screen'),
    path('dashboard/', pred.dashboard, name='dashboard'),
    path('get_plants/', pred.get_plants, name='get_plants'),
    path('get_lines/', pred.get_lines, name='get_lines'),

    path('organization_create', pred.organization_create, name='organization_create'),
    path('organization_list/', pred.organization_list, name='organization_list'),
    path('org_update/<int:id>/', pred.update_org, name='org_update'),
    path('organization_org/<int:id>/', pred.organization_org, name='organization_org'),
    path('summary_list/', pred.summary_list, name='summary_list'),

    path('email_list/', pred.email_list, name='email_list'),
    path('email_create/', pred.email_create, name='email_create'),
    path('email_update/<int:id>/', pred.email_update, name='email_update'),
    path('email_delete/<int:id>/', pred.email_delete, name='email_delete'),

    path('sensor_export/', pred.sensor_export,name='sensor_export'),
    path('sensor_import/', pred.sensor_import,name='sensor_import'),
    path('sensor_list/', pred.sensor_list, name='sensor_list'),
    path('sensor_create', pred.sensors_create, name='sensor_create'),
    path('sensor_update/<int:id>/', pred.update_sensor, name='sensor_update'),
    path('sensor_delete/<int:id>/', pred.delete_sensor, name='sensor_delete'),

    path('anomaly/', pred.anomaly_view, name='anomaly_view'),

    path('training_screen/', pred.training_screen, name='training_screen'),

    path('get_startdate/', pred.get_startdate, name='get_startdate'),

    path('predictive_screen/', pred.predictive_screen, name='predictive_screen'),
    path('run_predictions/', pred.run_predictions, name='ajax_predictive_screen-data'),
    path('run_predictions1/', pred.run_predictions1, name='ajax_predictive'),

   
    path('model_analysis/', pred.model_analysis, name='model_analysis'),
    path('get_models/', pred.get_models, name='get_models'),
    path('model_analysis_chart/', pred.model_evaluation, name='model_evaluation'),
    path('check_server/', pred.is_server_live),
    path('datalog/', pred.datalog),
    path('pred_sensors/', pred.get_pred_sensor_list),
    path('sensordata/', pred.get_sensor_data),
    path('datalog_sensor/', pred.datalog_sensor_list),
    path('error_log/', pred.error_log),
    path('test/', pred.test_function),
    path('train_model/', pred.train_model, name='train_model'),
    path('data/', pred.element_raw_data, name='ajax_sensor_data'),
    path('predict/', pred.run_predictions),
    path('delete_all/<str:sensor_id>', pred.delete_all_records),
    path('anamoly_records/', pred.refresh_anomalies),
    path('alert/', pred.email_anamoly_alert),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('exception_job/',pred.exception_job),
]