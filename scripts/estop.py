import argparse
import logging

import bosdyn.client.util

from bosdyn.client.estop import EstopEndpoint, EstopKeepAlive, EstopClient
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.robot_command import RobotCommandClient, blocking_stand


class EstopService():
    def __init__(self, hostname, username, password, timeout):
        sdk = bosdyn.client.create_standard_sdk('estop_service')
        robot = sdk.create_robot(hostname)
        robot.authenticate(username, password)

        self.estop_client = robot.ensure_client(EstopClient.default_service_name)
        ep = EstopEndpoint(self.estop_client, "anomaly_estop_service", timeout)
        ep.force_simple_setup()

        self.estop_keep_alive = EstopKeepAlive(ep)

        # Create robot state client for the robot
        self.state_client = robot.ensure_client(RobotStateClient.default_service_name)

        # Test block this will be replaces with deploy to waypoint code via a function
        lease_client = robot.ensure_client('lease')
        lease = lease_client.acquire()
        lease_keep_alive = bosdyn.client.lease.LeaseKeepAlive(lease_client)

        robot.power_on(timeout_sec=20)

        robot.time_sync.wait_for_sync()

        command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        blocking_stand(command_client, timeout_sec=10)
        robot.power_off(cut_immediately=False)

    def stop(self):
        self.estop_keep_alive.stop()

    def allow(self):
        self.estop_keep_alive.allow()

    def settle_then_cut(self):
        self.estop_keep_alive.settle_then_cut()
