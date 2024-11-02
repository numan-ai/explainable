import time

import explainable
from explainable import widget, source

explainable.init(wait_client=True, enable_history=False)


size = 50

from dataclasses import dataclass

@dataclass
class Screen:
    image: list[list[str]] 

width = 480
height = 320
scale = 0.3
screen = Screen([["#000"]*int(width * scale)]*int(height * scale))
print(len(screen.image[0]), len(screen.image))
screen = explainable.observe("view1", screen, widget=widget.VerticalListWidget(
  source=source.Reference("item.image"),
  item_widget=widget.ListWidget(item_widget=widget.TileWidget(
    height=source.Number(size),#source.Reference("item"),
    width=source.Number(size),
    color=source.Reference("item"),
   ),
  )
 )
)


import cv2
import numpy as np

def extract_frames_as_lists(video_path):
    cap = cv2.VideoCapture(video_path)
    
    skip_frame = 50000
    print(f"Frames per second: {skip_frame}")
    
    frame_count = 0
    frames_as_lists = []

    ret, frame = cap.read()
    frame_as_list = frame.tolist()
    frame_as_list = [line[::int(1 / scale)] for line in frame_as_list[::int(1 / scale)]]

    screen.image = [["#f00" if pixel == [0,0,0] else "#fff" for pixel in line] for line in frame_as_list]

    empty_pixel = [0, 0, 0]

    # print('pause')
    # time.sleep(5)
    # print('unpause')

    while True:
        print(f"Reading frame {frame_count}")
        ret, frame = cap.read()
        
        # if frame_count == 5:
        #     break

        if not ret:
            break
    
        
        if frame_count % skip_frame != 0:
            frame_as_list = frame.tolist()
            frame_as_list = [line[::int(1 / scale)] for line in frame_as_list[::int(1 / scale)]]

            for y, line in enumerate(frame_as_list):
                for x, pixel in enumerate(line):
                    old_value = screen.image[y][x]
                    new_value = "#f00" if pixel == empty_pixel else "#fff"
                    if old_value != new_value:
                        screen.image[y][x] = new_value

            # for i, line in enumerate(frame_as_list):
            #     screen.image[i] = ["#000000" if pixel == [0,0,0] else "#ffffff" for pixel in line]

            # screen.image = [["#000000" if pixel == [0,0,0] else "#ffffff" for pixel in line] for line in frame_as_list]
            
        time.sleep(0.01)

        frame_count += 1
        explainable.server.force_update()
    
    cap.release()
    print("Done extracting frames.")
    return frames_as_lists

# Example usage
video_path = 'bad_apple.mp4'
frames = extract_frames_as_lists(video_path)

#print("The sorted list is : " + str(test_list))
