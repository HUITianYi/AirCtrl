import pygame
import sys
from PyQt5 import QtWidgets, QtCore, QtGui

class PaddleVersus(QtWidgets.QWidget):
    """双人对战挡板球游戏（手势控制版）"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        
        # 初始化Pygame相关资源
        pygame.init()
        self.WHITE = (255, 255, 255)
        self.GREEN = (198, 255, 128)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)
        self.BLACK = (0, 0, 0)
        
        # 游戏元素
        self.left_paddle = Paddle(50, self.height()//2 - 50, 10, 100, 8)
        self.right_paddle = Paddle(self.width()-60, self.height()//2 - 50, 10, 100, 8)
        self.ball = Ball((self.width()//2, self.height()//2), (-5, 5), 10)
        
        # 分数
        self.left_score = 0
        self.right_score = 0
        self.font = pygame.font.SysFont("Arial", 36)
        
        # 手势位置存储（左手控制左挡板，右手控制右挡板）
        self.left_hand_pos = None  # 左手Y坐标
        self.right_hand_pos = None  # 右手Y坐标
        
        # 游戏状态
        self.game_running = True
        
        # 定时器驱动游戏循环
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.game_step)
        self.timer.start(16)  # ~60fps

    def resizeEvent(self, event):
        # 窗口大小变化时调整元素位置
        self.left_paddle.x = 50
        self.right_paddle.x = self.width() - 60
        self.ball.position = (self.width()//2, self.height()//2)
        super().resizeEvent(event)

    def game_step(self):
        if not self.game_running:
            return
            
        # 手势控制挡板移动
        self._control_paddles()
        
        # 更新球位置
        self.ball.update_position()
        self.ball.bounce(self.width(), self.height())
        self._check_collisions()
        self._check_score()
        
        # 重绘
        self.update()

    def _control_paddles(self):
        # 左手控制左挡板（Y坐标映射）
        if self.left_hand_pos is not None:
            # 将手势Y坐标映射到挡板位置（垂直方向）
            paddle_range = self.height() - self.left_paddle.h
            normalized_y = max(0, min(1, self.left_hand_pos[1] / self.height()))
            target_y = normalized_y * paddle_range
            self.left_paddle.y = target_y
            
        # 右手控制右挡板（Y坐标映射）
        if self.right_hand_pos is not None:
            paddle_range = self.height() - self.right_paddle.h
            normalized_y = max(0, min(1, self.right_hand_pos[1] / self.height()))
            target_y = normalized_y * paddle_range
            self.right_paddle.y = target_y

    def _check_collisions(self):
        # 检测球与挡板碰撞
        self.ball.bounce_paddle(
            (self.left_paddle.x, self.left_paddle.y), 
            self.left_paddle.w, 
            self.left_paddle.h
        )
        self.ball.bounce_paddle(
            (self.right_paddle.x, self.right_paddle.y), 
            self.right_paddle.w, 
            self.right_paddle.h
        )

    def _check_score(self):
        # 左方得分（球碰右边界）
        if self.ball.position[0] + self.ball.r >= self.width():
            self.left_score += 1
            self.reset_round()
        # 右方得分（球碰左边界）
        elif self.ball.position[0] - self.ball.r <= 0:
            self.right_score += 1
            self.reset_round()

    def reset_round(self):
        # 重置回合（球回到中心）
        self.ball.position = (self.width()//2, self.height()//2)
        self.ball.speed = (5 if self.right_score > self.left_score else -5, 
                          5 if self.ball.speed[1] > 0 else -5)

    def reset_game(self):
        # 重置整个游戏
        self.left_score = 0
        self.right_score = 0
        self.reset_round()
        self.game_running = True

    def update_hands(self, left_pos, right_pos):
        """更新左右手位置（从主程序接收）"""
        self.left_hand_pos = left_pos
        self.right_hand_pos = right_pos

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        
        # 绘制背景
        painter.fillRect(self.rect(), QtGui.QColor(*self.GREEN))
        
        # 绘制挡板
        painter.setBrush(QtGui.QColor(*self.RED))
        painter.drawRect(
            self.left_paddle.x, 
            self.left_paddle.y, 
            self.left_paddle.w, 
            self.left_paddle.h
        )
        painter.drawRect(
            self.right_paddle.x, 
            self.right_paddle.y, 
            self.right_paddle.w, 
            self.right_paddle.h
        )
        
        # 绘制球
        painter.setBrush(QtGui.QColor(*self.BLUE))
        painter.drawEllipse(
            int(self.ball.position[0] - self.ball.r),
            int(self.ball.position[1] - self.ball.r),
            self.ball.r * 2,
            self.ball.r * 2
        )
        
        # 绘制分数
        painter.setPen(QtGui.QColor(*self.BLACK))
        painter.setFont(QtGui.QFont("Arial", 36, QtGui.QFont.Bold))
        painter.drawText(100, 50, f"{self.left_score}")
        painter.drawText(self.width() - 150, 50, f"{self.right_score}")
        
        # 绘制分隔线
        painter.setPen(QtGui.QPen(QtGui.QColor(*self.BLACK), 2, QtCore.Qt.DashLine))
        painter.drawLine(self.width()//2, 0, self.width()//2, self.height())

class Paddle:
    """挡板类"""
    def __init__(self, x, y, w, h, s):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.speed = s  # 移动速度

class Ball:
    """球类"""
    def __init__(self, position, speed, r):
        self.position = position
        self.speed = speed
        self.r = r

    def update_position(self):
        self.position = (
            self.position[0] + self.speed[0],
            self.position[1] + self.speed[1]
        )

    def bounce(self, max_width, max_height):
        """碰到边界反弹"""
        # 上下边界
        if (self.position[1] - self.r <= 0) or (self.position[1] + self.r >= max_height):
            self.speed = (self.speed[0], -self.speed[1])

    def bounce_paddle(self, paddle_pos, paddle_w, paddle_h):
        """碰到挡板反弹"""
        px, py = paddle_pos
        # 检查碰撞
        if (self.position[0] - self.r <= px + paddle_w and 
            self.position[0] + self.r >= px and 
            self.position[1] >= py and 
            self.position[1] <= py + paddle_h):
            # 反弹时增加速度（略微）
            new_speed_x = -self.speed[0] * 1.05
            self.speed = (new_speed_x, self.speed[1])