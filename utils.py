import numpy as np

from optitrack_viewer.dataset import Detection2D

EPSILON = 1e-5

def est_colineaire(a: Detection2D, b: Detection2D, c: Detection2D) -> bool:
	return abs((b.x - a.x) * (c.x - a.x) + (b.y - a.y) * (c.y - a.y)) > 1.0 - 1e-5

