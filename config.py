from pathlib import Path

# -----------------------------------------------------------------------------
# A MODIFIER : chemin ABSOLU Windows du dossier d'un dataset OptiTrack.
# Exemple : Path(r"D:\TP_OptiTrack\datasets\wand_mobile_30s_01")
# -----------------------------------------------------------------------------
DATASET_DIRECTORY = Path(r"/home/llikian/classes/M2/ativ/guillou/Datasets/wand-A-013")

# La fenêtre ne dépassera jamais cette taille dans une dimension.
MAX_WINDOW_DIMENSION = 1280

# Taille d'une croix dans la vue affichée, en pixels écran.
CROSS_HALF_SIZE_PX = 6

# Si None, la fréquence demandée est lue dans session.txt ; à défaut 120 Hz.
PLAYBACK_FPS_OVERRIDE = None
