import json
import os

import requests
import schedule
import time
import datetime

from . import mailbody_anomaly

config = {'60'}
server_ip = "127.0.0.1:8000"
config_file = 'D:\PredictiMach\PredictiveMaintenance\Microservices_final\AIM_datalogger_config.json'
if os.path.exists(config_file):
    config = json.loads(open(config_file).read())
    server_ip = config["server_ip"]

def hourly_prediciton_trigger():
    pass

def exception_job():
    res = requests.post(f"http://{server_ip}/predictive/exception_job/")
    print(f"[{datetime.datetime.now()}] {res.json}")

#schedule.every(1).seconds.do(start1)
#schedule.every(7).seconds.do(start1)
schedule.every(10).minutes.do(mailbody_anomaly.analyse_anomaly)
schedule.every(1).minutes.do(exception_job)
# schedule.every().hour.at(":50").do(start)

while True:
    schedule.run_pending()
    time.sleep(1)