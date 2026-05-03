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
    if pd.isna(url) or not str(url).startswith("http"):
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

def get_max_id():
    if not os.path.exists(OUTPUT_CSV):
        return 0
    try:
        df = pd.read_csv(OUTPUT_CSV)
        if 'ID' in df.columns and not df.empty:
            return int(df['ID'].max())
    except pd.errors.EmptyDataError:
        pass
    return 0

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"Le fichier {INPUT_CSV} n'existe pas. Rien à télécharger.")
        return

    try:
        df_queue = pd.read_csv(INPUT_CSV)
    except pd.errors.EmptyDataError:
        print(f"Le fichier {INPUT_CSV} est vide. Rien à télécharger.")
        return

    if df_queue.empty:
        print("Aucune musique en attente de téléchargement dans le fichier provisoire.")
        return

    # On récupère le dernier ID utilisé
    current_max_id = get_max_id()

    # On garde une trace des lignes traitées avec succès
    indices_to_drop = []
    
    for index, row in df_queue.iterrows():
        titre = safe_filename(row.get('Titre', f"titre_{index}"))
        artiste = safe_filename(row.get('Artiste', f"artiste_{index}"))
        
        audio_url = row.get('preview_url_itunes')
        artwork_url = row.get('artwork_url_itunes')
        
        # Nouvel ID pour cette musique
        new_id = current_max_id + 1
        
        success_audio = False
        success_artwork = False
        
        local_audio_path = ""
        local_artwork_path = ""
        
        # --- Audio ---
        if pd.notna(audio_url) and str(audio_url).startswith("http"):
            audio_filename = f"{new_id}_{titre}_{artiste}.m4a"
            audio_path = os.path.join(AUDIO_DIR, audio_filename)
            if download_file(audio_url, audio_path):
                local_audio_path = f"./fichiers_audio/{audio_filename}"
                success_audio = True
        else:
            success_audio = True # Déjà local ou vide

        # --- Pochette ---
        if pd.notna(artwork_url) and str(artwork_url).startswith("http"):
            artwork_filename = f"{new_id}_{titre}_{artiste}.jpg"
            artwork_path = os.path.join(POCHETTES_DIR, artwork_filename)
            if download_file(artwork_url, artwork_path):
                local_artwork_path = f"./pochettes/{artwork_filename}"
                success_artwork = True
        else:
            success_artwork = True

        # --- Finalisation de la ligne ---
        if success_audio and success_artwork:
            row_dict = row.to_dict()
            row_dict['ID'] = new_id
            row_dict['local_preview_path'] = local_audio_path
            row_dict['local_artwork_path'] = local_artwork_path
            
            # On ajoute la ligne au fichier final
            df_final_row = pd.DataFrame([row_dict])
            
            # Ordre strict des colonnes
            columns_order = ['ID', 'Date_Ajout', 'Date_Sortie', 'Titre', 'Artiste', 'Genre', 'Difficulté', 'preview_url_itunes', 'artwork_url_itunes', 'local_preview_path', 'local_artwork_path']
            for col in columns_order:
                if col not in df_final_row.columns:
                    df_final_row[col] = ""
            df_final_row = df_final_row[columns_order]
            
            header_mode = not os.path.exists(OUTPUT_CSV)
            df_final_row.to_csv(OUTPUT_CSV, mode='a', header=header_mode, index=False)
            
            # Ligne traitée avec succès
            current_max_id = new_id
            indices_to_drop.append(index)
            print(f"✅ Ajouté à la base finale (ID {new_id}) : {row.get('Titre')}")
        else:
            print(f"❌ Échec pour : {row.get('Titre')}. Laissé en attente dans le fichier provisoire.")

    # --- Mise à jour du fichier provisoire ---
    df_queue = df_queue.drop(indices_to_drop)
    df_queue.to_csv(INPUT_CSV, index=False)
    
    print(f"\nTéléchargements terminés. {len(indices_to_drop)} musiques ont été basculées vers decibel_playlist.csv.")
    if not df_queue.empty:
        print(f"Il reste {len(df_queue)} musiques en échec dans decibel_playlist_prov.csv à retenter plus tard.")

if __name__ == "__main__":
    main()
