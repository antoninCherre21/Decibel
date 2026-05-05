# Décibel - Le Jeu Musical & Cinématographique Open Source

Décibel est un projet open-source permettant de créer, imprimer et jouer à un jeu de société moderne de type "Blind-Test" (inspiré de Hitster) à l'aide de véritables cartes physiques dotées de QR codes. Le jeu fonctionne via une Web App 100% statique (PWA) agissant comme un scanner natif.

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
├── webapp/                  # Les fichiers de la Progressive Web App
│   ├── scanner.html         # L'interface du scanner et du lecteur
│   ├── manifest.json        # Configuration d'installation PWA
│   ├── sw.js                # Service Worker (Cache offline)
│   └── img/                 # Logos et icônes
├── modes/                   # Dossier contenant tous les modes de jeu
│   ├── music/               # (Voir le README dans ce dossier pour plus de détails)
│   ├── movies/              # (À venir)
│   └── series/              # (À venir)
├── scripts/                 # Les scripts Python d'automatisation
│   ├── 0_recherche_API.py
│   ├── 1_download.py
│   └── ...
└── run_all.py               # Le script principal pour tout générer !
```

---

## 🛠️ Comment utiliser le projet ?

### 1. Prérequis (Pour l'ordinateur)
- Python 3.9+
- Librairies Python : `pip install pandas requests qrcode Pillow`

### 2. Comment ajouter de nouvelles cartes ?
1. Placez vos envies dans `modes/<mode>/to_add.json`.
2. Ouvrez un terminal à la racine du projet et lancez :
   ```bash
   python run_all.py
   ```
3. Suivez les instructions à l'écran. Le script vous demandera pour quel mode vous souhaitez travailler, puis exécutera la chaîne complète (Recherche API -> Téléchargement Media -> Génération QR -> Génération Cartes -> Génération PDF).

### 3. Comment jouer ? (Le Serveur Web)
Le dossier complet peut être poussé sur **GitHub Pages** ou un serveur web classique.
1. Ouvrez l'URL du site depuis un smartphone.
2. Cliquez sur le mode désiré (ex: *Musique*).
3. Acceptez l'utilisation de la caméra.
4. Flashez vos cartes imprimées. La musique ou l'extrait se lancera instantanément !

> 💡 **Astuce Pro :** Sur iOS/Android, cliquez sur "Partager" puis "Ajouter à l'écran d'accueil" pour installer le jeu comme une véritable application native.
