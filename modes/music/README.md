# Mode de Jeu : Musique (Décibel)

Ceci est le mode de jeu principal et historique de Décibel.
Il consiste à deviner la musique, l'artiste ou l'année de sortie à partir d'un extrait de 30 secondes.

## 📂 Structure des Fichiers

- `db.json` : La base de données principale (remplace l'ancien `.csv`). Elle contient les métadonnées (Titre, Artiste, Année) et les chemins vers les médias locaux.
- `to_add.json` : La liste d'attente. Ajoutez vos musiques ici sous la forme `[{"Titre": "...", "Artiste": "..."}]` pour que les scripts les traitent.
- `genres.json` : Base de données des genres musicaux et de leurs couleurs associées (pour la colorisation des logos sur les QR Codes).
- `stats.json` : Fichier généré automatiquement pour suivre vos statistiques de playlist.
- `/assets/` : Contient les médias téléchargés localement.
  - `/fichiers_audio/` : Fichiers `.m4a` récupérés depuis iTunes.
  - `/pochettes/` : Fichiers `.jpg` (600x600px) récupérés depuis iTunes.
- `/exports/` : Fichiers générés et prêts à l'emploi.
  - `/qrcodes/` : QR Codes individuels avec logo.
  - `/cartes/` : Cartes recto et verso individuelles.
  - `planches_impression_music.pdf` : Le rendu final à imprimer.

## 📝 Comment éditer les données manuellement ?

Le passage au format JSON rend la lecture et l'écriture très propres.

**Exemple d'une entrée dans `db.json` :**
```json
{
    "ID": 1,
    "Date_Ajout": "2024-01-01",
    "Date_Sortie": "1999-10-23",
    "Titre": "Californication",
    "Artiste": "Red Hot Chili Peppers",
    "Genre": 2,
    "Difficulté": "Facile",
    "preview_url_itunes": "https://...",
    "artwork_url_itunes": "https://...",
    "local_preview_path": "../modes/music/assets/fichiers_audio/1_Californication_Red_Hot.m4a",
    "local_artwork_path": "../modes/music/assets/pochettes/1_Californication_Red_Hot.jpg"
}
```

Si vous souhaitez forcer un changement d'année, modifiez simplement `Date_Sortie` dans ce fichier, puis relancez le script de génération de cartes (Script n°4) !
