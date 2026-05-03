import requests
import os
import shutil
import sys

# Tentative d'import de pyperclip pour le presse-papier
try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False
    print("Note: 'pyperclip' n'est pas installé. Le lien ne sera pas copié dans le presse-papier.")
    print("Vous pouvez l'installer avec: pip install pyperclip")

def clean_filename(filename):
    return "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).strip()

def search_artwork():
    print("--- Recherche de Pochette iTunes ---")
    titre = input("Titre de la musique : ").strip()
    artiste = input("Artiste : ").strip()

    if not titre or not artiste:
        print("Erreur: Titre et Artiste sont requis.")
        return

    term = f"{titre} {artiste}"
    url = "https://itunes.apple.com/search"
    params = {
        "term": term,
        "media": "music",
        "entity": "song",
        "limit": 20
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Erreur lors de la requête API : {e}")
        return

    results = data.get("results", [])
    if not results:
        print("Aucun résultat trouvé.")
        return

    # Création du dossier temporaire
    temp_dir = "./temp_pochettes"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    print(f"\n{len(results)} résultats trouvés. Téléchargement des aperçus dans '{temp_dir}'...\n")

    choices = []

    for i, item in enumerate(results):
        track_name = item.get("trackName", "Inconnu")
        artist_name = item.get("artistName", "Inconnu")
        album_name = item.get("collectionName", "Inconnu")
        release_date = item.get("releaseDate", "Inconnue")[:4] # Année seulement
        
        # Récupération de l'URL haute qualité (600x600)
        artwork_url_100 = item.get("artworkUrl100")
        if not artwork_url_100:
            print(f"{i+1}. Pas d'image pour {track_name}")
            continue
            
        artwork_url_hq = artwork_url_100.replace("100x100bb.jpg", "600x600bb.jpg")
        
        # Téléchargement de l'image
        try:
            img_resp = requests.get(artwork_url_hq)
            img_resp.raise_for_status()
            
            filename = f"{i+1}.jpg"
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(img_resp.content)
                
            print(f"[{i+1}] {track_name} - {artist_name}")
            print(f"    Album: {album_name} ({release_date})")
            print(f"    Image: {filepath}")
            
            choices.append(artwork_url_hq)
            
        except requests.RequestException:
            print(f"[{i+1}] Erreur de téléchargement pour {track_name}")
            choices.append(None)
        print("-" * 40)

    # Sélection utilisateur
    while True:
        try:
            choice_str = input("\nChoisissez le numéro de l'image (ou 'q' pour quitter) : ")
            if choice_str.lower() == 'q':
                break
            
            choice_idx = int(choice_str) - 1
            if 0 <= choice_idx < len(choices) and choices[choice_idx]:
                selected_url = choices[choice_idx]
                print("\n" + "="*60)
                print("Lien sélectionné :")
                print(selected_url)
                print("="*60)
                
                if HAS_CLIPBOARD:
                    try:
                        pyperclip.copy(selected_url)
                        print(">> Lien copié dans le presse-papier ! <<")
                    except Exception as e:
                        print(f"Erreur lors de la copie dans le presse-papier : {e}")
                else:
                    print("(Installez 'pyperclip' pour la copie automatique)")
                
                break
            else:
                print("Numéro invalide.")
        except ValueError:
            print("Entrée invalide.")

    # Nettoyage (Optionnel - on laisse pour l'instant pour que l'utilisateur puisse voir les fichiers)
    print(f"\nLes images sont disponibles dans {temp_dir} pour vérification.")

if __name__ == "__main__":
    search_artwork()
