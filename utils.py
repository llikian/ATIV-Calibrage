from optitrack_viewer.dataset import Detection2D, CameraFrame
from vec2 import *

EPSILON = 1e-4


def get_triplet(
    a: Detection2D, b: Detection2D, c: Detection2D
) -> None | tuple[Detection2D, Detection2D, Detection2D]:
    AB: vec2 = b.pos - a.pos
    AC: vec2 = c.pos - a.pos

    dist_AB: float = AB.length()
    dist_AC: float = AC.length()

    cos_angle: float = dot(AB, AC) / (dist_AB * dist_AC)

    if cos_angle > 1.0 - EPSILON:
        if dist_AB < dist_AC:
            return (a, b, c)
        else:
            return (a, c, b)
    elif cos_angle < -1.0 + EPSILON:
        # equivalent to (c, a, b) since we can only determine the center for now
        return (b, a, c)
    else:
        return None


def get_potential_triplets(frame: CameraFrame):
    count = len(frame.detections)
    potential_triplets = []

    for i in range(count - 2):
        for j in range(i + 1, count - 1):
            for k in range(j + 1, count):
                triplet = get_triplet(
                    frame.detections[i], frame.detections[j], frame.detections[k]
                )

                if triplet is not None:
                    potential_triplets.append(triplet)

    return potential_triplets
