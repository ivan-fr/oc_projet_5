Utilisez les données publiques de l'OpenFoodFacts
-

Cahier des charges [Lien trello](https://trello.com/b/JoVMG8ls/)

Description du parcours utilisateur

L'utilisateur est sur le terminal. Ce dernier lui affiche les choix suivants :

1. Quel aliment souhaitez-vous remplacer ? 
2. Retrouver mes aliments substitués.

L'utilisateur sélectionne 1. Le programme pose les questions suivantes à l'utilisateur et ce dernier sélectionne les réponses :

- L'utilisateur effectue une recherche afin de récuperer une liste d'aliment.
- Sélectionnez l'aliment. [Plusieurs propositions associées à un chiffre. L'utilisateur entre le chiffre correspondant à l'aliment choisi et appuie sur entrée]
- Le programme propose un substitut, sa description, un magasin ou l'acheter (le cas échéant) et un lien vers la page d'Open Food Facts concernant cet aliment.
- L'utilisateur a alors la possibilité d'enregistrer le résultat dans la base de données.

Si l'utilisateur sélectionne 2, le programme affiche la liste des produits substituables enregistrés dans la base de données :

- L'utilisateur reçoit une liste de produits substituables enregistrés dans la base de données.
- Selectionner l'aliment [Plusieurs propositions associées à un chiffre. L'utilisateur entre le chiffre correspondant à l'aliment choisi et appuie sur entrée]
- Le programme retourne l'aliment et ses substituts.
- L'utilisateur est renvoyé sur la sélection des commandes.

# Setup

## 1 - Requirements
*  **Python 3.x**.
* Utiliser une base de données MySQL

### Installation 
* Download ou clone le repository.
* Utiliser un **environnement virtuel** est recommandé.
    * Exécuter la ligne de commande : `python3 -m venv /path/to/new/virtual/environment`  
    puis `source <path/to/venv>/bin/activate` depuis MacOS  
    ou `<path/to/venv>\Scripts\activate.bat`depuis Windows
* Installer les dépendances : `pip install -r requirements.txt`

## 2 - Configuration de la base de données

* créer une database MySQL "openfoodfacts"
* connectez-vous à la base de données avec tout les droits
* executer le fichier bdd.sql

### constant.py
clé | valeur
----- | ---------------
host | Database host
database | database name (par défaut openfoodfacts)
user | user login
password | user password (si besoin) 

## 3 - Lancer le programme 
* Exécuter : `python main.py`  depuis la console
