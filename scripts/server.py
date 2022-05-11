from flask import Flask, request
from estop import EstopService

app = Flask(__name__)
estop = EstopService()

@app.route("/spot_deploy", methods=['POST'])
def servo1():
    request_data = request.get_json()

    waypoint_id = request_data['waypoint_id']

    # Get estop control
    estop.allow()

    # Send request to anomaly deploy with waypoint_id
