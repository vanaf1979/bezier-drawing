import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsItem, QGraphicsLineItem)
from PySide6.QtGui import QPainter, QPainterPath, QPen, QColor, QBrush
from PySide6.QtCore import QPointF, Qt, QObject, Signal, QRectF


class PointSignal(QObject):
    moved = Signal(QPointF)
    removed = Signal(QGraphicsItem)


class DraggablePointItem(QGraphicsItem):
    def __init__(self, x, y, color, parent=None):
        super().__init__(parent)
        self.setPos(x, y)
        self.color = color
        self.size = 8
        self.is_anchor = False

        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)

        self.point_signal = PointSignal()
        self.setAcceptedMouseButtons(Qt.LeftButton)

    def boundingRect(self):
        return QRectF(-self.size / 2, -self.size / 2, self.size, self.size)

    def paint(self, painter, option, widget):
        brush = QBrush(self.color)
        pen = QPen(self.color)
        pen.setWidth(1)

        painter.setBrush(brush)
        painter.setPen(pen)

        painter.drawEllipse(self.boundingRect())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.point_signal.moved.emit(value)
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        if self.is_anchor and self.scene() and event.button() == Qt.LeftButton:
            self.point_signal.removed.emit(self)


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
        path.cubicTo(self.control_one.pos(),
                     self.control_two.pos(),
                     self.end_point.pos())
        self.setPath(path)


