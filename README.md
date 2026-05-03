# Decibel 🎵

Ce projet consiste à créer son propre jeu de cartes nommé Decibel. Il contient une suite de scripts Python permettant de créer de A à Z votre propre jeu de cartes musical physique (inspiré de jeux comme Hitster). À partir d'une simple liste de musiques, ces outils génèrent automatiquement des cartes de jeu prêtes à imprimer, incluant les pochettes d'albums, les informations des morceaux, et des QR codes pour écouter les titres.

## 🌟 Fonctionnalités

Le projet est divisé en plusieurs scripts qui s'occupent de chaque étape de la création du jeu :

1. **Validation et préparation des données** : Vérification de votre playlist au format CSV et équilibrage des niveaux de difficulté (Facile, Moyen, Difficile).
2. **Récupération des médias** : Téléchargement automatique des pochettes d'album depuis internet.
3. **Génération de QR Codes** : Création de QR codes personnalisés pointant vers les morceaux (Spotify, YouTube, etc.).
4. **Génération des cartes** : Création des images des cartes (recto/verso) au format haute définition (300 DPI) avec les informations du morceau (Titre, Artiste, Année).
5. **Préparation à l'impression** : Assemblage des cartes sur des planches d'impression régulières (A4/A3) pour faciliter le découpage et la plastification.

## 📂 Structure du projet

* `decibel_playlist.csv` : Le fichier source contenant votre liste de musiques, artistes, années et liens d'écoute.
* `scripts/` : Le dossier contenant toute la logique du projet.
  * `0_recherche_API.py` / `recherche_pochette.py` : Scripts pour récupérer les informations et les pochettes.
  * `1_Vérification_csv.py` : Vérifie la structure et les données de votre CSV.
  * `2_generer_qrcodes.py` : Génère les QR codes avec un style graphique défini.
  * `3_generer_cartes_musique.py` : Assemble les textes, les pochettes et les QR codes sur les fonds de cartes.
  * `4_generer_planche_impression.py` : Crée les planches PDF/images finales prêtes pour votre imprimante.
* `cartes_musiques/` : Dossier de sortie contenant les cartes générées.
* `qrcodes_finaux/` : Dossier de sortie contenant les QR codes générés.

## 🛠️ Utilisation

1. Complétez le fichier `decibel_playlist.csv` avec vos musiques.
2. Exécutez les scripts dans l'ordre (de 1 à 4).
3. Récupérez vos planches d'impression générées.

## 🖨️ Conseils d'impression

Pour un rendu optimal "jeu de société" :
- Imprimez sur du papier mat épais (160 à 180 g/m²).
- Imprimez les rectos et les versos séparément.
- Collez-les ensemble, découpez grossièrement, plastifiez (pochettes 80 microns) puis effectuez la découpe finale.
