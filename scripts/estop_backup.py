import argparse
import logging
import time

import bosdyn.client.util

from bosdyn.client.estop import EstopEndpoint, EstopKeepAlive, EstopClient
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.robot_command import RobotCommandClient, blocking_stand
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive, LeaseWallet
from bosdyn.client.graph_nav import GraphNavClient
from bosdyn.client.power import safe_power_off, PowerClient, power_on
from bosdyn.client.frame_helpers import get_odom_tform_body
from bosdyn.api.graph_nav import nav_pb2

from bosdyn.api.graph_nav import map_pb2

import graph_nav_util

class EstopService():
    def __init__(self, hostname, username, password, timeout):

        # Authentication
        sdk = bosdyn.client.create_standard_sdk('estop_service')
        robot = sdk.create_robot(hostname)
        robot.authenticate(username, password)

        # Get estop client and keep alive
        self.estop_client = robot.ensure_client(EstopClient.default_service_name)
        ep = EstopEndpoint(self.estop_client, "anomaly_estop_service", timeout)
        ep.force_simple_setup()
        estop_keep_alive = EstopKeepAlive(ep)

        # Sync robot time
        robot.time_sync.wait_for_sync()

        # Get lease client and wallet
        lease_client = robot.ensure_client(LeaseClient.default_service_name)
        lease_wallet = lease_client.lease_wallet
        lease = lease_client.acquire()
        lease_keep_alive = bosdyn.client.lease.LeaseKeepAlive(lease_client)


        # Get command and state client
        command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        state_client = robot.ensure_client(RobotStateClient.default_service_name)

        # Get graph_nav client
        graph_nav_client = robot.ensure_client(GraphNavClient.default_service_name)

        # Get power client
        power_client = robot.ensure_client(PowerClient.default_service_name)

        # Boolean indicating the robot's power state.
        power_state = state_client.get_robot_state().power_state
        powered_on = (power_state.motor_power_state == power_state.STATE_ON)

        # Store the most recent knowledge of the state of the robot based on rpc calls.
        current_graph = None
        current_edges = dict()  #maps to_waypoint to list(from_waypoint)
        current_waypoint_snapshots = dict()  # maps id to waypoint snapshot
        current_edge_snapshots = dict()  # maps id to edge snapshot
        current_annotation_name_to_wp_id = dict()

        # folder path for graph_nav data
        #graph_nav_folder = "/app/graph_nav"
        graph_nav_folder = "../graph_nav/downloaded_graph"

        print("Reading in graph from graph_nav folder")
        with open(graph_nav_folder + "/graph", "rb") as graph_file:
            # Load the graph from file.
            data = graph_file.read()
            current_graph = map_pb2.Graph()
            current_graph.ParseFromString(data)
            print("Loaded graph has {} waypoints and {} edges".format(
                len(current_graph.waypoints), len(current_graph.edges)))

        for waypoint in current_graph.waypoints:
            # Load the waypoint snapshots from file.
            with open(graph_nav_folder + "/waypoint_snapshots/{}".format(waypoint.snapshot_id),
                      "rb") as snapshot_file:
                waypoint_snapshot = map_pb2.WaypointSnapshot()
                waypoint_snapshot.ParseFromString(snapshot_file.read())
                current_waypoint_snapshots[waypoint_snapshot.id] = waypoint_snapshot

        for edge in current_graph.edges:
            if len(edge.snapshot_id) == 0:
                continue
            # Load the edge snapshots from file.
            with open(graph_nav_folder + "/edge_snapshots/{}".format(edge.snapshot_id),
                      "rb") as snapshot_file:
                edge_snapshot = map_pb2.EdgeSnapshot()
                edge_snapshot.ParseFromString(snapshot_file.read())
                current_edge_snapshots[edge_snapshot.id] = edge_snapshot

        print("Uploading the graph and snapshots to the robot")
        true_if_empty = not len(current_graph.anchoring.anchors)
        response = graph_nav_client.upload_graph(lease=lease.lease_proto,
                                                 graph=current_graph,
                                                 generate_new_anchoring=true_if_empty)

        # Upload the snapshots to the robot.
        for snapshot_id in response.unknown_waypoint_snapshot_ids:
            waypoint_snapshot = current_waypoint_snapshots[snapshot_id]
            graph_nav_client.upload_waypoint_snapshot(waypoint_snapshot)
            print("Uploaded {}".format(waypoint_snapshot.id))

        for snapshot_id in response.unknown_edge_snapshot_ids:
            edge_snapshot = current_edge_snapshots[snapshot_id]
            graph_nav_client.upload_edge_snapshot(edge_snapshot)
            print("Uploaded {}".format(edge_snapshot.id))

        # Get waypoints for navigation

        # Download current graph
        graph = graph_nav_client.download_graph()
        if graph is None:
            print("Empty graph.")
            return
        current_graph = graph

        localization_id = graph_nav_client.get_localization_state().localization.waypoint_id

        # Update and print waypoints and edges
        current_annotation_name_to_wp_id, current_edges = graph_nav_util.update_waypoints_and_edges(
            graph, localization_id)

        # The upload is complete! Check that the robot is localized to the graph,

        robot_state = state_client.get_robot_state()
        current_odom_tform_body = get_odom_tform_body(
            robot_state.kinematic_state.transforms_snapshot).to_proto()

        # Create an empty instance for initial localization since we are asking it to localize
        # based on the nearest fiducial.
        localization = nav_pb2.Localization()
        graph_nav_client.set_localization(initial_guess_localization=localization,
                                                ko_tform_body=current_odom_tform_body)
        localization_state = graph_nav_client.get_localization_state()
        if not localization_state.localization.waypoint_id:
            print("The robot was unable to localize, shutting down")

        print("Robot is localized, navigating to destination waypoint")

        dest_waypoint = "fabled-ant-9U+9jNqo.Z+yNUDUEj2R.A=="
        # TODO do we need this
        lease = lease_wallet.get_lease()
        destination_waypoint = graph_nav_util.find_unique_waypoint_id(
            dest_waypoint, current_graph, current_annotation_name_to_wp_id)

        if not destination_waypoint:
            # TODO wrap the finish code in a function so robot doesnt just floop dowm
            print("Failed to find the unique waypoint id. Exiting")
            return

        robot.power_on(timeout_sec=20)
        powered_on = True;

        # Stop the lease keep-alive and create a new sublease for graph nav.
        lease = lease_wallet.advance()
        sublease = lease.create_sublease()
        lease_keep_alive.shutdown()

        # Navigate to the destination waypoint.
        nav_to_cmd_id = None
        is_finished = False
        while not is_finished:
            # Issue the navigation command about twice a second such that it is easy to terminate the
            # navigation command (with estop or killing the program).
            try:
                nav_to_cmd_id = graph_nav_client.navigate_to(destination_waypoint, 1.0,
                                                                   leases=[sublease.lease_proto],
                                                                   command_id=nav_to_cmd_id)
            except ResponseError as e:
                print("Error while navigating {}".format(e))
                break

            time.sleep(.5)  # Sleep for half a second to allow for command execution.
            # Poll the robot for feedback to determine if the navigation command is complete. Then sit
            # the robot down once it is finished.
            is_finished = self._check_success(nav_to_cmd_id)

        lease = lease_wallet.advance()
        lease_keep_alive = LeaseKeepAlive(lease_client)

        # Power off robot
        robot.power_off(cut_immediately=False)

    def _check_success(self, command_id=-1):
        """Use a navigation command id to get feedback from the robot and sit when command succeeds."""
        if command_id == -1:
            # No command, so we have not status to check.
            return False
        status = self._graph_nav_client.navigation_feedback(command_id)
        if status.status == graph_nav_pb2.NavigationFeedbackResponse.STATUS_REACHED_GOAL:
            # Successfully completed the navigation commands!
            return True
        elif status.status == graph_nav_pb2.NavigationFeedbackResponse.STATUS_LOST:
            print("Robot got lost when navigating the route, the robot will now sit down.")
            return True
        elif status.status == graph_nav_pb2.NavigationFeedbackResponse.STATUS_STUCK:
            print("Robot got stuck when navigating the route, the robot will now sit down.")
            return True
        elif status.status == graph_nav_pb2.NavigationFeedbackResponse.STATUS_ROBOT_IMPAIRED:
            print("Robot is impaired.")
            return True
        else:
            # Navigation command is not complete yet.
            return False
    #def stop(self):
    #    self.estop_keep_alive.stop()

    #def allow(self):
    #    self.estop_keep_alive.allow()

    #def settle_then_cut(self):
    #    self.estop_keep_alive.settle_then_cut()
