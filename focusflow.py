import cv2
import numpy as np
import pyautogui
import time
import tkinter as tk
from tkinter import ttk
import threading
from math import exp
import os
from pynput import mouse  # 新增

class ScreenRecorder:
    def __init__(self, filename='output.mp4', fps=30.0):
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.fps = fps
        self.filename = filename
        self.screen_size = pyautogui.size()
        self.out = None
        self.is_recording = False
        self.zoom_level = 1.0
        self.target_zoom = 1.0
        self.current_center = None
        self.target_center = None
        self.smoothing_factor = 0.15  # 调大平滑因子
        self.zoom_active = False
        self.listener = None
        self.last_click_pos = None  # 记录上次点击位置

    def on_click(self, x, y, button, pressed):
        if pressed:
            self.zoom_active = True
            self.target_zoom = 3.0
            self.target_center = (x, y)
            self.last_click_pos = (x, y)
        else:
            self.zoom_active = False
            self.target_zoom = 1.0
            # 松开时中心点保持在最后一次点击位置
            if self.last_click_pos:
                self.target_center = self.last_click_pos

    def get_zoomed_region(self, frame, center, zoom):
        h, w = frame.shape[:2]
        new_h = int(h / zoom)
        new_w = int(w / zoom)
        x = min(max(int(center[0] - new_w//2), 0), w - new_w)
        y = min(max(int(center[1] - new_h//2), 0), h - new_h)
        region = frame[y:y+new_h, x:x+new_w]
        return cv2.resize(region, (w, h))

    def smooth_track(self, current, target, factor):
        if current is None:
            return target
        return tuple(current[i] + (target[i] - current[i]) * factor for i in range(2))

    def record(self):
        time_per_frame = 1.0 / self.fps
        self.current_center = pyautogui.position()
        self.target_center = self.current_center
        self.zoom_level = 1.0
        start_time = time.time()
        while self.is_recording:
            frame_start = time.time()
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # 只在点击时更新target_center，松开时保持最后一次点击位置
            # 平滑过渡中心点和缩放级别
            self.current_center = self.smooth_track(self.current_center, self.target_center, self.smoothing_factor)
            self.zoom_level += (self.target_zoom - self.zoom_level) * self.smoothing_factor
            # 应用缩放
            if self.zoom_level > 1.01:
                frame = self.get_zoomed_region(frame, self.current_center, self.zoom_level)
            self.out.write(frame)
            # 帧率控制
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
            self.listener = mouse.Listener(on_click=self.on_click)
            self.listener.start()
            self.recording_thread = threading.Thread(target=self.record)
            self.recording_thread.start()

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.recording_thread.join()
            self.out.release()
            if self.listener:
                self.listener.stop()
                self.listener = None
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
