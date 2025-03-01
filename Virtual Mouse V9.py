import cv2
import mediapipe as mp
import pyautogui
import math
from PyInstaller.compat import system
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

# Set fail-safe to False to prevent the fail-safe mechanism from triggering
pyautogui.FAILSAFE = False


class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.orientation = 'vertical'

        self.control_button = Button(text='Control with Face')
        self.control_button.bind(on_press=self.toggle_control)
        self.add_widget(self.control_button)

        self.control_with_eye_button = Button(text='Control with Eye')
        self.control_with_eye_button.bind(on_press=self.toggle_control_eye)
        self.add_widget(self.control_with_eye_button)

        self.exit_button = Button(text='Exit')
        self.exit_button.bind(on_press=self.exit)
        self.add_widget(self.exit_button)

        self.is_control_active = False
        self.is_control_active_eye = False

        self.cam = cv2.VideoCapture(0)
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
        self.screen_w, self.screen_h = pyautogui.size()

        # Set default sensitivity factors for face control
        self.sensitivity_factor = 6
        self.diagonal_sensitivity_factor = 8

        # Initialize variables for EMA filter for face control
        self.alpha = 0.2
        self.prev_x = None
        self.prev_y = None

        # Counter for face visibility check
        self.face_not_visible_counter = 0
        self.max_face_not_visible_frames = 100  # Adjust this value according to your requirements

        # Flag for tracking teeth visibility and left click
        self.is_teeth_visible = False
        self.is_left_click_active = False

        # Flag for tracking tongue visibility and right click
        self.is_tongue_visible = False
        self.is_right_click_active = False

    def toggle_control(self, instance):
        if not self.is_control_active:
            self.is_control_active = True
            self.face_not_visible_counter = 0  # Reset the counter when control starts
            self.track_face_and_nose()
        else:
            self.is_control_active = False

    def toggle_control_eye(self, instance):
        if not self.is_control_active_eye:
            self.is_control_active_eye = True
            self.face_not_visible_counter = 0  # Reset the counter when control starts
            self.control_with_eye()
        else:
            self.is_control_active_eye = False

    def track_face_and_nose(self):
        while self.is_control_active:
            _, frame = self.cam.read()
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            output = self.face_mesh.process(rgb_frame)
            landmark_points = output.multi_face_landmarks
            frame_h, frame_w, _ = frame.shape

            if landmark_points:
                self.face_not_visible_counter = 0  # Reset the counter when face is visible
                landmarks = landmark_points[0].landmark

                nose_landmark = landmarks[2]  # Nose landmark index is 2

                # Calculate nose coordinates on the screen
                screen_x = self.screen_w * nose_landmark.x
                screen_y = self.screen_h * nose_landmark.y

                # Apply EMA filter for face control
                if self.prev_x is not None and self.prev_y is not None:
                    screen_x = self.prev_x + self.alpha * (screen_x - self.prev_x)
                    screen_y = self.prev_y + self.alpha * (screen_y - self.prev_y)

                self.prev_x = screen_x
                self.prev_y = screen_y

                # Calculate diagonal distance from the center of the screen for face control
                center_x = self.screen_w / 2
                center_y = self.screen_h / 2
                delta_x = screen_x - center_x
                delta_y = screen_y - center_y
                diagonal_distance = math.sqrt(delta_x ** 2 + delta_y ** 2)

                # Adjust sensitivity for diagonal movement for face control
                if abs(delta_x) > abs(delta_y):  # Horizontal movement dominates
                    new_diagonal_distance = diagonal_distance * self.sensitivity_factor
                else:  # Vertical movement dominates
                    new_diagonal_distance = diagonal_distance * self.diagonal_sensitivity_factor

                # Calculate new screen coordinates with adjusted sensitivity for face control
                if diagonal_distance > 0:  # Avoid division by zero
                    new_screen_x = center_x + delta_x * (new_diagonal_distance / diagonal_distance)
                    new_screen_y = center_y + delta_y * (new_diagonal_distance / diagonal_distance)
                else:  # If the nose is at the center of the screen
                    new_screen_x = center_x
                    new_screen_y = center_y

                # Move cursor according to nose movement with increased sensitivity for face control
                pyautogui.moveTo(new_screen_x, new_screen_y)

                # Check for mouse clicking (e.g., detect mouth opening and teeth visibility) for face control
                if self.detect_mouth_opening(landmarks):
                    pyautogui.click(button='left')

                # Handle teeth visibility for left click
                if self.detect_teeth_visibility(landmarks):
                    if not self.is_left_click_active:  # Perform left click action only once when teeth become visible
                        pyautogui.mouseDown(button='left')
                        self.is_left_click_active = True
                else:
                    if self.is_left_click_active:  # Release left click action when teeth are no longer visible
                        pyautogui.mouseUp(button='left')
                        self.is_left_click_active = False

                # Handle tongue visibility for right click
                if self.detect_tongue_visibility(landmarks):
                    if not self.is_right_click_active:  # Perform right click action only once when tongue becomes visible
                        pyautogui.click(button='right')
                        self.is_right_click_active = True
                else:
                    if self.is_right_click_active:  # Reset right click flag when tongue is no longer visible
                        self.is_right_click_active = False

                # Draw a circle at the nose landmark position for visualization
                x = int(nose_landmark.x * frame_w)
                y = int(nose_landmark.y * frame_h)
                cv2.circle(frame, (x, y), 3, (255, 0, 0), -1)

                # Highlight the mouth area
                upper_lip_landmark = landmarks[13]
                lower_lip_landmark = landmarks[14]
                upper_lip_x = int(upper_lip_landmark.x * frame_w)
                upper_lip_y = int(upper_lip_landmark.y * frame_h)
                lower_lip_x = int(lower_lip_landmark.x * frame_w)
                lower_lip_y = int(lower_lip_landmark.y * frame_h)
                cv2.circle(frame, (upper_lip_x, upper_lip_y), 3, (0, 255, 0), -1)
                cv2.circle(frame, (lower_lip_x, lower_lip_y), 3, (0, 255, 0), -1)

                # Highlight tongue area (using the midpoint between lips as reference)
                tongue_center_x = int((upper_lip_x + lower_lip_x) / 2)
                tongue_center_y = int((upper_lip_y + lower_lip_y) / 2)
                cv2.circle(frame, (tongue_center_x, tongue_center_y), 3, (0, 0, 255), -1)

                # Add status indicators to the frame
                tongue_status = "Tongue: Detected" if self.detect_tongue_visibility(
                    landmarks) else "Tongue: Not Detected"
                cv2.putText(frame, tongue_status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            else:
                # Increment the counter when face is not visible
                self.face_not_visible_counter += 1

            # Check if face is not visible for a certain number of frames
            if self.face_not_visible_counter >= self.max_face_not_visible_frames:
                self.is_control_active = False  # Exit control if face is not visible for too long

            cv2.imshow('Face Mesh', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def detect_mouth_opening(self, landmarks):
        # Select landmark indices for mouth opening detection (upper and lower lip landmarks)
        upper_lip_index = 13
        lower_lip_index = 14

        # Get the y-coordinates of the upper and lower lip landmarks
        upper_lip_y = landmarks[upper_lip_index].y * self.screen_h
        lower_lip_y = landmarks[lower_lip_index].y * self.screen_h

        # Calculate the distance between upper and lower lip landmarks
        lip_distance = lower_lip_y - upper_lip_y

        # Set threshold for mouth opening detection (adjust according to your requirements)
        mouth_open_threshold = 10

        # Check if mouth opening is detected based on the distance between upper and lower lips
        if lip_distance > mouth_open_threshold:
            return True
        else:
            return False

    def detect_teeth_visibility(self, landmarks):
        # Select landmark indices for teeth visibility detection (upper and lower lip landmarks)
        teeth_indices = [10, 11, 12, 13, 14, 15, 16]

        # Get the y-coordinates of the teeth landmarks
        teeth_y_coordinates = [landmarks[i].y * self.screen_h for i in teeth_indices]

        # Calculate the mean y-coordinate of the teeth landmarks
        mean_teeth_y = sum(teeth_y_coordinates) / len(teeth_y_coordinates)

        # Set threshold for teeth visibility detection (adjust according to your requirements)
        teeth_visible_threshold = 5

        # Check if the mean y-coordinate of teeth landmarks is below the threshold
        if mean_teeth_y < teeth_visible_threshold:
            return True
        else:
            return False

    def detect_tongue_visibility(self, landmarks):
        # Select landmark indices for inner mouth area where tongue would be visible
        # Using mouth interior landmarks (78, 81, 178, etc.)
        inner_mouth_indices = [78, 81, 178, 13, 14]

        # Get the relevant landmarks
        upper_lip = landmarks[13]
        lower_lip = landmarks[14]

        # Calculate distance between lips
        lip_distance = (lower_lip.y - upper_lip.y) * self.screen_h

        # Get color information from around the inner mouth area to detect the tongue
        # This is a simplification - in real implementation we would need to analyze
        # the actual image pixels around these landmarks for reddish color

        # For now, we'll use a combination of mouth opening detection and a specific gesture
        # The tongue is likely visible if the mouth is open more than the minimum threshold
        # and less than a maximum threshold (wide open mouth)
        min_tongue_threshold = 15
        max_tongue_threshold = 30

        # Also check if inner mouth landmarks are positioned in a way consistent with tongue protrusion
        # This is a simplified approximation - real tongue detection would require more sophisticated image analysis
        inner_landmarks_y = [landmarks[i].y for i in inner_mouth_indices]
        inner_landmarks_variance = sum(
            (y - sum(inner_landmarks_y) / len(inner_landmarks_y)) ** 2 for y in inner_landmarks_y)

        # If mouth is open an appropriate amount and the inner landmarks have high variance
        # (suggesting something is protruding), we assume the tongue is visible
        if (min_tongue_threshold < lip_distance < max_tongue_threshold) and (inner_landmarks_variance > 0.00005):
            return True
        else:
            return False

    def control_with_eye(self):
        while self.is_control_active_eye:
            _, frame = self.cam.read()
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            output = self.face_mesh.process(rgb_frame)
            landmark_points = output.multi_face_landmarks
            frame_h, frame_w, _ = frame.shape
            if landmark_points:
                landmarks = landmark_points[0].landmark
                for id, landmark in enumerate(landmarks[474:478]):
                    x = int(landmark.x * frame_w)
                    y = int(landmark.y * frame_h)
                    cv2.circle(frame, (x, y), 3, (0, 255, 0))
                    if id == 1:
                        screen_x = self.screen_w * landmark.x
                        screen_y = self.screen_h * landmark.y
                        pyautogui.moveTo(screen_x, screen_y)
                left = [landmarks[145], landmarks[159]]
                for landmark in left:
                    x = int(landmark.x * frame_w)
                    y = int(landmark.y * frame_h)
                    cv2.circle(frame, (x, y), 3, (0, 255, 255))
                if (left[0].y - left[1].y) < 0.004:
                    pyautogui.click()
                    pyautogui.sleep(1)

                # Add tongue detection for right click in eye control mode as well
                if self.detect_tongue_visibility(landmarks):
                    if not self.is_right_click_active:
                        pyautogui.click(button='right')
                        self.is_right_click_active = True
                        pyautogui.sleep(1)  # Add delay to prevent multiple clicks
                else:
                    self.is_right_click_active = False

            cv2.imshow('Eye Controlled Mouse', frame)
            if cv2.waitKey(1) == ord('q'):
                break
        cv2.destroyAllWindows()

    def exit(self, instance):
        self.cam.release()
        cv2.destroyAllWindows()
        system.exit()


class MyApp(App):
    def build(self):
        return MainScreen()


def start_app():
    MyApp().run()


# Ensure that the Kivy app doesn't run on import
if __name__ == '__main__':
    start_app()  # Only run the app when this function is called explicitly