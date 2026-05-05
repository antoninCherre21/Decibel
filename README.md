# Décibel - Le Jeu Musical & Cinématographique Open Source

Décibel est un projet open-source permettant de créer, imprimer et jouer à un jeu de société moderne de type "Blind-Test" (inspiré de Hitster) à l'aide de véritables cartes physiques dotées de QR codes. Le jeu fonctionne via une **Web App 100% statique (PWA)** agissant comme un scanner natif.

🎮 **Web App en ligne :** [https://antonincherre21.github.io/Decibel/](https://antonincherre21.github.io/Decibel/)

---

## 🚀 Fonctionnalités Clés

- **Système Multi-Modes :** Architecture modulable permettant d'ajouter facilement différents modes de jeu (`music`, `movies`, `series`).
- **Web App PWA :** Un scanner ultra-rapide (lecture de QR Codes en JS via la caméra), installable sur téléphone sans passer par l'App Store.
- **Base de Données Légère :** Utilisation du format JSON pour un chargement instantané dans la Web App.
- **Automatisation Totale (Python) :** Des scripts gèrent l'intégralité du cycle :
  - Connexion aux API (ex: iTunes) pour récupérer musiques, dates de sortie et pochettes HD.
  - Génération des QR Codes avec le logo de votre choix.
  - Mise en page automatique des cartes physiques (recto/verso) et génération des planches PDF prêtes à imprimer.

---

## 📁 Architecture du Dépôt

L'architecture est pensée pour être facilement hébergée sur **GitHub Pages** ou tout autre serveur statique (Apache, Nginx, OVH).

```text
/Decibel
├── index.html               # Le Menu Principal (choix du mode de jeu)
├── requirements.txt         # Dépendances Python à installer
├── run_all.py               # Le script principal pour tout générer !
├── webapp/                  # Les fichiers de la Progressive Web App
│   ├── scanner.html         # L'interface du scanner et du lecteur
│   ├── manifest.json        # Configuration d'installation PWA
│   ├── sw.js                # Service Worker (Cache offline)
│   └── img/                 # Logos et icônes
├── modes/                   # Dossier contenant tous les modes de jeu
│   ├── music/               # (Voir le README dans ce dossier pour plus de détails)
│   ├── movies/              # (À venir)
│   └── series/              # (À venir)
└── scripts/                 # Les scripts Python d'automatisation
    ├── utils.py             # Fonctions partagées (chemins, JSON, etc.)
    ├── 0_recherche_API.py
    ├── 1_download.py
    ├── 2_Verification_BDD.py
    ├── 3_generer_qrcodes.py
    ├── 4_generer_cartes_musique.py
    ├── 5_generer_planche_impression.py
    ├── recherche_pochette.py
    └── supprimer_musique.py
```

---

## 🛠️ Comment utiliser le projet ?

### 1. Prérequis — Installer les dépendances Python

Le projet utilise un fichier `requirements.txt` qui liste toutes les librairies nécessaires. Pour les installer automatiquement en une seule commande :

```bash
pip install -r requirements.txt
```

> Cela installera : `requests`, `Pillow`, `qrcode[pil]`. Aucune autre dépendance n'est requise (Python 3.9+ suffit).

---

### 2. Comment ajouter de nouvelles cartes ?

1. Placez vos musiques dans `modes/<mode>/to_add.json` au format suivant :
   ```json
   [
       {
           "Titre": "Nom de la chanson",
           "Artiste": "Nom de l'artiste",
           "Date": "YYYY-MM-DD",
           "Genre": "Pop",
           "Difficulté": "Facile"
       }
   ]
   ```
2. Ouvrez un terminal à la racine du projet et lancez :
   ```bash
   python run_all.py
   ```
3. Suivez les instructions à l'écran. Le script demandera pour quel mode travailler, puis exécutera la chaîne complète :
   **Recherche API → Téléchargement Media → Génération QR → Génération Cartes → Génération PDF**

---

### 3. Personnaliser une pochette d'album

Si une pochette récupérée automatiquement ne vous convient pas, vous pouvez en sélectionner une autre parmi les résultats iTunes :

```bash
python scripts/recherche_pochette.py --mode music
```

Le script vous permet de :
1. Rechercher une musique dans votre base par **titre ou artiste**.
2. Voir tous les résultats disponibles sur iTunes.
3. Choisir la pochette qui vous plaît le mieux.
4. Mettre à jour automatiquement la base de données et le fichier image local.

---

### 4. Ajuster le zoom d'une pochette

Certaines pochettes peuvent être mal cadrées sur la carte recto. Vous pouvez ajuster le zoom de deux façons :

**Option A — Via `db.json` (méthode recommandée) :**
Ajoutez les champs optionnels `zoom` et/ou `y_offset` directement sur l'entrée dans `modes/<mode>/db.json` :
```json
{
    "ID": 42,
    "Titre": "Ma chanson",
    "zoom": 1.15,
    "y_offset": -20
}
```
- `zoom` : facteur de zoom (ex: `1.15` = zoom +15%). Valeur par défaut : `1.0`.
- `y_offset` : décalage vertical en pixels (positif = vers le bas, négatif = vers le haut). Valeur par défaut : `0`.

**Option B — Via la table `ZOOMS_SPECIFIQUES` dans le script 4 :**
Ouvrez `scripts/4_generer_cartes_musique.py` et ajoutez une entrée dans le dictionnaire `ZOOMS_SPECIFIQUES` en haut du fichier :
```python
ZOOMS_SPECIFIQUES = {
    ...
    ("Titre de la chanson", "Nom de l'artiste"): {"ratio": 1.15, "y_offset": -20},
}
```
> 💡 La méthode A (via `db.json`) est préférable car elle ne nécessite pas de modifier le code.

---

### 5. Comment jouer ? (Le Serveur Web)

Le dossier complet est hébergé sur **GitHub Pages** et accessible directement depuis n'importe quel smartphone.

🔗 **[https://antonincherre21.github.io/Decibel/](https://antonincherre21.github.io/Decibel/)**

1. Ouvrez ce lien depuis un smartphone.
2. Cliquez sur le mode désiré (ex: *Musique*).
3. Acceptez l'utilisation de la caméra.
4. Flashez vos cartes imprimées. La musique ou l'extrait se lancera instantanément !

> 💡 **Astuce Pro :** Sur iOS/Android, cliquez sur "Partager" puis "Ajouter à l'écran d'accueil" pour installer le jeu comme une véritable application native, sans passer par l'App Store.
