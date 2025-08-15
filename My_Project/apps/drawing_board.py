from PyQt5 import QtWidgets, QtGui, QtCore
import time
import os

class DrawingBoard(QtWidgets.QWidget):
    """
    改进的画板：
    - 增大手指位置提示点，在所有工具模式下均有效
    - 使用捏合手势作为落笔动作
    - 画笔光标始终显示在最上层
    - 支持贴图功能
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)
        self.setAttribute(QtCore.Qt.WA_StaticContents)
        
        # 分屏比例
        self.toolbar_width = 200  # 工具栏宽度
        
        # 绘图参数
        self.pen_width = 6
        self.pen_color = QtGui.QColor(10, 10, 200)
        self.eraser_width = 20
        self.current_tool = 'pen'  # 'pen', 'eraser', 'drag', 'sticker'
        
        # 光标尺寸参数（增大提示点）
        self.cursor_outer_radius = 40  # 外圆半径
        self.cursor_inner_radius = 15  # 内圆半径
        self.cursor_cross_length = 12  # 十字线长度
        
        # 图像和状态
        self.image = QtGui.QImage(self.size(), QtGui.QImage.Format_RGB32)
        self.image.fill(QtGui.QColor('white'))
        self.last_point = None
        self.drag_start = None
        self.drag_offset = QtCore.QPoint(0, 0)
        
        # 光标设置（始终显示在最上层）
        self.cursor_pos = None
        self.cursor_visible = False
        
        # 贴图功能
        self.stickers = []  # 存储已放置的贴图
        self.available_stickers = self._load_stickers()  # 可用贴图
        self.selected_sticker_idx = 0  # 当前选中的贴图索引
        self.placing_sticker = None  # 正在放置的贴图
        
        # 工具栏按钮
        self.tools = [
            {'name': 'pen', 'text': '画笔', 'rect': None},
            {'name': 'eraser', 'text': '橡皮', 'rect': None},
            {'name': 'drag', 'text': '拖拽', 'rect': None},
            {'name': 'sticker', 'text': '贴图', 'rect': None},
            {'name': 'clear', 'text': '清除', 'rect': None},
            {'name': 'back', 'text': '返回', 'rect': None}
        ]
        
        # 颜色选择
        self.colors = [
            QtGui.QColor('black'), QtGui.QColor('red'),
            QtGui.QColor('green'), QtGui.QColor('blue'),
            QtGui.QColor('yellow'), QtGui.QColor('purple')
        ]
        self.color_rects = []
        
        # 手势状态
        self.hover_tool = None
        self.hover_start = None
        self.dwell_time = 0.8
        self.last_hover_tool = None
        
        # 绘制状态跟踪
        self.is_drawing = False

    def _load_stickers(self):
        """加载可用的贴图"""
        stickers = []
        try:
            # 创建示例贴图
            for i in range(3):
                sticker = QtGui.QImage(100, 100, QtGui.QImage.Format_ARGB32)
                sticker.fill(QtGui.QColor(0, 0, 0, 0))  # 透明背景
                painter = QtGui.QPainter(sticker)
                
                # 不同颜色的示例形状
                colors = [QtGui.QColor(255, 0, 0, 180), 
                          QtGui.QColor(0, 255, 0, 180), 
                          QtGui.QColor(0, 0, 255, 180)]
                
                painter.setBrush(colors[i])
                painter.setPen(QtCore.Qt.NoPen)
                
                if i == 0:
                    painter.drawEllipse(10, 10, 80, 80)  # 圆形
                elif i == 1:
                    painter.drawRect(10, 10, 80, 80)     # 方形
                else:
                    painter.drawPolygon(
                        QtGui.QPolygon([
                            QtCore.QPoint(50, 10),
                            QtCore.QPoint(90, 90),
                            QtCore.QPoint(10, 90)
                        ])
                    )  # 三角形
                painter.end()
                stickers.append(sticker)
        except Exception as e:
            print(f"加载贴图失败: {e}")
        
        return stickers

    def resizeEvent(self, event):
        # 计算工具栏按钮位置
        toolbar_height = self.height()
        button_height = min(60, toolbar_height // 10)
        top_margin = 20
        
        # 更新工具按钮位置
        for i, tool in enumerate(self.tools):
            tool['rect'] = QtCore.QRect(
                10, 
                top_margin + i * (button_height + 10),
                self.toolbar_width - 20,
                button_height
            )
        
        # 更新颜色选择位置
        self.color_rects = []
        color_top = top_margin + len(self.tools) * (button_height + 10) + 20
        color_size = 30
        colors_per_row = 3
        for i, color in enumerate(self.colors):
            row = i // colors_per_row
            col = i % colors_per_row
            self.color_rects.append({
                'color': color,
                'rect': QtCore.QRect(
                    20 + col * (color_size + 10),
                    color_top + row * (color_size + 10),
                    color_size,
                    color_size
                )
            })
        
        # 更新贴图选择位置
        self.sticker_rects = []
        if self.available_stickers:
            sticker_top = color_top + (len(self.colors) // colors_per_row + 1) * (color_size + 10) + 20
            sticker_size = 60
            stickers_per_row = 2
            for i, sticker in enumerate(self.available_stickers):
                row = i // stickers_per_row
                col = i % stickers_per_row
                self.sticker_rects.append({
                    'index': i,
                    'rect': QtCore.QRect(
                        20 + col * (sticker_size + 10),
                        sticker_top + row * (sticker_size + 10),
                        sticker_size,
                        sticker_size
                    )
                })
        
        # 调整图像大小
        if self.image.size() != self.size():
            new_img = QtGui.QImage(self.size(), QtGui.QImage.Format_RGB32)
            new_img.fill(QtGui.QColor('white'))
            painter = QtGui.QPainter(new_img)
            painter.drawImage(self.drag_offset.x(), self.drag_offset.y(), self.image)
            painter.end()
            self.image = new_img
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        
        # 1. 绘制工具栏背景
        painter.fillRect(0, 0, self.toolbar_width, self.height(), QtGui.QColor(50, 50, 50))
        
        # 2. 绘制工具按钮
        for tool in self.tools:
            # 按钮背景
            if tool['name'] == self.hover_tool:
                painter.fillRect(tool['rect'], QtGui.QColor(100, 100, 200))
            else:
                painter.fillRect(tool['rect'], QtGui.QColor(70, 70, 100))
            
            # 按钮文本
            painter.setPen(QtGui.QColor('white'))
            painter.drawText(tool['rect'], QtCore.Qt.AlignCenter, tool['text'])
            
            # 当前选中的工具标记
            if tool['name'] == self.current_tool:
                painter.setPen(QtGui.QPen(QtGui.QColor('yellow'), 3))
                painter.drawRect(tool['rect'])
        
        # 3. 绘制颜色选择
        painter.setPen(QtGui.QColor('white'))
        painter.drawText(10, self.color_rects[0]['rect'].y() - 15, "颜色:")
        for color_item in self.color_rects:
            painter.fillRect(color_item['rect'], color_item['color'])
            if color_item['color'] == self.pen_color:
                painter.setPen(QtGui.QPen(QtGui.QColor('yellow'), 2))
                painter.drawRect(color_item['rect'])
        
        # 4. 绘制贴图选择
        if self.available_stickers and self.sticker_rects:
            painter.setPen(QtGui.QColor('white'))
            painter.drawText(10, self.sticker_rects[0]['rect'].y() - 15, "贴图:")
            for sticker_item in self.sticker_rects:
                # 绘制贴图预览
                sticker = self.available_stickers[sticker_item['index']]
                painter.drawImage(
                    sticker_item['rect'].topLeft(), 
                    sticker.scaled(
                        sticker_item['rect'].size(), 
                        QtCore.Qt.KeepAspectRatio, 
                        QtCore.Qt.SmoothTransformation
                    )
                )
                # 选中的贴图标记
                if sticker_item['index'] == self.selected_sticker_idx:
                    painter.setPen(QtGui.QPen(QtGui.QColor('yellow'), 2))
                    painter.drawRect(sticker_item['rect'])
        
        # 5. 绘制画布和已放置的贴图
        painter.drawImage(
            self.toolbar_width + self.drag_offset.x(), 
            self.drag_offset.y(), 
            self.image
        )
        
        # 6. 绘制已放置的贴图
        for sticker in self.stickers:
            painter.drawImage(
                self.toolbar_width + self.drag_offset.x() + sticker['x'],
                self.drag_offset.y() + sticker['y'],
                sticker['image']
            )
        
        # 7. 绘制正在放置的贴图
        if self.placing_sticker:
            painter.setOpacity(0.7)  # 半透明效果
            painter.drawImage(
                self.placing_sticker['x'],
                self.placing_sticker['y'],
                self.placing_sticker['image']
            )
            painter.setOpacity(1.0)
        
        # 8. 绘制画笔光标（最后绘制，确保在最上层）
        if self.cursor_visible and self.cursor_pos:
            self._draw_cursor(painter)
        
        painter.end()

    def _draw_cursor(self, painter):
        """绘制自定义光标，所有工具模式下均显示大光点"""
        x, y = self.cursor_pos
        
        # 所有工具模式下都显示大光点作为基础
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 0), 2))
        # 外圆
        painter.drawEllipse(
            int(x - self.cursor_outer_radius), 
            int(y - self.cursor_outer_radius), 
            self.cursor_outer_radius * 2, 
            self.cursor_outer_radius * 2
        )
        # 内圆
        painter.setBrush(QtGui.QColor(0, 120, 255, 180))
        painter.setPen(QtGui.QPen(QtGui.QColor('white'), 1))
        painter.drawEllipse(
            int(x - self.cursor_inner_radius), 
            int(y - self.cursor_inner_radius), 
            self.cursor_inner_radius * 2, 
            self.cursor_inner_radius * 2
        )
        # 十字线
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 2))
        painter.drawLine(
            int(x - self.cursor_cross_length), y, 
            int(x + self.cursor_cross_length), y
        )
        painter.drawLine(
            x, int(y - self.cursor_cross_length), 
            x, int(y + self.cursor_cross_length)
        )
        
        # 根据工具类型添加特定指示
        if self.current_tool == 'pen':
            # 画笔工具：在中心显示画笔大小和颜色
            pen_x = int(x - self.pen_width/2)
            pen_y = int(y - self.pen_width/2)
            painter.setBrush(QtGui.QBrush(self.pen_color))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(pen_x, pen_y, self.pen_width, self.pen_width)
        elif self.current_tool == 'eraser':
            # 橡皮工具：在中心显示橡皮大小
            eraser_x = int(x - self.eraser_width/2)
            eraser_y = int(y - self.eraser_width/2)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0), 2))
            painter.drawEllipse(eraser_x, eraser_y, self.eraser_width, self.eraser_width)

    def update_cursor(self, pos, is_drawing):
        """更新光标位置和状态，使用is_drawing作为落笔信号"""
        # 更新光标位置和可见性
        self.cursor_pos = pos
        self.cursor_visible = (pos is not None)
        self.is_drawing = is_drawing  # 更新绘制状态
        
        if pos is None:
            self.last_point = None
            self.drag_start = None
            self.hover_tool = None
            self.hover_start = None
            self.placing_sticker = None
            self.update()
            return

        x, y = pos
        now = time.time()
        
        # 检查是否在工具栏区域
        if x < self.toolbar_width:
            # 重置绘图状态
            self.last_point = None
            self.drag_start = None
            self.placing_sticker = None
            
            # 检查悬停在哪个工具上
            current_hover = None
            
            # 检查工具按钮
            for tool in self.tools:
                if tool['rect'].contains(QtCore.QPoint(x, y)):
                    current_hover = tool['name']
                    break
            
            # 检查颜色选择
            if current_hover is None:
                for i, color_item in enumerate(self.color_rects):
                    if color_item['rect'].contains(QtCore.QPoint(x, y)):
                        current_hover = f"color_{i}"
                        break
            
            # 检查贴图选择
            if current_hover is None and hasattr(self, 'sticker_rects'):
                for item in self.sticker_rects:
                    if item['rect'].contains(QtCore.QPoint(x, y)):
                        current_hover = f"sticker_{item['index']}"
                        break
            
            # 更新悬停状态
            if current_hover != self.last_hover_tool:
                self.last_hover_tool = current_hover
                self.hover_start = now
                self.hover_tool = current_hover
            
            # 检查是否触发工具
            if self.hover_tool and now - self.hover_start >= self.dwell_time:
                self._activate_tool(self.hover_tool)
                # 重置悬停状态
                self.hover_start = now + 9999  # 防止立即再次触发
                self.last_hover_tool = None
                self.hover_tool = None
            
            self.update()
            return
        
        # 在绘图区域
        # 调整坐标（减去工具栏偏移）
        draw_x = x - self.toolbar_width - self.drag_offset.x()
        draw_y = y - self.drag_offset.y()
        
        # 贴图工具逻辑
        if self.current_tool == 'sticker' and self.available_stickers:
            if is_drawing:
                if not self.placing_sticker:
                    # 开始放置新贴图
                    sticker_img = self.available_stickers[self.selected_sticker_idx]
                    self.placing_sticker = {
                        'image': sticker_img,
                        'x': x,
                        'y': y
                    }
                else:
                    # 移动正在放置的贴图
                    self.placing_sticker['x'] = x
                    self.placing_sticker['y'] = y
            else:
                if self.placing_sticker:
                    # 确认放置贴图
                    final_x = self.placing_sticker['x'] - self.toolbar_width - self.drag_offset.x()
                    final_y = self.placing_sticker['y'] - self.drag_offset.y()
                    self.stickers.append({
                        'image': self.placing_sticker['image'],
                        'x': final_x,
                        'y': final_y
                    })
                    self.placing_sticker = None
            self.update()
            return
        
        # 拖拽画布
        if self.current_tool == 'drag':
            if is_drawing:
                if self.drag_start is None:
                    self.drag_start = (x, y)
                else:
                    dx = x - self.drag_start[0]
                    dy = y - self.drag_start[1]
                    self.drag_offset.setX(self.drag_offset.x() + dx)
                    self.drag_offset.setY(self.drag_offset.y() + dy)
                    self.drag_start = (x, y)
            else:
                self.drag_start = None
            self.update()
            return
        
        # 绘图或擦除
        if is_drawing:  # 当捏合时才进行绘制
            painter = QtGui.QPainter(self.image)
            
            if self.current_tool == 'pen':
                pen = QtGui.QPen(self.pen_color, self.pen_width, QtCore.Qt.SolidLine, 
                                QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
                painter.setPen(pen)
            elif self.current_tool == 'eraser':
                pen = QtGui.QPen(QtGui.QColor('white'), self.eraser_width, 
                                QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
                painter.setPen(pen)
            
            if self.last_point is not None:
                # 绘制线条（两点之间）
                painter.drawLine(self.last_point[0], self.last_point[1], draw_x, draw_y)
            else:
                # 绘制初始点
                painter.drawPoint(draw_x, draw_y)
            
            painter.end()
            self.last_point = (draw_x, draw_y)  # 更新最后一个点
        else:
            # 不绘制时重置最后一个点
            self.last_point = None
        
        self.update()

    def _activate_tool(self, tool_name):
        """激活选中的工具"""
        if tool_name == 'back':
            # 返回主菜单
            parent_window = self.parent().parent()
            if hasattr(parent_window, '_return_to_menu'):
                parent_window._return_to_menu()
            return
        
        if tool_name == 'clear':
            self.clear()
            return
        
        if tool_name == 'pen':
            self.current_tool = 'pen'
        elif tool_name == 'eraser':
            self.current_tool = 'eraser'
        elif tool_name == 'drag':
            self.current_tool = 'drag'
        elif tool_name == 'sticker':
            self.current_tool = 'sticker'
        elif tool_name.startswith('color_'):
            try:
                color_index = int(tool_name.split('_')[1])
                if 0 <= color_index < len(self.colors):
                    self.pen_color = self.colors[color_index]
            except:
                pass
        elif tool_name.startswith('sticker_'):
            try:
                sticker_index = int(tool_name.split('_')[1])
                if 0 <= sticker_index < len(self.available_stickers):
                    self.selected_sticker_idx = sticker_index
            except:
                pass
        
        self.update()

    def clear(self):
        self.image.fill(QtGui.QColor('white'))
        self.drag_offset = QtCore.QPoint(0, 0)
        self.stickers = []  # 清除所有贴图
        self.update()
