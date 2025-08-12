import os
import csv
import json
import shutil
import smtplib
import regex as re
import traceback
from datetime import datetime, timedelta
from collections import defaultdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from asyncio import sleep

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max, F
from django.db.models.signals import post_save, post_delete
from django.db.models.functions import TruncHour, TruncMinute
from django.dispatch import receiver
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.conf import settings

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import *
from .serializer import *
from .LSTM import ModelBuilder, predictor, anamoly_limits
from .utils import get_sidebar_counts

MODEL_MAIN_PATH = 'all_models/'
ANOMALY_VARIABLES = {}
HOUR_MODE = False


def get_lines(request):
    company_code = request.GET.get('company_code')
    plant_code = request.GET.get('plant_code')
    lines = []
    if company_code and plant_code:
        # Query for distinct line codes for the given company and plant
        lines_qs = SettingsOrg.objects.filter(company_code=company_code, plant_code=plant_code).values(
            'line_code').distinct()
        lines = [l['line_code'] for l in lines_qs]
    return JsonResponse({'lines': lines})


def plant_code(request):
    if request.method == "POST":
        data = json.loads(request.body)
        plant_code = data.get("plant_code")
        line_code = data.get("line_code")
        # Save to user profile or wherever needed
        # request.user.profile.plant_code = plant_code
        # request.user.profile.line_code = line_code
        # request.user.profile.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)


def get_plants(request):
    company_code = request.GET.get('company_code')
    print(company_code, 'company_code')
    plants = []
    if company_code:
        plants_qs = SettingsOrg.objects.filter(company_code=company_code).values('plant_code').distinct()
        plants = [p['plant_code'] for p in plants_qs]
    return JsonResponse({'plants': plants})


def dashboard(request):
    company_list = []
    company_list = SettingsOrg.objects.values('company_code').distinct()
    return render(request, "dashboard.html", {'company_list': company_list})

@login_required(login_url='login_screen')
def get_startdate(request):
    if request.method == "GET" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        element_id = request.GET.get('sensor_name')
        try:
            earliest_date = SensorDataLog.objects.filter(element_id=element_id).earliest('timestamp').timestamp

            return JsonResponse({"success": True, "earliest_date": earliest_date.strftime("%Y-%m-%dT%H:%M")})
        except SensorDataLog.DoesNotExist:
            return JsonResponse({"success": False, "message": "No logged records found for the selected sensor."})


def send_email_to_multiple_recipients(subject, body, email_details):
    """
    Sends an email to multiple recipients with optional CC and BCC.

    Args:
        subject (str): The subject of the email.
        body (str): The body of the email (in HTML format).
        email_details (dict): A dictionary containing:
            - 'to' (list or str): List or comma-separated string of recipient emails.
            - 'cc' (list or str): List or comma-separated string of CC emails (optional).
            - 'bcc' (list or str): List or comma-separated string of BCC emails (optional).
            - 'sender' (str): The sender's email address.
    """
    # SMTP server configuration for sending emails using Outlook
    smtp_server = 'smtp.office365.com'
    smtp_port = 587
    sender_email = email_details.get('sender', 'tealappmailer1@titan.co.in')

    # WARNING: Replace hard-coded password with a secure credential storage method
    sender_password = 'Teal5959@'

    # Extract and parse email recipients from input
    to_email = email_details.get('to', [])
    cc_email = email_details.get('cc', [])
    bcc_email = email_details.get('bcc', [])

    # Convert string inputs to lists for consistency
    if isinstance(to_email, str):
        to_email = to_email.split(",")
    if isinstance(cc_email, str):
        cc_email = cc_email.split(",")
    if isinstance(bcc_email, str):
        bcc_email = bcc_email.split(",")

    try:
        # Create an email object with subject, sender, and recipients
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = ", ".join(to_email)
        msg["Cc"] = ", ".join(cc_email)
        msg["In-Reply-To"] = "tealappmailer1@titan.co.in"

        # Attach the email body as HTML
        html_body = MIMEText(body, "html")
        msg.attach(html_body)

        # Combine all recipients (To, CC, BCC) for the SMTP server
        all_recipients = to_email + cc_email + bcc_email

        # Connect to the SMTP server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection using TLS
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, all_recipients, msg.as_string())
            print("Email sent successfully.")
            return "Email sent successfully."
        return f"Failed to send email"
    except Exception as e:
        return traceback.format_exc()


def get_folders_in_directory(directory_path):
    return [f for f in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, f))]


