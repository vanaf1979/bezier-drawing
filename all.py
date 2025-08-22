import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsItem,
                               QGraphicsLineItem, QStyleOptionGraphicsItem, QWidget)
from PySide6.QtGui import QColor, QPainter, QBrush, QPen
from PySide6.QtCore import Qt, QRectF, QObject, Signal, QPointF


################################
# Class: PointSignal
################################
class PointSignal(QObject):
    moved = Signal(QPointF)
    ended = Signal(QGraphicsItem)


################################
# Class: AnchorPoint
################################
class AnchorPoint(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.point_signal = PointSignal()

    def boundingRect(self):
        return QRectF(-6, -6, 12, 12)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        brush = QBrush(QColor.fromHsl(220, 120, 175))
        pen = QPen(QColor.fromHsl(220, 120, 175))
        pen.setWidth(1)
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawEllipse(-3, -3, 6, 6)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.point_signal.moved.emit(value)
        return super().itemChange(change, value)


################################
# Class: ControlPoint
################################
class ControlPoint(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.radius = 4
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.point_signal = PointSignal()

    def boundingRect(self):
        return QRectF(-6, -6, 12, 12)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None):
        brush = QBrush(QColor.fromHsl(220, 60, 120))
        pen = QPen(QColor.fromHsl(220, 60, 120))
        pen.setWidth(1)
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawEllipse(-3, -3, 6, 6)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.point_signal.moved.emit(value)
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.point_signal.ended.emit(self)
        super().mouseReleaseEvent(event)


################################
# Class: ControControlLinelPoint
################################
class ControlLine(QGraphicsLineItem):
    def __init__(self, start_point, end_point):
        super().__init__()

        self.start_point = start_point
        self.end_point = end_point

        pen = QPen(QColor(150, 150, 150))
        pen.setWidth(1)
        pen.setStyle(Qt.DotLine)
        self.setPen(pen)

        self.update_line()

    def update_line(self):
        self.setLine(self.start_point.pos().x(), self.start_point.pos().y(), self.end_point.pos().x(), self.end_point.pos().y())


################################
# Class: Point
################################
class Point(QObject):
    delete_point = Signal(QObject)

    def __init__(self, x, y, scene, parent=None):
        super().__init__(parent)
        self.x = x
        self.y = y
        self.scene = scene
        self.point = None
        self.c1 = None
        self.c1_offset = {'x': 50, 'y': 50}
        self.c1_line = None
        self.c2 = None
        self.c2_offset = {'x': -50, 'y': -50}
        self.c2_line = None
        self.status = "only"
        self.setup()

    def setup(self):
        # Create the point
        self.point = AnchorPoint()
        self.point.setPos(self.x, self.y)
        self.point.point_signal.moved.connect(self.update_point)

        self.point.mouseDoubleClickEvent = self.on_double_click

        # Create control point 1
        self.c1 = ControlPoint()
        self.c1.setPos(self.x - 50, self.y - 50)
        self.c1.point_signal.moved.connect(self.update_lines)
        self.c1.point_signal.ended.connect(self.update_control_point_1)

        # Create control point 2
        self.c2 = ControlPoint()
        self.c2.setPos(self.x + 50, self.y + 50)
        self.c2.point_signal.moved.connect(self.update_lines)
        self.c2.point_signal.ended.connect(self.update_control_point_2)

        # Create line between point and control point 1
        self.c1_line = ControlLine(self.point, self.c1)

        # Create line between point and control point 2
        self.c2_line = ControlLine(self.point, self.c2)

        self.scene.addItem(self.c1_line)
        self.scene.addItem(self.c1)
        self.scene.addItem(self.c2_line)
        self.scene.addItem(self.c2)
        self.scene.addItem(self.point)

        self.display_control_points()

    def set_status(self, status):
        self.status = status
        self.display_control_points()

    def display_control_points(self ):
        if self.status != "only" and  self.status != "last":
            self.c1_line.setVisible(True)
            self.c1.setVisible(True)
        else:
            self.c1_line.setVisible(False)
            self.c1.setVisible(False)

        if self.status != "only" and  self.status != "first":
            self.c2_line.setVisible(True)
            self.c2.setVisible(True)
        else:
            self.c2_line.setVisible(False)
            self.c2.setVisible(False)

    def update_point(self):
        self.c1.setPos(self.point.pos().x() - self.c1_offset['x'], self.point.pos().y() - self.c1_offset['y'])
        self.c2.setPos(self.point.pos().x() - self.c2_offset['x'], self.point.pos().y() - self.c2_offset['y'])
        self.update_lines()

    def update_control_point_1(self, cp):
        self.c1_offset['x'] = self.point.pos().x() - self.c1.pos().x()
        self.c1_offset['y'] = self.point.pos().y() - self.c1.pos().y()
        self.update_lines()

    def update_control_point_2(self, cp):
        self.c2_offset['x'] = self.point.pos().x() - self.c2.pos().x()
        self.c2_offset['y'] = self.point.pos().y() - self.c2.pos().y()
        self.update_lines()

    def update_lines(self):
        self.c1_line.update_line()
        self.c2_line.update_line()

    def on_double_click(self, event):
        self.delete_point.emit(self)

    def cleanup(self):
        self.scene.removeItem(self.point)
        self.scene.removeItem(self.c1)
        self.scene.removeItem(self.c1_line)
        self.scene.removeItem(self.c2)
        self.scene.removeItem(self.c2_line)


################################
# Class: MainWindow
################################
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 Multi-Point Bezier Curve Tool")
        self.setGeometry(100, 100, 800, 600)
        self.scene = None
        self.view = None
        self.points = []
        self.setup_ui()

    def setup_ui(self):
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-1000, -1000, 1000, 1000)
        self.scene.setBackgroundBrush(QColor("black"))

        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setSceneRect(QRectF(0, 0, 800, 600))
        self.view.mousePressEvent = self.on_mouse_press

        self.setCentralWidget(self.view)

    def on_mouse_press(self, event):
        if not self.item_at_event_position(event):
            point = Point(event.position().x(), event.position().y(), self.scene, self)
            point.delete_point.connect(self.delete_point)

            if len(self.points) == 0:
                point.set_status("only")
            else:
                for p in self.points:
                    p.set_status("center")

                self.points[0].set_status("first")
                point.set_status("last")

            self.points.append(point)
        QGraphicsView.mousePressEvent(self.view, event)

    def delete_point(self, point):
        point.cleanup()
        self.points.remove(point)

    def on_double_click(self, event):
        if self.item_at_event_position(event):
            scene_pos = self.view.mapToScene(event.position().x(), event.position().y())
            item_at_pos = self.scene.itemAt(scene_pos, self.view.transform())
        QGraphicsView.mouseDoubleClickEvent(self.view, event)

    def item_at_event_position(self, event):
        scene_pos = self.view.mapToScene(event.position().x(), event.position().y())
        item_at_pos = self.scene.itemAt(scene_pos, self.view.transform())
        return not item_at_pos is None


################################
# Main loop
################################
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
