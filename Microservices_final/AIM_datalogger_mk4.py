
'''
Diffrence in mk3 and mk4 version : added exception handling
'''

import time
import threading
import datetime
import pandas as pd
import requests
from colorama import Fore, Back, Style, init
import warnings
import traceback
from opcua import Client
import os
import json
import inspect

#Thread - Cyan
#Errors - Red
#API - Magenta
#troubleshooting - yellow


warnings.filterwarnings("ignore")
init(autoreset=True)

login_creds = {"username": "admin", "password": "LastDance"}
server_ip = "192.168.1.104:9001"
generate_token_url = f"http://{server_ip}/predictive/token/"
get_plc_nos = f"http://{server_ip}/predictive/datalog_sensor/"
error_log_url = f"http://{server_ip}/predictive/error_log/"
data_log_url = f"http://{server_ip}/predictive/datalog/"
globals()['res_json'] = {}
exception_details = {}
exception_timerepeat = {'5': 5,'4': 10, '3':15 ,'2':15,'1':20}
service = "DataLog"

def color_printer(type,data):
    type_dict = {"thread": Fore.CYAN , "error": Fore.RED , "request": Fore.MAGENTA , "troubleshoot": Fore.YELLOW ,"opcua":Fore.GREEN}
    print(type_dict[type]+"["+get_timestamp()+"] "+type+" " + data  + Fore.WHITE)


def get_timestamp():
    return str(datetime.datetime.now()).split('.')[0]

def get_dt():
    return datetime.datetime.strptime(get_timestamp(), "%Y-%m-%d %H:%M:%S")
def exception_logger(exp_type,exp_severity,exp_shrt,exp_json):
    try:
        exp_shrt = str(exp_shrt)
        color_printer("error", exp_shrt + exp_type)
        if exp_type in exception_details:
            time_elapsed = (datetime.datetime.strptime(get_timestamp(),"%Y-%m-%d %H:%M:%S") - exception_details[exp_type]['last_occurred']).seconds
            if exception_details[exp_type]['e_short'] != exp_shrt:
                exception_details[exp_type] = {'last_occurred': get_dt(), 'e_short': exp_shrt}
                print(get_timestamp()+" >> "+'mod time log', exception_details)
                try:
                    post_data(exp_json, "error_log")
                except:
                    pass
            if time_elapsed >= int(exception_timerepeat[str(exp_severity)]):
                print(get_timestamp()+" >> "+'exception repeating', time_elapsed)
                exception_details[exp_type] = {'last_occurred': get_dt(), 'e_short': exp_shrt}
        else:
            exception_details[exp_type] = {'last_occurred': get_dt(), 'e_short': exp_shrt}
            print(get_timestamp()+" >> "+'first time log', exception_details)
            # try:
            #     post_data(exp_json, "error_log")
            # except:
            #     pass
    except Exception as e:
        print(get_timestamp()+" >> "+ "---handled1---")
        traceback.print_exc()



def post_data(data_json,type_):
    url_type = {"data": data_log_url,"error_log": error_log_url,"get_sensors": get_plc_nos}
    try:
        bearer_token = requests.post(generate_token_url,json =login_creds)
        # print(Fore.GREEN + str(bearer_token.json()["access"])+ "----"+str(data_json))
        headers = {"Authorization": f"Bearer {bearer_token.json()["access"]}",'Content-Type':'application/json'}
        res = requests.post(url_type[type_],json =data_json,headers=headers)
        color_printer("request", str(res.json()))

        globals()['res_json'] = res.json() if type_ == 'get_sensors' else globals()['res_json']
        # print(data_json)
        # pass
    except Exception as e:
        color_printer("error", "postdata"+str(e))
        # traceback.print_exc()
        # print("---handled2---"+get_timestamp())
# try:
#     post_data({"service" : "DataLog","error_category" : "Program start log","error_text":str("No error, using as log"),"severity" : 1,"timestamp":get_timestamp()},"error_log")
# except:
#     pass