def login_screen(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            request.session["show_company_modal"] = True  # Set flag
            # return redirect('training_screen')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'login.html', {'show_nav': False})
    else:
        return render(request, 'login.html', {'show_nav': False})


@api_view(['POST'])
def run_predictions(request):
    is_api_call = False
    if request.method == 'POST':
        params = {
            'element_id': request.POST.get('sensor_name'),
            'no_of_prediction': request.POST.get('number_predications'),
            'with_actual': request.POST.get('additionalFeature'),
        }

        if params['element_id'] is None:
            is_api_call = True
            params = {
                'element_id': request.data['sensor_name'],
                'no_of_prediction': request.data['number_predications'],
                'with_actual': request.data['with_actual'],
            }

        print("params", params, is_api_call)

        model_data = SettingsElement.objects.filter(element_id=params['element_id']).values('model_path')

        for file in os.listdir(model_data[0]['model_path']):
            if file.find('.h5') != -1:
                path = model_data[0]['model_path']
                match = re.search(r'-(\d+)\.', file)
                sequence_length = int(match.group(1))
                print
                if match:
                    params['sequence_length'] = sequence_length
                    hour_labeled = orm_sensor_data(params, 'predict')

                    inputs = [float(object['value']) for object in hour_labeled]
                    time_stamps = [str(object['time']) for object in hour_labeled]

                    inputs = inputs[::-1]
                    time_stamps = time_stamps[::-1]

                    if params['with_actual'] == 'false':
                        print("with actual data is True")
                        input_set = inputs[:-int(params['no_of_prediction'])][-sequence_length:]
                        last_time = datetime.strptime(time_stamps[-1],
                                                      "%Y-%m-%dT%H:%M:%S")  # or whatever format your data uses
                        interval = 5  # 5 minutes
                        pred_time_stamps = [
                            (last_time + timedelta(minutes=interval * i)).strftime("%Y-%m-%dT%H:%M:%S")
                            for i in range(1, int(params['no_of_prediction']) + 1)
                        ]
                        print(f"**no_of_prediction: {params['no_of_prediction']} ** sequence_length: {sequence_length}")
                        print("***************  INPUTS  *******************************")
                        print(inputs)
                        print("***************** TIME_STAMP ********************")
                        print(time_stamps)
                        print("***************  INPUT_SET  *******************************")
                        print(input_set)
                        print("****************** PRED TIME_STAMP ******************")
                        print(pred_time_stamps)

                        res, msg = predictor(input_set, path, sequence_length,
                                             no_of_pred=int(params['no_of_prediction']), result=True)
                        predictions = []
                        for id, pred in enumerate(msg):
                            predictions.append({'time': pred_time_stamps[id], 'value': pred})

                        # predictions.insert(0, list(hour_labeled)[int(params['no_of_prediction'])])
                        print(predictions, "----------------------------pred")
                        if res:
                            final_res = {
                                "success": True,
                                "data": {
                                    "actual_data": list(hour_labeled)[::-1],
                                    "predictions": predictions,
                                    "is_actual": params['with_actual']
                                }
                            }
                            return JsonResponse(final_res, safe=False)
                        else:
                            return JsonResponse({'message': msg}, safe=False)


                    else:

                        print("with actual data is False")
                        print(len(hour_labeled))

                        input_set = inputs[-sequence_length:]
                        print(input_set)
                        timestamp_set = time_stamps[-sequence_length:]
                        print(timestamp_set)
                        res, msg = predictor(input_set, path, sequence_length,

                                             no_of_pred=int(params['no_of_prediction']), result=True)
                        print(msg)

                        def is_number(val):

                            try:

                                float(val)

                                return True

                            except ValueError:

                                return False

                        predictions = []

                        if len(msg) < 24:

                            predictions = [{"time": f"hour{id + 1}", "value": float(i)} for id, i in enumerate(msg) if
                                           is_number(i)]
                            predictions.insert(0, list(hour_labeled)[0])



                        else:

                            for day in range(0, len(msg), 24):
                                raw_vals = msg[day:day + 24]
                                day_vals = [float(val) for val in raw_vals if is_number(val)]

                                if day_vals:
                                    day_avg = sum(day_vals) / len(day_vals)
                                    predictions.append({"time": f"day{len(predictions) + 1}",
                                                        "value": round(day_avg, 2)})

                            if hour_labeled:
                                predictions.insert(0, list(hour_labeled)[0])

                        if res:
                            final_res = {
                                "success": True,
                                "data": {
                                    "actual_data": list(hour_labeled)[::-1],
                                    # ✅ limit actual data to 20 recent points
                                    "predictions": predictions
                                },
                                "is_actual": params['with_actual']
                            }
                            return JsonResponse(final_res, safe=False)
                        else:
                            return JsonResponse({'message': msg}, safe=False)


def two_point_ref_scaling():
    pass


@api_view(['POST'])
def run_predictions1(request):
    is_api_call = False
    if request.method == 'POST':
        params = {
            'element_id': request.POST.get('sensor_name'),
            'no_of_prediction': request.POST.get('number_predications'),
            'with_actual': request.POST.get('additionalFeature'),
        }

        if params['element_id'] is None:
            is_api_call = True
            params = {
                'element_id': request.data['sensor_name'],
                'no_of_prediction': request.data['number_predications'],
                'with_actual': request.data['with_actual'],
            }

        print("params", params, is_api_call)

        model_data = SettingsElement.objects.filter(element_id=params['element_id']).values('model_path')
        for file in os.listdir(model_data[0]['model_path']):
            if file.find('.h5') != -1:
                path = model_data[0]['model_path']
                match = re.search(r'-(\d+)\.', file)
                sequence_length = int(match.group(1))
                if match:
                    params['sequence_length'] = sequence_length
                    hour_labeled = orm_sensor_data(params, 'predict')
                    inputs = [float(object['value']) for object in hour_labeled]
                    time_stamps = [str(object['time']) for object in hour_labeled]
                    # !!
                    if params['with_actual'] == 'true':
                        print("with actual data is True")
                        input_set = inputs[:-int(params['no_of_prediction'])][-sequence_length:]
                        pred_time_stamps = time_stamps[-int(params['no_of_prediction']):]
                        print(f"**no_of_prediction: {params['no_of_prediction']} ** sequence_length: {sequence_length}")
                        print("***************  INPUTS  *******************************")
                        print(inputs)
                        print("***************** TIME_STAMP ********************")
                        print(time_stamps)
                        print("***************  INPUT_SET  *******************************")
                        print(input_set)
                        print("****************** PRED TIME_STAMP ******************")
                        print(pred_time_stamps)

                        res, msg = predictor(input_set, path, sequence_length,
                                             no_of_pred=int(params['no_of_prediction']), result=True)
                        predictions = []
                        for id, pred in enumerate(msg):
                            predictions.append({'time': pred_time_stamps[id], 'value': pred})

                        # predictions.insert(0, list(hour_labeled)[int(params['no_of_prediction'])])
                        print(predictions, "----------------------------pred")
                        if res:
                            final_res = {
                                "success": True,
                                "data": {
                                    "actual_data": list(hour_labeled)[::-1],
                                    "predictions": predictions,
                                    "is_actual": params['with_actual']
                                }
                            }
                            return JsonResponse(final_res, safe=False)
                        else:
                            return JsonResponse({'message': msg}, safe=False)

                    else:  # only predicition
                        print("with actual data is False")
                        print(len(hour_labeled))
                        input_set = inputs[-sequence_length:]
                        print(input_set)
                        timestamp_set = time_stamps[-sequence_length:]

                        res, msg = predictor(input_set, path, sequence_length,
                                             no_of_pred=int(params['no_of_prediction']), result=True)

                        predictions = [{'time': 'hour' + str(id + 1), 'value': i} for id, i in enumerate(msg)]

                        predictions.insert(0, list(hour_labeled)[0])

                        if res:
                            final_res = {
                                "success": True,
                                "data": {
                                    "actual_data": list(hour_labeled)[::-1]
                                    ,
                                    "predictions": predictions},
                                "is_actual": params['with_actual']
                            }
                            return JsonResponse(final_res, safe=False)
                        else:
                            return JsonResponse({'message': msg}, safe=False)

                else:
                    return JsonResponse({'message': "Couldn't find the seq len in  model name"}, safe=False)

            return JsonResponse({"message": 'Model not found in the given path'}, safe=False)


def ajax_predictive_screen1(request):
    """
    Handles POST requests to filter and return data based on the provided
    sensor name and date range (start_datetime and end_datetime).
    Returns a JSON response with filtered data for chart rendering.
    """
    if request.method == 'POST':
        sensor_name = request.POST.get('sensor_name')
        start_datetime = request.POST.get('start_datetime')
        end_datetime = request.POST.get('end_datetime')
        number_predications = request.POST.get('number_predications')
        additional_feature = request.POST.get('additionalFeature') == 'true'

        print(sensor_name, start_datetime, end_datetime, number_predications, additional_feature, 'number_predications')

        path = f'predictive.json'
        try:
            data = json.loads(open(path).read())

            return JsonResponse({
                "success": True,
                "data": data['data'],

            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request"})


@login_required
@never_cache
def predictive_screen(request):
    """
    Retrieves all sensor data from SettingsElement and renders it in the
    'predictive_maintenance.html' template.
    """
    # sensors = SettingsElement.objects.all().order_by('-element_id')
    sensors = SettingsElement.objects.filter(prediction=True, org_id = request.session.get('ORG_ID')).values('element_id', 'element_name',
                                                                     'possible_prediction_nos')
    sidebar_counts = get_sidebar_counts(request)

    return render(request, 'predictive_screen.html', {'sensors': sensors, 'show_nav': True,**sidebar_counts})


def model_evaluation(request):
    if request.method == 'POST':
        element_name = request.POST.get('element_name')
        graph_type = request.POST.get('loss_function')
        model = request.POST.get('model_path')

        path = f'{MODEL_MAIN_PATH}{element_name}/{model}/{element_name}_metrics.json'
        try:
            data = json.loads(open(path).read())
            graph_data = data[graph_type][20:]
            return JsonResponse({
                'labels': [i for i in range(1, 1 + len(graph_data))],
                'data': graph_data,
                'title': f'{graph_type} Graph'
            })
        except:
            return JsonResponse({
                'labels': [0],
                'data': [0],
                'title': f'No data to Load {graph_type} Graph'
            })


@login_required
@never_cache
def training_screen(request):
    # Get query parameters or existing session values
    company = request.GET.get('company') or request.session.get('selected_company')
    plant = request.GET.get('plant') or request.session.get('selected_plant')
    line = request.GET.get('line') or request.session.get('selected_line')

    # Store them in session (if present)
    if company: request.session['selected_company'] = company
    if plant:   request.session['selected_plant'] = plant
    if line:    request.session['selected_line'] = line

    # Look up org object and update session ORG_ID
    org_obj = SettingsOrg.objects.filter(company_code=company, plant_code=plant, line_code=line).first()

    request.session['ORG_ID'] = org_obj.org_id if org_obj else None

    # Get sensors or empty result
    sensor_list = SettingsElement.objects.filter(org_id=org_obj.org_id) if org_obj else SettingsElement.objects.none()

    sidebar_counts = get_sidebar_counts(request)
    show_popup = request.session.pop('show_training_popup', False)  # Show only once

    return render(
        request,
        'training_screen.html',
        {
            'sensors': sensor_list,
            'show_nav': True,
            'show_popup': show_popup,
            **sidebar_counts
        }
    )


# def show_sensor(request):
#   latest_question_list = SettingsElement.objects.all()
#   paginator = Paginator(latest_question_list, 3)  # Show 10 sensors per page
#   page_number = request.GET.get('page')
#   page_obj = paginator.get_page(page_number)
#
#   return render(request,'show.html',{'page_obj': page_obj, 'show_nav':True})

def sensor_list(request):
    latest_question_list = SettingsElement.objects.filter(prediction=True, org_id=request.session.get('ORG_ID'))
    paginator = Paginator(latest_question_list, 5)  # Show 3 sensors per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    sidebar_counts = get_sidebar_counts(request)
    return render(request, 'sensordeatils/sensor_list.html', {'page_obj': page_obj, 'show_nav': True, **sidebar_counts})


####################sensor Detail #########################

def sensors_create(request):
    if request.method == 'POST':
        data = request.POST

        # Extracting fields with default fallback
        element_id = data.get('element_id', '').strip()
        element_name = data.get('element_name', '').strip()
        tag = data.get('tag', '').strip()
        server_ip = data.get('server_ip', '').strip()
        machine_code = data.get('machine_code', '').strip()
        element_type = data.get('element_type', '').strip()
        model_path = data.get('model_path', '').strip()
        upper_anamoly_limit = data.get('upper_anamoly_limit', '').strip()
        lower_anamoly_limit = data.get('lower_anamoly_limit', '').strip()
        remarks = data.get('remarks', '').strip()
        org_id = data.get('org_id', '').strip()
        active = data.get('active') == 'on'
        prediction = data.get('prediction') == 'on'

        # Optional: Basic validation (could be expanded)

        # Create the sensor object
        SettingsElement.objects.create(
            element_id=element_id,
            element_name=element_name,
            tag=tag,
            server_ip=server_ip,
            machine_code=machine_code,
            element_type=element_type,
            model_path=model_path,
            upper_anamoly_limit=upper_anamoly_limit,
            lower_anamoly_limit=lower_anamoly_limit,
            remarks=remarks,
            org_id=org_id,
            active=active,
            prediction=prediction,
        )
        return redirect('sensor_list')

    # GET request
    return render(request, 'sensordeatils/sensor_create.html', {
        'show_nav': True
    })


def update_sensor(request, id):
    queryset = SettingsElement.objects.get(id=id)

    if request.method == 'POST':
        data = request.POST

        element_id = data.get('element_id')
        element_name = data.get('element_name')
        tag = data.get('tag')
        server_ip = data.get('server_ip')
        machine_code = data.get('machine_code')
        element_type = data.get('element_type')

        upper_anamoly_limit = data.get('upper_anamoly_limit')
        lower_anamoly_limit = data.get('lower_anamoly_limit')

        remarks = data.get('remarks')
        org_id = data.get('org_id')
        active = True if data.get('active') == 'on' else False
        prediction = True if data.get('prediction') == 'on' else False

        queryset.element_id = element_id
        queryset.element_name = element_name
        queryset.tag = tag
        queryset.server_ip = server_ip
        queryset.machine_code = machine_code
        queryset.element_type = element_type

        queryset.upper_anamoly_limit = upper_anamoly_limit
        queryset.lower_anamoly_limit = lower_anamoly_limit

        queryset.remarks = remarks
        queryset.org_id = org_id
        queryset.active = active
        queryset.prediction = prediction

        queryset.save()
        return redirect('sensor_list')

    return render(request, 'sensordeatils/sensor_update.html', {'sensor_view': queryset, 'show_nav': True})


def delete_sensor(request, id):
    queryset = SettingsElement.objects.get(id=id)
    queryset.delete()
    return redirect('sensor_list')


def sensor_export(request):
    timestamp = now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"settings_elements_{timestamp}.csv"

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    exclude_fields = ['model_path']

    writer = csv.writer(response)

    # Write header row based on model fields
    writer.writerow([field.name for field in SettingsElement._meta.fields if field.name not in exclude_fields])

    # Write data rows
    for obj in SettingsElement.objects.all():
        writer.writerow(
            [getattr(obj, field.name) for field in SettingsElement._meta.fields if field.name not in exclude_fields])

    return response


def sensor_import(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Please upload a valid CSV file.")
            return redirect('sensor_import')  # Use your URL name

        try:
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            with transaction.atomic():
                for i, row in enumerate(reader, start=1):
                    if SettingsElement.objects.filter(element_id=row['element_id']).exists():
                        messages.error(request, f"Duplicate element_id found at row {i}: '{row['element_id']}'.")
                        return redirect('sensor_import')

                    SettingsElement.objects.create(
                        element_id=row['element_id'],
                        element_name=row['element_name'],
                        tag=row['tag'],
                        server_ip=row['server_ip'],
                        machine_code=row['machine_code'],
                        element_type=row['element_type'],
                        upper_anamoly_limit=row['upper_anamoly_limit'],
                        lower_anamoly_limit=row['lower_anamoly_limit'],
                        remarks=row['remarks'],
                        org_id=row['org_id'],
                        active=row['active'],
                        prediction=row['prediction'],
                    )

            messages.success(request, "CSV data imported successfully.")
            return redirect('sensor_import')

        except KeyError as e:
            messages.error(request, f"Missing field: {e}")
            return redirect('sensor_import')

        except ValidationError as e:
            messages.error(request, f"Invalid data: {e}")
            return redirect('sensor_import')

        except Exception as e:
            messages.error(request, f"Error processing CSV file: {e}")
            return redirect('sensor_import')

    return render(request, 'sensordeatils/import_csv.html')

from collections import defaultdict

################### end  sensor   #########################
def anomaly_view(request):
    # Fetch and order data by machine
    data = AnomalyDataLog.objects.filter(
        org_id=request.session.get('ORG_ID')
    ).order_by('machine')

    # Group data by machine using defaultdict
    grouped_by_machine = defaultdict(list)
    for row in data:
        grouped_by_machine[row.machine].append(row)

    # Get sidebar counts (assumes it's a dict)
    sidebar_counts = get_sidebar_counts(request)

    # Pass grouped data and other context to template
    return render(request, 'anomaly.html', {
        'grouped_data': grouped_by_machine.items(),  # converts to list of tuples
        'show_nav': True,
        **sidebar_counts
    })



def organization_list(request):
    latest_question_list = SettingsOrg.objects.all()
    paginator = Paginator(latest_question_list, 5)  # Show 10 sensors per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    sidebar_counts = get_sidebar_counts(request)

    return render(request, 'organizationsetting/organization_list.html',
                  {'page_obj': page_obj, 'show_nav': True, **sidebar_counts})


def organization_create(request):
    if request.method == 'POST':
        data = request.POST
        company_code = data.get('company_code')
        plant_code = data.get('plant_code')
        line_code = data.get('line_code')
        timestamp = data.get('timestamp')
        updated_at = data.get('updated_at')

        SettingsOrg.objects.create(
            company_code=company_code,
            plant_code=plant_code,
            line_code=line_code,
            timestamp=timestamp,
            updated_at=updated_at,

        )
        return redirect('organization_list')

    queryset = SettingsOrg.objects.all()

    return render(request, 'organizationsetting/organization_create.html', {'settings_org': queryset, 'show_nav': True})


def update_org(request, id):
    queryset = SettingsOrg.objects.get(org_id=id)
    if request.method == 'POST':
        data = request.POST
        company_code = data.get('company_code')
        plant_code = data.get('plant_code')
        line_code = data.get('line_code')

        updated_at = data.get('updated_at')

        queryset.company_code = company_code
        queryset.plant_code = plant_code
        queryset.line_code = line_code

        queryset.updated_at = updated_at

        queryset.save()
        return redirect('organization_list')

    return render(request, 'organizationsetting/organization_update.html', {'settings_org': queryset, 'show_nav': True})


def organization_org(request, id):
    anomaly = SettingsOrg.objects.get(org_id=id)
    anomaly.delete()
    return redirect('organization_list')


def email_list(request):
    latest_question_list = SettingsEmailRecipients.objects.all()
    paginator = Paginator(latest_question_list, 5)  # Show 10 sensors per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    sidebar_counts = get_sidebar_counts(request)

    return render(request, 'email/email_list.html', {'page_obj': page_obj, 'show_nav': True, **sidebar_counts})


def email_create(request):
    if request.method == 'POST':
        data = request.POST

        name = data.get('name')
        email = data.get('email')
        org_id = data.get('org_id')
        status = True if data.get('status') == 'True' else False
        recipient_type = data.get('recipient_type')

        SettingsEmailRecipients.objects.create(

            name=name,
            email=email,
            org_id=org_id,
            status=status,
            recipient_type=recipient_type,

        )
        return redirect('email_list')

    queryset = SettingsEmailRecipients.objects.all()

    return render(request, 'email/email_create.html', {'settings_org': queryset, 'show_nav': True})


def email_update(request, id):
    queryset = SettingsEmailRecipients.objects.get(id=id)
    if request.method == 'POST':
        data = request.POST

        name = data.get('name')
        email = data.get('email')
        org_id = data.get('org_id')
        status = True if data.get('status') == 'True' else False
        recipient_type = data.get('recipient_type')

        queryset.name = name
        queryset.email = email
        queryset.org_id = org_id
        queryset.status = status
        queryset.recipient_type = recipient_type

        queryset.save()
        return redirect('email_list')

    return render(request, 'email/email_update.html', {'settings_org': queryset, 'show_nav': True})


def email_delete(request, id):
    email = SettingsEmailRecipients.objects.get(id=id)
    email.delete()
    return redirect('email_list')

def summary_list(request):
    latest_question_list = SettingsElement.objects.all()
    paginator = Paginator(latest_question_list, 10)  # Show 10 sensors per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    sidebar_counts = get_sidebar_counts(request)
    return render(request, 'summary.html', {'page_obj': page_obj, 'show_nav': True, **sidebar_counts})


def get_models(request):
    try:
        element_id = request.GET.get('element_id')

        # Check if element_id is provided in the request
        if not element_id:
            return JsonResponse({'error': 'element_id is required'}, status=400)

        base_directory = os.getcwd()  # Gets the current working directory

        directory_path = os.path.join(base_directory, 'all_models', element_id)

        # Attempt to get the folders from the directory
        models_data = get_folders_in_directory(directory_path)

        # Return the models data as a JSON response
        return JsonResponse({'models': models_data[::-1]})

    except FileNotFoundError:
        return JsonResponse({'error': f"Directory '{directory_path}' not found."}, status=404)

    except PermissionError:
        return JsonResponse({'error': f"Permission denied to access '{directory_path}'."}, status=403)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def model_analysis(request):
    sensors = SettingsElement.objects.filter(prediction=True, org_id=request.session.get('ORG_ID')).order_by(
        '-element_id')
    sidebar_counts = get_sidebar_counts(request)
    return render(request, 'model_analysis.html', {'sensors': sensors, 'show_nav': True, **sidebar_counts})


#######################################################################################################################
#################################################### end ##############################################################

async def my_async_view(request):
    await sleep(5)  # Simulate a time-consuming operation
    return JsonResponse({"message": "This is an async response!"})

@api_view(['GET'])
def is_server_live(requests):
    return JsonResponse({"status": "True"}, safe=False)


@api_view(['POST'])
# @permission_classes([permissions.IsAuthenticated])
def datalog(request):
    if request.method == 'POST':
        datalog_serializer = SensorDataLogSerializer(data=request.data)
        if datalog_serializer.is_valid():
            datalog_serializer.save()
            return Response({"message": "data saved successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response(datalog_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
# @permission_classes([permissions.IsAuthenticated])
def get_pred_sensor_list(request):
    sensor_list = SettingsElement.objects.filter(prediction=True).values('element_id', 'model_path',

                                                                         'org_id', 'upper_anamoly_limit',
                                                                         'lower_anamoly_limit')

    res = defaultdict(list)
    for element in list(sensor_list):
        res[element['org_id']].append(element)

    return JsonResponse(res, safe=False)


@api_view(['POST'])
def get_sensor_data(request):
    try:
        MANDATORY_FIELD = ['element_id', 'count', 'end_date']
        sensor_params = request.data

        if set(MANDATORY_FIELD).issubset(set(sensor_params)):
            if sensor_params['end_date'] == '': sensor_params['end_date'] = datetime.now().date()
            start_date = sensor_params['end_date'] - timedelta(days=int(sensor_params['count']))

            sensor_data = SensorDataLog.objects.filter(element_id=sensor_params['element_id'],
                                                       timestamp__range=['2024-12-28 00:00:00.00',
                                                                         '2024-12-28 23:00:00.00'])  # [sensor_params['end_date'] , start_date])
            return JsonResponse(list(sensor_data.values()), safe=False)
        else:
            return JsonResponse({'message': f'some parameters in {MANDATORY_FIELD} are missing'}, safe=False)
    except Exception as e:
        return JsonResponse({'error': f'{e}'}, safe=False)


@api_view(['POST'])
def train_model(requests):
    if requests.method == 'POST':
        train_params = {
            'element_id': requests.POST.get('sensor_name'),
            'start_time': requests.POST.get('start_datetime'),
            'end_time': requests.POST.get('end_datetime'),
            'epochs': int(requests.POST.get('No_of_Epochs')),
            'sequence_length': int(requests.POST.get('No_of_steps')),
            'anomaly_percentage': requests.POST.get('anomaly_percentage')
        }

        min_data_to_train = 49

        q1 = orm_sensor_data(train_params, 'train')
        train_data = [float(object['value']) for object in q1]
        print(train_data)

        if len(train_data) >= min_data_to_train:
            modeling_start_time = datetime.now()
            model_path = f"{MODEL_MAIN_PATH}{train_params['element_id']}"
            try:
                anamoly_results = anamoly_limits(train_data, train_params['anomaly_percentage'])
                print(anamoly_results)
                if not anamoly_results['status']: return JsonResponse(
                    {"success": "False", "message": anamoly_results['error']}, safe=False)
                # model builder
                model = ModelBuilder(train_params['element_id'], model_path, train_params['epochs'],
                                     train_params['sequence_length'])
                res, msg = model.build_model(train_data)
                print(res, msg)

                if res:
                    ModelLog(start_time=str(modeling_start_time), model_path=msg, model_created='True',
                             remarks='Successfully created', log_time=str(datetime.now())).save()
                    print(anamoly_results)
                    SettingsElement.objects.filter(element_id=train_params['element_id']).update(model_path=msg,
                                                                                                 upper_anamoly_limit=
                                                                                                 round(anamoly_results[
                                                                                                           'upper_limit'],
                                                                                                       2),
                                                                                                 lower_anamoly_limit=
                                                                                                 round(anamoly_results[
                                                                                                           'lower_limit'],
                                                                                                       2),
                                                                                                 aggregation_type='max',
                                                                                                 prediction=True,
                                                                                                 train_dataset_size=len(
                                                                                                     train_data),
                                                                                                 possible_prediction_nos=round(
                                                                                                     len(train_data) * 0.01))
                    return JsonResponse({"success": "True", "message": f"Model Created at {msg}"}, safe=False)
                else:
                    ModelLog(start_time=str(modeling_start_time), model_path=msg, model_created='False',
                             remarks=msg, log_time=str(datetime.now())).save()
                    return JsonResponse({"success": "False", "message": f"{msg}"}, safe=False)
            except Exception as e:
                ModelLog(start_time=str(modeling_start_time), model_path=model_path, model_created='False',
                         remarks=e, log_time=str(datetime.now())).save()
                return JsonResponse({"success": "False", "message": e}, safe=False)
        else:
            return JsonResponse({"message": f"Need min of {min_data_to_train} datas got {len(train_data)}"},
                                safe=False)


def train_model1():
    queryset = SettingsElement.objects.all()
    for i in queryset:
        element_id = i.element_id
        log_qs = SensorDataLog.objects.filter(element_id=element_id).order_by('timestamp')
        if not log_qs.exists():
            return JsonResponse({"success": "False", "message": "No logs available for this sensor"}, safe=False)

        start_time = log_qs.first().timestamp
        end_time = log_qs.last().timestamp

        train_params = {
            'element_id': element_id,
            'start_time': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_time': end_time.strftime('%Y-%m-%dT%H:%M'),
            'epochs': 150,
            'sequence_length': 10,
            'anomaly_percentage': 3
        }

        min_data_to_train = 49
        modeling_start_time = datetime.now()
        model_path = f"{MODEL_MAIN_PATH}{train_params['element_id']}"

        # Fetch training data
        q1 = orm_sensor_data(train_params, 'train')
        train_data = [float(obj['value']) for obj in q1]
        print(train_data)

        if len(train_data) < min_data_to_train:
            print(f"[{element_id}] ❌ Not enough data to train")
            continue

        try:
            # Calculate anomaly limits
            anamoly_results = anamoly_limits(train_data, train_params['anomaly_percentage'])
            if not anamoly_results['status']:
                print(f"[{element_id}] ❌ Anomaly limit error: {anamoly_results['error']}")
                continue

            # Build the model
            model = ModelBuilder(train_params['element_id'], model_path,
                                 train_params['epochs'], train_params['sequence_length'])
            res, msg = model.build_model(train_data)

            if res:
                ModelLog(
                    start_time=str(modeling_start_time),
                    model_path=msg,
                    model_created='True',
                    remarks='Successfully created',
                    log_time=str(datetime.now())
                ).save()

                SettingsElement.objects.filter(element_id=train_params['element_id']).update(
                    model_path=msg,
                    upper_anamoly_limit=anamoly_results['upper_limit'],
                    lower_anamoly_limit=anamoly_results['lower_limit'],
                    aggregation_type='max',
                    prediction=True,
                    train_dataset_size=len(train_data),
                    possible_prediction_nos=round(len(train_data) * 0.01)
                )

                print(f"[{element_id}] ✅ Model created successfully at {msg}")
            else:
                print(f"[{element_id}] ❌ Model creation failed: {msg}")

        except Exception as e:
            ModelLog(
                start_time=str(modeling_start_time),
                model_path=model_path,
                model_created='False',
                remarks=str(e),
                log_time=str(datetime.now())
            ).save()
            print(f"[{element_id}] ❌ Exception occurred: {str(e)}")


def anomaly_check(sender, instance, created, **kwargs):
    print(instance.element_id, instance.max)
    limits = SettingsElement.objects.filter(element_id=instance.element_id).values('element_id', 'element_name',
                                                                                   'upper_anamoly_limit',
                                                                                   'lower_anamoly_limit', 'prediction')
    try:
        if not limits[0]['upper_anamoly_limit'] == 'model not created':
            if not float(limits[0]['lower_anamoly_limit']) <= float(instance.max) <= float(
                    limits[0]['upper_anamoly_limit']):
                print(
                    f"Alert - Anomaly ---- HL {limits[0]['upper_anamoly_limit']} , LL {limits[0]['lower_anamoly_limit']} , Value {instance.max}")
                data = {
                    'time_stamp': '',
                    'sensor_name': limits[0]['element_name'],
                    'ranges': f"{limits[0]['upper_anamoly_limit']} - {limits[0]['lower_anamoly_limit']}",
                    'actual': instance.max
                }

                print(limits[0]['prediction'], "check thus")
                # print(alert_anamoly(['faj@titan.co.in', 'akashadi@titan.co.in', 'bsh.wed@delphitvs.com'], data))
    except Exception as e:
        pass


@receiver(post_save, sender=SettingsElement)
def create_model_folder(sender, instance, created, **kwargs):
    if created:
        os.makedirs(MODEL_MAIN_PATH + str(instance.element_id), exist_ok=True)


@receiver(post_delete, sender=SettingsElement)
def delete_model_folder(sender, instance, **kwargs):
    try:
        shutil.rmtree(MODEL_MAIN_PATH + str(instance.element_id))
    except:
        print(f"Error on deleteing model path {MODEL_MAIN_PATH + str(instance.element_id)}")


@api_view(['POST'])
def datalog_sensor_list(request):
    res = {}
    sensor_list = SettingsElement.objects.filter(active=True)
    sensor = list(sensor_list.values('element_id', 'tag', 'org_id', 'server_ip', 'rec_train_data'))

    for i in sensor:
        try:
            res[i['server_ip']]
        except:
            res[i['server_ip']] = {}
        res[i['server_ip']][i['element_id']] = [i['tag'], i['org_id'], i['rec_train_data']]

    return JsonResponse(res, safe=False)


@api_view(['POST'])
# @permission_classes([permissions.IsAuthenticated])
def error_log(request):
    if request.method == 'POST':
        error_log_serializer = ErrorLogSerializer(data=request.data)
        if error_log_serializer.is_valid():
            error_log_serializer.save()
            return Response({"message": "error logged successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response(error_log_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def alert_anamoly(recipient_list, table_data):
    try:
        subject = "Alert-Anamoly"
        message = "This is a test email from Django."
        from_email = "tealappmailer1@titan.co.in"
        html_message = f'''
        <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>Alert Email</title>
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
      <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #dddddd;">
        <div style="background-color:  #FFFF00; color: black; padding: 20px; text-align: center;">
          <h1 style="margin: 0;">Alert | Anamoly in Injector Line!</h1>
        </div>
        <div style="padding: 20px;">
          <p>Following are the list of anomalies found {datetime.now()}</p>
          <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
            <thead>
              <tr>
                <th style="border: 1px solid #dddddd; padding: 8px; background-color: #f4f4f4;">Sno</th>
                <th style="border: 1px solid #dddddd; padding: 8px; background-color: #f4f4f4;">Sensor</th>
                <th style="border: 1px solid #dddddd; padding: 8px; background-color: #f4f4f4;">Limits -°C</th>
		        <th style="border: 1px solid #dddddd; padding: 8px; background-color: #f4f4f4;">Actual Value</th>
              </tr>
            </thead>
            <tbody>
               <tr>
                    <td style="border: 1px solid #dddddd; padding: 4px;">1</td>
                    <td style="border: 1px solid #dddddd; padding: 8px;">{table_data['sensor_name']}</td>
                    <td style="border: 1px solid #dddddd; padding: 8px;">{table_data['ranges']}</td>
                    <td style="border: 1px solid #dddddd; padding: 8px;">{table_data['actual']}</td>
                  </tr>
            </tbody>
          </table>
          <p style="margin-top: 20px;">This is test version of email</p>
        </div>
        <div style="background-color: #f4f4f4; color: #777; text-align: center; padding: 10px;">
          <p style="margin: 0;">© 2025 TEAL. All rights reserved.</p>
        </div>
      </div>
    </body>
    </html>
        '''

        send_mail(subject, message, from_email, recipient_list, html_message=html_message)

        return JsonResponse({"status": 'sent email'}, safe=False)
    except Exception as E:
        return JsonResponse({"status": E}, safe=False)


@api_view(['POST'])
def element_raw_data(request):
    if request.method == 'POST':
        data = {
            'element_id': request.POST.get('sensor_name'),
            'start_time': request.POST.get('start_datetime'),
            'end_time': request.POST.get('end_datetime')
        }
        element_data = orm_sensor_data(data, 'train')
        res = {
            "success": True,
            "data": {"chartData": list(element_data)}
        }
        print("----------------------------------- raw data -------------------------------------")
        print([i['value'] for i in list(element_data)])
        return JsonResponse(res, safe=False)


def delete_all_records(request, sensor_id):
    try:
        count = SensorDataLog.objects.filter(element_id=sensor_id)
        print(len(count))

        SensorDataLog.objects.filter(element_id=sensor_id, max__gt=45).delete()
        return JsonResponse({"status": f"deleted , {len(count)}"}, safe=False)
    except Exception as e:
        return JsonResponse({"status": e}, safe=False)


def test_function(requests):
    pass


def orm_sensor_data(data, usecase):
    if HOUR_MODE:
        if usecase == 'train':
            return (SensorDataLog.objects.filter(timestamp__range=[data['start_time'], data['end_time']],
                                                 element_id=data['element_id'])
                    .annotate(time=TruncHour('timestamp'))
                    .values('time')
                    .annotate(value=Max('max')).
                    values('time', 'value'))

        elif usecase == 'predict':
            no_of_points = data['sequence_length'] + int(data['no_of_prediction'])
            return (SensorDataLog.objects.filter(element_id=data['element_id'])
                    .annotate(time=TruncHour('timestamp'))
                    .values('time').annotate(value=Max('max'))
                    .values('time', 'value')
                    .order_by('-timestamp')[:no_of_points])

    else:
        print("Minute Mode")
        if usecase == 'train':
            return (SensorDataLog.objects.filter(timestamp__range=[data['start_time'], data['end_time']],
                                                 element_id=data['element_id'], max__gt=0.01)
                    .annotate(time=F('timestamp'))
                    .annotate(value=F('max'))
                    .values('time', 'value')
                    .order_by('time'))

        elif usecase == 'predict':
            no_of_points = data['sequence_length'] + int(data['no_of_prediction'])
            qs = (
                SensorDataLog.objects
                .filter(
                    element_id=data['element_id'],
                    max__gt=0.01
                )
                .annotate(time=TruncMinute('timestamp'))
                .annotate(value=F('max'))
                .values('time', 'value')
                .order_by('-time')  # most recent first
                [:no_of_points]
            )
            # qs is a Django ValuesQuerySet, so to reverse it in Python:
            return list(qs)


@receiver(post_save, sender=SensorDataLog)
def anomaly_logger(sender, instance, created, **kwargs):
    setting_data = SettingsElement.objects.filter(
        element_id=instance.element_id
    ).values(
        'element_name', 'upper_anamoly_limit', 'lower_anamoly_limit',
        'prediction', 'aggregation_type', 'machine_code'
    ).first()

    if not setting_data or setting_data["lower_anamoly_limit"] == 'model not created':
        return

    if not setting_data["prediction"]:
        return

    try:
        lower = float(setting_data['lower_anamoly_limit'])
        upper = float(setting_data['upper_anamoly_limit'])
        machine_code = setting_data['machine_code'] 
        current_value = float(instance.max)
    except (ValueError, TypeError):
        return  # Exit if conversion fails

    if not (lower <= current_value <= upper):
        # Anomaly detected
        agg_type = 'min' if current_value < lower else 'max'

        anamoly_record = AnomalyDataLog.objects.filter(
            element_id=instance.element_id,
            new_anamoly=True
        )

        if anamoly_record.exists():
            anamoly_record.update(
                current_value=current_value,
                aggregation_type=agg_type,
                time_stamp=instance.timestamp,
                no_of_records=instance.no_of_records,
            )
        else:
            AnomalyDataLog.objects.create(
                element_name=setting_data["element_name"],
                element_id=instance.element_id,
                current_value=current_value,
                aggregation_type=agg_type,
                time_stamp=instance.timestamp,
                no_of_records=instance.no_of_records,
                org_id=instance.org_id,
                anomaly_ranges=f"{lower} to {upper}",
                machine= machine_code,
            )


@api_view(['POST'])
def refresh_anomalies(requests):
    try:
        res = {
            'new_set': [],
            'old_set': []
        }
        data = AnomalyDataLog.objects.all()
        for record in list(data.values()):
            print('----', record)
            if record['new_anamoly']:
                res['new_set'].append(record)
            else:
                res['old_set'].append(record)
        if not requests.data['trail_request']:
            try:
                print("its not trail request")
                a = AnomalyDataLog.objects.filter(new_anamoly=False).delete()
                b = AnomalyDataLog.objects.all().update(new_anamoly=False)
                after_data = AnomalyDataLog.objects.all()
                return JsonResponse(res, safe=False)

            except Exception as e:
                return JsonResponse({"error": e}, safe=False)
        else:
            res['trail_request'] = 'trail request'
            return JsonResponse(['enable trail request to True'], safe=False)
    except Exception as e:
        return JsonResponse([traceback.format_exc()], safe=False)


def dynamic_string(str_, **kwargs):
    return str_.format(**kwargs)


@api_view(['POST'])
def exception_job(requests):
    try:
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        new_errors = ErrorLog.objects.filter(timestamp__gte=five_minutes_ago)

        if not new_errors.exists():
            return JsonResponse("No new errors in the last 5 minutes.", safe=False)

        # Format email body
        email_body = email_body = f"""
        <h2>🛑 Recent Error Logs (last 5 minutes):{len(new_errors)} Nos</h2>
        """

        for error in new_errors:
            email_body += f"""
            <div style="margin-bottom: 20px; padding: 10px; border-bottom: 1px solid #ccc;">
                <p><strong>Service:</strong> {error.service}</p>
                <p><strong>Category:</strong> {error.error_category}</p>
                <p><strong>Severity:</strong> {error.severity}</p>
                <p><strong>Time:</strong> {error.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Details:</strong><br>{error.error_text}</p>
            </div>
            """

        reply = send_email_to_multiple_recipients("AIM Exception Mails for Developer", email_body,
                                                  {"to": "akashadi@titan.ci.in"})
        return JsonResponse(reply, safe=False)
    except Exception as e:
        return JsonResponse(str(e), safe=False)


@api_view(['POST'])
def email_anamoly_alert(requests):
    final_data = requests.data['email_data']
    html_message = open('templates/mailbody.html', mode='r').read()
    start, end = html_message.find("<!--st-->"), html_message.find("<!--ed-->")
    row_format = html_message[start + 9:end]

    html_rows_dict = dict()
    for table_data in final_data:
        if table_data['org_id'] not in html_rows_dict:
            html_rows_dict[table_data['org_id']] = ''
            print('first')

        html_rows_dict[table_data['org_id']] += dynamic_string(row_format, Sensor=table_data['element_name'],
                                                               Limits=table_data['anomaly_ranges'],
                                                               Actual=table_data['current_value'],
                                                               Aggregation=table_data['aggregation_type'],
                                                               Status=table_data['Status'])
        # print(dynamic_string(row_format, Sensor=table_data['element_name'],
        #                              Limits=table_data['anomaly_ranges'], Actual=table_data['current_value'],
        #                              Aggregation=table_data['aggregation_type'],
        #                              Status=table_data['Status']))

    if len(html_rows_dict) != 0:
        try:
            for i in html_rows_dict:
                try:
                    line = SettingsOrg.objects.filter(org_id=i).values('line_code')[0]['line_code']
                except:
                    print(SettingsOrg.objects.filter(org_id=i).values('line_code'))
                    line = 'error'
                    traceback.print_exc()
                html_message_ = html_message.replace(row_format, str(html_rows_dict[i]))

                email = SettingsEmailRecipients.objects.filter(org_id=i).values('email')
                html_message = dynamic_string(html_message_, line=line)
                # if os.path.exists(i+'.html'): os.remove(i+'.html')
                # open(i+'.html', mode='w').write(html_message)
                response = send_email_to_multiple_recipients("Anomaly alert|" + line, html_message,
                                                             {"to": list(email.values_list('email', flat=True))})
                return JsonResponse(response, safe=False)
        except Exception as e:
            return JsonResponse(str(traceback.format_exc()), safe=False)
    return JsonResponse("no records for anomalies", safe=False)
