import os
from colorama import Fore, Back, Style, init
import datetime
import requests
import traceback
import inspect
import json

login_creds = {"username": "admin", "password": "LastDance"}
server_ip = "127.0.0.1:8000"
generate_token_url = f"http://{server_ip}/predictive/token/"
get_anomaly_url = f"http://{server_ip}/predictive/anamoly_records/"
error_log_url = f"http://{server_ip}/predictive/error_log/"
alert = f"http://{server_ip}/predictive/alert/"
globals()['res_json'] = {}
exception_details = {}
exception_timerepeat = {'5': 5,'4': 10, '3':15 ,'2':15,'1':20}
service = "Anamoly"
identity = "main"

def color_printer(type,data):
    type_dict = {"thread": Fore.CYAN , "error": Fore.RED , "request": Fore.MAGENTA , "troubleshoot": Fore.YELLOW ,"opcua":Fore.GREEN}
    print(type_dict[type]+"["+get_timestamp()+"]"+type+" " + data  + Fore.WHITE)


def get_timestamp():
    return str(datetime.datetime.now()).split('.')[0]


def convert_dt(time):
    return datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S")


def exception_logger(exp_type,exp_severity,exp_shrt,exp_json):
    try:
        exp_shrt = str(exp_shrt)
        color_printer("error", exp_shrt + exp_type)
        if exp_type in exception_details:
            time_elapsed = (datetime.datetime.strptime(get_timestamp(),"%Y-%m-%d %H:%M:%S") - exception_details[exp_type]['last_occurred']).seconds
            if exception_details[exp_type]['e_short'] != exp_shrt:
                exception_details[exp_type] = {'last_occurred': convert_dt(get_timestamp()), 'e_short': exp_shrt}
                # print(get_timestamp()+" >> "+'mod time log', exception_details)
                try:
                    post_data(exp_json, "error_log")
                except:
                    pass
            if time_elapsed >= int(exception_timerepeat[str(exp_severity)]):
                # print(get_timestamp()+" >> "+'exception repeating', time_elapsed)
                exception_details[exp_type] = {'last_occurred': convert_dt(get_timestamp()), 'e_short': exp_shrt}
        else:
            exception_details[exp_type] = {'last_occurred': convert_dt(get_timestamp()), 'e_short': exp_shrt}
            # print(get_timestamp()+" >> "+'first time log', exception_details)
            try:
                post_data(exp_json, "error_log")
            except:
                pass
    except Exception as e:
        print(get_timestamp()+" >> "+ "---handled1---")
        traceback.print_exc()


def post_data(data_json,type_):
    
    url_type = {"anomaly": get_anomaly_url,"error_log": error_log_url,"alert":alert}

    try:
        bearer_token = requests.post(generate_token_url,json =login_creds)
        
        headers = {
            "Authorization": f"Bearer {bearer_token.json()['access']}",
            "Content-Type": "application/json"
        }

        res = requests.post(url_type[type_],json =data_json,headers=headers)
        color_printer("request", str(res.json()))

        # globals()['res_json'] = res.json() if type_ == 'anomaly' else globals()['res_json']
        return res.json()
    except Exception as e:
        color_printer("error", str(e)+"postdata")
        # traceback.print_exc()


