from PyQt5 import QtWidgets, QtGui, QtCore
import numpy as np
import math
import time

class VRPVPMode(QtWidgets.QWidget):
    """VR PVP模式：修复屏幕中心退出按钮功能"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # 确保正确接收父窗口引用
        self.setMinimumSize(1200, 600)
        
        # 虚拟世界设置
        self.world_size = (1500, 1000)
        self.player1_pos = [self.world_size[0]//3, self.world_size[1]//2]
        self.player2_pos = [self.world_size[0]//3*2, self.world_size[1]//2]
        self.player_size = 30
        self.player_speed = 4
        self.player1_direction = 0
        self.player2_direction = 180
        
        # 玩家颜色
        self.player1_color = QtGui.QColor(50, 150, 255, 200)
        self.player2_color = QtGui.QColor(255, 100, 100, 200)
        
        # 游戏元素
        self.obstacles = [
            {"pos": [300, 300], "size": 80, "color": QtGui.QColor(255, 100, 100)},
            {"pos": [1200, 400], "size": 120, "color": QtGui.QColor(100, 255, 100)},
            {"pos": [750, 200], "size": 100, "color": QtGui.QColor(100, 100, 255)},
            {"pos": [750, 800], "size": 100, "color": QtGui.QColor(255, 200, 100)},
            {"pos": [300, 700], "size": 70, "color": QtGui.QColor(200, 100, 255)},
            {"pos": [1200, 700], "size": 70, "color": QtGui.QColor(100, 255, 255)},
        ]
        
        # 收集物和分数
        self.collectibles = []
        self.generate_collectibles(30)
        self.score1 = 0
        self.score2 = 0
        
        # 摄像头背景
        self.camera_background = None
        
        # 退出按钮设置（屏幕中间）
        self.exit_button = {
            "rect": None,  # 在resizeEvent中设置
            "text": "退出游戏",
            "hovered": False,
            "required_hover_time": 1.2,  # 悬停时间
            "current_hover_time": 0,
            "pulse_animation": 0  # 呼吸动画
        }
        
        # 手势位置跟踪
        self.left_hand_pos = None
        self.right_hand_pos = None
        
        # 游戏定时器
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.game_step)
        self.timer.start(16)  # ~60fps
        self.last_time = time.time()

    def resizeEvent(self, event):
        """窗口大小变化时调整按钮位置（确保在屏幕中心）"""
        super().resizeEvent(event)
        # 增大按钮尺寸便于定位
        btn_width, btn_height = 220, 100
        self.exit_button["rect"] = QtCore.QRect(
            (self.width() - btn_width) // 2,
            (self.height() - btn_height) // 2,
            btn_width,
            btn_height
        )

    def generate_collectibles(self, count):
        """生成可收集物品"""
        for _ in range(count):
            while True:
                x = np.random.randint(100, self.world_size[0]-100)
                y = np.random.randint(100, self.world_size[1]-100)
                
                dist1 = math.hypot(x - self.player1_pos[0], y - self.player1_pos[1])
                dist2 = math.hypot(x - self.player2_pos[0], y - self.player2_pos[1])
                
                if dist1 > 150 and dist2 > 150:
                    break
            
            self.collectibles.append({
                "pos": [x, y],
                "size": 15,
                "color": QtGui.QColor(255, 255, 0),
                "collected": False,
                "collector": None
            })

    def game_step(self):
        """游戏逻辑更新"""
        current_time = time.time()
        delta_time = current_time - self.last_time
        self.last_time = current_time
        
        # 检查收集物
        for item in self.collectibles:
            if not item["collected"]:
                dist1 = math.hypot(self.player1_pos[0] - item["pos"][0], 
                                 self.player1_pos[1] - item["pos"][1])
                if dist1 < (self.player_size + item["size"]):
                    item["collected"] = True
                    item["collector"] = 1
                    self.score1 += 10
                
                dist2 = math.hypot(self.player2_pos[0] - item["pos"][0], 
                                 self.player2_pos[1] - item["pos"][1])
                if dist2 < (self.player_size + item["size"]):
                    item["collected"] = True
                    item["collector"] = 2
                    self.score2 += 10
        
        # 处理退出按钮悬停（关键修复）
        if self.exit_button["rect"]:
            self._handle_exit_button_hover(delta_time)
        
        # 更新按钮呼吸动画
        self.exit_button["pulse_animation"] = (self.exit_button["pulse_animation"] + delta_time * 2) % (2 * math.pi)
        
        self.update()

    def _handle_exit_button_hover(self, delta_time):
        """处理退出按钮悬停检测和退出逻辑"""
        hovering = False
        btn_rect = self.exit_button["rect"]
        
        # 检查任何一只手是否悬停在按钮上（坐标检测修复）
        if self.left_hand_pos:
            # 确保坐标在窗口范围内
            if 0 <= self.left_hand_pos[0] < self.width() and 0 <= self.left_hand_pos[1] < self.height():
                hovering = btn_rect.contains(
                    QtCore.QPoint(self.left_hand_pos[0], self.left_hand_pos[1])
                )
        
        if not hovering and self.right_hand_pos:
            if 0 <= self.right_hand_pos[0] < self.width() and 0 <= self.right_hand_pos[1] < self.height():
                hovering = btn_rect.contains(
                    QtCore.QPoint(self.right_hand_pos[0], self.right_hand_pos[1])
                )
        
        # 更新悬停状态
        if hovering:
            if not self.exit_button["hovered"]:
                self.exit_button["hovered"] = True
                self.exit_button["current_hover_time"] = 0
            else:
                self.exit_button["current_hover_time"] += delta_time
                
                # 达到所需悬停时间则退出（关键修复）
                if self.exit_button["current_hover_time"] >= self.exit_button["required_hover_time"]:
                    self._exit_to_menu()
        else:
            self.exit_button["hovered"] = False
            self.exit_button["current_hover_time"] = 0

    def _exit_to_menu(self):
        """退出到主菜单 - 简化调用逻辑"""
        if self.parent and hasattr(self.parent, '_return_to_menu'):
            # 使用直接调用而非invokeMethod，避免跨线程问题
            self.parent._return_to_menu()
        else:
            print("错误：无法找到返回菜单的方法")

    def update_camera_background(self, frame):
        """更新摄像头背景帧"""
        self.camera_background = frame

    def update_hand_positions(self, pos1, pos2):
        """更新手部位置（确保坐标正确）"""
        # 验证坐标有效性
        def validate_pos(pos):
            if pos is None:
                return None
            x, y = pos
            # 限制坐标在窗口范围内
            x = max(0, min(self.width()-1, x))
            y = max(0, min(self.height()-1, y))
            return (x, y)
            
        self.left_hand_pos = validate_pos(pos1)
        self.right_hand_pos = validate_pos(pos2)
        
        # 更新玩家位置
        if pos1 is not None:
            self._update_player_position(1, pos1)
            
        if pos2 is not None:
            self._update_player_position(2, pos2)

    # 其余方法保持不变...
    def _update_player_position(self, player_id, pos):
        if player_id == 1:
            player_pos = self.player1_pos
        else:
            player_pos = self.player2_pos
        
        if player_id == 1:
            center_x, center_y = (self.width()//4, self.height()//2)
        else:
            center_x, center_y = (self.width()//4*3, self.height()//2)
            
        dx = pos[0] - center_x
        dy = pos[1] - center_y
        
        angle = math.degrees(math.atan2(dy, dx)) % 360
        if player_id == 1:
            self.player1_direction = angle
        else:
            self.player2_direction = angle
        
        rad = math.radians(angle)
        move_x = self.player_speed * math.cos(rad)
        move_y = self.player_speed * math.sin(rad)
        
        new_x = max(self.player_size, min(self.world_size[0]-self.player_size, player_pos[0] + move_x))
        new_y = max(self.player_size, min(self.world_size[1]-self.player_size, player_pos[1] + move_y))
        
        collision = False
        for obstacle in self.obstacles:
            dist = math.hypot(new_x - obstacle["pos"][0], new_y - obstacle["pos"][1])
            if dist < (self.player_size + obstacle["size"]//2):
                collision = True
                break
        
        other_pos = self.player2_pos if player_id == 1 else self.player1_pos
        player_dist = math.hypot(new_x - other_pos[0], new_y - other_pos[1])
        if player_dist < (self.player_size * 2):
            collision = True
        
        if not collision:
            if player_id == 1:
                self.player1_pos[0] = new_x
                self.player1_pos[1] = new_y
            else:
                self.player2_pos[0] = new_x
                self.player2_pos[1] = new_y

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        
        # 1. 绘制完整摄像头背景
        if self.camera_background is not None:
            h, w = self.camera_background.shape[:2]
            bytes_per_line = 3 * w
            q_img = QtGui.QImage(
                self.camera_background.data, 
                w, h, 
                bytes_per_line, 
                QtGui.QImage.Format_RGB888
            )
            painter.drawImage(
                self.rect(), 
                q_img.scaled(
                    self.size(), 
                    QtCore.Qt.KeepAspectRatio, 
                    QtCore.Qt.SmoothTransformation
                )
            )
        
        # 2. 绘制中间分割线
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0, 200), 4))
        mid_x = self.width() // 2
        painter.drawLine(mid_x, 0, mid_x, self.height())
        
        # 3. 绘制半透明覆盖层
        overlay = QtGui.QColor(0, 0, 0, 80)
        painter.fillRect(self.rect(), overlay)
        
        # 4. 绘制游戏视图
        self._draw_view(painter, 1, 0, 0, mid_x, self.height())
        self._draw_view(painter, 2, mid_x, 0, mid_x, self.height())
        
        # 5. 绘制分数
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.setFont(QtGui.QFont('Arial', 24))
        painter.drawText(20, 50, f"玩家1分数: {self.score1}")
        painter.drawText(mid_x + 20, 50, f"玩家2分数: {self.score2}")
        
        # 6. 绘制提示文字
        painter.setFont(QtGui.QFont('Arial', 16))
        painter.drawText(20, self.height() - 40, "左侧玩家：移动左手控制角色")
        painter.drawText(mid_x + 20, self.height() - 40, "右侧玩家：移动右手控制角色")
        painter.drawText(20, self.height() - 65, "退出：将手移至屏幕中间按钮并保持")
        
        # 7. 绘制屏幕中间的退出按钮
        self._draw_exit_button(painter)
        
        painter.end()

    def _draw_exit_button(self, painter):
        btn = self.exit_button
        if not btn["rect"]:
            return
            
        rect = btn["rect"]
        current_time = btn["current_hover_time"]
        required_time = btn["required_hover_time"]
        
        # 呼吸动画
        pulse_factor = (math.sin(btn["pulse_animation"]) + 1) / 4 + 0.7
        
        # 按钮背景
        if btn["hovered"]:
            gradient = QtGui.QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradient.setColorAt(0, QtGui.QColor(255, 80, 80, 240))
            gradient.setColorAt(1, QtGui.QColor(220, 50, 50, 240))
            painter.setBrush(gradient)
            
            # 进度条
            progress = min(1.0, current_time / required_time)
            progress_rect = QtCore.QRect(
                rect.x(), rect.bottom() - 6, 
                int(rect.width() * progress), 6
            )
            painter.fillRect(progress_rect, QtGui.QColor(0, 255, 0, 220))
        else:
            base_color = QtGui.QColor(200, 60, 60)
            alpha = int(180 * pulse_factor)
            base_color.setAlpha(alpha)
            painter.setBrush(base_color)
        
        # 按钮边框
        border_color = QtGui.QColor(255, 255, 255, 220)
        painter.setPen(QtGui.QPen(border_color, 3))
        painter.drawRoundedRect(rect, 12, 12)
        
        # 按钮文字
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.setFont(QtGui.QFont('Arial', 18, QtGui.QFont.Bold))
        painter.drawText(rect, QtCore.Qt.AlignCenter, btn["text"])
        
        # 悬停提示
        if btn["hovered"]:
            remaining = max(0, required_time - current_time)
            painter.setFont(QtGui.QFont('Arial', 14))
            painter.drawText(
                rect.center().x() - 80, rect.y() - 25, 
                f"再停留 {remaining:.1f} 秒"
            )

    def _draw_view(self, painter, player_id, x, y, width, height):
        painter.save()
        
        view_rect = QtCore.QRect(x, y, width, height)
        painter.setClipRect(view_rect)
        
        world_rect = QtCore.QRect(
            x + width//2 - 250,
            y + height//2 - 250,
            500, 500
        )
        
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 150), 2))
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawRect(world_rect)
        
        painter.save()
        painter.translate(world_rect.center())
        scale = min(world_rect.width()/self.world_size[0], world_rect.height()/self.world_size[1])
        painter.scale(scale, scale)
        
        if player_id == 1:
            painter.translate(-self.player1_pos[0], -self.player1_pos[1])
        else:
            painter.translate(-self.player2_pos[0], -self.player2_pos[1])
        
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
        
        # 绘制收集物
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
        
        # 绘制玩家1
        painter.setBrush(self.player1_color)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 2))
        painter.drawEllipse(
            int(self.player1_pos[0] - self.player_size),
            int(self.player1_pos[1] - self.player_size),
            self.player_size * 2,
            self.player_size * 2
        )
        
        # 玩家1方向指示器
        rad1 = math.radians(self.player1_direction)
        dir1_x = self.player1_pos[0] + math.cos(rad1) * self.player_size * 1.5
        dir1_y = self.player1_pos[1] + math.sin(rad1) * self.player_size * 1.5
        painter.drawLine(
            int(self.player1_pos[0]), int(self.player1_pos[1]),
            int(dir1_x), int(dir1_y)
        )
        
        # 绘制玩家2
        painter.setBrush(self.player2_color)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 2))
        painter.drawEllipse(
            int(self.player2_pos[0] - self.player_size),
            int(self.player2_pos[1] - self.player_size),
            self.player_size * 2,
            self.player_size * 2
        )
        
        # 玩家2方向指示器
        rad2 = math.radians(self.player2_direction)
        dir2_x = self.player2_pos[0] + math.cos(rad2) * self.player_size * 1.5
        dir2_y = self.player2_pos[1] + math.sin(rad2) * self.player_size * 1.5
        painter.drawLine(
            int(self.player2_pos[0]), int(self.player2_pos[1]),
            int(dir2_x), int(dir2_y)
        )
        
        painter.restore()
        painter.restore()