class AIM_Logger_main:
    def __init__(self):
        self.plc_nos = 0
        self.identity = 'AIM_Logger_main'
        self.thread_active_nos = 1
        self.active_threads = {}
        # self.generate_token_url = "http://192.168.19.119:9001/predictive/token/"
        # self.login_creds = {"username": "admin", "password": "LastDance"}
        # self.get_plc_nos = "http://192.168.19.119:9001/predictive/datalog_sensor/"
        # self.error_log_url = "http://192.168.19.119:9001/predictive/error_log/"
        globals()['res_json'] ={}
        self.current_min = ''

    def plc_thread_manager(self):
        while True:
            current_minute = datetime.datetime.now().minute
            # current_sec = get_timestamp().second

            if self.current_min != current_minute:
                self.current_min = current_minute

                try:
                    # self.get_objs()
                    post_data({},"get_sensors")
                    self.plc_nos = len(globals()['res_json'])

                    set_server = set(globals()['res_json'].keys())
                    set_threads = set(self.active_threads.keys())
                    delete_threads = set_threads-set_server

                    # color_printer("troubleshoot",str(self.active_threads))
                    # color_printer("thread", "Deleted Threads:"+str(delete_threads))

                    for i in globals()['res_json']:
                        if i not in self.active_threads:
                            color_printer("thread", "Thread created:" + str(i))
                            self.thread_active_nos += 1
                            self.active_threads[i] = sensor_creator(i)
                            self.active_threads[i].start_logging()
                            # color_printer("troubleshoot", str(type(self.active_threads[i])))
                            # self.active_threads[i].start()
                        else:
                            # print('no new threads to be created,current active threads :',self.thread_active_nos)
                            pass

                    for j in delete_threads:
                        # color_printer("troubleshoot",str(self.active_threads.keys()))
                        self.active_threads[j].logging_active = False
                        color_printer("thread", 'Terminating thread externally ' + str(j))
                        self.active_threads.pop(j, None)

                    color_printer("troubleshoot", get_timestamp()+str(self.active_threads.keys()))
                except Exception as e:
                    exp_severity = 5
                    f_name = self.identity + '>' + inspect.currentframe().f_code.co_name
                    json_ = {"service": service, "error_category": f_name, "error_text": traceback.format_exc(),
                             "severity": exp_severity, "timestamp": get_timestamp()}
                    exception_logger(f_name+'_', exp_severity, e, json_)

'''
    def get_objs(self):
        try:
            bearer_token = requests.post(self.generate_token_url, json=self.login_creds)
            headers = {"Authorization": f"Bearer {bearer_token.json()["access"]}", 'Content-Type': 'application/json'}
            res = requests.post(self.get_plc_nos, headers=headers)
            color_printer("request", str(res.json()))
            # res = {"192.168.1.119":{'s1':['tag1','1'],'s2':['tag2','1']},"192.168.11.119":{'s3':['tag3','3']}}
            globals()['res_json'] = res.json()
        except Exception as e:
            color_printer("error", str(e))
            post_data({}, "error_log")
'''

