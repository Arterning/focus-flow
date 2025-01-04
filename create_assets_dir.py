import os

if not os.path.exists('assets'):
    os.makedirs('assets')

# 创建图标
import numpy as np
import cv2

# 创建一个 512x512 的透明背景图像
logo = np.zeros((512, 512, 4), dtype=np.uint8)

# 设置背景色为深蓝色
background_color = (41, 128, 185, 255)  # 深蓝色
cv2.circle(logo, (256, 256), 256, background_color, -1)

# 绘制聚焦效果
for i in range(3):
    radius = 180 - i * 40
    color = (236, 240, 241, 255)  # 浅灰色
    thickness = 15
    cv2.circle(logo, (256, 256), radius, color, thickness)

# 绘制中心点
center_color = (231, 76, 60, 255)  # 红色
cv2.circle(logo, (256, 256), 20, center_color, -1)

# 保存图标
cv2.imwrite('assets/logo.png', logo)
