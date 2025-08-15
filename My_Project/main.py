import sys
import cv2
import math
import os
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import pyqtSlot

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2

from hand_tracker import HandTracker
from gesture_logic import GestureLogic  # 使用提供的GestureLogic类
from apps.drawing_board import DrawingBoard
from apps.paddle_game import PaddleGame
from apps.paddle_versus import PaddleVersus 
from apps.vr_mode import VRMode
from apps.vr_pvp_mode import VRPVPMode

# 初始化MediaPipe手部解决方案
mp_hands = solutions.hands

class CameraLabel(QtWidgets.QLabel):
    """保持不变，用于显示摄像头画面和UI元素"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScaledContents(True)
        self.cursor_pos = None
        self.show_cursor = True
        self.show_buttons = True

        self.button_radius = 80
        self.button_spacing = 200
        self.buttons = {
            'Drawing': QtCore.QPoint(0, 0),
            'Game': QtCore.QPoint(0, 0),
            'VR': QtCore.QPoint(0, 0),
            'VR PVP': QtCore.QPoint(0, 0), 
            'Clear': QtCore.QPoint(0, 0)
        }

        self.hover_button = None
        self.hover_progress = 0.0
        self.clicked_button = None
        self.hand_gestures = []  # 存储手势信息用于显示
        self.official_gestures = []  # 存储官方模型识别的手势

    def update_button_positions(self):
        center_x = self.width() // 2
        center_y = self.height() // 2
        offset = -self.button_spacing
        for name in self.buttons.keys():
            self.buttons[name] = QtCore.QPoint(center_x + offset, center_y)
            offset += self.button_spacing

    def set_hand_gestures(self, gestures):
        self.hand_gestures = gestures
        self.update()

    def set_official_gestures(self, gestures):
        self.official_gestures = gestures
        self.update()

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

        # 合并后的手势标签显示逻辑
        for i in range(max(len(self.hand_gestures), len(self.official_gestures))):
            # 获取对应索引的手势数据（处理左右手可能数量不同的情况）
            hand_gesture = self.hand_gestures[i] if i < len(self.hand_gestures) else None
            official_gesture = self.official_gestures[i] if i < len(self.official_gestures) else None
            
            # 确定基础位置（优先使用原有手势位置，无则使用官方手势位置）
            if hand_gesture:
                x, y, _ = hand_gesture
            elif official_gesture:
                x, y, _ = official_gesture
            else:
                continue  # 无数据则跳过
            
            # 判断是否为pinch手势
            is_pinch = hand_gesture and "pinch" in hand_gesture[2].lower()
            
            # 根据是否为pinch手势选择显示内容和样式
            if is_pinch:
                # 显示原有pinch标签（黑色背景）
                gesture_text = hand_gesture[2].replace("_", " ")
                bg_color = QtGui.QColor(0, 0, 0, 180)
                rect_y = y - 25
                text_y = y
            else:
                # 显示官方模型识别结果（蓝色背景）
                if official_gesture:
                    gesture_text = official_gesture[2].replace("_", " ")
                else:
                    gesture_text = "unknown"  # 无官方结果时显示unknown
                bg_color = QtGui.QColor(0, 0, 255, 180)
                rect_y = y - 25  # 保持原有显示位置
                text_y = y
            
            # 绘制背景
            painter.setBrush(bg_color)
            painter.setPen(QtCore.Qt.NoPen)
            text_width = len(gesture_text) * 15
            painter.drawRoundedRect(x - 10, rect_y, text_width + 20, 35, 8, 8)
            
            # 绘制文本
            painter.setFont(QtGui.QFont('Arial', 12, QtGui.QFont.Bold))
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))
            painter.drawText(x, text_y, gesture_text)


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

        # 初始化手势分类器
        self._init_gesture_classifier()

        # 摄像头初始化
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if sys.platform.startswith('win') else 0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # 手势跟踪器 - 适配新的GestureLogic参数
        self.tracker = HandTracker(max_num_hands=2, min_detection_confidence=0.6, min_tracking_confidence=0.6)
        self.glogic = GestureLogic(
            pinch_threshold_px=40,        # 保留pinch阈值参数
            dwell_time=0.8,               # 停留时间参数
            angle_threshold=30,           # 新增角度阈值参数
            gesture_stability=3           # 新增手势稳定性参数
        )
        
        # 主容器
        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        # 场景1：主菜单
        self.menu_widget = QtWidgets.QWidget()
        vbox_menu = QtWidgets.QVBoxLayout(self.menu_widget)
        vbox_menu.setContentsMargins(0, 0, 0, 0)
        vbox_menu.setSpacing(0)
        self.cam_label = CameraLabel()
        vbox_menu.addWidget(self.cam_label)
        self.stack.addWidget(self.menu_widget)

        # 初始化应用实例变量
        self.drawing_app = None
        self.game_app = None
        self.vr_app = None
        self.vr_pvp_app = None

        self.current_mode = "menu"
        self.cam_label.update_button_positions()

        self.button_actions = {
            'Drawing': self._start_drawing,
            'Game': self._start_game,
            'VR': self._start_vr,
            'VR PVP': self._start_vr_pvp,  
            'Clear': self._clear_drawing
        }

        self.last_hover_name = None
        self.hover_start_time = QtCore.QTime.currentTime()

        # 主定时器
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(30)

    def _init_gesture_classifier(self):
        """初始化手势分类模型"""
        self.gesture_recognizer = None
        try:
            model_path = r"C:\Users\Hui\Documents\GitHub\AirCtrl2\My_Project\resource\gesture_recognizer.task"
            if os.path.exists(model_path):
                base_options = python.BaseOptions(model_asset_path=model_path)
                options = vision.GestureRecognizerOptions(base_options=base_options)
                self.gesture_recognizer = vision.GestureRecognizer.create_from_options(options)
                print(f"成功加载手势识别模型: {model_path}")
            else:
                print(f"模型文件不存在: {model_path}，将仅使用基础手势识别")
        except Exception as e:
            print(f"初始化手势分类器失败: {e}，将仅使用基础手势识别")

    def _process_frame_with_recognizer(self, frame):
        """使用官方模型处理帧并返回手势识别结果"""
        if not self.gesture_recognizer:
            return []
            
        try:
            # 转换为MediaPipe格式
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            
            # 识别手势
            result = self.gesture_recognizer.recognize(mp_image)
            
            # 处理结果
            gestures = []
            if result.gestures:
                for gesture in result.gestures:
                    # 获取最可能的手势
                    top_gesture = max(gesture, key=lambda g: g.score)
                    if top_gesture.score > 0.5:  # 过滤低置信度结果
                        # 获取手部 landmarks 用于定位显示
                        if result.hand_landmarks:
                            hand_landmarks = result.hand_landmarks[0]
                            # 使用手腕位置作为显示位置
                            wrist_x = hand_landmarks[0].x * frame.shape[1]
                            wrist_y = hand_landmarks[0].y * frame.shape[0]
                            gestures.append((wrist_x, wrist_y, top_gesture.category_name))
            
            return gestures
        except Exception as e:
            print(f"模型识别出错: {e}")
            return []

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
        self._cleanup_apps()
        event.accept()

    def _cleanup_apps(self):
        """清理所有应用实例，释放资源"""
        if self.drawing_app:
            self.stack.removeWidget(self.drawing_app)
            self.drawing_app.deleteLater()
            self.drawing_app = None
            
        if self.game_app:
            self.stack.removeWidget(self.game_app)
            self.game_app.deleteLater()
            self.game_app = None
            
        if self.vr_app:
            self.stack.removeWidget(self.vr_app)
            self.vr_app.deleteLater()
            self.vr_app = None
            
        if self.vr_pvp_app:
            self.stack.removeWidget(self.vr_pvp_app)
            self.vr_pvp_app.deleteLater()
            self.vr_pvp_app = None

    # 应用切换方法
    def _start_drawing(self):
        self._cleanup_apps()
        self.drawing_app = DrawingBoard()
        self.stack.addWidget(self.drawing_app)
        self.stack.setCurrentWidget(self.drawing_app)
        self.current_mode = "drawing"

    def _start_game(self):
        self._cleanup_apps()
        self.game_app = PaddleGame()
        self.stack.addWidget(self.game_app)
        self.stack.setCurrentWidget(self.game_app)
        self.current_mode = "game"

    def _clear_drawing(self):
        if self.current_mode == "drawing" and self.drawing_app:
            self.drawing_app.clear()
    
    def _start_vr(self):
        self._cleanup_apps()
        self.vr_app = VRMode(parent=self)
        self.stack.addWidget(self.vr_app)
        self.stack.setCurrentWidget(self.vr_app)
        self.current_mode = "vr"

    def _start_vr_pvp(self):
        self._cleanup_apps()
        self.vr_pvp_app = VRPVPMode(parent=self)
        self.stack.addWidget(self.vr_pvp_app)
        self.stack.setCurrentWidget(self.vr_pvp_app)
        self.current_mode = "vr_pvp"

    @pyqtSlot()
    def _return_to_menu(self):
        """返回主菜单，清理当前应用"""
        self.current_mode = "menu"
        self.stack.setCurrentWidget(self.menu_widget)
        QtCore.QTimer.singleShot(500, self._cleanup_apps)

    # 绘制手部关键点和连接线（使用官方21点连线）
    def _draw_hand_landmarks(self, frame, hands):
        # 仅在主页面使用官方连线
        if self.current_mode == "menu":
            # 转换为RGB用于MediaPipe绘制
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 创建一个空白图像用于绘制手部关键点
            annotated_image = frame.copy()
            
            for hand in hands:
                # 将手部关键点转换为MediaPipe格式
                landmarks = hand['landmarks']
                mp_landmarks = landmark_pb2.NormalizedLandmarkList()
                for x, y, z in landmarks:
                    # 归一化坐标
                    h, w, _ = frame.shape
                    norm_x = x / w
                    norm_y = y / h
                    mp_landmarks.landmark.add(x=norm_x, y=norm_y, z=z)
                
                # 使用MediaPipe的官方绘制方法
                solutions.drawing_utils.draw_landmarks(
                    annotated_image,
                    mp_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    solutions.drawing_styles.get_default_hand_landmarks_style(),
                    solutions.drawing_styles.get_default_hand_connections_style()
                )
            
            return annotated_image
        else:
            # 在其他页面使用原有绘制方式
            for hand in hands:
                landmarks = hand['landmarks']
                
                # 绘制连接线
                for (start, end) in [
                    (0, 1), (1, 2), (2, 3), (3, 4),  # 拇指
                    (0, 5), (5, 6), (6, 7), (7, 8),  # 食指
                    (0, 9), (9, 10), (10, 11), (11, 12),  # 中指
                    (0, 13), (13, 14), (14, 15), (15, 16),  # 无名指
                    (0, 17), (17, 18), (18, 19), (19, 20)   # 小指
                ]:
                    x1, y1, _ = landmarks[start]
                    x2, y2, _ = landmarks[end]
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                # 绘制所有21个关键点
                for (x, y, _) in landmarks:
                    cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
            
            return frame

    # 获取手势信息用于显示
    def _get_gesture_info(self, hands):
        gesture_info = []
        for hand in hands:
            # 使用GestureLogic获取手势（保持原有逻辑不变）
            gesture = self.glogic.get_hand_gesture(hand) or "unknown"
            
            if gesture and gesture != "unknown":
                # 使用手腕位置作为手势标签位置
                wrist_x, wrist_y, _ = hand['landmarks'][0]
                # 稍微偏移避免遮挡
                display_x = wrist_x - 50
                display_y = wrist_y - 30
                gesture_info.append((display_x, display_y, gesture))
        return gesture_info

    def _update(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.flip(frame, 1)
        annotated, hands = self.tracker.process(frame)
        
        # 绘制手掌连线和关键点（根据当前模式使用不同绘制方式）
        annotated = self._draw_hand_landmarks(annotated, hands)

        if self.current_mode == "menu":
            # 转换为RGB用于显示和模型处理
            frame_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            h, w, _ = frame_rgb.shape
            
            # 仅在主页面使用官方模型识别手势
            official_gestures = self._process_frame_with_recognizer(frame_rgb)
            
            # 转换为QPixmap显示
            qt_img = QtGui.QImage(frame_rgb.data, w, h, QtGui.QImage.Format_RGB888)
            pix = QtGui.QPixmap.fromImage(qt_img).scaled(self.cam_label.size(),
                                                         QtCore.Qt.KeepAspectRatioByExpanding)
            self.cam_label.setPixmap(pix)

            # 更新原有手势信息显示
            gesture_info = self._get_gesture_info(hands)
            # 坐标映射到UI尺寸
            mapped_gestures = []
            scale_x = self.cam_label.width() / w
            scale_y = self.cam_label.height() / h
            for (x, y, gesture) in gesture_info:
                mapped_x = int(x * scale_x)
                mapped_y = int(y * scale_y)
                mapped_gestures.append((mapped_x, mapped_y, gesture))
            self.cam_label.set_hand_gestures(mapped_gestures)

            # 处理官方模型识别的手势并显示
            mapped_official = []
            for (x, y, gesture) in official_gestures:
                mapped_x = int(x * scale_x)
                mapped_y = int(y * scale_y)
                mapped_official.append((mapped_x, mapped_y, gesture))
            self.cam_label.set_official_gestures(mapped_official)

            # 手指位置处理
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
            # 优先右手作为主控制手
            primary = next((h for h in hands if h['handedness'] == 'Right'), hands[0] if hands else None)
            
            # 保留pinch手势功能 - 返回主菜单
            if primary and self.glogic.is_pinch(primary) and self.current_mode not in ["drawing", "vr_pvp"]:
                self._return_to_menu()
                return

            # 更新应用
            index_tip = self.glogic.extract_index_tip(hands)
            target_pos = None
            if index_tip is not None:
                frame_h, frame_w = frame.shape[:2]
                rel_x = index_tip[0] / frame_w
                rel_y = index_tip[1] / frame_h
                app_w = self.stack.currentWidget().width()
                app_h = self.stack.currentWidget().height()
                target_pos = (int(rel_x * app_w), int(rel_y * app_h))

            # 判断是否捏合（用于绘图等功能）
            is_pinch = primary and self.glogic.is_pinch(primary)

            # 根据当前模式更新对应应用
            if self.current_mode == "drawing" and self.drawing_app:
                self.drawing_app.update_cursor(target_pos, is_pinch)  # 传递pinch状态
            elif self.current_mode == "game" and self.game_app:
                self.game_app.update_cursor(target_pos)
            elif self.current_mode == "vr" and self.vr_app:
                if frame is not None:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.vr_app.update_camera_frame(frame_rgb.copy())
                
                palm_center = None
                if hands:
                    primary = next((h for h in hands if h['handedness'] == 'Right'), hands[0])
                    if primary:
                        x, y, _ = primary['landmarks'][0]
                        frame_h, frame_w = frame.shape[:2]
                        app_w = self.stack.currentWidget().width()
                        app_h = self.stack.currentWidget().height()
                        palm_center = (int(x * app_w / frame_w), int(y * app_h / frame_h))
                
                self.vr_app.update_hand_position(palm_center)
            elif self.current_mode == "vr_pvp" and self.vr_pvp_app:
                if frame is not None:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.vr_pvp_app.update_camera_background(frame_rgb)
                
                # 分离左右手控制
                left_hand = next((h for h in hands if h['handedness'] == 'Left'), None)
                right_hand = next((h for h in hands if h['handedness'] == 'Right'), None)
                
                pos1 = None
                if left_hand:
                    x, y, _ = left_hand['landmarks'][0]
                    frame_h, frame_w = frame.shape[:2]
                    app_w = self.stack.currentWidget().width()
                    app_h = self.stack.currentWidget().height()
                    pos1 = (int(x * app_w / frame_w), int(y * app_h / frame_h))
                
                pos2 = None
                if right_hand:
                    x, y, _ = right_hand['landmarks'][0]
                    frame_h, frame_w = frame.shape[:2]
                    app_w = self.stack.currentWidget().width()
                    app_h = self.stack.currentWidget().height()
                    pos2 = (int(x * app_w / frame_w), int(y * app_h / frame_h))
                
                self.vr_pvp_app.update_hand_positions(pos1, pos2)

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