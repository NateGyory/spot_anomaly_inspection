import argparse
import sys
import logging

import bosdyn.client.util

from bosdyn.client.estop import EstopEndpoint, EstopKeepAlive, EstopClient
from bosdyn.client.robot_state import RobotStateClient


class EstopService():
    def __init__(self):
        sdk = bosdyn.client.create_standard_sdk('estop_service')

        #robot = sdk.create_robot(options.hostname)
        robot = sdk.create_robot("192.168.80.5")

        # TODO do we need this???
        #robot.authenticate(options.username, options.password)

        estop_client = robot.ensure_client(EstopClient.default_service_name)

        #ep = EstopEndpoint(estop_client, "Estop Service", options.timeout)
        ep = EstopEndpoint(estop_client, "Estop Service", 5)

        # TODO consider changing this. This removes all other etop endpoints
        ep.force_simple_setup()

        # Begin periodic check-in between keep-alive and robot
        self.estop_keep_alive = EstopKeepAlive(ep)

        # Release the estop
        self.estop_keep_alive.allow()

        # Create robot state client for the robot
        self.state_client = robot.ensure_client(RobotStateClient.default_service_name)

    # TODO consider deleting
    def __enter__(self):
        pass

    # TODO consider deleting
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.estop_keep_alive.end_periodic_check_in()

    def stop(self):
        self.estop_keep_alive.stop()

    def allow(self):
        self.estop_keep_alive.allow()

    def settle_then_cut(self):
        self.estop_keep_alive.settle_then_cut()