class sensor_creator:
    def __init__(self,identity):
        # self.sensor_type = sensor_type
        # self.element_id = element_id
        # self.run_every = 1
        self.identity = identity
        # self.generate_token_url = "http://192.168.19.119:9001/predictive/token/"
        # self.data_log_url = "http://192.168.19.119:9001/predictive/datalog/"
        # self.login_creds = {"username":"admin","password":"LastDance"}
        self.logging_active = False
        # self.df = pd.DataFrame(columns = ['timestamp','value'])
        # pd.to_datetime(self.df["timestamp"])
        # self.df.set_index("timestamp", inplace=True)
        self.current_min = datetime.datetime.now().minute
        self.current_sec = datetime.datetime.now().second
        self.dfs = {}
        self.name_space = "ns=2"
        self.prev_conn_status = False
        self.endpoint_con_status =  False
        self.trigger_tag = ""

    def start_logging(self):
        # if not self.logging_active:
        #     self.logging_active = True

        for df in globals()['res_json'][self.identity]:
            self.dfs[df] = pd.DataFrame(columns = ['timestamp','value'])
            pd.to_datetime(self.dfs[df]["timestamp"])
            self.dfs[df].set_index("timestamp", inplace=True)
        self.connect_server()
        self.logger_thread = threading.Thread(target=self.csv_logger, daemon=True)
        self.logger_thread.start()

    def connect_server(self):

        try:

            self.client = Client(self.identity)
            self.client.connect()
            self.endpoint_con_status = True
            color_printer('opcua',f"server initializing for end point {self.identity}  is successful ::: - {get_timestamp()}"
            '''self.client.get_node("ns=2;s=ProcessTrigger").set_value(True)''')
            self.prev_conn_status = True

            # try:
            #     self.trigger_tag =  re.findall('\d+', str(globals()['res_json'][self.identity][df][0]))
            #     self.client.get_node(f'ns=2;i=1').set_value(True)
            # except:
            #     pass
            # self.datalog('Msg', 'Msg', f'{self.server_name} Thread Initialised!')



        except Exception as e:
            exp_severity = 5
            f_name = self.identity + '>' + inspect.currentframe().f_code.co_name
            json_ = {"service": service, "error_category": f_name, "error_text": traceback.format_exc(),
                     "severity": exp_severity, "timestamp": get_timestamp()}
            exception_logger(f_name + '_', exp_severity, e, json_)

            # color_printer("error",f"server initializing for end point {self.identity} is unsuccessful will be retry in 5 Sec ::: - {get_timestamp()}")
            time.sleep(5)
            self.prev_conn_status = False


        # self.onchange_monitor()

    def csv_read_send(self,key):
        # self.logging_active = False
        summary = self.data_summarizer(key)
        self.dfs[key] = pd.DataFrame(columns=['timestamp', 'value'])
        pd.to_datetime(self.dfs[key]["timestamp"])
        self.dfs[key].set_index("timestamp", inplace=True)
        # self.logging_active = True

        values = [key,*summary,globals()['res_json'][self.identity][key][1],globals()['res_json'][self.identity][key][2]]
        keys = ["element_id","timestamp","max", "min","avg","no_of_records","org_id","rec_train_data"]
        json = dict(zip(keys,values))
        # print(json)
        if json["no_of_records"]>0:
            post_data(json,"data")
        else:
            print(get_timestamp()+" >> "+"records 0 "+self.identity)
    def data_summarizer(self,id):
        count = len(self.dfs[id])
        summary = self.dfs[id].agg(["max", "min", "mean"])
        # print(type(summary),summary['value'])
        summarized_data = summary['value'].tolist()
        # print(id,"--",summarized_data)
        rounded_sum_data = [round(x, 4) for x in summarized_data]
        rounded_sum_data.insert(0,get_timestamp())
        rounded_sum_data.append(count)

        return rounded_sum_data



    def csv_logger(self):
        self.logging_active = True
        while self.logging_active:
            # print("true","ji")

            # Detect minute change
            current_minute = datetime.datetime.now().minute
            current_sec = datetime.datetime.now().second

            keys = {}
            try:
                keys = globals()['res_json'][self.identity]
            except:
                self.logging_active = False
                color_printer("error", 'Stopping thread internally '+self.identity)
                # post_data({}, "error_log")

            try:
                # print(keys,keys.keys())
                if self.current_min != current_minute:
                    self.current_min = current_minute
                    # print(self.identity,'', keys.keys())
                    # print('00000000000000000000',key)
                    for key in keys:
                        self.csv_read_send(key)
                    # print("--------------------------------")
            except Exception as e:
                exp_severity = 5
                f_name = self.identity + '>' + inspect.currentframe().f_code.co_name
                json_ = {"service": service, "error_category": f_name, "error_text": traceback.format_exc(),
                         "severity": exp_severity, "timestamp": get_timestamp()}
                exception_logger(f_name + '_', exp_severity, e, json_)


            try:

                if self.current_sec != current_sec:
                    self.current_sec = current_sec

                    for df in keys:
                        if df not in self.dfs:
                            self.dfs[df] = pd.DataFrame(columns=['timestamp', 'value'])
                            pd.to_datetime(self.dfs[df]["timestamp"])
                            self.dfs[df].set_index("timestamp", inplace=True)
                            color_printer("thread", 'new sensor created:'+str(df))
                            # print('new sensor created:',df)
                        if self.endpoint_con_status:
                            try:  # check for opcua connected
                                b = self.client.get_endpoints()
                                try:
                                    tag = str(globals()['res_json'][self.identity][df][0])
                                    # tag_trig =tag.replace("Row", "Trigger")
                                    # self.client.get_node(tag_trig).set_value(True)
                                    value = self.client.get_node(tag).get_value()
                                    if value != '':
                                        new_row = {'timestamp': get_timestamp(), 'value': float(value)}
                                        new_row_df = pd.DataFrame([new_row])
                                        new_row_df['timestamp'] = pd.to_datetime(new_row_df['timestamp'])
                                        self.dfs[df] = pd.concat([self.dfs[df], new_row_df], ignore_index=True)
                                        self.dfs[df].set_index('timestamp', inplace=True)
                                except Exception as e:
                                    exp_severity = 5
                                    f_name = self.identity + '>' + inspect.currentframe().f_code.co_name
                                    json_ = {"service": service, "error_category": f_name,
                                             "error_text": traceback.format_exc(),
                                             "severity": exp_severity, "timestamp": get_timestamp()}
                                    exception_logger(f_name + '_', exp_severity, e, json_)

                            except Exception as e:
                                exp_severity = 5
                                f_name = self.identity + '>' + inspect.currentframe().f_code.co_name
                                json_ = {"service": service, "error_category": f_name,
                                         "error_text": traceback.format_exc(),
                                         "severity": exp_severity, "timestamp": get_timestamp()}
                                exception_logger(f_name + '_', exp_severity, e, json_)

                                self.endpoint_con_status = False
                                break
                                # time.sleep(self.config_data['connection_retry_time'] / 1000)
                                # self.connect_server()
                        else:
                            time.sleep(5)
                            self.connect_server()

                    # self.connect_server()

            except Exception as e:
                exp_severity = 5
                f_name = self.identity + '>' + inspect.currentframe().f_code.co_name
                json_ = {"service": service, "error_category": f_name, "error_text": traceback.format_exc(),
                         "severity": exp_severity, "timestamp": get_timestamp()}
                exception_logger(f_name + '_', exp_severity, e, json_)


if __name__ == "__main__":
    config_file = r'D:\PredictiMach\PredictiveMaintenance\Microservices_final\AIM_datalogger_config.json'
    if os.path.exists(config_file):
        config = json.loads(open(config_file).read())
        login_creds = {"username": config["username"], "password": config["password"]}
        server_ip = config["server_ip"]
        sense1 = AIM_Logger_main()
        sense1.plc_thread_manager()
    else:
        print(config_file, "config file not available to run gateway microservice.")

