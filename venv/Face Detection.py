import cv2 as cv
import PySimpleGUI as sg
import os
from datetime import datetime
import time
import face_recognition

# Capture video from webcam
cap = cv.VideoCapture(0)

# Set theme of GUI
sg.theme('TanBlue')

# Set layout of GUI
rgb_column = [
    [
        sg.Text('R:  ', pad=((40, 0), 3)),
        sg.Slider(key='red_slider', range=(-180, 180), default_value=0, orientation='h', size=(60, 15))
    ],
    [
        sg.Text('G:  ', pad=((40, 0), 3)),
        sg.Slider(key='green_slider', range=(-180, 180), default_value=0, orientation='h', size=(60, 15))
    ],
    [
        sg.Text('B:  ', pad=((40, 0), 3)),
        sg.Slider(key='blue_slider', range=(-180, 180), default_value=0, orientation='h', size=(60, 15))
    ],
    [
        sg.Button('Reset Colors', size=(10, 1), focus=False, pad=((40, 0), 3))
    ]
]

layout = [
    [
        sg.Image(filename='', key='image', pad=(0, 0)),
        sg.Image(filename='', key='flip', pad=(0, 0))],
    [
        sg.Button('Snap', size=(8, 1), focus=False, pad=((296, 0), 3))
    ],
    [
        sg.Checkbox('Detect Face', key='d_face', pad=((40, 0), 3)),
        sg.Checkbox('Mirror', key='flip_box'),
        sg.Checkbox('Black and White', key='b_w')
    ],
    [
        sg.Column(rgb_column, key='rgb_tools')
    ],
    [
        sg.Text('Save Name:  ', pad=((40, 0), 3)),
        sg.Input(key='save_name', size=(20, 1))
    ],
    [
        sg.Text('Save Dimensions: Height: ', pad=((40, 0), 3)),
        sg.Input(key='save_height', size=(5, 1), default_text='480'),
        sg.Text('Width: '),
        sg.Input(key='save_width', size=(5, 1), default_text='640')
    ],
    [
        sg.Text('Save Path', size=(8, 1), pad=((40, 0), 3)),
        sg.Input(key='save_path'),
        sg.FolderBrowse(size=(8, 1)),
        sg.Exit('Exit', size=(8, 1))
    ]
]

# GUI settings
window = sg.Window('Face Detection', location=(100, 100), no_titlebar=True)

# Apply layout to window
window.layout(layout).Finalize()

# Set size of window in pixels
window.Size = (640, 800)


# Time function for title of saved pictures
def get_time():
    return datetime.now().strftime("%D_%I.%M.%S").replace('/', '-')


# Function to save photo to snap_path
def snap(capture_frame):
    # Name for saved files
    save_name = window.find_element('save_name').Get()

    # Path for saved photos
    snap_path = window.find_element('save_path').Get()

    # Dimensions for saved photo
    snap_x = window.find_element('save_width').Get()
    snap_y = window.find_element('save_height').Get()

    if snap_path == '':
        sg.popup('Error', 'You must select a folder to save photos.')
    elif not snap_x or not snap_y:
        sg.popup('Error', 'You must enter dimensions for the photos.\nDefault: H=480 W=640')
    else:
        capture_frame = cv.resize(capture_frame,
                                  (int(snap_x), int(snap_y)),
                                  interpolation=cv.INTER_CUBIC)
        img_name = '{}{}.png'.format(save_name, get_time())
        print(img_name)
        cv.imwrite(os.path.join(snap_path, img_name), capture_frame)
        time.sleep(1)


#Function to control RGB sliders
def rgb_sliders(color, slider_val):
    if slider_val >= 0:
        return color + slider_val
    else:
        return color - abs(slider_val)


#Function to reset RGB sliders
def reset_sliders():
    window['red_slider'].Update(0)
    window['green_slider'].Update(0)
    window['blue_slider'].Update(0)


# Button dictionary
button_dictionary = {'Snap': snap,
                     'reset_sliders': reset_sliders}

# Booleans for buttons/switches
flip_bool = False
detect_face = False
update_gui = False

# Check for webcam connection
if not cap.isOpened():
    sg.popup('Error', 'No webcam found. Closing.')
else:
    # Continuously update the window with the current frame
    while True:
        event, values = window.read(timeout=20)

        # Exit loop if button is pressed
        if event in ('Exit', None):
            if flip_bool:
                flip_bool = False
            else:
                break

        # Store web cam data as a frame
        ret, frame = cap.read()
        rgb_frame = frame[:, :, ::-1]

        # Handle Black and White checkbox
        if window.find_element('b_w').Get():
            window.find_element('rgb_tools').Update(visible=False)
            frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        else:
            window.find_element('rgb_tools').Update(visible=True)
            # Link sliders to color ranges
            blue, green, red = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
            red = rgb_sliders(red, int(values['red_slider']))
            green = rgb_sliders(green, int(values['green_slider']))
            blue = rgb_sliders(blue, int(values['blue_slider']))
            frame = cv.merge((blue, green, red))

        # Handle face detection checkbox
        if window.find_element('d_face').Get():

            # Get coordinates of detected face
            face_locations = face_recognition.face_locations(rgb_frame)

            # If a face is found, crop and resize to the location of the face
            if face_locations:
                frame = cv.resize(frame[face_locations[0][0]:face_locations[0][2],
                                  face_locations[0][3]:face_locations[0][1]],
                                  (640, 480),
                                  interpolation=cv.INTER_CUBIC)

        # Change image data to bytes and update the GUI with the image bytes and handle image flip
        if window.find_element('flip_box').Get():
            if not update_gui:
                window['Snap'].Update(visible=False)
                update_gui = True
            frame_left = frame[0:480, :320]
            frame_right = cv.flip(frame[0:480, 0:320], 1)
            imgbytes = cv.imencode('.png', frame_left)[1].tobytes()
            flipbytes = cv.imencode('.png', frame_right)[1].tobytes()
            window['flip'].Update(data=flipbytes)
            window['image'].Update(data=imgbytes)
        else:
            if update_gui:
                window['Snap'].Update(visible=True)
                window['Exit'].Update('Exit')
                update_gui = False
            imgbytes = cv.imencode('.png', frame)[1].tobytes()
            window['image'].Update(data=imgbytes)

        # Actions for buttons
        if event == 'Snap':
            snap(frame)
        if event == 'Flip':
            flip_bool = True
        if event == 'Detect Face':
            detect_face = True
        if event == "Reset Colors":
            reset_sliders()
