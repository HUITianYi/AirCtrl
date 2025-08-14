# vr_mode.py
from PyQt5 import QtWidgets, QtGui, QtCore
import numpy as np
import math

class VRMode(QtWidgets.QWidget):
    """VR模式：手势控制虚拟人物移动，虚拟世界与显示世界叠加"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        
        # 虚拟世界设置
        self.world_size = (1000, 1000)  # 虚拟世界尺寸
        self.player_pos = [self.world_size[0]//2, self.world_size[1]//2]  # 玩家初始位置
        self.player_size = 30  # 玩家尺寸
        self.player_speed = 5  # 玩家移动速度
        self.player_direction = 0  # 玩家方向 (0-360度)
        
        # 虚拟世界元素
        self.obstacles = [
            {"pos": [200, 300], "size": 80, "color": QtGui.QColor(255, 100, 100)},
            {"pos": [700, 400], "size": 120, "color": QtGui.QColor(100, 255, 100)},
            {"pos": [400, 700], "size": 60, "color": QtGui.QColor(100, 100, 255)},
            {"pos": [800, 800], "size": 100, "color": QtGui.QColor(255, 200, 100)},
        ]
        
        # 可收集物品
        self.collectibles = []
        self.generate_collectibles(20)
        
        self.score = 0
        self.camera_frame = None  # 存储摄像头帧
        
        # 游戏定时器
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.game_step)
        self.timer.start(16)  # ~60fps

    def generate_collectibles(self, count):
        """生成可收集物品"""
        for _ in range(count):
            self.collectibles.append({
                "pos": [
                    np.random.randint(100, self.world_size[0]-100),
                    np.random.randint(100, self.world_size[1]-100)
                ],
                "size": 15,
                "color": QtGui.QColor(255, 255, 0),
                "collected": False
            })

    def game_step(self):
        """游戏逻辑更新"""
        # 检查收集物品
        for item in self.collectibles:
            if not item["collected"]:
                dist = math.sqrt((self.player_pos[0] - item["pos"][0])**2 + 
                                (self.player_pos[1] - item["pos"][1])**2)
                if dist < (self.player_size + item["size"]):
                    item["collected"] = True
                    self.score += 10
        
        # 重绘
        self.update()

    def update_camera_frame(self, frame):
        """更新摄像头帧"""
        self.camera_frame = frame

    def update_hand_position(self, pos):
        """根据手势位置更新玩家移动方向"""
        if pos is None:
            return
            
        # 计算玩家方向（相对于屏幕中心）
        center_x, center_y = self.width()//2, self.height()//2
        dx = pos[0] - center_x
        dy = pos[1] - center_y
        
        # 计算角度（0-360度）
        angle = math.degrees(math.atan2(dy, dx)) % 360
        
        # 更新玩家方向
        self.player_direction = angle
        
        # 计算移动向量
        rad = math.radians(angle)
        move_x = self.player_speed * math.cos(rad)
        move_y = self.player_speed * math.sin(rad)
        
        # 更新玩家位置（边界检查）
        new_x = max(self.player_size, min(self.world_size[0]-self.player_size, self.player_pos[0] + move_x))
        new_y = max(self.player_size, min(self.world_size[1]-self.player_size, self.player_pos[1] + move_y))
        
        # 检查障碍物碰撞
        collision = False
        for obstacle in self.obstacles:
            dist = math.sqrt((new_x - obstacle["pos"][0])**2 + 
                            (new_y - obstacle["pos"][1])**2)
            if dist < (self.player_size + obstacle["size"]//2):
                collision = True
                break
        
        # 如果没有碰撞，则更新位置
        if not collision:
            self.player_pos[0] = new_x
            self.player_pos[1] = new_y

    def paintEvent(self, event):
        """绘制VR世界"""
        painter = QtGui.QPainter(self)
        
        # 如果有摄像头帧，绘制为背景
        if self.camera_frame is not None:
            h, w = self.camera_frame.shape[:2]
            bytes_per_line = 3 * w
            q_img = QtGui.QImage(self.camera_frame.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
            painter.drawImage(self.rect(), q_img)
        
        # 绘制半透明覆盖层
        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 100))
        
        # 设置虚拟世界绘制区域（中心区域）
        world_rect = QtCore.QRect(
            self.width()//2 - 300,
            self.height()//2 - 300,
            600, 600
        )
        
        # 绘制世界边界
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 2))
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawRect(world_rect)
        
        # 设置世界坐标系变换
        painter.save()
        painter.translate(world_rect.center())
        scale = min(world_rect.width()/self.world_size[0], world_rect.height()/self.world_size[1])
        painter.scale(scale, scale)
        painter.translate(-self.player_pos[0], -self.player_pos[1])
        
        # 绘制障碍物
        for obstacle in self.obstacles:
            painter.setBrush(obstacle["color"])
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(
                int(obstacle["pos"][0] - obstacle["size"]//2),
                int(obstacle["pos"][1] - obstacle["size"]//2),
                obstacle["size"],
                obstacle["size"]
            )
        
        # 绘制可收集物品
        for item in self.collectibles:
            if not item["collected"]:
                painter.setBrush(item["color"])
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(
                    int(item["pos"][0] - item["size"]//2),
                    int(item["pos"][1] - item["size"]//2),
                    item["size"],
                    item["size"]
                )
        
        # 绘制玩家（带方向指示）
        painter.setBrush(QtGui.QColor(50, 150, 255, 200))
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 2))
        painter.drawEllipse(
            int(self.player_pos[0] - self.player_size),
            int(self.player_pos[1] - self.player_size),
            self.player_size * 2,
            self.player_size * 2
        )
        
        # 绘制方向指示器
        rad = math.radians(self.player_direction)
        dir_x = self.player_pos[0] + math.cos(rad) * self.player_size * 1.5
        dir_y = self.player_pos[1] + math.sin(rad) * self.player_size * 1.5
        painter.drawLine(
            int(self.player_pos[0]),
            int(self.player_pos[1]),
            int(dir_x),
            int(dir_y)
        )
        
        # 恢复坐标系
        painter.restore()
        
        # 绘制分数
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.setFont(QtGui.QFont('Arial', 24))
        painter.drawText(20, 50, f"Score: {self.score}")
        
        # 绘制提示文字
        painter.setFont(QtGui.QFont('Arial', 16))
        painter.drawText(20, self.height() - 40, "移动手部控制角色方向，收集黄色物品")
        
        painter.end()