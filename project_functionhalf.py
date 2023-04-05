import stepper_leo
from gpiozero import Button
import cv2
import sys
import time
from time import sleep
from google_spreadsheet import submitLogtoSheet
## Initialize USB camera & QR detector
cap = cv2.VideoCapture(0)           # Initialize camera
detector = cv2.QRCodeDetector()     # Initialize QR code detector
## Pinout setup
pulse_pin = 14
direction_pin = 15
enable_pin = 18
front_limit = Button(27)
back_limit = Button(26)

## Process parameters
delay = 0.0012             # Time (s) elasped for holding each pulse
sleep_step = 0.1          # If continuous=False, we use this as wait time before next step
buffer_clear_time = 2       # This prevent too rapidly read same QR code, set to 2 secs

## Initialize belt/stepper motor control
belt = stepper_leo.stepper(pulse_pin, direction_pin, enable_pin,
                           delay, sleep_step)
width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) 
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
center = (width//2, height//2)
class funcmove:
    def forward(self):
        while True:
            if front_limit.is_pressed:
                belt.stop()
                print("The object has reached the frontlimit")
                break
            else:
                belt.forward(step=1, continuous=True)
                print("Moving the object forward until reach the limit")

    def backward(self):
        while True:
            if back_limit.is_pressed:
                belt.stop()
                print("The object has reached the back limit")
                break
            else:
                belt.backward(step=1, continuous=True)
                print("Moving the object backward until reach the limit")

def forwardtimer(x):
    t = time.perf_counter()
    while t < x:
        belt.forward(step=1, continuous=True)
            
def backwardtimer(x):
    t = time.perf_counter()
    while t < x:
        belt.backward(step=1, continuous=True)

def video_capture():
    global success, img
    success, img = cap.read()
    cv2.imshow("Camera", img)
    ## exit program if we press "q" on the keyboard while in camera window
    if cv2.waitKey(1) == ord("q"):
        belt.stop()
        return False
    return True

def QR_condition_control(decoded_string):
    if decoded_string == "center":
        funcmove.backward()
        funcmove.forward()
        belt.backward(step=350 ,continuous=True)
    elif decoded_string == "centerbelt":
        funcmove.forward()
        tic1 = time.perf_counter()
        funcmove.backward()
        toc1 = time.perf_counter()
        x1 = (tic1-toc1)
        funcmove.forward()
        backwardtimer(x1/2)
    elif decoded_string == "backwardStop":
        funcmove.backward()
    elif decoded_string == "forwardStop":
        funcmove.forward()
    elif decoded_string == "centerCam":
        center_of_camera()
    else:
        print("This decoded command is not registered")
        
def center_of_camera():
    _ = video_capture()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # setting threshold of gray image
    _, threshold = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY) 
    # using a findContours() function
    contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    i = 0
    # list for storing names of shapes
    for contour in contours:
        # here we are ignoring first counter because 
        # findcontour function detects whole image as shape
        if i == 0:
            i = 1
            continue
        # cv2.approxPloyDP() function to approximate the shape
        approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)
        # using drawContours() function
        cv2.drawContours(img, [contour], 0, (0, 0, 255), 5)
        # finding center point of shape
        M = cv2.moments(contour)
        if M['m00'] != 0.0:
            x = int(M['m10']/M['m00'])
            y = int(M['m01']/M['m00'])
        # putting shape name at center of each shape
        while not (width//2) - 10 <= x <=(width//2) + 10:
            M = cv2.moments(contour)
            if M['m00'] != 0.0:
                x = int(M['m10']/M['m00'])
                y = int(M['m01']/M['m00'])
            if len(approx) == 3:
                cv2.putText(img, 'Triangle', (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            elif len(approx) == 4:
                cv2.putText(img, 'Quadrilateral', (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            elif len(approx) == 5:
                cv2.putText(img, 'Pentagon', (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            elif len(approx) == 6:
                cv2.putText(img, 'Hexagon', (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            else:
                cv2.putText(img, 'circle', (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            ## move object to center of camera
            if 0 <= x < (width//2) - 10:
                forwardtimer(1) ## still unreliable
            elif width >= x > (width//2) + 10:
                backwardtimer(1) ## still unreliable
        belt.stop()
        
def decode_QR(image):
    ## Detect and Decode
    decoded_command, bbox, _ = detector.detectAndDecode(image) 
    
    ## Check if there is a QRCode in the image
    if decoded_command:
        print("DECODE COMMAND: ", decoded_command)
        return decoded_command

def camera_main():
    while True:
        ## Capture & Show a captured frame from USB camera
        ## If we press "q" while on camera window, it will exit the program
        if not video_capture():
            break
        
        ## Check if there is a QRCode in the image
        ## If QRcode found, return the decoded command
        command = decode_QR(img)
        if command:
            return command

def camera_alternative():
    while True:
        ## Capture & Show a captured frame from USB camera
        ## If we press "q" while on camera window, it will exit the program
        if not video_capture():
            break
        
        ## Detect and Decode
        decoded_command, bbox, _ = detector.detectAndDecode(img) 
        
        ## Check if there is a QRCode in the image
        if decoded_command:
            print("DECODE COMMAND: ", decoded_command)
            submitLogtoSheet(decoded_command, "QR (Camera)")
            QR_condition_control(decoded_command)
            ## Cooldown between QR code command executions
            start_time = time.time()
            while True:
                elapsed_time = time.time() - start_time
                if not video_capture():
                    break
                if elapsed_time > buffer_clear_time:
                    break

### Only run below code when this program is execute directly, not imported as a module
if __name__ == '__main__':
    camera_main()
    sys.exit()
