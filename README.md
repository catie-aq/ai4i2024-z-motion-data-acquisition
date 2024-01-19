# Z_Motion data acquisition tools

## Présentation générale

Script permettant la capture et l'enregistrement de données transmises par la centrale inertielle Z_Motion développée dans le cadre du projet [6TRON](https://6tron.io) porté par le [Centre Aquitain des Technologies de l'Information et Electroniques](https://www.catie.fr) (CATIE).

## Installation

Dans un environnement virtuel python python 3.8 dédié, effectuer :

```
pip install -r requirements.txt
```

## Enregistrement des données transmises par le capteur

Le script `data_acquisition.py` permet de capturer, en une seule session, plusieurs jeux de données et de les enregistrer sous la forme de fichiers CSV séparés.

Une fois le script lancé et l'objet connecté en bluetooth, appuyer sur la touche [espace] pour commencer à enregistrer les données dans un fichier CSV.

Appuyer de nouveau sur [espace] pour interrompre l'enregistrement.

Un nouvel appui sur [espace] relancera l'enregistrement dans un nouveau fichier CSV et ainsi de suite...

Une fois la session de travail terminée, appuyer sur [q] puis [ctrl+c] pour quitter le programme.

Dans tous les cas, suivre les instructions affichées dans le terminal.


Utilisation :

```
usage: rdata_acquisition.py  [-h] [--stream-config STREAM_CONFIG]
                                  [--output-dir OUTPUT_DIR]
                                  [--files-prefix FILES_PREFIX]
                                  SENSOR_NAME
```

- STREAM_CONFIG : configuration relative aux données à récupérer auprès de l'objet. Trois valeurs possibles : 1, 2 et 3. Voir plus bas leur définition.
- OUTPUT_DIR : répertoire dans lequel seront enregistrés tous les fichiers capturés durant la session.
- FILES_PREFIX : préfixe des fichiers CSV correspondant aux différentes captures.
- BLE_SENSOR_NAME : nom de l'objet Z_Motion (exemple : "6TRON Sensor 1").

Exemple :

```
python data_acquisition.py "6TRON Sensor 1" --output-dir acquired_data/ --files-prefix 1_ --stream-config 1
```

Enregistre une série de fichiers CSV dans le répertoire acquired_data/. 
Ces fichiers seront respectivement nommés : 1_1.csv, 1_2.csv, 1_3.csv...


## Troubleshooting
