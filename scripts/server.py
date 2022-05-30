import os
import time

from flask import Flask, request
import json
from estop import EstopService

hostname = os.getenv('HOSTNAME')
username = os.getenv('SPOT_USER')
password = os.getenv('SPOT_PASSWORD')
timeout = int(os.getenv('TIMEOUT'))

app = Flask(__name__)

@app.route("/spot_deploy", methods=['POST'])
def spot_deploy():
    estop = EstopService(hostname, username, password, timeout)
    request_data = request.get_json()

    waypoint_id = request_data['waypoint_id']

    print('waypoint_id is: ', waypoint_id)

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

