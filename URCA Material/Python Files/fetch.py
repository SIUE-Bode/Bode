# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

#

# Downloading, reproducing, distributing or otherwise using the SDK Software

# is subject to the terms and conditions of the Boston Dynamics Software

# Development Kit License (20191101-BDSDK-SL).



import argparse

import math

import sys

import time



import cv2

import numpy as np

from google.protobuf import wrappers_pb2



import bosdyn.client

import bosdyn.client.util

from bosdyn.api import (basic_command_pb2, geometry_pb2, image_pb2, manipulation_api_pb2,

                        network_compute_bridge_pb2)

from bosdyn.client import frame_helpers, math_helpers

from bosdyn.client.lease import LeaseClient, LeaseKeepAlive

from bosdyn.client.manipulation_api_client import ManipulationApiClient

from bosdyn.client.network_compute_bridge_client import (ExternalServerError,

                                                         NetworkComputeBridgeClient)

from bosdyn.client.robot_command import (RobotCommandBuilder, RobotCommandClient,

                                         block_for_trajectory_cmd, block_until_arm_arrives)

from bosdyn.client.robot_state import RobotStateClient

from bosdyn.client.directory import DirectoryClient



kImageSources = [

    'frontleft_fisheye_image', 'frontright_fisheye_image', 'left_fisheye_image',

    'right_fisheye_image', 'back_fisheye_image'

]





def get_obj_and_img(network_compute_client, server, model, confidence, image_sources, label):



    for source in image_sources:

        # Build a network compute request for this image source.

        image_source_and_service = network_compute_bridge_pb2.ImageSourceAndService(

            image_source=source)



        # Input data:

        #   model name

        #   minimum confidence (between 0 and 1)

        #   if we should automatically rotate the image

        input_data = network_compute_bridge_pb2.NetworkComputeInputData(

            image_source_and_service=image_source_and_service, model_name=model,

            min_confidence=confidence, rotate_image=network_compute_bridge_pb2.

            NetworkComputeInputData.ROTATE_IMAGE_ALIGN_HORIZONTAL)



        # Server data: the service name

        server_data = network_compute_bridge_pb2.NetworkComputeServerConfiguration(

            service_name=server)



        # Pack and send the request.

        process_img_req = network_compute_bridge_pb2.NetworkComputeRequest(

            input_data=input_data, server_config=server_data)



        try:

            resp = network_compute_client.network_compute_bridge_command(process_img_req)

        except ExternalServerError:

            # This sometimes happens if the NCB is unreachable due to intermittent wifi failures.

            print('Error connecting to network compute bridge. This may be temporary.')

            return None, None, None



        best_obj = None

        highest_conf = 0.0

        best_vision_tform_obj = None



        img = get_bounding_box_image(resp)

        image_full = resp.image_response



        # Show the image

        cv2.imshow("Fetch", img)

        cv2.waitKey(15)



        if len(resp.object_in_image) > 0:

            for obj in resp.object_in_image:

                # Get the label

                obj_label = obj.name.split('_label_')[-1]

                if obj_label != label:

                    continue

                conf_msg = wrappers_pb2.FloatValue()

                obj.additional_properties.Unpack(conf_msg)

                conf = conf_msg.value



                try:

                    vision_tform_obj = frame_helpers.get_a_tform_b(

                        obj.transforms_snapshot, frame_helpers.VISION_FRAME_NAME,

                        obj.image_properties.frame_name_image_coordinates)

                except bosdyn.client.frame_helpers.ValidateFrameTreeError:

                    # No depth data available.

                    vision_tform_obj = None



                if conf > highest_conf and vision_tform_obj is not None:

                    highest_conf = conf

                    best_obj = obj

                    best_vision_tform_obj = vision_tform_obj



        if best_obj is not None:

            return best_obj, image_full, best_vision_tform_obj



    return None, None, None





