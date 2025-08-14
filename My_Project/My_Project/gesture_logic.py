import math
import time
from collections import deque

class GestureLogic:
    """
    高级手势识别逻辑，基于关节角度计算实现更精准的手势判断
    支持多种手势：捏合、握拳、五指张开、三指张开、食指指向上、点赞等
    """
    def __init__(self, 
                 pinch_threshold_px=40, 
                 dwell_time=0.6,
                 angle_threshold=30,  # 关节弯曲角度阈值（度）
                 gesture_stability=3):  # 手势稳定帧数
        self.pinch_threshold_px = pinch_threshold_px
        self.dwell_time = dwell_time
        self.angle_threshold = angle_threshold  # 小于此角度认为关节弯曲
        self.gesture_stability = gesture_stability  # 需要连续识别相同手势的帧数
        
        # 存储最近的手势识别结果，用于稳定性判断
        self.gesture_history = deque(maxlen=gesture_stability)
        
        # 悬停点击相关变量
        self._hover_start = None
        self._hover_pos = None
        
        # 存储分类器结果（如果使用外部分类器）
        self.classifier_result = None

    @staticmethod
    def _distance(a, b):
        """计算两点之间的欧氏距离"""
        return math.hypot(a[0]-b[0], a[1]-b[1])

    @staticmethod
    def _calculate_angle(a, b, c):
        """
        计算三点形成的角度（b为顶点）
        返回角度（度），0-180
        """
        # 向量计算
        ab = (a[0]-b[0], a[1]-b[1])
        bc = (c[0]-b[0], c[1]-b[1])
        
        # 点积
        dot_product = ab[0] * bc[0] + ab[1] * bc[1]
        # 模长
        mag_ab = math.sqrt(ab[0]**2 + ab[1]** 2)
        mag_bc = math.sqrt(bc[0]**2 + bc[1]** 2)
        
        if mag_ab == 0 or mag_bc == 0:
            return 180.0  # 避免除以零
        
        # 计算余弦值并转换为角度
        cos_theta = dot_product / (mag_ab * mag_bc)
        # 防止数值误差导致的范围问题
        cos_theta = max(min(cos_theta, 1.0), -1.0)
        theta_rad = math.acos(cos_theta)
        
        return math.degrees(theta_rad)

    def extract_index_tip(self, hands):
        """提取食指指尖位置"""
        if not hands:
            return None
        # 优先右手
        right = next((h for h in hands if h['handedness'] == 'Right'), None)
        chosen = right or hands[0]
        try:
            x,y,_ = chosen['landmarks'][8]  # 食指尖(8)
            return (x,y)
        except Exception:
            return None

    def is_pinch(self, hand):
        """判断拇指和食指是否捏合"""
        if not hand:
            return False
        lm = hand['landmarks']
        thumb_tip = lm[4][:2]
        index_tip = lm[8][:2]
        return self._distance(thumb_tip, index_tip) < self.pinch_threshold_px

    def check_dwell_click(self, pos):
        """基于位置停留判断点击"""
        now = time.time()
        if pos is None:
            self._hover_start = None
            self._hover_pos = None
            return False

        if self._hover_pos is None:
            self._hover_pos = pos
            self._hover_start = now
            return False

        # 若移动超出容差，则重置
        if self._distance(pos, self._hover_pos) > 20:
            self._hover_pos = pos
            self._hover_start = now
            return False

        if now - self._hover_start >= self.dwell_time:
            # 触发一次点击并重置
            self._hover_start = now + 9999  # 避免重复触发
            return True

    def extract_palm_center(self, hands):
        """提取手掌中心位置（手腕点）"""
        if not hands:
            return None
        
        # 优先右手
        right = next((h for h in hands if h['handedness'] == 'Right'), None)
        chosen = right or hands[0]
        try:
            x,y,_ = chosen['landmarks'][0]  # 手腕点(0)
            return (x,y)
        except Exception:
            return None

    # 手指弯曲判断（基于关节角度）
    def is_thumb_bent(self, hand):
        """判断拇指是否弯曲"""
        if not hand:
            return True  # 默认视为弯曲
            
        lm = hand['landmarks']
        # 拇指关节点：掌指关节(1)、近节指骨(2)、远节指骨(3)、指尖(4)
        angle1 = self._calculate_angle(lm[0], lm[1], lm[2])  # 手腕-拇指根-拇指第一关节
        angle2 = self._calculate_angle(lm[1], lm[2], lm[3])  # 拇指根-第一关节-第二关节
        
        # 两个关节中只要有一个明显弯曲，就认为拇指弯曲
        return angle1 < self.angle_threshold + 20 or angle2 < self.angle_threshold

    def is_index_bent(self, hand):
        """判断食指是否弯曲"""
        if not hand:
            return True
            
        lm = hand['landmarks']
        # 食指关节点：掌指关节(5)、近节指骨(6)、中节指骨(7)、指尖(8)
        angle1 = self._calculate_angle(lm[0], lm[5], lm[6])  # 手腕-食指根-食指第一关节
        angle2 = self._calculate_angle(lm[5], lm[6], lm[7])  # 食指根-第一关节-第二关节
        
        # 两个关节都需要判断
        return angle1 < self.angle_threshold or angle2 < self.angle_threshold - 10

    def is_middle_bent(self, hand):
        """判断中指是否弯曲"""
        if not hand:
            return True
            
        lm = hand['landmarks']
        # 中指关节点：掌指关节(9)、近节指骨(10)、中节指骨(11)、指尖(12)
        angle1 = self._calculate_angle(lm[0], lm[9], lm[10])
        angle2 = self._calculate_angle(lm[9], lm[10], lm[11])
        
        return angle1 < self.angle_threshold or angle2 < self.angle_threshold - 10

    def is_ring_bent(self, hand):
        """判断无名指是否弯曲"""
        if not hand:
            return True
            
        lm = hand['landmarks']
        # 无名指关节点：掌指关节(13)、近节指骨(14)、中节指骨(15)、指尖(16)
        angle1 = self._calculate_angle(lm[0], lm[13], lm[14])
        angle2 = self._calculate_angle(lm[13], lm[14], lm[15])
        
        return angle1 < self.angle_threshold or angle2 < self.angle_threshold - 10

    def is_pinky_bent(self, hand):
        """判断小指是否弯曲"""
        if not hand:
            return True
            
        lm = hand['landmarks']
        # 小指关节点：掌指关节(17)、近节指骨(18)、中节指骨(19)、指尖(20)
        angle1 = self._calculate_angle(lm[0], lm[17], lm[18])
        angle2 = self._calculate_angle(lm[17], lm[18], lm[19])
        
        return angle1 < self.angle_threshold or angle2 < self.angle_threshold - 10

    # 手指张开判断（弯曲的反义）
    def is_thumb_open(self, hand):
        return not self.is_thumb_bent(hand)
        
    def is_index_open(self, hand):
        return not self.is_index_bent(hand)
        
    def is_middle_open(self, hand):
        return not self.is_middle_bent(hand)
        
    def is_ring_open(self, hand):
        return not self.is_ring_bent(hand)
        
    def is_pinky_open(self, hand):
        return not self.is_pinky_bent(hand)

    # 具体手势判断
    def is_five_fingers_open(self, hand):
        """判断是否五指张开"""
        if not hand:
            return False
            
        # 所有手指都必须张开，且手掌有一定张开度
        return (self.is_thumb_open(hand) and 
                self.is_index_open(hand) and 
                self.is_middle_open(hand) and 
                self.is_ring_open(hand) and 
                self.is_pinky_open(hand) and
                # 额外检查手掌张开程度（拇指根到小指根的距离）
                self._distance(hand['landmarks'][1][:2], hand['landmarks'][17][:2]) > 100)

    def is_three_fingers_open(self, hand):
        """判断是否食指、中指、大拇指张开（三指张开）"""
        if not hand:
            return False
            
        # 拇指、食指、中指张开，无名指和小指弯曲
        return (self.is_thumb_open(hand) and 
                self.is_index_open(hand) and 
                self.is_middle_open(hand) and 
                self.is_ring_bent(hand) and 
                self.is_pinky_bent(hand))

    def is_fist(self, hand):
        """判断是否握拳"""
        if not hand:
            return False
            
        # 所有手指都弯曲，且拇指包裹在其他手指上
        thumb_tip = hand['landmarks'][4][:2]
        index_mcp = hand['landmarks'][5][:2]
        
        return (self.is_thumb_bent(hand) and 
                self.is_index_bent(hand) and 
                self.is_middle_bent(hand) and 
                self.is_ring_bent(hand) and 
                self.is_pinky_bent(hand) and
                # 拇指尖靠近食指根部，表明握拳状态
                self._distance(thumb_tip, index_mcp) < 50)

    def is_index_up(self, hand):
        """判断是否仅食指张开（指示手势）"""
        if not hand:
            return False
            
        # 只有食指张开，其他手指弯曲
        return (self.is_thumb_bent(hand) and 
                self.is_index_open(hand) and 
                self.is_middle_bent(hand) and 
                self.is_ring_bent(hand) and 
                self.is_pinky_bent(hand))

    def is_thumb_up(self, hand):
        """判断是否点赞手势（仅拇指张开）"""
        if not hand:
            return False
            
        # 只有拇指张开，其他手指弯曲
        return (self.is_thumb_open(hand) and 
                self.is_index_bent(hand) and 
                self.is_middle_bent(hand) and 
                self.is_ring_bent(hand) and 
                self.is_pinky_bent(hand) and
                # 确保拇指向上（y坐标低于掌指关节）
                hand['landmarks'][4][1] < hand['landmarks'][1][1])

    def is_victory(self, hand):
        """判断是否胜利手势（食指和中指张开）"""
        if not hand:
            return False
            
        # 食指和中指张开，其他手指弯曲
        return (self.is_thumb_bent(hand) and 
                self.is_index_open(hand) and 
                self.is_middle_open(hand) and 
                self.is_ring_bent(hand) and 
                self.is_pinky_bent(hand))

    def is_iloveyou(self, hand):
        """判断是否爱心手势（食指、中指和拇指张开）"""
        if not hand:
            return False
            
        # 食指、中指和拇指张开，无名指和小指弯曲
        return (self.is_thumb_open(hand) and 
                self.is_index_open(hand) and 
                self.is_middle_open(hand) and 
                self.is_ring_bent(hand) and 
                self.is_pinky_bent(hand))

    def set_classifier_result(self, result):
        """设置外部分类器的结果"""
        self.classifier_result = result

    def get_hand_gesture(self, hand):
        """
        获取稳定的手部手势类型
        加入手势稳定性判断，避免瞬间误判
        """
        if not hand:
            self.gesture_history.clear()
            return None
            
        # 单次手势识别
        current_gesture = None
        
        # 优先判断特殊交互手势
        if self.is_pinch(hand):
            current_gesture = "pinch"
        elif self.is_fist(hand):
            current_gesture = "Closed_Fist"
        elif self.is_thumb_up(hand):
            current_gesture = "Thumb_Up"
        elif self.is_index_up(hand):
            current_gesture = "Pointing_Up"
        elif self.is_five_fingers_open(hand):
            current_gesture = "Open_Palm"
        elif self.is_victory(hand):
            current_gesture = "Victory"
        elif self.is_iloveyou(hand):
            current_gesture = "ILoveYou"
        elif self.is_three_fingers_open(hand):
            current_gesture = "three_fingers_open"
        else:
            current_gesture = "Unknown"
            
        # 添加到历史记录
        self.gesture_history.append(current_gesture)
        
        # 只有当连续识别到相同手势时才确认
        if len(self.gesture_history) == self.gesture_stability:
            # 检查历史记录中是否大多数是同一手势
            gesture_counts = {}
            for g in self.gesture_history:
                gesture_counts[g] = gesture_counts.get(g, 0) + 1
            
            # 找到出现次数最多的手势
            most_common = max(gesture_counts.items(), key=lambda x: x[1])
            if most_common[1] >= self.gesture_stability * 0.6:  # 超过60%的帧一致
                return most_common[0]
        
        # 尚未达到稳定状态，返回None或上一次确认的手势
        return None if len(self.gesture_history) < self.gesture_stability else self.gesture_history[-1]
