from stepper_leo_v2 import stepper
from gpiozero import Button
import cv2
import time
from google_spreadsheet import submitLogtoSheet
import numpy as np

## Initialize USB camera & QR detector
cap = cv2.VideoCapture(0)           # Initialize camera
detector = cv2.QRCodeDetector()     # Initialize QR code detector

## Pinout setup
pulse_pin = 14
direction_pin = 15
enable_pin = 18
front_limit = Button(5)
back_limit = Button(6)

## Process parameters
delay = 0.001               # Time (s) elasped between pulse state change

## Initialize belt/stepper motor control
belt = stepper(pulse_pin, direction_pin, enable_pin, delay)

width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) 
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
center = (width//2, height//2)
center_tolerance = 10 # pixels
print("Camera frame: ", width, "x", height)
print("Center at ", center)

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
        forward_count = 0
        while back_limit.is_pressed:
            belt.backward(step=10)
        while front_limit.is_pressed:
            belt.forward(step=10)
            forward_count += 10
        belt.backward(step=forward_count//2)
        print("Belt-centered, Belt length: ", forward_count, " [steps]")
        return
    
    elif decoded_string == "backwardStop":
        while back_limit.is_pressed:
            belt.backward(step=10)
        print("Reached the back-limit")
        return
                
    elif decoded_string == "forwardStop":
        while front_limit.is_pressed:
            belt.forward(step=10)
        print("Reached the front-limit")
        return
    
    elif decoded_string == "centerCam":
        buffer_clear(clear_time=2)
        center_of_camera()
        
    else:
        print("This command is not registered")

def center_of_camera(calibrating_steps = 200):
    try:
        global img
        _, img = cap.read()
        cv2.imshow("Camera", img)
        x0,y0 = center_object(img)
        print("(x0,y0) = (", x0, ",", y0, ")")
        if x0 < center[0] - center_tolerance:
            belt.backward(step=calibrating_steps)     
        elif x0 > center[0] + center_tolerance:
            belt.forward(step=calibrating_steps)
        
        buffer_clear(clear_time=1)
        _, img = cap.read()
        x1,y1 = center_object(img)
        print("(x1,y1) = (", x1, ",", y1, ")")
        step_per_pixel = calibrating_steps/abs(x1-x0)  
        print("Stepping Coeffcient = ", step_per_pixel, " [stp/px]")
        
        if x1 < center[0] - center_tolerance:
            belt.backward(step=round((center[0] - x1)*step_per_pixel))     
        elif x1 > center[0] + center_tolerance:
            belt.forward(step=round((x1 - center[0])*step_per_pixel))
            
        show_afterCentered((0,255,0), (0,0,255), "Centered-cam")
    
    except:
        print("try to adjust the camera")
        
def center_object(img):
    try:
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_bound = np.array([90, 120, 25])
        upper_bound = np.array([120, 255, 180]) # HSV (min,min,min) - (max,max,max) : (0,0,0) - (180,255,255)
        mask = cv2.inRange(hsv, lower_bound, upper_bound)
        kernel = np.ones((7,7), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)
            
            M = cv2.moments(contour)
            if M['m00'] != 0.0:
                x = int(M['m10']/M['m00'])
                y = int(M['m01']/M['m00'])
            print("Found a shape of ", len(approx), "vertices at (", x, ",", y, ")")
        return x,y
    except:
        return "cannot detect object"

def show_afterCentered(line_color_code, dot_color_code, name):
    buffer_clear(clear_time=0.5)
    _, img = cap.read()
    x2,y2 = center_object(img)
    cv2.line(img, (0,center[1]), (width-1,center[1]), line_color_code, 2)
    cv2.line(img, (center[0],0), (center[0],height-1), line_color_code, 2)
    cv2.circle(img, (x2,y2), 5, dot_color_code, -1)
    cv2.imshow("Centered-cam", img)

def decode_QR(image):
    try:
        decoded_command, bbox, _ = detector.detectAndDecode(image) 
        if decoded_command:
            print("DECODE COMMAND: ", decoded_command)
            return decoded_command
    except:
        print("cannot read QR code.")

def buffer_clear(clear_time=2):
    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        if not video_capture():
            break
        if elapsed_time > clear_time:
            break

def camera_alternative():
    while True:
        ## If we press "q" while on camera window, it will exit the program
        if not video_capture():
            break
        decoded_command, bbox, _ = detector.detectAndDecode(img) 
        ## Check if there is a QRCode in the image
        if decoded_command:
            print("DECODE COMMAND: ", decoded_command)
            submitLogtoSheet(decoded_command, "QR (Camera)")
            QR_condition_control(decoded_command)
            ## Cooldown between QR code command executions
            buffer_clear(clear_time=2)