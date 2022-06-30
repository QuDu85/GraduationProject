from collections import deque
from pathlib import Path
import keras
import numpy as np
import PIL
import cv2

image_size = (299,299)
window_size = 3
model_path = "C:\\Users\\admin\\Desktop\\Projects\\Project_Final\\Model\\nsfw.299x299.h5" 
lb = ['drawings', 'hentai', 'neutral', 'porn', 'sexy']

def predict_video(video):
    label = None
    safe = True
    total_per_label = [0,0,0,0]
    start = 0

    # initialize the video stream, pointer to output video file, and
    # frame dimensions
    vs = cv2.VideoCapture(video)
    Q = deque(maxlen=window_size)

    print("Loading model")
    model = keras.models.load_model(model_path)

    # loop over frames from the video file stream
    while True:
        start +=1
        # read the next frame from the file
        (grabbed, frame) = vs.read()

        # if the frame was not grabbed, then we have reached the end
        # of the stream
        if not grabbed:
            break

        # clone the output frame, then convert it from BGR to RGB
        # ordering, resize the frame to a fixed 224x224, and then
        # perform mean subtraction
        frame = cv2.resize(frame, image_size).astype("float32")
        frame /= 255
        
        # make predictions on the frame and then update the predictions
        # queue
        preds = model.predict(np.expand_dims(frame, axis=0))[0]
        Q.append(preds)

        # perform prediction averaging over the current history of
        # previous predictions
        results = np.array(Q).mean(axis=0)
        i = np.argmax(results)
        if i!=0 and i!=2 and start>=window_size:
            safe = False
            label = lb[i]
            break
        total_per_label[i]+=1
    
    #get the largest safe category in vid
    if label is None:
        i = np.argmax(total_per_label)
        label = lb[i]

    print("Video processed: ",video)

    return safe, label
