import json
import os
import time

import requests
from opcua import Server, ua
import traceback


sensor_config = {'Vibration_sensor':'3'}
end_point = "opc.tcp://192.168.119.1:4840"
last_value = {}
IFM_ip = '192.168.119.101'
def get_sensor_value(sensor_name):
    try:
        res = requests.get(f'http://{IFM_ip}/iolinkmaster/port[{sensor_config[sensor_name]}]/iolinkdevice/pdin/getdata')
        if res.status_code == 200:
            print(res.json())
            value = int(res.json()['data']['value'][:4],16)*0.1
            last_value[sensor_name] = value
            return value
        else:
            return last_value.get(sensor_name, 0)
    except Exception as e:
        print(e)
        traceback.print_exc()
        return last_value.get(sensor_name,0)

def start_server():
    print("initialising server at ",end_point,"....")
    globals()['server'] = Server()
    globals()['server'].set_endpoint(end_point)
    idx = globals()['server'].register_namespace("xyz")
    objects = globals()['server'].get_objects_node()
    myobj = objects.add_object(ua.NodeId("", idx), "zxy")
    print("creating variables....")
    for i in sensor_config:
        globals()[i] = myobj.add_variable(ua.NodeId(i, idx), i, 0.0)
        # print(get_sensor_value(i))
        globals()[i].set_writable()
    globals()['server'].start()
    print("server started")

def run():
    start_server()
    while True:
        try:
            for i in sensor_config:
                try:
                    val = get_sensor_value(i)
                    print(i,val)
                    globals()[i].set_value(val)

                except Exception as e:
                    print(e,'IFM')
                    traceback.print_exc()
            time.sleep(1)
        except Exception as e:
            print('main-',e)
            traceback.print_exc()
            time.sleep(5)
            start_server()


if __name__ == '__main__':
    if os.path.exists('IFMServer_config.json'):
        config = json.loads(open('IFMServer_config.json').read())
        login_creds = {"username": config["AIMServer_username"], "password": config["AIMServer_password"]}
        server_ip = config["AIMServer_ip"]
        end_point = config["opcua_endpoint"]
        sensor_config = config["sensor_config"]
        IFM_ip = config["IFM_ip"]

    run()






