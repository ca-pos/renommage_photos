# Cahier des charges

## Opérations à réaliser

1. lire les fichiers raw tels qu'issus de la carte mémoire
1. lire les exif (dans un objet Photo)
1. grouper photos par date et ordonnées chronologiquement
1. les afficher (vignettes)
1. afficher la date (jour)
1. (optionnel) les agrandir en cliquant dessus
1. boutons "Masquer" (flouter) et "Afficher"
1. bouton de suppresion des vignettes masquées
1. pour les photos conservées, selection d'une ou plusieurs photos
1. demander le titre du répertoire
1. demander s'il y a plusieurs répertoires pour une même journée (groupes)
1. créer la date de prise de vue au format condensé par décennie
1. ajouter, si nécessaire, a. b. etc.
1. renommer au format suivant :
    1. date au format AAAA-MM-JJ entre parenthéses
    1. souligné, numéro d'ordre en 3 chiffres_ souligné
    1. nom d'origine (DSCxxxx)
    1. tiret haut
    1. date au format condensé (avec groupe éventuel)
    1. tiret haut
    1. nom du répertoire
1. créer le répertoire au format suivant :
    1. date au format condensé
    1. tiret haut
    1. nom du répertoire
1. copier la photo à son emplacement

## Contrôles
### Entrées
1. répertoire d'origine (par défaut carte mémoire ?)
1. répertoire de sortie
1. sous/répertoire de sortie par dates ou sous/dates
### Opérations
1. ajout d'un suffixe aux vignettes sélectionnées (vérifier qu'elles sont d'une même journée)
1. réinitialer la sélection (first = -1, last = -1, checked_list = [])
1. suppression de l'affichage des vignettes masquées
1. supprimer les vignettes sélectionnées
1. supprimer les vignettes masquées
1. bouton "Exécuter"

## Objet photo
### Reçoit
chemin vers une photo au format NEF
### Paramètres
1. thumbnail
1. file_path
1. file_name
1. file_extension
1. file_number
1. orientation
### Méthodes
1. extraire un petit jpeg (thumbnail ?)
1. les différentes composantes du chemin
1. extraire les exif (date, orientation)

## Widgets

1. QLabel : affichage des photos
1. sous les photos, 2 QRadioButton : conserver, supprimer
1. QLabel : affichage de la date
1. QPushButton (2) : raw & rvb (raw checked by default)
1. QFileDialog + QLabel : répertoire d'origine (défaut, répertoire courant)
1. QFileDialog + QLabel : répertoire destination (défaut, répertoire courant)
1. QLabel + QTextEdit : nom du répertoire
1. QPushButton : exécuter 

