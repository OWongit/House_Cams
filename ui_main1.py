from PyQt6 import QtCore, QtGui, QtWidgets

class VideoView(QtWidgets.QWidget):
    def __init__(self, title: str = "Camera", parent=None):
        super().__init__(parent)
        self.title = title
        self.label = QtWidgets.QLabel("No Signal", self)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setMinimumSize(320, 240)
        self.label.setStyleSheet("background:#111; color:#888; border:1px solid #333;" )

        self.status = QtWidgets.QLabel(" ", self)
        self.status.setStyleSheet("color:#999; font-size: 11px;")

        title_lbl = QtWidgets.QLabel(title, self)
        title_lbl.setStyleSheet("font-weight:600;" )

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6,6,6,6)
        layout.setSpacing(6)
        layout.addWidget(title_lbl)
        layout.addWidget(self.label, 1)
        layout.addWidget(self.status)

    def show_frame(self, qimg: QtGui.QImage):
        # Scale while keeping aspect ratio
        pix = QtGui.QPixmap.fromImage(qimg)
        target_size = self.label.size()
        if target_size.width() > 0 and target_size.height() > 0:
            pix = pix.scaled(target_size, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                             QtCore.Qt.TransformationMode.SmoothTransformation)
        self.label.setPixmap(pix)

    def resizeEvent(self, e: QtGui.QResizeEvent):
        # Trigger a redraw scale
        if self.label.pixmap():
            self.show_frame(self.label.pixmap().toImage())
        super().resizeEvent(e)

    def set_status(self, text: str):
        self.status.setText(text)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("UniFi Dual-Cam Viewer")
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)

        self.front_view = VideoView("Front Camera")
        self.back_view  = VideoView("Back Camera")

        # Use a horizontal splitter so the user can resize the two feeds
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, central)
        splitter.addWidget(self.front_view)
        splitter.addWidget(self.back_view)
        splitter.setChildrenCollapsible(False)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(10,10,10,10)
        layout.setSpacing(12)
        layout.addWidget(splitter, 1)

        # No need to preset a size; we'll go fullscreen on show.
        # self.resize(1200, 600)

        # Guard to run fullscreen logic once
        self._fullscreen_initialized = False

    def bind_streams(self, front_worker, back_worker):
        front_worker.frameReady.connect(self.front_view.show_frame)
        front_worker.statusChanged.connect(self.front_view.set_status)

        back_worker.frameReady.connect(self.back_view.show_frame)
        back_worker.statusChanged.connect(self.back_view.set_status)

    def showEvent(self, e: QtGui.QShowEvent) -> None:
        super().showEvent(e)
        if self._fullscreen_initialized:
            return

        # Try to find a 1920x1080 monitor
        target_screen = None
        for s in QtGui.QGuiApplication.screens():
            if s.geometry().size() == QtCore.QSize(1920, 1080):
                target_screen = s
                break

        # Fallback: use the primary screen
        if target_screen is None:
            target_screen = QtGui.QGuiApplication.primaryScreen()

        # Move the window to the top-left of the target screen and go fullscreen
        geo = target_screen.geometry()
        self.move(geo.topLeft())
        self.showFullScreen()

        self._fullscreen_initialized = True
