import shutil

import fastapi.responses
from moviepy.editor import VideoFileClip
import numpy as np
from threading import Thread
import os
import time
from datetime import timedelta
from fastapi import FastAPI, UploadFile, Request, requests, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from typing import Union
from pydantic import BaseModel
import json
import cv2
from model import get_caption_model, generate_caption
from PIL import Image
from queue import Queue
import subprocess
import imutils
from pydub import AudioSegment
import gtts
import httpx
from playsound import playsound
from mutagen.mp3 import MP3
from translate import Translator
from argostranslate import package, translate
import argostranslate
import io

from_code = 'en'
to_code = 'ru'

package.update_package_index()
available_packages = argostranslate.package.get_available_packages()
available_package = list(
    filter(
        lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
    )
)[0]

download_path = available_package.download()

argostranslate.package.install_from_path(download_path)

installed_languages = translate.get_installed_languages()
[str(lang) for lang in installed_languages]
translation_en_ru = installed_languages[0].get_translation(installed_languages[1])



SAVING_FRAMES_PER_SECOND = 60

"""
class FileVideoStream:
    def __init__(self, name, amount, reslist):
        print(name)
        self.vidcap = cv2.VideoCapture(f'./raw/{name}')
        self.results = reslist
        self.amount = amount


    def behaviour(self, threadnum,success=True):
        while success:
            success, image = self.vidcap.read()
            name = "frame"
            cv2.imwrite(f"./frames/{name}{threadnum}.png", image)  # save frame as JPEG file
            model = get_caption_model()
            pred = generate_caption(f"./frames/{name}{threadnum}.png", model)
            print(pred)
            self.results.append(pred)
        print("ENDED!")
    def execute(self):
        for i in range(self.amount):
            print(f"starting {i} thread")
            thread = Thread(target=self.behaviour, args=[i])
            thread1 = Thread(target=self.behaviour, args=[1])
            thread2 = Thread(target=self.behaviour, args=[2])
            thread.start()
            thread1.start()
            thread2.start()

"""
"""
class FileVideoStream:
    def __init__(self, path, queueSize=128):
        # initialize the file video stream along with the boolean
        # used to indicate if the thread should be stopped or not
        # self.stream = cv2.VideoCapture(path)
        # self.stopped = False
        # initialize the queue used to store frames read from
        # the video file
        self.Q = Queue(maxsize=queueSize)
    def start(self):
        # start a thread to read frames from the file video stream
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self
    def update(self):
        # keep looping infinitely
        while True:
            # if the thread indicator variable is set, stop the
            # thread
            if self.stopped:
                return
            # otherwise, ensure the queue has room in it
            if not self.Q.full():
                # read the next frame from the file
                (grabbed, frame) = self.stream.read()
                # if the `grabbed` boolean is `False`, then we have
                # reached the end of the video file
                if not grabbed:
                    self.stop()
                    return
                # add the frame to the queue
                self.Q.put(frame)
    def read(self):
        # return next frame in the queue
        return self.Q.get()
    def more(self):
        # return True if there are still frames in the queue
        return self.Q.qsize() > 0
    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
"""
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://localhost:8000/"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
        name: str
        spgz: str
        kpgz: str
@app.get('/')
def home():
    return{"key": "Hello"}

@app.get('/tiflovideo')
def vedeos():
    with open("result.json") as file:
       fil = json.load(file)
       return JSONResponse(fil)

@app.post('/analyze/{name}')
def analyze(name:str):
    model = get_caption_model()
    pred = generate_caption(f"./frames/{name}.png", model)
    return JSONResponse(pred)

@app.post('/vidanalyze/{name}')
def vidanalyze(name:str):
    vidcap = cv2.VideoCapture(f'./videos/{name}.mp4')
    count = 0
    currency = 5
    reslist = list()
    while True:
        success, image = vidcap.read()
        if not success:
            break
        count += 1
        name = "frame"
        img_PIL = Image.new("RGB", (1920, 1080))
        img_PIL.save(f"./frames/{name}.png")
        cv2.imwrite(f"./frames/{name}.png", image)  # save frame as JPEG file
        success, image = vidcap.read()
        if count % currency == 0:
            model = get_caption_model()
            pred = generate_caption(f"./frames/{name}.png", model)
            reslist.append(pred)
            print(pred)
    return reslist

