from PyQt5 import QtWidgets, QtGui, QtCore
import random

class PaddleGame(QtWidgets.QWidget):
    """
    挡板球游戏（支持挡板XY双方向移动）：
      - 用手指的(x,y)坐标控制挡板位置
      - 挡板被限制在屏幕下半区域移动
      - 多个球会反弹，若任一球落到底部则重置所有球
    接口：
      - update_cursor(pos): pos 为 (x,y) 或 None
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 480)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.game_step)
        self.timer.start(16)  # ~60fps

        # 挡板设置（支持XY移动）
        self.paddle_w = 120
        self.paddle_h = 16
        # 初始位置设为屏幕下半区中间
        self.paddle_x = (self.width() - self.paddle_w) // 2
        self.paddle_y = (self.height() * 3) // 4  # 初始在屏幕3/4高度处（下半区）

        # 球设置
        self.ball_r = 18
        self.num_balls = 3
        self.balls = []

        # 速度设置
        self.speed_increment = 1
        self.max_speed = 20

        self.score = 0
        self.reset_balls()

    def resizeEvent(self, event):
        # 窗口大小变化时，保持挡板在合理的下半区域
        self.paddle_x = max(0, min(self.width() - self.paddle_w, self.paddle_x))
        self.paddle_y = max(self.height() // 2, min(self.height() - self.paddle_h - 20, self.paddle_y))
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor('white'))

        # 绘制挡板（绿色）
        painter.setBrush(QtGui.QColor(30, 120, 30))
        painter.drawRect(self.paddle_x, self.paddle_y, self.paddle_w, self.paddle_h)

        # 绘制多个彩色球
        colors = [
            QtGui.QColor(200, 30, 30),    # 红
            QtGui.QColor(30, 30, 200),    # 蓝
            QtGui.QColor(200, 200, 30),   # 黄
            QtGui.QColor(200, 30, 200),   # 紫
            QtGui.QColor(30, 200, 200)    # 青
        ]
        
        for i, ball in enumerate(self.balls):
            color = colors[i % len(colors)]
            painter.setBrush(color)
            painter.drawEllipse(
                int(ball['x'] - self.ball_r), 
                int(ball['y'] - self.ball_r),
                int(self.ball_r * 2), 
                int(self.ball_r * 2)
            )

        # 绘制分数
        painter.setPen(QtGui.QColor(0,0,0))
        painter.setFont(QtGui.QFont('Arial', 14))
        painter.drawText(10, 20, f"Score: {self.score}")

        painter.end()

    def game_step(self):
        # 更新所有球的位置
        for ball in self.balls:
            ball['x'] += ball['vx']
            ball['y'] += ball['vy']

            # 墙壁碰撞检测
            if ball['x'] - self.ball_r <= 0 or ball['x'] + self.ball_r >= self.width():
                ball['vx'] *= -1
            if ball['y'] - self.ball_r <= 0:
                ball['vy'] *= -1

            # 挡板碰撞检测（适配挡板XY移动的逻辑）
            if (self.paddle_y <= ball['y'] + self.ball_r <= self.paddle_y + self.paddle_h and
                self.paddle_x <= ball['x'] <= self.paddle_x + self.paddle_w and ball['vy'] > 0):
                ball['vy'] *= -1
                self.score += 1

                # 碰球后加速
                current_vx_abs = abs(ball['vx'])
                new_vx_abs = min(current_vx_abs + self.speed_increment, self.max_speed)
                ball['vx'] = (ball['vx'] / current_vx_abs) * new_vx_abs

                current_vy_abs = abs(ball['vy'])
                new_vy_abs = min(current_vy_abs + self.speed_increment, self.max_speed)
                ball['vy'] = (ball['vy'] / current_vy_abs) * new_vy_abs

            # 检测球是否落到底部（游戏失败）
            if ball['y'] - self.ball_r > self.height():
                self.reset_balls()
                self.score = 0
                break

        self.update()

    def reset_balls(self):
        """重置所有球到初始位置"""
        self.balls = []
        for i in range(self.num_balls):
            offset_x = (i - self.num_balls // 2) * 50
            offset_y = i * 30
            
            self.balls.append({
                'x': self.width() // 2 + offset_x,
                'y': self.height() // 2 + offset_y,
                'vx': random.choice([-3, -2, 2, 3]),
                'vy': 3 + i * 0.5
            })

    def update_cursor(self, pos):
        """
        根据手势位置更新挡板的XY坐标（限制在屏幕下半区域）
        pos: (x,y) 手势在游戏窗口中的坐标
        """
        if pos is None:
            return
        x, y = pos
        
        # 计算挡板新X坐标（限制在窗口水平范围内）
        new_x = int(x - self.paddle_w / 2)
        new_x = max(0, min(self.width() - self.paddle_w, new_x))
        
        # 计算挡板新Y坐标（限制在屏幕下半区域：从屏幕中点到屏幕底部上方）
        half_height = self.height() // 2  # 下半区起点（屏幕中点）
        max_y = self.height() - self.paddle_h - 20  # 最大Y（底部留20像素边距）
        new_y = int(y - self.paddle_h / 2)  # 以手势为中心
        new_y = max(half_height, min(max_y, new_y))  # 限制在上下边界内
        
        # 更新挡板位置
        self.paddle_x = new_x
        self.paddle_y = new_y