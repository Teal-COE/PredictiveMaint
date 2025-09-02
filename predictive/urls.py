from django.urls import path
from predictive import views as pdm
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('', pdm.login_screen, name='login_screen'),
    path('dashboard/', pdm.dashboard, name='dashboard'),
    path('get_plants/', pdm.get_plants, name='get_plants'),
    path('get_lines/', pdm.get_lines, name='get_lines'),

    path('training_screen/', pdm.training_screen, name='training_screen'),

    path('model_analysis/', pdm.model_analysis, name='model_analysis'),
    path('get_models/', pdm.get_models, name='get_models'),
    path('model_analysis_chart/', pdm.model_evaluation, name='model_evaluation'),

    path('organization_create', pdm.organization_create, name='organization_create'),
    path('organization_list/', pdm.organization_list, name='organization_list'),
    path('org_update/<int:id>/', pdm.update_org, name='org_update'),
    path('organization_org/<int:id>/', pdm.organization_org, name='organization_org'),

    path('summary_list/', pdm.summary_list, name='summary_list'),

    path('email_list/', pdm.email_list, name='email_list'),
    path('email_create/', pdm.email_create, name='email_create'),
    path('email_update/<int:id>/', pdm.email_update, name='email_update'),
    path('email_delete/<int:id>/', pdm.email_delete, name='email_delete'),

    path('sensor_export/', pdm.sensor_export,name='sensor_export'),
    path('sensor_import/', pdm.sensor_import,name='sensor_import'),
    path('sensor_list/', pdm.sensor_list, name='sensor_list'),
    path('sensor_create', pdm.sensors_create, name='sensor_create'),
    path('sensor_update/<int:id>/', pdm.update_sensor, name='sensor_update'),
    path('sensor_delete/<int:id>/', pdm.delete_sensor, name='sensor_delete'),

    path('anomaly/', pdm.anomaly_view, name='anomaly_view'),
    path('get_startdate/', pdm.get_startdate, name='get_startdate'),

    path('predictive_screen/', pdm.predictive_screen, name='predictive_screen'),
    path('run_predictions/', pdm.run_predictions, name='ajax_predictive_screen-data'),
    path('run_predictions1/', pdm.run_predictionsAkash, name='ajax_predictive'),

    path('check_server/', pdm.is_server_live),
    path('datalog/', pdm.datalog),
    path('pred_sensors/', pdm.get_pred_sensor_list),
    path('sensordata/', pdm.get_sensor_data),
    path('datalog_sensor/', pdm.datalog_sensor_list),
    path('error_log/', pdm.error_log),
    path('test/', pdm.test_function),
    path('train_model/', pdm.train_model, name='train_model'),
    path('data/', pdm.element_raw_data, name='ajax_sensor_data'),
    path('predict/', pdm.run_predictions),
    path('delete_all/<str:sensor_id>', pdm.delete_all_records),
    path('anamoly_records/', pdm.refresh_anomalies),
    path('alert/', pdm.email_anamoly_alert),
    path('exception_job/',pdm.exception_job),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh')
]