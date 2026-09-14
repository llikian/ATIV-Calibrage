# OptiTrack 2D Viewer

Petit visualiseur Python/PySide6 pour les datasets enregistrés par le programme de capture OptiTrack du TP.

## Configuration

Modifier uniquement, au minimum, la constante `DATASET_DIRECTORY` dans `config.py` :

```python
DATASET_DIRECTORY = Path(r"D:\TP_OptiTrack\datasets\wand_mobile_30s_01")
```

Le chemin doit désigner **le dossier d'un dataset** contenant notamment :

- `session.txt` (recommandé) ;
- `camera_XX_serial_YYYY_frames.csv` ;
- `camera_XX_serial_YYYY_objects.csv` ;
- éventuellement `frame_groups.csv`.

Le nombre de caméras est détecté automatiquement. La grille utilise `ceil(sqrt(n))` colonnes et le nombre de lignes nécessaire : pour 8 caméras, la vue est donc en 3 x 3.

## Installation

Python 3.10 ou plus récent recommandé.

```bat
python -m pip install -r requirements.txt
```

Puis :

```bat
python main.py
```

ou lancer `run.bat`.

## Commandes

- `P` : pause / lecture ;
- flèche gauche : frame précédente **quand la lecture est en pause** ;
- flèche droite : frame suivante **quand la lecture est en pause** ;
- `Home` : retour à la première frame **quand la lecture est en pause**.

La lecture démarre automatiquement et boucle à la fin du dataset.

## Affichage

Chaque caméra est représentée par une image noire aux proportions du capteur. Les coordonnées `(x_px, y_px)` sont affichées par une croix blanche et le nombre d'objets détectés est indiqué dans la vue. Le bandeau supérieur affiche :

```text
frame 00001/21600    [PLAY]
```

La taille maximale de la fenêtre est fixée à 1280 x 1280 pixels et la taille initiale est aussi limitée par l'écran disponible.

## Remarques sur les données

Le chargeur accepte les colonnes supplémentaires dans les CSV : seules les colonnes nécessaires au visualiseur sont lues. Les colonnes minimales attendues sont :

- `frames.csv` : `sync_group_id`, avec `frame_present` et `object_count` utilisés lorsqu'ils existent ;
- `objects.csv` : `sync_group_id`, `x_px`, `y_px`, et éventuellement `object_index`.

Si `frame_groups.csv` existe et contient `sync_group_id`, son ordre est utilisé comme ordre global de lecture. Sinon, l'ordre est construit à partir de l'union des `sync_group_id` des caméras.