@app.post('/mp4analyze')
def fileanalyze(file: UploadFile):
    with open('raw/'+file.filename, "wb") as wf:
        shutil.copyfileobj(file.file, wf)
        file.file.close()
        name = file.filename
        vidcap = cv2.VideoCapture(f'./raw/{name}')
        count = 0
        currency = 5
        reslist = list()
        while True:
            if count % currency == 0:
                success, image = vidcap.read()
                name = "frame"
                img_PIL = Image.new("RGB", (1920, 1080))
                img_PIL.save(f"./frames/{name}.png")
                cv2.imwrite(f"./frames/{name}.png", image)  # save frame as JPEG file
                model = get_caption_model()
                pred = generate_caption(f"./frames/{name}.png", model)
                reslist.append(pred)
                print(pred)
            else:
                success = vidcap.grab()
            if not success:
                break
            count += 1

        return reslist


@app.post('/mp4')
def mp4_conversion(file: UploadFile):
    with open('raw/' + file.filename, "wb") as wf:
        shutil.copyfileobj(file.file, wf)
        file.file.close()
        name = file.filename
        vidcap = cv2.VideoCapture(f'./raw/{name}')
        fps = vidcap.get(cv2.CAP_PROP_FPS)

        subprocess.run(['mkdir', 'currentrun'])
        subprocess.run(['ffmpeg', '-i', f'./raw/{name}', './currentrun/frame%d.jpg'])
        reslist = list()
        amount = sorted(list(map(lambda x: int((x.replace('frame', '')).replace(".jpg", '')), os.listdir('./currentrun'))))[-1]

        threadsnum = 1

        frequency = 10

        filenums = list(range(1, amount, int(fps) * frequency))


        print(filenums)
        threads = list()
        for i in range(threadsnum):
            current = filenums[i: len(filenums): threadsnum]
            thread = Thread(target=threadbehaviour, args=[current, reslist], daemon=True)
            threads.append(thread)

        for thread in threads:
            print("Starting thread")
            thread.start()

        for thread in threads:
            thread.join()

        while True:
            if len(reslist) == len(filenums):
                subprocess.run(['rm', "-r", 'currentrun'])
                reslist = list(map(lambda x: translation_en_ru.translate(x), reslist))
                t1 = gtts.gTTS(file.filename, lang='ru')
                t1.save("./sounds/speech.mp3")
                sound = AudioSegment.from_mp3("./sounds/speech.mp3")
                print("Processing speech...")
                for res in reslist:
                    sound = addsound(res, sound)
                sound.export("./sounds/speech.mp3", format="mp3")
                print(time.process_time())
                #with open("./sounds/speech.mp3", mode="rb") as file:
                #    header = {'Content-Length': str(len(file))}
                def iterfile():
                    with open("./sounds/speech.mp3", mode="rb") as file:
                        data = file.read()
                        yield data


                headers = {
                    'Content-Disposition': 'attachment; filename="./sounds/speech.mp3"'
                }
                #return fastapi.responses.FileResponse(os.fspath("./sounds/speech.mp3"), media_type="audio/mp3", headers=headers)
                #return StreamingResponse(iter(), media_type="video/mp4")
                return StreamingResponse(iterfile(), media_type="audio/mp3", headers=headers)


def threadbehaviour(targets,  reslist):
    model = get_caption_model()
    print("Started thread")
    for i in targets:
        pred = generate_caption(f"./currentrun/frame{i}.jpg", model)
        print(pred)
        reslist.append(pred)

def get5stalk(line):
    t1 = gtts.gTTS(line, lang='ru')
    t1.save("./sounds/speech.mp3")
    playsound("./sounds/speech.mp3")
    audio = MP3("./sounds/speech.mp3")
    print(audio.info.length)
    sound1 = AudioSegment.from_mp3("./sounds/speech.mp3")
    sound2 = AudioSegment.from_mp3("./sounds/silence.mp3")
    sound1.append(sound2)
    sound1.export("./sounds/speech.mp3", format="mp3")

def addsound(line, sound):
    t1 = gtts.gTTS(line, lang='ru')
    t1.save("./sounds/part.mp3")
    audio = MP3("./sounds/part.mp3")
    sound2 = AudioSegment.from_mp3("./sounds/part.mp3")
    if audio.info.length < 10:
        sound = (sound + sound2 + AudioSegment.silent((10 - audio.info.length)*1000))
    else:
        sound = sound + sound2
    return sound