class CurveManager:
    def __init__(self, scene):
        self.scene = scene
        self.segments = []
        self.points = []

    def add_point(self, pos):
        new_anchor = DraggablePointItem(pos.x(), pos.y(), QColor.fromHsl(220, 50, 128))
        new_anchor.is_anchor = True
        self.points.append(new_anchor)
        self.scene.addItem(new_anchor)
        new_anchor.point_signal.removed.connect(self.remove_point)

        if len(self.points) > 1:
            # We have at least two points, so we can create a new segment
            start_point = self.points[-2]
            end_point = new_anchor

            # Check if this is the very first segment being created
            if not self.segments:
                # First segment creation, no previous control point to mirror
                control_one = DraggablePointItem(start_point.pos().x() + 50, start_point.pos().y() + 50, QColor.fromHsl(220, 100, 128))
            else:
                # Subsequent segments, apply mirroring logic
                last_segment = self.segments[-1]
                last_control_two = last_segment['control_two']
                mirror_pos_x = start_point.pos().x() - (last_control_two.pos().x() - start_point.pos().x())
                mirror_pos_y = start_point.pos().y() - (last_control_two.pos().y() - start_point.pos().y())
                control_one = DraggablePointItem(mirror_pos_x, mirror_pos_y, QColor.fromHsl(220, 100, 128))

            # Create the second control point for the new segment
            control_two = DraggablePointItem(end_point.pos().x() - 50, end_point.pos().y() + 50, QColor.fromHsl(220, 100, 128))

            # Add all new items to the scene
            self.scene.addItem(control_one)
            self.scene.addItem(control_two)

            new_curve_item = BezierCurveItem(start_point, control_one, control_two, end_point)
            new_line_one = ControlLineItem(start_point, control_one)
            new_line_two = ControlLineItem(end_point, control_two)

            self.scene.addItem(new_line_one)
            self.scene.addItem(new_line_two)
            self.scene.addItem(new_curve_item)

            # Store the segment data
            self.segments.append({
                'curve': new_curve_item,
                'start_point': start_point,
                'control_one': control_one,
                'control_two': control_two,
                'end_point': end_point,
                'line_one': new_line_one,
                'line_two': new_line_two
            })

            # Connect signals for all points in the new segment to update the graphics
            start_point.point_signal.moved.connect(self.update_graphics)
            end_point.point_signal.moved.connect(self.update_graphics)
            control_one.point_signal.moved.connect(self.update_graphics)
            control_two.point_signal.moved.connect(self.update_graphics)

        self.update_graphics()

    def remove_point(self, point_to_remove):
        """
        Removes an anchor point and its associated curve segments.
        """
        if len(self.points) <= 1:
            return  # Don't remove the last point

        point_index = self.points.index(point_to_remove)

        # Handle removing the first or last point
        if point_index == 0:
            # Removing the first point, so remove the first segment
            if len(self.segments) > 0:
                segment_to_remove = self.segments.pop(0)
                self.scene.removeItem(segment_to_remove['curve'])
                self.scene.removeItem(segment_to_remove['control_one'])
                self.scene.removeItem(segment_to_remove['line_one'])
                self.scene.removeItem(segment_to_remove['control_two'])
                self.scene.removeItem(segment_to_remove['line_two'])
        elif point_index == len(self.points) - 1:
            # Removing the last point, so remove the last segment
            segment_to_remove = self.segments.pop()
            self.scene.removeItem(segment_to_remove['curve'])
            self.scene.removeItem(segment_to_remove['control_one'])
            self.scene.removeItem(segment_to_remove['line_one'])
            self.scene.removeItem(segment_to_remove['control_two'])
            self.scene.removeItem(segment_to_remove['line_two'])
        else:
            # Removing a middle point
            # Remove the segment after the point
            segment_to_remove = self.segments.pop(point_index)
            self.scene.removeItem(segment_to_remove['curve'])
            self.scene.removeItem(segment_to_remove['control_one'])
            self.scene.removeItem(segment_to_remove['line_one'])
            self.scene.removeItem(segment_to_remove['control_two'])
            self.scene.removeItem(segment_to_remove['line_two'])

            # Remove the segment before the point
            segment_to_remove = self.segments.pop(point_index - 1)
            self.scene.removeItem(segment_to_remove['curve'])
            self.scene.removeItem(segment_to_remove['control_one'])
            self.scene.removeItem(segment_to_remove['line_one'])
            self.scene.removeItem(segment_to_remove['control_two'])
            self.scene.removeItem(segment_to_remove['line_two'])

            # Create a new segment to connect the two remaining ones
            start_point = self.points[point_index - 1]
            end_point = self.points[point_index + 1]

            control_one = DraggablePointItem(start_point.pos().x() + 50, start_point.pos().y() + 50, QColor.fromHsl(220, 100, 128))
            control_two = DraggablePointItem(end_point.pos().x() - 50, end_point.pos().y() + 50, QColor.fromHsl(220, 100, 128))

            self.scene.addItem(control_one)
            self.scene.addItem(control_two)

            new_curve_item = BezierCurveItem(start_point, control_one, control_two, end_point)
            new_line_one = ControlLineItem(start_point, control_one)
            new_line_two = ControlLineItem(end_point, control_two)
            self.scene.addItem(new_line_one)
            self.scene.addItem(new_line_two)
            self.scene.addItem(new_curve_item)

            self.segments.insert(point_index - 1, {
                'curve': new_curve_item,
                'start_point': start_point,
                'control_one': control_one,
                'control_two': control_two,
                'end_point': end_point,
                'line_one': new_line_one,
                'line_two': new_line_two
            })
            start_point.point_signal.moved.connect(self.update_graphics)
            end_point.point_signal.moved.connect(self.update_graphics)
            control_one.point_signal.moved.connect(self.update_graphics)
            control_two.point_signal.moved.connect(self.update_graphics)

        # Clean up the anchor point
        self.scene.removeItem(point_to_remove)
        self.points.remove(point_to_remove)
        self.update_graphics()

    def update_graphics(self):
        for segment in self.segments:
            segment['curve'].update_path()
            segment['line_one'].update_line()
            segment['line_two'].update_line()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 Multi-Point Bezier Curve Tool")
        self.setGeometry(100, 100, 800, 600)

        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QColor("black"))

        self.curve_manager = CurveManager(self.scene)

        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setSceneRect(QRectF(0, 0, 800, 600))

        self.view.mousePressEvent = self.on_mouse_press

        self.setCentralWidget(self.view)

    def on_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            scene_pos = self.view.mapToScene(event.pos())
            # Check if an item exists at the clicked position
            item_at_pos = self.scene.itemAt(scene_pos, self.view.transform())

            # If no item is found, add a new point
            if item_at_pos is None:
                self.curve_manager.add_point(scene_pos)
        # Restore default mouse event handling
        QGraphicsView.mousePressEvent(self.view, event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