def get_bounding_box_image(response):

    dtype = np.uint8

    img = np.fromstring(response.image_response.shot.image.data, dtype=dtype)

    if response.image_response.shot.image.format == image_pb2.Image.FORMAT_RAW:

        img = img.reshape(response.image_response.shot.image.rows,

                          response.image_response.shot.image.cols)

    else:

        img = cv2.imdecode(img, -1)



    # Convert to BGR so we can draw colors

    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)



    # Draw bounding boxes in the image for all the detections.

    for obj in response.object_in_image:

        conf_msg = wrappers_pb2.FloatValue()

        obj.additional_properties.Unpack(conf_msg)

        confidence = conf_msg.value



        polygon = []

        min_x = float('inf')

        min_y = float('inf')

        for v in obj.image_properties.coordinates.vertexes:

            polygon.append([v.x, v.y])

            min_x = min(min_x, v.x)

            min_y = min(min_y, v.y)



        polygon = np.array(polygon, np.int32)

        polygon = polygon.reshape((-1, 1, 2))

        cv2.polylines(img, [polygon], True, (0, 255, 0), 2)



        caption = "{} {:.3f}".format(obj.name, confidence)

        cv2.putText(img, caption, (int(min_x), int(min_y)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,

                    (0, 255, 0), 2)



    return img





def find_center_px(polygon):

    min_x = math.inf

    min_y = math.inf

    max_x = -math.inf

    max_y = -math.inf

    for vert in polygon.vertexes:

        if vert.x < min_x:

            min_x = vert.x

        if vert.y < min_y:

            min_y = vert.y

        if vert.x > max_x:

            max_x = vert.x

        if vert.y > max_y:

            max_y = vert.y

    x = math.fabs(max_x - min_x) / 2.0 + min_x

    y = math.fabs(max_y - min_y) / 2.0 + min_y

    return (x, y)





def main(argv):

    parser = argparse.ArgumentParser()

    bosdyn.client.util.add_base_arguments(parser)

    parser.add_argument('-s', '--ml-service',

                        help='Service name of external machine learning server.', required=True)

    parser.add_argument('-m', '--model', help='Model name running on the external server.',

                        required=True)

    parser.add_argument('-p', '--person-model',

                        help='Person detection model name running on the external server.')

    parser.add_argument('-c', '--confidence-dogtoy',

                        help='Minimum confidence to return an object for the dogoy (0.0 to 1.0)',

                        default=0.5, type=float)

    parser.add_argument('-e', '--confidence-person',

                        help='Minimum confidence for person detection (0.0 to 1.0)', default=0.6,

                        type=float)

    options = parser.parse_args(argv)



    cv2.namedWindow("Fetch")

    cv2.waitKey(500)



    sdk = bosdyn.client.create_standard_sdk('SpotFetchClient')

    sdk.register_service_client(NetworkComputeBridgeClient)

    robot = sdk.create_robot(options.hostname)

    bosdyn.client.util.authenticate(robot)



    # Time sync is necessary so that time-based filter requests can be converted

    robot.time_sync.wait_for_sync()



    network_compute_client = robot.ensure_client(NetworkComputeBridgeClient.default_service_name)

    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)

    command_client = robot.ensure_client(RobotCommandClient.default_service_name)

    lease_client = robot.ensure_client(LeaseClient.default_service_name)


    # This script assumes the robot is already standing via the tablet.  We'll take over from the

    # tablet.

    lease_client.take()

    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):

        # Store the position of the hand at the last toy drop point.

        vision_tform_hand_at_drop = None



        while True:

            holding_toy = False

            while not holding_toy:

                # Capture an image and run ML on it.

                dogtoy, image, vision_tform_dogtoy = get_obj_and_img(

                    network_compute_client, options.ml_service, options.model,

                    options.confidence_dogtoy, kImageSources, 'dogtoy')



                if dogtoy is None:

                    # Didn't find anything, keep searching.

                    continue



                # If we have already dropped the toy off, make sure it has moved a sufficient amount before

                # picking it up again

                if vision_tform_hand_at_drop is not None and pose_dist(

                        vision_tform_hand_at_drop, vision_tform_dogtoy) < 0.5:

                    print('Found dogtoy, but it hasn\'t moved.  Waiting...')

                    time.sleep(1)

                    continue



                print('Found dogtoy...')



                # Got a dogtoy.  Request pick up.



                # Walk to the object.

                walk_rt_vision, heading_rt_vision = compute_stand_location_and_yaw(

                    vision_tform_dogtoy, robot_state_client, distance_margin=1.0)



                se2_pose = geometry_pb2.SE2Pose(

                    position=geometry_pb2.Vec2(x=walk_rt_vision[0], y=walk_rt_vision[1]),

                    angle=heading_rt_vision)

                move_cmd = RobotCommandBuilder.synchro_se2_trajectory_command(

                    se2_pose, frame_name=frame_helpers.VISION_FRAME_NAME,

                    params=get_walking_params(0.5, 0.5))

                end_time = 5.0

                cmd_id = command_client.robot_command(command=move_cmd,

                                                      end_time_secs=time.time() + end_time)



                # Wait until the robot reports that it is at the goal.

                block_for_trajectory_cmd(command_client, cmd_id, timeout_sec=5)



                # The ML result is a bounding box.  Find the center.

                (center_px_x, center_px_y) = find_center_px(dogtoy.image_properties.coordinates)



            # Wait for the carry command to finish

            time.sleep(0.75)



            person = None

            while person is None:

                # Find a person to deliver the toy to

                person, image, vision_tform_person = get_obj_and_img(

                    network_compute_client, options.ml_service, options.person_model,

                    options.confidence_person, kImageSources, 'person')



            # We now have found a person to drop the toy off near.

            drop_position_rt_vision, heading_rt_vision = compute_stand_location_and_yaw(

                vision_tform_person, robot_state_client, distance_margin=2.0)



            wait_position_rt_vision, wait_heading_rt_vision = compute_stand_location_and_yaw(

                vision_tform_person, robot_state_client, distance_margin=3.0)



            # Tell the robot to go there



            # Limit the speed so we don't charge at the person.

            se2_pose = geometry_pb2.SE2Pose(

                position=geometry_pb2.Vec2(x=drop_position_rt_vision[0],

                                           y=drop_position_rt_vision[1]), angle=heading_rt_vision)

            move_cmd = RobotCommandBuilder.synchro_se2_trajectory_command(

                se2_pose, frame_name=frame_helpers.VISION_FRAME_NAME,

                params=get_walking_params(0.5, 0.5))

            end_time = 5.0

            cmd_id = command_client.robot_command(command=move_cmd,

                                                  end_time_secs=time.time() + end_time)



            # Wait until the robot reports that it is at the goal.

            block_for_trajectory_cmd(command_client, cmd_id, timeout_sec=5)



            print('Arrived at goal, dropping object...')



            time.sleep(1)



            print('Backing up and waiting...')



            # Back up one meter and wait for the person to throw the object again.

            se2_pose = geometry_pb2.SE2Pose(

                position=geometry_pb2.Vec2(x=wait_position_rt_vision[0],

                                           y=wait_position_rt_vision[1]),

                angle=wait_heading_rt_vision)

            move_cmd = RobotCommandBuilder.synchro_se2_trajectory_command(

                se2_pose, frame_name=frame_helpers.VISION_FRAME_NAME,

                params=get_walking_params(0.5, 0.5))

            end_time = 5.0

            cmd_id = command_client.robot_command(command=move_cmd,

                                                  end_time_secs=time.time() + end_time)



            # Wait until the robot reports that it is at the goal.

            block_for_trajectory_cmd(command_client, cmd_id, timeout_sec=5)





