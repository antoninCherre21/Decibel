import pandas as pd
import requests
import os
import time

# Chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # /home/etud/Decibel
INPUT_CSV = os.path.join(BASE_DIR, "scripts", "decibel_playlist_prov.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "decibel_playlist.csv")

AUDIO_DIR = os.path.join(BASE_DIR, "fichiers_audio")
POCHETTES_DIR = os.path.join(BASE_DIR, "pochettes")

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(POCHETTES_DIR, exist_ok=True)

def safe_filename(name):
    """Nettoie le nom pour qu'il soit un nom de fichier valide"""
    return "".join([c for c in str(name) if c.isalnum() or c in [' ', '-', '_']]).strip().replace(' ', '_')

def download_file(url, filepath):
    if pd.isna(url) or not url.startswith("http"):
        return False
    if os.path.exists(filepath):
        return True # Déjà téléchargé
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            time.sleep(0.1) # Petite pause pour ne pas spammer les serveurs
            return True
        else:
            print(f"Erreur HTTP {response.status_code} pour {url}")
    except Exception as e:
        print(f"Erreur lors du téléchargement de {url}: {e}")
    return False

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"Erreur: le fichier d'entrée {INPUT_CSV} n'existe pas.")
        return

    df = pd.read_csv(INPUT_CSV)
    
    for index, row in df.iterrows():
        titre = safe_filename(row.get('Titre', f"titre_{index}"))
        artiste = safe_filename(row.get('Artiste', f"artiste_{index}"))
        
        # --- Audio ---
        audio_url = row.get('preview_url')
        if pd.notna(audio_url) and isinstance(audio_url, str) and audio_url.startswith("http"):
            audio_filename = f"{index}_{titre}_{artiste}.m4a" # Itunes renvoie souvent du m4a
            audio_path = os.path.join(AUDIO_DIR, audio_filename)
            if download_file(audio_url, audio_path):
                # On met à jour l'URL avec le chemin local relatif à la racine du projet
                df.at[index, 'preview_url'] = f"./fichiers_audio/{audio_filename}"

        # --- Pochette ---
        artwork_url = row.get('artwork_url')
        if pd.notna(artwork_url) and isinstance(artwork_url, str) and artwork_url.startswith("http"):
            artwork_filename = f"{index}_{titre}_{artiste}.jpg"
            artwork_path = os.path.join(POCHETTES_DIR, artwork_filename)
            if download_file(artwork_url, artwork_path):
                # On met à jour l'URL avec le chemin local relatif à la racine du projet
                df.at[index, 'artwork_url'] = f"./pochettes/{artwork_filename}"
                
        print(f"Traitement terminé pour la ligne {index}: {row.get('Titre')}")

    # Sauvegarde finale
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Téléchargements terminés. Données sauvegardées dans {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
