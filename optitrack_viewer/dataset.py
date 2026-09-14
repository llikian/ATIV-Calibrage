from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


_CAMERA_FILE_RE = re.compile(
    r"^camera_(?P<index>\d+)_serial_(?P<serial>\d+)_(?P<kind>frames|objects)\.csv$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Detection2D:
    x: float
    y: float
    object_index: Optional[int] = None


@dataclass
class CameraInfo:
    index: int
    serial: int
    width: int = 1280
    height: int = 1024


@dataclass
class CameraFrame:
    present: bool = False
    object_count: int = 0
    detections: List[Detection2D] = field(default_factory=list)


@dataclass
class CameraData:
    info: CameraInfo
    frames: Dict[int, CameraFrame] = field(default_factory=dict)


class DatasetError(RuntimeError):
    pass


class OptiTrackDataset:
    """Dataset synchronisé multi-caméras chargé depuis les CSV du TP."""

    def __init__(
        self,
        directory: Path,
        cameras: List[CameraData],
        sync_group_ids: List[int],
        playback_fps: float,
    ) -> None:
        self.directory = directory
        self.cameras = cameras
        self.sync_group_ids = sync_group_ids
        self.playback_fps = playback_fps

    @property
    def frame_count(self) -> int:
        return len(self.sync_group_ids)

    @property
    def camera_count(self) -> int:
        return len(self.cameras)

    def sync_group_id_at(self, frame_index: int) -> int:
        return self.sync_group_ids[frame_index]

    @classmethod
    def load(cls, directory: Path, fps_override: Optional[float] = None) -> "OptiTrackDataset":
        directory = directory.expanduser()
        if not directory.is_dir():
            raise DatasetError(f"Le dossier du dataset n'existe pas : {directory}")

        session, session_cameras = _read_session_file(directory / "session.txt")
        discovered = _discover_camera_files(directory)
        if not discovered:
            raise DatasetError(
                "Aucun fichier camera_XX_serial_YYYY_frames.csv / objects.csv trouvé "
                f"dans {directory}"
            )

        cameras: List[CameraData] = []
        all_sync_ids = set()

        for camera_index in sorted(discovered):
            entry = discovered[camera_index]
            serial = entry["serial"]
            width, height = session_cameras.get(camera_index, (1280, 1024))
            info = CameraInfo(camera_index, serial, width, height)
            camera = CameraData(info=info)

            frame_path = entry.get("frames")
            object_path = entry.get("objects")
            if frame_path is None:
                raise DatasetError(f"Fichier frames.csv manquant pour la caméra {camera_index}")
            if object_path is None:
                raise DatasetError(f"Fichier objects.csv manquant pour la caméra {camera_index}")

            _load_camera_frames(frame_path, camera.frames, all_sync_ids)
            _load_camera_objects(object_path, camera.frames, all_sync_ids)
            cameras.append(camera)

        # frame_groups.csv est prioritaire s'il fournit la liste globale des groupes.
        frame_groups_path = directory / "frame_groups.csv"
        sync_ids_from_global = _load_global_sync_ids(frame_groups_path)
        if sync_ids_from_global:
            sync_group_ids = sync_ids_from_global
        else:
            sync_group_ids = sorted(all_sync_ids)

        if not sync_group_ids:
            raise DatasetError("Le dataset ne contient aucun groupe synchronisé.")

        if fps_override is not None:
            playback_fps = float(fps_override)
        else:
            playback_fps = _extract_fps(session)

        if not math.isfinite(playback_fps) or playback_fps <= 0:
            playback_fps = 120.0

        return cls(directory, cameras, sync_group_ids, playback_fps)


def _discover_camera_files(directory: Path) -> Dict[int, dict]:
    cameras: Dict[int, dict] = {}
    for path in directory.glob("camera_*_serial_*_*.csv"):
        match = _CAMERA_FILE_RE.match(path.name)
        if not match:
            continue
        index = int(match.group("index"))
        serial = int(match.group("serial"))
        kind = match.group("kind").lower()
        entry = cameras.setdefault(index, {"serial": serial})
        if entry["serial"] != serial:
            raise DatasetError(
                f"Plusieurs numéros de série associés à la caméra {index}: "
                f"{entry['serial']} et {serial}"
            )
        entry[kind] = path
    return cameras


def _read_session_file(path: Path) -> Tuple[Dict[str, str], Dict[int, Tuple[int, int]]]:
    global_values: Dict[str, str] = {}
    cameras: Dict[int, Dict[str, str]] = {}
    if not path.is_file():
        return global_values, {}

    current_camera: Optional[int] = None
    section_re = re.compile(r"^\[camera\s+(\d+)\]$", re.IGNORECASE)

    for raw_line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        section = section_re.match(line)
        if section:
            current_camera = int(section.group(1))
            cameras.setdefault(current_camera, {})
            continue
        if "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if current_camera is None:
            global_values[key.lower()] = value
        else:
            cameras[current_camera][key.lower()] = value

    dimensions: Dict[int, Tuple[int, int]] = {}
    for index, values in cameras.items():
        try:
            width = int(float(values.get("width", "1280")))
            height = int(float(values.get("height", "1024")))
        except ValueError:
            width, height = 1280, 1024
        if width <= 0 or height <= 0:
            width, height = 1280, 1024
        dimensions[index] = (width, height)

    return global_values, dimensions


def _extract_fps(session: Dict[str, str]) -> float:
    for key in (
        "requested_frame_rate_fps",
        "frame_rate_fps",
        "frame_rate",
        "fps",
    ):
        value = session.get(key)
        if value is not None:
            try:
                return float(value)
            except ValueError:
                pass
    return 120.0


def _bool_from_csv(value: Optional[str], default: bool = True) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() not in {"0", "false", "no", "non"}


def _load_camera_frames(
    path: Path,
    destination: Dict[int, CameraFrame],
    all_sync_ids: set,
) -> None:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "sync_group_id" not in reader.fieldnames:
            raise DatasetError(f"Colonne sync_group_id absente de {path.name}")
        for row in reader:
            try:
                sync_id = int(row["sync_group_id"])
            except (TypeError, ValueError):
                continue
            all_sync_ids.add(sync_id)
            frame = destination.setdefault(sync_id, CameraFrame())
            frame.present = _bool_from_csv(row.get("frame_present"), default=True)
            try:
                frame.object_count = int(row.get("object_count", "0") or 0)
            except ValueError:
                frame.object_count = 0


def _load_camera_objects(
    path: Path,
    destination: Dict[int, CameraFrame],
    all_sync_ids: set,
) -> None:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"sync_group_id", "x_px", "y_px"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            missing = required.difference(reader.fieldnames or [])
            raise DatasetError(f"Colonnes {sorted(missing)} absentes de {path.name}")

        for row in reader:
            try:
                sync_id = int(row["sync_group_id"])
                x = float(row["x_px"])
                y = float(row["y_px"])
            except (TypeError, ValueError):
                continue

            object_index: Optional[int]
            try:
                raw_index = row.get("object_index")
                object_index = int(raw_index) if raw_index not in (None, "") else None
            except ValueError:
                object_index = None

            all_sync_ids.add(sync_id)
            frame = destination.setdefault(sync_id, CameraFrame(present=True))
            frame.detections.append(Detection2D(x=x, y=y, object_index=object_index))

    # Si object_count n'est pas fiable/présent, la liste d'objets est la référence visuelle.
    for frame in destination.values():
        if frame.detections:
            frame.object_count = len(frame.detections)


def _load_global_sync_ids(path: Path) -> List[int]:
    if not path.is_file():
        return []
    ids: List[int] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "sync_group_id" not in reader.fieldnames:
            return []
        for row in reader:
            try:
                ids.append(int(row["sync_group_id"]))
            except (TypeError, ValueError):
                continue
    # Préserver l'ordre du fichier tout en supprimant d'éventuels doublons.
    return list(dict.fromkeys(ids))
