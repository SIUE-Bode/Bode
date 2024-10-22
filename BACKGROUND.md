# Background Documentation for BODe
## SPOT Identification
- Model: Explorer
- S/N: spot-BD-10740003
- P/N: 02-040236-001
- PDB S/N: a2-20416-0001
- SIUE ID: E891632
- IP Address: https://192.168.80.3
- Core I/O IP Address: 192.168.80.3:21443
## Operations
### Start-Up Procedure
SPOT:
1)	Press & Hold the Power button
2)	Wait until fans turn off and rainbow status lights start blinking
	- Power on Controller
3)	Press Motor Lockout button (will light up Red)
![Controller](https://github.com/user-attachments/assets/3a06b317-98c6-480f-bfcd-eb4d70d69a02)

Controller:
1)	Power on controller and open BD (Spot) App
2)	Select SPOT Network: spot-BD-10740003
3)	Enter Username & Password
4)	Select Operate

API:
1)	A
2)	B
3)	C
4)	D

### Controlling SPOT
Controller:
1)	Select Walk from action menu. If Spot is sitting, it will stand up.
2)	Use the right joystick to turn Spot.
3)	Use left joystick to move Spot’s body forward, backward, right, and left.
4)	To stop movement, release fingers from joysticks

API:
1)	A
2)	B
3)	C
4)	D
### Shutdown Procedure
SPOT:
1)	Sit Spot (laying on the ground)
2)	Power off motors with controller
3)	Press Motor Lockout button (no light)
4)	Press and Hold Power button

Controller/Tablet:
1)	Power off motors when directed
2)	Close BD (Spot) App
3)	Power off controller

API:
1)	A
2)	B
3)	C
4)	D
## Updates
### Updating Software
![Update Warning](https://github.com/user-attachments/assets/07e04fa9-eb57-4ed2-8553-18d6811303ac)

#### Boston Dynamics recommends that you: 
-	Update Spot and each controller to the latest software version as soon as it becomes available.
-	Keep each payload updated to the latest available software version for that payload.
-	Keep each controller's operating system and firmware up to date.

Check Software Version:
1)	Power on SPOT and login to Controller
2)	Press the Menu bars (top left of screen)
3)	Select “About” tab
4)	Verify that SPOT software version matches the controller’s (Ex. V4.0.1 = V4.0.1)

SPOT Software Update:
1)	You will need a computer with ethernet capability and an ethernet cable
2)	Verify the current software version for SPOT (Skipping updates may cause failures)
3)	Navigate to SPOT Software Download Page and login with a Boston Dynamics account
4)	Download the .bde file for the version that directly follows SPOT’s current version
5)	Connect the Power Supply directly to SPOT, this is considered Shore Power
6)	Connect the computer to SPOT with the ethernet cable

Controller/Tablet Software Update:
1)	Ensure that SPOT has been updated before you update the controller
2)	After SPOT is updated, the controller will prompt you to update upon login
3)	Select the update prompt and wait for update to finish 
