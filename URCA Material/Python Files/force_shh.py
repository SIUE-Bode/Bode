from bosdyn.client import create_standard_sdk
from bosdyn.client.robot import Robot

SPOT_IP = "192.168.80.3"
USERNAME = "#######"
PASSWORD = "#############"

def force_activate_ssh():
    sdk = create_standard_sdk("spot_force_ssh")
    robot = sdk.create_robot(SPOT_IP)
    robot.authenticate(USERNAME, PASSWORD)

    robot.operator_comment("Force activating SSH Key")
    print("SSH Key force activated")

if __name__ == "__main__":
    force_activate_ssh()
