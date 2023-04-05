import cv2
import numpy as np

cap = cv2.VideoCapture(0)           # Initialize camera
success, img = cap.read()
cv2.imshow("Camera", img)

cv2.waitKey(0)
cv2.destroyAllWindows()

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

cv2.imshow("Camera", hsv)
cv2.waitKey(0)
cv2.destroyAllWindows()

lower_bound = np.array([100, 200, 20])
upper_bound = np.array([120, 255, 90])

mask = cv2.inRange(hsv, lower_bound, upper_bound)
cv2.imshow("Camera", mask)
cv2.waitKey(0)
cv2.destroyAllWindows()

kernel = np.ones((7,7), np.uint8)

mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
cv2.imshow("Camera", mask)
cv2.waitKey(0)
cv2.destroyAllWindows()

segmented_img = cv2.bitwise_and(img, img, mask=mask)
contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

output = cv2.drawContours(segmented_img, contours, -1, (0, 0, 255), 1)
cv2.imshow("Camera", output)
cv2.waitKey(0)
cv2.destroyAllWindows()

for contour in contours:
    approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)
    
    M = cv2.moments(contour)
    if M['m00'] != 0.0:
        x = int(M['m10']/M['m00'])
        y = int(M['m01']/M['m00'])
    cv2.circle(output, (x,y), 3, (0,0,255), -1)
    print("Found a shape of ", len(approx), "vertices")
    
cv2.imshow("Camera", output)
cv2.waitKey(0)
cv2.destroyAllWindows()