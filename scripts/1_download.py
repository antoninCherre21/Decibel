import pandas as pd
import requests
import os
import time
import argparse

def safe_filename(name):
    return "".join([c for c in str(name) if c.isalnum() or c in [' ', '-', '_']]).strip().replace(' ', '_')

def download_file(url, filepath):
    if pd.isna(url) or not str(url).startswith("http"):
        return False
    if os.path.exists(filepath):
        return True
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            time.sleep(0.1)
            return True
        else:
            print(f"Erreur HTTP {response.status_code} pour {url}")
    except Exception as e:
        print(f"Erreur lors du téléchargement de {url}: {e}")
    return False

def get_max_id(output_file):
    if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
        return 0
    try:
        df = pd.read_json(output_file)
        if 'ID' in df.columns and not df.empty:
            return int(df['ID'].max())
    except Exception:
        pass
    return 0

def main():
    parser = argparse.ArgumentParser(description="Téléchargement des médias")
    parser.add_argument("--mode", type=str, default="music", help="Mode de jeu (ex: music, movies)")
    args = parser.add_argument() if False else parser.parse_args()
    
    mode = args.mode
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT_FILE = os.path.join(BASE_DIR, "scripts", f"{mode}_playlist_prov.json")
    OUTPUT_FILE = os.path.join(BASE_DIR, "modes", mode, "db.json")

    AUDIO_DIR = os.path.join(BASE_DIR, "modes", mode, "assets", "fichiers_audio")
    POCHETTES_DIR = os.path.join(BASE_DIR, "modes", mode, "assets", "pochettes")

    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(POCHETTES_DIR, exist_ok=True)

    if not os.path.exists(INPUT_FILE) or os.path.getsize(INPUT_FILE) == 0:
        print(f"Le fichier {INPUT_FILE} est vide ou n'existe pas. Rien à télécharger.")
        return

    try:
        df_queue = pd.read_json(INPUT_FILE)
    except Exception:
        print(f"Le fichier {INPUT_FILE} est vide. Rien à télécharger.")
        return

    if df_queue.empty:
        print("Aucune musique en attente de téléchargement dans le fichier provisoire.")
        return

    current_max_id = get_max_id(OUTPUT_FILE)
    indices_to_drop = []
    
    for index, row in df_queue.iterrows():
        titre = safe_filename(row.get('Titre', f"titre_{index}"))
        artiste = safe_filename(row.get('Artiste', f"artiste_{index}"))
        
        audio_url = row.get('preview_url_itunes')
        artwork_url = row.get('artwork_url_itunes')
        
        new_id = current_max_id + 1
        success_audio = False
        success_artwork = False
        local_audio_path = ""
        local_artwork_path = ""
        
        if pd.notna(audio_url) and str(audio_url).startswith("http"):
            audio_filename = f"{new_id}_{titre}_{artiste}.m4a"
            audio_path = os.path.join(AUDIO_DIR, audio_filename)
            if download_file(audio_url, audio_path):
                local_audio_path = f"../modes/{mode}/assets/fichiers_audio/{audio_filename}"
                success_audio = True
        else:
            print(f"⚠️ URL audio invalide ou manquante pour {titre}.")

        if pd.notna(artwork_url) and str(artwork_url).startswith("http"):
            artwork_filename = f"{new_id}_{titre}_{artiste}.jpg"
            artwork_path = os.path.join(POCHETTES_DIR, artwork_filename)
            if download_file(artwork_url, artwork_path):
                local_artwork_path = f"../modes/{mode}/assets/pochettes/{artwork_filename}"
                success_artwork = True
        else:
            print(f"⚠️ URL pochette invalide ou manquante pour {titre}.")

        if success_audio and success_artwork:
            row_dict = row.to_dict()
            row_dict['ID'] = new_id
            row_dict['local_preview_path'] = local_audio_path
            row_dict['local_artwork_path'] = local_artwork_path
            
            columns_order = ['ID', 'Date_Ajout', 'Date_Sortie', 'Titre', 'Artiste', 'Genre', 'Difficulté', 'preview_url_itunes', 'artwork_url_itunes', 'local_preview_path', 'local_artwork_path']
            
            if os.path.exists(OUTPUT_FILE) and os.path.getsize(OUTPUT_FILE) > 0:
                df_final = pd.read_json(OUTPUT_FILE)
            else:
                df_final = pd.DataFrame(columns=columns_order)
                
            df_final_row = pd.DataFrame([row_dict])
            for col in columns_order:
                if col not in df_final_row.columns:
                    df_final_row[col] = ""
            df_final_row = df_final_row[columns_order]
            
            df_final = pd.concat([df_final, df_final_row], ignore_index=True)
            df_final.to_json(OUTPUT_FILE, orient="records", indent=4, force_ascii=False)
            
            current_max_id = new_id
            indices_to_drop.append(index)
            print(f"✅ Ajouté à la base finale (ID {new_id}) : {row.get('Titre')}")
        else:
            print(f"❌ Échec pour : {row.get('Titre')}. Laissé en attente dans le fichier provisoire.")

    df_queue = df_queue.drop(indices_to_drop)
    df_queue.to_json(INPUT_FILE, orient="records", indent=4, force_ascii=False)
    
    print(f"\nTéléchargements terminés. {len(indices_to_drop)} musiques ont été basculées vers db.json.")
    if not df_queue.empty:
        print(f"Il reste {len(df_queue)} musiques en échec dans {mode}_playlist_prov.json à retenter plus tard.")

if __name__ == "__main__":
    main()
