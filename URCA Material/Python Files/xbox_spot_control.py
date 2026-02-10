import pygame
import time
import bosdyn.client.lease
from bosdyn.client import create_standard_sdk
from bosdyn.client.robot_command import RobotCommandClient, RobotCommandBuilder
from bosdyn.client.lease import LeaseClient
from bosdyn.client.estop import EstopClient, EstopEndpoint
from bosdyn.client.power import PowerClient

# Spot Configuration - Change IP and Credentials
SPOT_IP = "192.168.80.3"  # Replace with Spot’s IP
USERNAME = "#####"  # Replace with Spot’s username
PASSWORD = "#####"  # Replace with Spot’s password

# Initialize SDK and connect to Spot
sdk = create_standard_sdk('XboxControllerSpot')
robot = sdk.create_robot(SPOT_IP)
robot.authenticate(USERNAME, PASSWORD)
robot.time_sync.wait_for_sync()

# Create clients
command_client = robot.ensure_client(RobotCommandClient.default_service_name)
lease_client = robot.ensure_client(LeaseClient.default_service_name)
estop_client = robot.ensure_client(EstopClient.default_service_name)
power_client = robot.ensure_client(PowerClient.default_service_name)

# Obtain a lease to control Spot
try:
    lease = lease_client.take()  # Take control of Spot
    lease_keepalive = bosdyn.client.lease.LeaseKeepAlive(lease_client)  # Maintain lease
    print("Lease acquired successfully.")
except bosdyn.client.lease.ResourceAlreadyClaimedError as e:
    print(f"Failed to take lease: {e}")
    exit(1)  # Exit if lease cannot be taken

# Establish E-Stop endpoint to ensure Spot is safe
estop_endpoint = EstopEndpoint(estop_client, 'Xbox_Controller', estop_timeout=5.0)
estop_endpoint.force_simple_setup()
estop_endpoint.allow()

# Power on Spot if not already on
if not robot.is_powered_on():
    print("Powering on Spot...")
    robot.power_on()  # Corrected method
    robot.wait_until_powered_on(timeout_sec=20)
    print("Spot is now powered on.")

# Initialize Pygame for Xbox Controller
pygame.init()
pygame.joystick.init()

# Check if Xbox controller is connected
if pygame.joystick.get_count() == 0:
    print("No controller detected. Connect an Xbox One controller and try again.")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Connected to: {joystick.get_name()}")

# Main loop for controller input
try:
    while True:
        pygame.event.pump()

        # Read joystick values
        left_x = joystick.get_axis(0)  # Strafe left/right
        left_y = -joystick.get_axis(1)  # Forward/backward (inverted)
        right_x = joystick.get_axis(2)  # Turn left/right

        # Scale movement speed (adjust as needed)
        speed = 0.5
        cmd = RobotCommandBuilder.synchro_velocity_command(
            v_x=speed * left_y, v_y=speed * left_x, v_rot=speed * right_x
        )

        # Send movement command to Spot
        command_client.robot_command(cmd)

        # Check for controller button presses
        if joystick.get_button(0):  # 'A' button makes Spot sit
            print("Sit Command Sent")
            sit_cmd = RobotCommandBuilder.synchro_sit_command()
            command_client.robot_command(sit_cmd)

        if joystick.get_button(1):  # 'B' button makes Spot stand
            print("Stand Command Sent")
            stand_cmd = RobotCommandBuilder.synchro_stand_command()
            command_client.robot_command(stand_cmd)

        if joystick.get_button(7):  # 'Start' button to quit
            print("Exiting control loop...")
            break

        time.sleep(0.1)  # Short delay to prevent excessive commands

except KeyboardInterrupt:
    print("\nStopping control...")

finally:
    print("Releasing Spot lease and stopping control...")
    lease_keepalive.shutdown()
    estop_endpoint.stop()