def analyse_anomaly():
    print("______________ANALYSING ANOMALIES____________")
    try:
        req = post_data({"trail_request":False},"anomaly")
        print(req)
        old = req['old_set']
        new = req['new_set']

        old_ele = {i['element_name'] for i in old}
        new_ele = {i['element_name'] for i in new}

        still_active = old_ele & new_ele  #in both sets
        new_amly = new_ele - old_ele #present in 2nd set but not in 1st
        closed_amly = old_ele - new_ele #present in 1st set but not in 2nd

        res_still_active_old = [next((sub for sub in old if sub['element_name'] == ele)) for ele in still_active]
        res_still_active_new = [next((sub for sub in new if sub['element_name'] == ele)) for ele in still_active]
        res_new = [next((sub for sub in new if sub['element_name'] == ele)) for ele in new_amly]
        res_closed = [next((sub for sub in old if sub['element_name'] == ele)) for ele in closed_amly]


        still_active_for = {ele:convert_dt(next((sub['time_stamp'] for sub in res_still_active_new if sub['element_name'] == ele)))
               -convert_dt(next((sub['time_stamp'] for sub in res_still_active_old if sub['element_name'] == ele)))
               for ele in still_active}
        print(res_closed,'--',res_new,'--',res_still_active_new)

        # row_format
        '''
        html_message = open('mailbody.html', mode='r').read()
        start, end = html_message.find("<!--st-->"), html_message.find("<!--ed-->")
        row_format = html_message[start + 9:end]
        final_rows = ""


        for i,table_data in enumerate(res_new):

            final_rows += dynamic_string(row_format,Sno=i,Sensor=table_data['element_name'],
                                         Limits=table_data['anomaly_ranges'],Actual=table_data['current_value'],
                                         Aggregation=table_data['aggregation_type'],Status='NEW')
        for i,table_data in enumerate(res_still_active_new):

            final_rows += dynamic_string(row_format, Sno=i, Sensor=table_data['element_name'],
                                         Limits=table_data['anomaly_ranges'], Actual=table_data['current_value'],
                                         Aggregation=table_data['aggregation_type'], Status='ACTIVE FOR '+str(still_active_for[table_data['element_name']]))
        for i,table_data in enumerate(res_closed):

            final_rows += dynamic_string(row_format, Sno=i, Sensor=table_data['element_name'],
                                         Limits=table_data['anomaly_ranges'], Actual=table_data['current_value'],
                                         Aggregation=table_data['aggregation_type'],
                                         Status='CLOSED')

        html_message=html_message.replace(row_format,str(final_rows))

        print(type(html_message))
        if os.path.exists('x.html'):os.remove('x.html')
        open('x.html',mode='x').write(html_message)
        '''
        columns = ['Sensor','element_name','anomaly_ranges','current_value','aggregation_type','Status','org_id']

        f1 = [{'element_name':table_data['element_name'],'anomaly_ranges':table_data['anomaly_ranges'],'current_value':table_data['current_value'],
                                         'aggregation_type':table_data['aggregation_type'],'Status':'NEW','org_id':table_data['org_id']} for table_data in res_new]
        f2 = [{'element_name': table_data['element_name'], 'anomaly_ranges': table_data['anomaly_ranges'],
                      'current_value': table_data['current_value'],
                      'aggregation_type': table_data['aggregation_type'],'Status':'CLOSED','org_id':table_data['org_id']} for table_data in res_closed]

        f3 = [{'element_name': table_data['element_name'], 'anomaly_ranges': table_data['anomaly_ranges'],
                      'current_value': table_data['current_value'],
                      'aggregation_type': table_data['aggregation_type'], 'Status': 'ACTIVE FOR '+str(still_active_for[table_data['element_name']]),'org_id':table_data['org_id']} for table_data in res_still_active_old]

        final_data= [*f1,*f2,*f3]
        # print(final_data)
        post_data({'email_data':final_data}, 'alert')

    except Exception as e:
        exp_severity = 5
        f_name = identity + '>' + inspect.currentframe().f_code.co_name
        json_ = {"service": service, "error_category": f_name, "error_text": traceback.format_exc(),
                 "severity": exp_severity, "timestamp": get_timestamp()}
        exception_logger(f_name + '_', exp_severity, e, json_)
        # traceback.print_exc()

if __name__=="__main__":
    config_file = 'D:\PredictiMach\PredictiveMaintenance\Microservices_final\AIM_datalogger_config.json'
    if os.path.exists(config_file):
        config = json.loads(open(config_file).read())
        login_creds = {"username": config["username"], "password": config["password"]}
        server_ip = config["server_ip"]
        analyse_anomaly()
    else:
        print(config_file,"config file not available to run Anomaly microservice.")


