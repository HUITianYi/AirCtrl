import mediapipe as mp
import cv2

class HandTracker:
    """
    封装 MediaPipe Hands。process(frame) 接受 BGR 图像，返回 landmark 列表（像素坐标）。
    每只手为一个长度 21 的 (x, y, z) 列表（x,y 为像素坐标，z 为相对深度）。
    """
    def __init__(self,
                 static_image_mode=False,
                 max_num_hands=2,
                 min_detection_confidence=0.7,
                 min_tracking_confidence=0.7):
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mpDraw = mp.solutions.drawing_utils

    def process(self, frame_bgr):
        """
        处理 BGR 帧并返回 (annotated_frame, hands_list)
        hands_list: 每个手为字典 {'landmarks': [(x_px,y_px,z), ...], 'handedness': 'Left'/'Right'}
        annotated_frame: 未改变图像或可供可视化的同一帧（BGR）
        """
        img_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)
        h, w = frame_bgr.shape[:2]
        hands_out = []

        if results.multi_hand_landmarks:
            for hand_landmarks, hand_handedness in zip(results.multi_hand_landmarks, 
                                                       results.multi_handedness):
                lm_list = []
                for lm in hand_landmarks.landmark:
                    x_px = int(lm.x * w)
                    y_px = int(lm.y * h)
                    lm_list.append((x_px, y_px, lm.z))
                handedness_label = hand_handedness.classification[0].label
                hands_out.append({'landmarks': lm_list, 'handedness': handedness_label})

        return frame_bgr, hands_out

    def close(self):
        if self.hands:
            self.hands.close()
