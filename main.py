from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from config import (
    CROSS_HALF_SIZE_PX,
    DATASET_DIRECTORY,
    MAX_WINDOW_DIMENSION,
    PLAYBACK_FPS_OVERRIDE,
)
from optitrack_viewer.dataset import DatasetError, OptiTrackDataset, Detection2D
from optitrack_viewer.viewer import MainWindow

def est_collineaire(a : Detection2D, b: Detection2D, c:Detection2D) -> bool:
    return abs((b.x - a.x) * (c.x - a.x) + (b.y - a.y) * (c.y - a.y)) > 1.0 - 1e-5

def question1_1() :
    

    pass

def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("OptiTrack 2D Viewer")

    try:
        dataset = OptiTrackDataset.load(
            DATASET_DIRECTORY,
            fps_override=PLAYBACK_FPS_OVERRIDE,
        )
        
        

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
