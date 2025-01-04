import cv2
import numpy as np
import pyautogui
import time
import tkinter as tk
from tkinter import ttk
import threading
from math import exp
import os

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
        self.smoothing_factor = 0.05  # 减小平滑因子，使过渡更加丝滑
        self.mouse_moved = False
        self.last_significant_move_time = 0
        self.move_threshold = 5  # 鼠标移动阈值
        
    def get_zoomed_region(self, frame, center, zoom):
        """获取缩放后的区域"""
        h, w = frame.shape[:2]
        # 计算缩放后的尺寸
        new_h = int(h / zoom)
        new_w = int(w / zoom)
        
        # 确保中心点在有效范围内
        x = min(max(int(center[0] - new_w//2), 0), w - new_w)
        y = min(max(int(center[1] - new_h//2), 0), h - new_h)
        
        # 提取区域并调整大小
        region = frame[y:y+new_h, x:x+new_w]
        return cv2.resize(region, (w, h))
    
    def smooth_track(self, current, target, factor):
        """平滑跟踪函数"""
        if current is None:
            return target
        return tuple(current[i] + (target[i] - current[i]) * factor for i in range(2))
    
    def calculate_zoom_level(self, mouse_speed):
        """根据鼠标速度计算缩放级别"""
        base_zoom = 1.0
        max_zoom = 2.0  # 最大缩放倍数
        speed_threshold = 100  # 速度阈值
        
        if mouse_speed > speed_threshold:
            zoom = base_zoom + (max_zoom - base_zoom) * (1 - exp(-mouse_speed/speed_threshold))
        else:
            zoom = base_zoom
        
        return min(zoom, max_zoom)
    
    def record(self):
        last_mouse_pos = pyautogui.position()
        last_time = time.time()
        
        while self.is_recording:
            # 捕获屏幕
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 计算鼠标速度和位置
            current_mouse_pos = pyautogui.position()
            current_time = time.time()
            
            dx = current_mouse_pos[0] - last_mouse_pos[0]
            dy = current_mouse_pos[1] - last_mouse_pos[1]
            movement = (dx**2 + dy**2)**0.5
            
            # 检测显著的鼠标移动
            if movement > self.move_threshold:
                self.mouse_moved = True
                self.last_significant_move_time = current_time
                self.target_zoom = 3.0  # 增大缩放比例到3倍
                self.target_center = current_mouse_pos
            
            # 平滑过渡
            if self.mouse_moved:
                self.zoom_level += (self.target_zoom - self.zoom_level) * self.smoothing_factor
                self.current_center = self.smooth_track(self.current_center, self.target_center, self.smoothing_factor)
            
            # 应用缩放效果
            if self.zoom_level > 1.0:
                frame = self.get_zoomed_region(frame, self.current_center, self.zoom_level)
            
            # 写入视频
            self.out.write(frame)
            
            # 更新上一帧的数据
            last_mouse_pos = current_mouse_pos
            last_time = current_time
    
    def preview_recording(self):
        """预览录制的视频"""
        if not os.path.exists(self.filename):
            return
            
        cap = cv2.VideoCapture(self.filename)
        
        # 获取视频的尺寸
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 计算预览窗口的大小（保持宽高比）
        preview_width = 960
        preview_height = int(height * (preview_width / width))
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # 调整预览窗口大小
            frame = cv2.resize(frame, (preview_width, preview_height))
            cv2.imshow('Recording Preview', frame)
            
            # 按空格键暂停/继续，按q键退出
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
            # 启动预览线程
            preview_thread = threading.Thread(target=self.preview_recording)
            preview_thread.start()

class RecorderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Screen Studio Alternative")
        self.root.geometry("300x150")
        
        self.recorder = ScreenRecorder()
        
        style = ttk.Style()
        style.configure('Custom.TButton', padding=10)
        
        # 只创建一个按钮
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
