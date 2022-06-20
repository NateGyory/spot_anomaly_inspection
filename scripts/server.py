import os
import time

from flask import Flask, request
import json
from anomaly_deploy_service import AnomalyDeployService

hostname = os.getenv('HOSTNAME')
username = os.getenv('SPOT_USER')
password = os.getenv('SPOT_PASSWORD')
timeout = int(os.getenv('TIMEOUT'))

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
#anomaly_deploy = AnomalyDeployService(hostname, username, password, timeout)
#
#try:
#    anomaly_deploy.run("fabled-ant-9U+9jNqo.Z+yNUDUEj2R.A==")
#except Exception as exc:  # pylint: disable=broad-except
#    print(exc)
#    print("ERROR")
#    anomaly_deploy.return_lease()