def compute_stand_location_and_yaw(vision_tform_target, robot_state_client, distance_margin):

    # Compute drop-off location:

    #   Draw a line from Spot to the person

    #   Back up 2.0 meters on that line

    vision_tform_robot = frame_helpers.get_a_tform_b(

        robot_state_client.get_robot_state().kinematic_state.transforms_snapshot,

        frame_helpers.VISION_FRAME_NAME, frame_helpers.GRAV_ALIGNED_BODY_FRAME_NAME)



    # Compute vector between robot and person

    robot_rt_person_ewrt_vision = [

        vision_tform_robot.x - vision_tform_target.x, vision_tform_robot.y - vision_tform_target.y,

        vision_tform_robot.z - vision_tform_target.z

    ]



    # Compute the unit vector.

    if np.linalg.norm(robot_rt_person_ewrt_vision) < 0.01:

        robot_rt_person_ewrt_vision_hat = vision_tform_robot.transform_point(1, 0, 0)

    else:

        robot_rt_person_ewrt_vision_hat = robot_rt_person_ewrt_vision / np.linalg.norm(

            robot_rt_person_ewrt_vision)



    # Starting at the person, back up meters along the unit vector.

    drop_position_rt_vision = [

        vision_tform_target.x + robot_rt_person_ewrt_vision_hat[0] * distance_margin,

        vision_tform_target.y + robot_rt_person_ewrt_vision_hat[1] * distance_margin,

        vision_tform_target.z + robot_rt_person_ewrt_vision_hat[2] * distance_margin

    ]



    # We also want to compute a rotation (yaw) so that we will face the person when dropping.

    # We'll do this by computing a rotation matrix with X along

    #   -robot_rt_person_ewrt_vision_hat (pointing from the robot to the person) and Z straight up:

    xhat = -robot_rt_person_ewrt_vision_hat

    zhat = [0.0, 0.0, 1.0]

    yhat = np.cross(zhat, xhat)

    mat = np.matrix([xhat, yhat, zhat]).transpose()

    heading_rt_vision = math_helpers.Quat.from_matrix(mat).to_yaw()



    return drop_position_rt_vision, heading_rt_vision





def pose_dist(pose1, pose2):

    diff_vec = [pose1.x - pose2.x, pose1.y - pose2.y, pose1.z - pose2.z]

    return np.linalg.norm(diff_vec)





def get_walking_params(max_linear_vel, max_rotation_vel):

    max_vel_linear = geometry_pb2.Vec2(x=max_linear_vel, y=max_linear_vel)

    max_vel_se2 = geometry_pb2.SE2Velocity(linear=max_vel_linear, angular=max_rotation_vel)

    vel_limit = geometry_pb2.SE2VelocityLimit(max_vel=max_vel_se2)

    params = RobotCommandBuilder.mobility_params()

    params.vel_limit.CopyFrom(vel_limit)

    return params





if __name__ == '__main__':

    if not main(sys.argv[1:]):

        sys.exit(1)
