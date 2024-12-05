# Playing fetch with Bode
Bode can be commanded to find and pickup a toy ball and then bring it to a human. Using image recognition, BOde identifies the ball and walks to its location. With an external arm connected to the CORE I/O's GPIO ports, Bode picks up the ball from the previously identified location. Once again using image recognition, Bode finds a human, walks to them, and drops the ball next to them.

Much of the inspiration for this portion of the project was derived from the Boston Dynamics [fetch tutorial](https://dev.bostondynamics.com/docs/python/fetch_tutorial/fetch1).
## Ball Recognition
A ball with multiple high contrast colors was selected because it will be easier for Bode to recognize. Bode is not able to fetch for anything else.

<img src="https://github.com/user-attachments/assets/d88bc860-8cd4-4a3a-8df0-f10f58e2c98e" alt="dogtoy" width="400"/>

To be able to identify the ball, first training data is collected. Spot was used to capture images which include the ball placed in different locations taken from various angles. These images were then processed with the labelImg python package. A bounding box is drawn around the ball on the image by the user. This box along with the image will be used to train the machine learning model to identify the ball.

<img src="https://github.com/user-attachments/assets/3e038394-df52-4243-81b7-7247ddc7f104" alt="Bounding box being drawn around dogtoy" width="600"/>

These training data are then fed into tensorflow along with a pretrained multi-purpose model to create a model which can effectively identify the ball.
