from bosdyn.client import create_standard_sdk
from bosdyn.client.robot import Robot

# Set Spot's IP address
SPOT_IP = "192.168.80.3"

# Path to your public key file
SSH_KEY_PATH = r"####################"

def upload_ssh_key():
    # Create the SDK
    sdk = create_standard_sdk("spot_ssh_key_uploader")
    robot = sdk.create_robot(SPOT_IP)

    # Authenticate with Spot (default password)
    username = "Fill in username"
    password = "Fill in password"
    robot.authenticate(username, password)

    # Read your public key
    with open(SSH_KEY_PATH, "r") as key_file:
        public_key = key_file.read()

    # Upload the key as an operator comment
    robot.operator_comment("Uploading SSH Key")
    robot.operator_comment(f"SSH Key: {public_key}")

    print("SSH Key uploaded successfully!")

if __name__ == "__main__":
    upload_ssh_key()
