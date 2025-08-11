from PyQt5 import QtWidgets, QtGui, QtCore

class DrawingBoard(QtWidgets.QWidget):
    """
    简单的画板，用手指（index tip）绘制线条。
    接口：
      - update_cursor(pos, is_drawing): 每帧调用 pos=(x,y) or None, is_drawing: bool (True 绘制)
      - clear()
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)
        self.setAttribute(QtCore.Qt.WA_StaticContents)
        self.pen_width = 6
        self.pen_color = QtGui.QColor(10, 10, 200)
        self.image = QtGui.QImage(self.size(), QtGui.QImage.Format_RGB32)
        self.image.fill(QtGui.QColor('white'))
        self.last_point = None

    def resizeEvent(self, event):
        if self.image.size() != self.size():
            new_img = QtGui.QImage(self.size(), QtGui.QImage.Format_RGB32)
            new_img.fill(QtGui.QColor('white'))
            painter = QtGui.QPainter(new_img)
            painter.drawImage(0,0, self.image)
            painter.end()
            self.image = new_img
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawImage(0,0, self.image)
        painter.end()

    def update_cursor(self, pos, is_drawing):
        """
        pos: (x,y) in widget coords or None
        is_drawing: True means draw a point/line to pos
        """
        if pos is None:
            self.last_point = None
            return

        x,y = pos
        painter = QtGui.QPainter(self.image)
        pen = QtGui.QPen(self.pen_color, self.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        if is_drawing and self.last_point is not None:
            painter.drawLine(self.last_point[0], self.last_point[1], x, y)
        else:
            # draw dot
            painter.drawPoint(x, y)
        painter.end()
        self.last_point = (x,y)
        self.update()

    def clear(self):
        self.image.fill(QtGui.QColor('white'))
        self.update()
