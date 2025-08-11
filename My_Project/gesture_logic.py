import math
import time

class GestureLogic:
    """
    将 hand landmarks 转化为交互语义
    - index_tip(): 返回第一个检测到手的 食指尖点 (id 8) 的像素坐标或 None
    - is_pinch(): 检测拇指尖(4) 与食指尖(8) 是否靠近（作为点击）
    - dwell_click: 如果食指持续悬停在某区域超过 dwell_time -> 触发点击
    """
    def __init__(self, pinch_threshold_px=50, dwell_time=0.6):
        self.pinch_threshold_px = pinch_threshold_px
        self.dwell_time = dwell_time
        self._hover_start = None
        self._hover_pos = None

    @staticmethod
    def _distance(a, b):
        return math.hypot(a[0]-b[0], a[1]-b[1])

    def extract_index_tip(self, hands):
        """
        hands: hand list from HandTracker.process
        返回 (x,y) 或 None（优先右手，然后左手，最后任意手）
        """
        if not hands:
            return None
        # prefer Right hand if present
        right = next((h for h in hands if h['handedness'] == 'Right'), None)
        chosen = right or hands[0]
        try:
            x,y,_ = chosen['landmarks'][8]  # index tip
            return (x,y)
        except Exception:
            return None

    def is_pinch(self, hand):
        """
        hand: 单只手 dict (landmarks)
        基于拇指尖(4) 与食指尖(8) 距离判断
        """
        if not hand:
            return False
        lm = hand['landmarks']
        a = lm[4][:2]
        b = lm[8][:2]
        return self._distance(a,b) < self.pinch_threshold_px

    def check_dwell_click(self, pos):
        """
        基于位置停留判断点击（适用于无捏合硬点击时）
        pos: (x,y) 或 None
        返回 True/False 表示是否发出一次点击（单次触发）
        """
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
            # 触发一次点击并重置（避免重复触发）
            self._hover_start = now + 9999  # 设置大值避免重复触发，直到位置改变
            return True

        return False
