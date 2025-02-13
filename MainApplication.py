from PyQt5.QtWidgets import *
from PyQt5.QtGui import QTransform, QPainter, QIcon, QColor

from graph_managers import GraphManager
from data_parser import processFrontendData, processBackendData

import pickle
import sys


class MyWindow(QMainWindow):

    def __init__(self, width, height):
        super().__init__()
        self.setWindowTitle("Graph Viewer")
        self.resize(width, height)
        self.setStyleSheet("QMainWindow {background: 'grey';}")

        self.view = GraphViewer()

        newFileAction = QAction("New Graph", self)
        newFileAction.triggered.connect(self.newGraph)
        self.newFileAction = newFileAction

        openFileAction = QAction("Open Graph", self)
        openFileAction.triggered.connect(self.openGraph)
        self.openFileAction = openFileAction

        saveFileAction = QAction("Save Graph", self)
        saveFileAction.triggered.connect(self.saveGraph)
        saveFileAction.setDisabled(True)
        self.saveFileAction = saveFileAction

        menuBar = QMenuBar()
        fileMenu = menuBar.addMenu("File")
        fileMenu.addAction(newFileAction)
        fileMenu.addAction(openFileAction)
        fileMenu.addAction(saveFileAction)

        redColorAction = QAction(QIcon('red_color.png'), "Set Red Pen", self)
        redColorAction.triggered.connect(self.setRedPen)

        blueColorAction = QAction(QIcon('blue_color.jpg'), "Set Blue Pen", self)
        blueColorAction.triggered.connect(self.setBluePen)

        blackColorAction = QAction(QIcon('black_color.jpg'), "Set Black Pen", self)
        blackColorAction.triggered.connect(self.setBlackPen)

        toolBar = self.addToolBar("Pen Color")
        toolBar.addAction(redColorAction)
        toolBar.addAction(blueColorAction)
        toolBar.addAction(blackColorAction)

        self.isViewMounted = False

        self.setMenuBar(menuBar)
        self.show()

    def setRedPen(self):
        self.view.setPenColor(QColor(255, 0, 0))

    def setBluePen(self):
        self.view.setPenColor(QColor(0, 0, 255))

    def setBlackPen(self):
        self.view.setPenColor(QColor(0, 0, 0))

    def newGraph(self):

        if self.saveFileAction.isEnabled():
            choice = QMessageBox.question(self, "Graph Viewer", "Are you sure? All unsaved changes will be lost",
                                          QMessageBox.Yes | QMessageBox.No)
            if choice == QMessageBox.No:
                return

        if not self.isViewMounted:
            self.setCentralWidget(self.view)
            self.isViewMounted = True

        self.view.newData()
        self.saveFileAction.setDisabled(False)

    def openGraph(self):
        filename = QFileDialog.getOpenFileName(self, 'Open file', '/', 'Graph files (*.graph)')
        try:
            graphFile = open(filename[0], 'rb')
        except FileNotFoundError:
            QMessageBox.information(self, "Graph Viewer", "No such file found")
        else:
            graphData = pickle.load(graphFile)
            nodes = graphData['nodes']
            edges = graphData['edges']
            rotation_angle = graphData['angle']
            node_objs, edge_matrix = processBackendData(nodes, edges)
            self.view.setData(node_objs, edge_matrix, rotation_angle)
            graphFile.close()
            self.saveFileAction.setDisabled(False)

            if not self.isViewMounted:
                self.setCentralWidget(self.view)


    def saveGraph(self):
        graphData = self.view.getData()
        filename = QFileDialog.getSaveFileName(self, "Save File", '/', 'Graph files (*.graph)')
        graphFile = open(filename[0], 'wb')
        pickle.dump(graphData, graphFile)
        graphFile.close()


    def closeEvent(self, event):
        close = QMessageBox.question(self,
                                     "Quit Graph-Visualization",
                                     "Are you sure you want to quit? All unsaved changes will be lost",
                                     QMessageBox.Yes | QMessageBox.No)
        if close == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


class GraphViewer(QGraphicsView):

    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.container = None
        self.angle = 0

    def newData(self):
        self.setData({}, [], 0)

    def getData(self):
        data = self.container.getGraphData()
        data['angle'] = self.angle
        return data

    def setData(self, node_objs, edge_matrix, rotation_angle):
        self.container = GraphContainer(node_objs, edge_matrix)
        self.setScene(self.container)

    def setPenColor(self, color):
        self.container.setPenColor(color)


class GraphContainer(QGraphicsScene):

    def __init__(self, node_objs, edge_matrix):
        super().__init__()
        self.pressed = False
        self.drawing_edge = None
        self.graph_manager = GraphManager(self, node_objs, edge_matrix)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.pressed = True

        mousePos = event.scenePos()
        item = self.itemAt(mousePos.x(), mousePos.y(), QTransform())
        self.graph_manager.mousePressEvent(event, item)
        self.update()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self.pressed:
            # Captures Drag events

            mousePos = event.scenePos()
            item = self.itemAt(mousePos.x(), mousePos.y(), QTransform())
            self.graph_manager.mouseMoveEvent(event, item)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.pressed = False

        mousePos = event.scenePos()
        item = self.itemAt(mousePos.x(), mousePos.y(), QTransform())
        self.graph_manager.mouseReleaseEvent(event, item)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        mousePos = event.scenePos()
        item = self.itemAt(mousePos.x(), mousePos.y(), QTransform())
        self.graph_manager.mouseDoubleClickEvent(event, item)

    def getGraphData(self):
        node_objs, edge_matrix = self.graph_manager.getData()
        return processFrontendData(node_objs, edge_matrix)

    def setGraphData(self, node_objs, edge_matrix):
        self.clear()
        self.graph_manager = GraphManager(self, node_objs, edge_matrix)
        self.update()

    def setPenColor(self, color):
        self.graph_manager.setPenColor(color)


if __name__ == '__main__':
    app = QApplication([])

    desktop = QDesktopWidget()
    panel = MyWindow(desktop.width(), desktop.height())

    ret = app.exec_()
    sys.exit(ret)