import os
import time

from flask import Flask, request
import json
from anomaly_deploy_service import AnomalyDeployService

#hostname = os.getenv('HOSTNAME')
#username = os.getenv('SPOT_USER')
#password = os.getenv('SPOT_PASSWORD')
#timeout = int(os.getenv('TIMEOUT'))

hostname = '192.168.80.3'
username = 'user'
password = 'y8m534wfdfde'
timeout = 10

#anomaly_deploy = AnomalyDeployService(hostname, username, password, timeout)
#try:
#    anomaly_deploy.run('hedged-whale-twQBHx1YyDBR2tbLzRtVlw==')
#except Exception as exc:  # pylint: disable=broad-except
#    print(exc)
#    print("ERROR")
#    anomaly_deploy.return_lease()
    #return json.dumps({'Error':"Some error :("}), 400, {'ContentType':'application/json'}

app = Flask(__name__)

@app.route("/spot_deploy", methods=['POST'])
def spot_deploy():
    request_data = request.get_json()

    waypoint_id = request_data['waypoint_id']

    print('waypoint_id is: ', waypoint_id)

    anomaly_deploy = AnomalyDeployService(hostname, username, password, timeout)

    try:
        anomaly_deploy.run(waypoint_id)
    except Exception as exc:  # pylint: disable=broad-except
        print(exc)
        print("ERROR")
        anomaly_deploy.return_lease()
        return json.dumps({'Error':"Some error :("}), 400, {'ContentType':'application/json'}

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route("/test", methods=['POST'])
def test():
    request_data = request.get_json()

    waypoint_id = request_data['waypoint_id']

    print('waypoint_id is: ', waypoint_id)
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
