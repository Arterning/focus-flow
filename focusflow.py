import cv2
import numpy as np
import pyautogui
import time
import tkinter as tk
from tkinter import ttk
import threading
import os

class ScreenRecorder:
    def __init__(self, filename='output.mp4', fps=30.0):
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.fps = fps
        self.filename = filename
        self.screen_size = pyautogui.size()
        self.out = None
        self.is_recording = False
        self.recording_thread = None

    def record(self):
        time_per_frame = 1.0 / self.fps
        while self.is_recording:
            frame_start = time.time()
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.out.write(frame)
            elapsed = time.time() - frame_start
            sleep_time = time_per_frame - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def preview_recording(self):
        if not os.path.exists(self.filename):
            return
        cap = cv2.VideoCapture(self.filename)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        preview_width = 960
        preview_height = int(height * (preview_width / width))
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.resize(frame, (preview_width, preview_height))
            cv2.imshow('Recording Preview', frame)
            key = cv2.waitKey(int(1000/self.fps)) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' '):
                cv2.waitKey(0)
        cap.release()
        cv2.destroyAllWindows()

    def start_recording(self):
        if not self.is_recording:
            self.out = cv2.VideoWriter(self.filename, self.fourcc, self.fps, 
                                       (self.screen_size.width, self.screen_size.height))
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self.record)
            self.recording_thread.start()

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.recording_thread.join()
            self.out.release()
            preview_thread = threading.Thread(target=self.preview_recording)
            preview_thread.start()

class RecorderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FocusFlow")
        self.root.geometry("300x150")
        self.recorder = ScreenRecorder()
        style = ttk.Style()
        style.configure('Custom.TButton', padding=10)
        self.record_button = ttk.Button(
            self.root, 
            text="开始录制", 
            command=self.toggle_recording,
            style='Custom.TButton'
        )
        self.record_button.pack(pady=20)
        self.is_recording = False
    def toggle_recording(self):
        if not self.is_recording:
            self.recorder.start_recording()
            self.record_button.config(text="停止录制")
            self.is_recording = True
        else:
            self.recorder.stop_recording()
            self.record_button.config(text="开始录制")
            self.is_recording = False
    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    gui = RecorderGUI()
    gui.run()
