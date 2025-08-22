import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsLineItem, QGraphicsItem)
from PySide6.QtGui import QPainter, QPainterPath, QPen, QColor, QBrush
from PySide6.QtCore import QPointF, Qt, QObject, Signal, QRectF


class PointMovedSignal(QObject):
    moved = Signal(QPointF)


class DraggablePointItem(QGraphicsItem):
    def __init__(self, x, y, color=QColor.fromHsl(220, 100, 128), parent=None):
        super().__init__(parent)
        self.setPos(x, y)
        self.color = color

        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)

        self.pos_changed = PointMovedSignal()

    def boundingRect(self):
        return QRectF(-3, -3, 6, 6)

    def paint(self, painter, option, widget):
        # Set up the brush and pen for drawing the ellipse
        brush = QBrush(self.color)
        pen = QPen(self.color)
        pen.setWidth(0)

        painter.setBrush(brush)
        painter.setPen(pen)

        painter.drawEllipse(self.boundingRect())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.pos_changed.moved.emit(value)
        return super().itemChange(change, value)


class ControlLineItem(QGraphicsLineItem):
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


class BezierCurveItem(QGraphicsPathItem):
    def __init__(self, start_point, control_one, control_two, end_point):
        super().__init__()

        self.start_point = start_point
        self.control_one = control_one
        self.control_two = control_two
        self.end_point = end_point

        pen = QPen(QColor("white"))
        pen.setWidth(1)
        self.setPen(pen)

        self.update_path()

    def update_path(self):
        path = QPainterPath(self.start_point.pos())

        path.cubicTo(self.control_one.pos(), self.control_two.pos(), self.end_point.pos())

        self.setPath(path)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 Interactive Bezier Curve")
        self.setGeometry(100, 100, 800, 600)

        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QColor.fromHsl(0, 0, 18))

        start_point = DraggablePointItem(200, 400, QColor.fromHsl(220, 0, 255))
        control_one = DraggablePointItem(225, 200, QColor.fromHsl(220, 100, 128))
        self.line_one = ControlLineItem(start_point, control_one)

        end_point = DraggablePointItem(600, 400, QColor.fromHsl(220, 0, 255))
        control_two = DraggablePointItem(575, 200, QColor.fromHsl(220, 100, 128))
        self.line_two = ControlLineItem(end_point, control_two)

        self.curve = BezierCurveItem(start_point, control_one, control_two, end_point)

        self.scene.addItem(self.curve)
        self.scene.addItem(self.line_one)
        self.scene.addItem(self.line_two)
        self.scene.addItem(start_point)
        self.scene.addItem(control_one)
        self.scene.addItem(end_point)
        self.scene.addItem(control_two)

        start_point.pos_changed.moved.connect(self.update_graphics)
        control_one.pos_changed.moved.connect(self.update_graphics)
        control_two.pos_changed.moved.connect(self.update_graphics)
        end_point.pos_changed.moved.connect(self.update_graphics)

        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setSceneRect(QRectF(0, 0, 800, 600))

        self.setCentralWidget(self.view)

    def update_graphics(self):
        self.curve.update_path()
        self.line_one.update_line()
        self.line_two.update_line()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
