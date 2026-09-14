from __future__ import annotations

import math
from typing import List

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QKeyEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .dataset import CameraData, CameraFrame, OptiTrackDataset


class CameraView(QWidget):
    def __init__(self, camera: CameraData, cross_half_size_px: int = 6) -> None:
        super().__init__()
        self.camera = camera
        self.cross_half_size_px = cross_half_size_px
        self.frame = CameraFrame()
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(120, 90)

    def set_frame(self, frame: CameraFrame) -> None:
        self.frame = frame
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(self.rect(), QColor(0, 0, 0))

        sensor_w = max(1, self.camera.info.width)
        sensor_h = max(1, self.camera.info.height)
        widget_w = max(1, self.width())
        widget_h = max(1, self.height())

        # Conserver le ratio du capteur et centrer l'image noire dans la tuile.
        scale = min(widget_w / sensor_w, widget_h / sensor_h)
        display_w = sensor_w * scale
        display_h = sensor_h * scale
        offset_x = (widget_w - display_w) * 0.5
        offset_y = (widget_h - display_h) * 0.5

        # Cadre du capteur.
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawRect(
            int(round(offset_x)),
            int(round(offset_y)),
            max(0, int(round(display_w)) - 1),
            max(0, int(round(display_h)) - 1),
        )

        # Croix aux positions des objets détectés.
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        h = self.cross_half_size_px
        for detection in self.frame.detections:
            x = offset_x + detection.x * scale
            y = offset_y + detection.y * scale
            xi = int(round(x))
            yi = int(round(y))
            painter.drawLine(xi - h, yi, xi + h, yi)
            painter.drawLine(xi, yi - h, xi, yi + h)

        # Bandeau de texte dans chaque vue.
        painter.setFont(QFont("Consolas", 9))
        painter.setPen(QColor(230, 230, 230))
        serial = self.camera.info.serial
        camera_text = f"Camera {self.camera.info.index:02d}  serial {serial}"
        painter.drawText(8, 17, camera_text)

        count_text = f"Objects: {len(self.frame.detections)}"
        painter.drawText(8, 34, count_text)

        if not self.frame.present:
            painter.setPen(QColor(170, 170, 170))
            painter.drawText(8, 51, "frame absente")


class MainWindow(QMainWindow):
    def __init__(
        self,
        dataset: OptiTrackDataset,
        max_window_dimension: int = 1280,
        cross_half_size_px: int = 6,
    ) -> None:
        super().__init__()
        self.dataset = dataset
        self.current_index = 0
        self.paused = False

        self.setWindowTitle(f"OptiTrack 2D viewer - {dataset.directory.name}")
        self.setMaximumSize(max_window_dimension, max_window_dimension)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        central = QWidget(self)
        central.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(6, 6, 6, 6)
        root_layout.setSpacing(5)

        self.frame_label = QLabel()
        self.frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frame_label.setFont(QFont("Consolas", 13, QFont.Weight.Bold))
        self.frame_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        root_layout.addWidget(self.frame_label, 0)

        grid_host = QWidget()
        grid_host.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)

        count = dataset.camera_count
        columns = max(1, math.ceil(math.sqrt(count)))
        rows = max(1, math.ceil(count / columns))
        self.grid_rows = rows
        self.grid_columns = columns

        self.camera_views: List[CameraView] = []
        for position, camera in enumerate(dataset.cameras):
            view = CameraView(camera, cross_half_size_px=cross_half_size_px)
            self.camera_views.append(view)
            row = position // columns
            col = position % columns
            grid.addWidget(view, row, col)

        for row in range(rows):
            grid.setRowStretch(row, 1)
        for col in range(columns):
            grid.setColumnStretch(col, 1)

        root_layout.addWidget(grid_host, 1)
        self.setCentralWidget(central)

        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        interval_ms = max(1, int(round(1000.0 / dataset.playback_fps)))
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self._advance_playback)

        self._set_initial_size(max_window_dimension)
        self._show_current_frame()
        self.timer.start()

    def _set_initial_size(self, hard_max: int) -> None:
        app = QApplication.instance()
        screen = app.primaryScreen() if app is not None else None
        if screen is not None:
            available = screen.availableGeometry()
            max_w = min(hard_max, max(640, available.width() - 40))
            max_h = min(hard_max, max(480, available.height() - 60))
        else:
            max_w = hard_max
            max_h = min(hard_max, 900)

        # Chercher une taille donnant des cellules proches du ratio Flex13 5:4,
        # sans jamais dépasser les limites demandées.
        target_cell_ratio = 1280 / 1024
        header_h = 42
        width_from_height = int((max_h - header_h) * self.grid_columns * target_cell_ratio / self.grid_rows)
        width = min(max_w, max(700, width_from_height))
        height_from_width = int(width * self.grid_rows / (self.grid_columns * target_cell_ratio)) + header_h
        height = min(max_h, max(520, height_from_width))
        self.resize(min(width, hard_max), min(height, hard_max))

    def _advance_playback(self) -> None:
        if self.paused or self.dataset.frame_count == 0:
            return
        self.current_index = (self.current_index + 1) % self.dataset.frame_count
        self._show_current_frame()

    def _show_current_frame(self) -> None:
        if self.dataset.frame_count == 0:
            return
        sync_id = self.dataset.sync_group_id_at(self.current_index)
        current_display = self.current_index + 1
        total = self.dataset.frame_count
        state = "PAUSE" if self.paused else "PLAY"
        self.frame_label.setText(f"frame {current_display:05d}/{total:05d}    [{state}]")

        for view, camera in zip(self.camera_views, self.dataset.cameras):
            frame = camera.frames.get(sync_id, CameraFrame(present=False))
            view.set_frame(frame)

    def _toggle_pause(self) -> None:
        self.paused = not self.paused
        self._show_current_frame()

    def _step(self, delta: int) -> None:
        if not self.paused or self.dataset.frame_count == 0:
            return
        self.current_index = (self.current_index + delta) % self.dataset.frame_count
        self._show_current_frame()

    def _home(self) -> None:
        if not self.paused or self.dataset.frame_count == 0:
            return
        self.current_index = 0
        self._show_current_frame()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key = event.key()
        if key == Qt.Key.Key_P:
            self._toggle_pause()
            event.accept()
            return
        if key == Qt.Key.Key_Left:
            self._step(-1)
            event.accept()
            return
        if key == Qt.Key.Key_Right:
            self._step(+1)
            event.accept()
            return
        if key == Qt.Key.Key_Home:
            self._home()
            event.accept()
            return
        super().keyPressEvent(event)
