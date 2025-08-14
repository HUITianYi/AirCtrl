from PyQt5 import QtCore, QtGui

# 新增游戏适配包装类，不修改原游戏逻辑
class GameAdapter:
    """游戏适配包装类，用于在不修改原游戏的情况下添加pinch支持"""
    
    @staticmethod
    def wrap_paddle_game(original_game):
        """包装挡板游戏以支持pinch状态"""
        class WrappedPaddleGame(original_game):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.pinch_state = False  # 新增pinch状态存储
                
            def set_pinch_state(self, state):
                """新增方法用于设置pinch状态"""
                self.pinch_state = state
                # 在这里映射pinch状态到游戏操作（如暂停）
                if self.pinch_state:
                    # 模拟空格键按下以暂停游戏（不修改原游戏逻辑）
                    event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, QtCore.Qt.Key_Space, QtCore.Qt.NoModifier)
                    QtCore.QCoreApplication.postEvent(self, event)
                    
        return WrappedPaddleGame
    
    @staticmethod
    def wrap_third_game(original_game):
        """包装第三游戏以支持pinch状态"""
        class WrappedThirdGame(original_game):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.pinch_state = False
                
            def set_pinch(self, state):
                """新增方法用于接收pinch状态"""
                if state and not self.pinch_state:
                    # 当检测到捏合时，模拟鼠标点击
                    center_x = self.width() // 2
                    center_y = self.height() // 2
                    click_event = QtGui.QMouseEvent(
                        QtCore.QEvent.MouseButtonPress,
                        QtCore.QPoint(center_x, center_y),
                        QtCore.Qt.LeftButton,
                        QtCore.Qt.LeftButton,
                        QtCore.Qt.NoModifier
                    )
                    QtCore.QCoreApplication.postEvent(self, click_event)
                    
                self.pinch_state = state
                
        return WrappedThirdGame
    