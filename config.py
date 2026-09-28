from env import ENV_DATASET_DIRECTORY

DATASET_DIRECTORY = ENV_DATASET_DIRECTORY

# La fenêtre ne dépassera jamais cette taille dans une dimension.
MAX_WINDOW_DIMENSION = 1280

# Taille d'une croix dans la vue affichée, en pixels écran.
CROSS_HALF_SIZE_PX = 6

# Si None, la fréquence demandée est lue dans session.txt ; à défaut 120 Hz.
PLAYBACK_FPS_OVERRIDE = None
