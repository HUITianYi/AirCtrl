# main.py
import sys
import cv2
from PyQt5 import QtWidgets, QtGui, QtCore

from hand_tracker import HandTracker
from gesture_logic import GestureLogic
from apps.drawing_board import DrawingBoard
from apps.paddle_game import PaddleGame
from apps.paddle_versus import PaddleVersus 

class CameraLabel(QtWidgets.QLabel):
    """摄像头显示 + 按钮绘制"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScaledContents(True)
        self.cursor_pos = None
        self.show_cursor = True
        self.show_buttons = True  # 控制是否绘制任务按钮

        # 按钮参数
        self.button_radius = 80
        self.button_spacing = 200
        self.buttons = {
            'Drawing': QtCore.QPoint(0, 0),
            'Game': QtCore.QPoint(0, 0),
            'Clear': QtCore.QPoint(0, 0)
        }

        # 状态记录
        self.hover_button = None
        self.hover_progress = 0.0
        self.clicked_button = None

    def update_button_positions(self):
        """根据窗口大小更新按钮中心点坐标"""
        center_x = self.width() // 2
        center_y = self.height() // 2
        offset = -self.button_spacing
        for name in self.buttons.keys():
            self.buttons[name] = QtCore.QPoint(center_x + offset, center_y)
            offset += self.button_spacing

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self)

        if self.show_buttons:
            for name, center in self.buttons.items():
                base_color = QtGui.QColor(60, 60, 60, 200)
                if name == self.hover_button:
                    base_color = QtGui.QColor(100, 100, 255, 220)
                if name == self.clicked_button:
                    base_color = QtGui.QColor(0, 200, 0, 255)

                grad = QtGui.QRadialGradient(center, self.button_radius)
                grad.setColorAt(0, base_color.lighter(150))
                grad.setColorAt(1, base_color.darker(150))
                painter.setBrush(QtGui.QBrush(grad))
                painter.setPen(QtGui.QPen(QtGui.QColor("white"), 3))
                painter.drawEllipse(center, self.button_radius, self.button_radius)

                painter.setFont(QtGui.QFont('Arial', 14, QtGui.QFont.Bold))
                painter.setPen(QtGui.QPen(QtGui.QColor("white")))
                text_rect = QtCore.QRect(
                    center.x() - self.button_radius,
                    center.y() - self.button_radius,
                    self.button_radius * 2,
                    self.button_radius * 2
                )
                painter.drawText(text_rect, QtCore.Qt.AlignCenter, name)

                # 悬停进度环
                if name == self.hover_button and self.hover_progress > 0:
                    pen = QtGui.QPen(QtGui.QColor(255, 255, 0), 5)
                    painter.setPen(pen)
                    painter.setBrush(QtCore.Qt.NoBrush)
                    start_angle = 90 * 16
                    span_angle = int(-self.hover_progress * 360 * 16)
                    painter.drawArc(center.x() - self.button_radius - 6,
                                    center.y() - self.button_radius - 6,
                                    (self.button_radius + 6) * 2,
                                    (self.button_radius + 6) * 2,
                                    start_angle, span_angle)

        # 手势光标
        if self.show_cursor and self.cursor_pos is not None:
            painter.setBrush(QtGui.QColor(0, 120, 255, 180))
            painter.setPen(QtGui.QPen(QtGui.QColor('white'), 2))
            x, y = self.cursor_pos
            painter.drawEllipse(x - 12, y - 12, 24, 24)

        painter.end()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AirCtrl - Gesture Interaction")
        self.showFullScreen()

        # 摄像头
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if sys.platform.startswith('win') else 0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # 手势
        self.tracker = HandTracker(max_num_hands=2, min_detection_confidence=0.6, min_tracking_confidence=0.6)
        self.glogic = GestureLogic(pinch_threshold_px=40, dwell_time=0.8)

        # 主容器
        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        # 场景1：主菜单（摄像头+按钮）
        self.menu_widget = QtWidgets.QWidget()
        vbox_menu = QtWidgets.QVBoxLayout(self.menu_widget)
        vbox_menu.setContentsMargins(0, 0, 0, 0)
        vbox_menu.setSpacing(0)
        self.cam_label = CameraLabel()
        vbox_menu.addWidget(self.cam_label)
        self.stack.addWidget(self.menu_widget)

        # 场景2：画板
        self.drawing_app = DrawingBoard()
        self.stack.addWidget(self.drawing_app)

        # 场景3：游戏
        self.game_app = PaddleGame()
        self.stack.addWidget(self.game_app)

        self.current_mode = "menu"  # menu, drawing, game
        self.cam_label.update_button_positions()

        self.button_actions = {
            'Drawing': self._start_drawing,
            'Game': self._start_game,
            'Clear': self._clear_drawing
        }

        self.last_hover_name = None
        self.hover_start_time = None

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(30)

    def resizeEvent(self, event):
        if hasattr(self, "cam_label") and self.cam_label is not None:
            self.cam_label.update_button_positions()
        super().resizeEvent(event)

    def closeEvent(self, event):
        self.timer.stop()
        if self.cap:
            self.cap.release()
        if self.tracker:
            self.tracker.close()
        event.accept()

    # 按钮动作
    def _start_drawing(self):
        self.drawing_app.clear()
        self.stack.setCurrentWidget(self.drawing_app)
        self.current_mode = "drawing"

    def _start_game(self):
        self.game_app.reset_balls()
        self.stack.setCurrentWidget(self.game_app)
        self.current_mode = "game"

    def _clear_drawing(self):
        if self.current_mode == "drawing":
            self.drawing_app.clear()

    def _return_to_menu(self):
        self.stack.setCurrentWidget(self.menu_widget)
        self.current_mode = "menu"

    def _update(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.flip(frame, 1)
        annotated, hands = self.tracker.process(frame)

        # 摄像头只在主菜单模式下绘制
        if self.current_mode == "menu":
            frame_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            h, w, _ = frame_rgb.shape
            qt_img = QtGui.QImage(frame_rgb.data, w, h, QtGui.QImage.Format_RGB888)
            pix = QtGui.QPixmap.fromImage(qt_img).scaled(self.cam_label.size(),
                                                         QtCore.Qt.KeepAspectRatioByExpanding)
            self.cam_label.setPixmap(pix)

            # 手指位置
            index_tip = self.glogic.extract_index_tip(hands)
            if index_tip is not None:
                scale_x = self.cam_label.width() / w
                scale_y = self.cam_label.height() / h
                x_mapped = int(index_tip[0] * scale_x)
                y_mapped = int(index_tip[1] * scale_y)
                self.cam_label.cursor_pos = (x_mapped, y_mapped)
            else:
                self.cam_label.cursor_pos = None

            # 悬停检测
            hover_name = None
            if self.cam_label.cursor_pos is not None:
                cursor_pt = QtCore.QPoint(*self.cam_label.cursor_pos)
                for name, center in self.cam_label.buttons.items():
                    if (center - cursor_pt).manhattanLength() < self.cam_label.button_radius:
                        hover_name = name
                        break

            if hover_name != self.last_hover_name:
                self.last_hover_name = hover_name
                self.hover_start_time = QtCore.QTime.currentTime()

            if hover_name:
                elapsed = self.hover_start_time.msecsTo(QtCore.QTime.currentTime()) / 1000
                progress = min(1.0, elapsed / self.glogic.dwell_time)
                self.cam_label.hover_button = hover_name
                self.cam_label.hover_progress = progress
                if progress >= 1.0:
                    self._trigger_button(hover_name)
            else:
                self.cam_label.hover_button = None
                self.cam_label.hover_progress = 0.0

            self.cam_label.update()

        else:
            # 应用模式下检测 pinch 返回
            if hands:
                primary = next((h for h in hands if h['handedness'] == 'Right'), hands[0])
                if self.glogic.is_pinch(primary):
                    self._return_to_menu()

            # 更新应用
            index_tip = self.glogic.extract_index_tip(hands)
            target_pos = None
            if index_tip is not None:
                # 应用直接用摄像头坐标映射
                frame_h, frame_w = frame.shape[:2]
                rel_x = index_tip[0] / frame_w
                rel_y = index_tip[1] / frame_h
                app_w = self.stack.currentWidget().width()
                app_h = self.stack.currentWidget().height()
                target_pos = (int(rel_x * app_w), int(rel_y * app_h))

            is_drawing = False
            if hands:
                primary = next((h for h in hands if h['handedness'] == 'Right'), hands[0])
                is_drawing = self.glogic.is_pinch(primary)

            if self.current_mode == "drawing":
                self.drawing_app.update_cursor(target_pos, is_drawing)
            elif self.current_mode == "game":
                self.game_app.update_cursor(target_pos)

    def _trigger_button(self, name):
        if name in self.button_actions:
            self.button_actions[name]()
            self.cam_label.clicked_button = name
            QtCore.QTimer.singleShot(300, self._clear_click_flash)

    def _clear_click_flash(self):
        self.cam_label.clicked_button = None


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
