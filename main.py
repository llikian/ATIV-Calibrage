from __future__ import annotations
from utils import *

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from config import (
    CROSS_HALF_SIZE_PX,
    DATASET_DIRECTORY,
    MAX_WINDOW_DIMENSION,
    PLAYBACK_FPS_OVERRIDE,
)
from optitrack_viewer.dataset import (
    DatasetError,
    OptiTrackDataset,
    Detection2D,
    CameraFrame,
)
from optitrack_viewer.viewer import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("OptiTrack 2D Viewer")

    try:
        dataset = OptiTrackDataset.load(
            DATASET_DIRECTORY,
            fps_override=PLAYBACK_FPS_OVERRIDE,
        )

        print("cameras: ", dataset.camera_count)
        print("frames: ", dataset.frame_count)

    except (DatasetError, OSError) as exc:
        QMessageBox.critical(
            None,
            "Erreur de chargement",
            f"Impossible de charger le dataset :\n\n{exc}",
        )
        return 1

    window = MainWindow(
        dataset,
        max_window_dimension=MAX_WINDOW_DIMENSION,
        cross_half_size_px=CROSS_HALF_SIZE_PX,
    )
    window.show()
    window.activateWindow()
    window.setFocus()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
