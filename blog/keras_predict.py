from collections import deque
from distutils import extension
from pathlib import Path
import keras
import numpy as np
import PIL
import cv2
import os

image_size = (299,299)
window_size = 3
exts = ['.mp4','.ts','.jpg','.jpeg','.png','.avi']
model_file = "C:\\Users\\admin\\Desktop\\Projects\\Project_Final\\Sample Web\\Django-WebApp\\django_web_app\\blog\\nsfw.299x299.h5" 
weights_file = "C:\\Users\\admin\\Desktop\\Projects\\Project_Final\\Sample Web\\Django-WebApp\\django_web_app\\blog\\weights.best_inception299.hdf5"
lb = ['drawings', 'hentai', 'neutral', 'porn', 'sexy']

def predict_video(video):
    file, ext = os.path.splitext(video)
    print(ext)
    if ext not in exts:
        print("Not a video:",video)
        return None, 'Invalid' 
    label = None
    safe = True
    total_per_label = [0,0,0,0]
    start = 0

    # initialize the video stream, pointer to output video file, and
    # frame dimensions
    vs = cv2.VideoCapture(video)
    Q = deque(maxlen=window_size)

    print("Loading model")
    model = keras.models.load_model(model_file)
    

    # Load checkpoint if one is found
    if os.path.exists(weights_file):
        print ("loading ", weights_file)
        model.load_weights(weights_file)

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
        try:
            preds = model.predict(np.expand_dims(frame, axis=0))[0]
        except:
            print("Error processin: ",video)
            return False, 'Unknown'
        Q.append(preds)

        # perform prediction averaging over the current history of
        # previous predictions
        results = np.array(Q).mean(axis=0)
        i = np.argmax(results)
        if i!=0 and i!=2:
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
