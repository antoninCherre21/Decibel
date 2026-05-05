import pandas as pd
import os
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="music", help="Mode de jeu")
    args = parser.add_argument() if False else parser.parse_args()
    
    mode = args.mode
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PLAYLIST_PATH = os.path.join(BASE_DIR, "modes", mode, "db.json")
    AUDIO_DIR = os.path.join(BASE_DIR, "modes", mode, "assets", "fichiers_audio")
    ARTWORK_DIR = os.path.join(BASE_DIR, "modes", mode, "assets", "pochettes")

    if not os.path.exists(PLAYLIST_PATH):
        print(f"Erreur: {PLAYLIST_PATH} introuvable.")
        return

    try:
        df = pd.read_json(PLAYLIST_PATH)
    except Exception as e:
        print(f"Erreur lors de la lecture du JSON: {e}")
        return

    try:
        id_to_delete = int(input("Entrez l'ID de l'élément à supprimer : "))
    except ValueError:
        print("Veuillez entrer un nombre valide.")
        return

    if id_to_delete not in df['ID'].values:
        print(f"L'ID {id_to_delete} n'existe pas dans la base de données.")
        return

    row_to_delete = df[df['ID'] == id_to_delete].iloc[0]
    titre = row_to_delete.get('Titre', '')
    artiste = row_to_delete.get('Artiste', '')
    
    print(f"\nVous allez supprimer : {titre} - {artiste}")
    confirm = input("Êtes-vous sûr ? Cette action est irréversible (o/n) : ")
    
    if confirm.lower() != 'o':
        print("Annulation.")
        return

    print(f"\nSuppression des fichiers pour l'ID {id_to_delete}...")
    
    audio_path = os.path.join(BASE_DIR, str(row_to_delete.get('local_preview_path', '')).replace('../', ''))
    artwork_path = os.path.join(BASE_DIR, str(row_to_delete.get('local_artwork_path', '')).replace('../', ''))
    
    if os.path.exists(audio_path):
        os.remove(audio_path)
        print(f" - Supprimé : {os.path.basename(audio_path)}")
    
    if os.path.exists(artwork_path):
        os.remove(artwork_path)
        print(f" - Supprimé : {os.path.basename(artwork_path)}")

    df = df[df['ID'] != id_to_delete].reset_index(drop=True)

    print("Décalage des IDs suivants et renommage des fichiers...")
    
    count_shifted = 0
    for idx in range(len(df)):
        current_id = df.at[idx, 'ID']
        
        if current_id > id_to_delete:
            new_id = current_id - 1
            
            old_audio_rel = str(df.at[idx, 'local_preview_path'])
            old_artwork_rel = str(df.at[idx, 'local_artwork_path'])
            
            old_audio_abs = os.path.join(BASE_DIR, old_audio_rel.replace('../', ''))
            old_artwork_abs = os.path.join(BASE_DIR, old_artwork_rel.replace('../', ''))
            
            audio_filename = os.path.basename(old_audio_abs)
            artwork_filename = os.path.basename(old_artwork_abs)
            
            if '_' in audio_filename:
                new_audio_filename = f"{new_id}_{audio_filename.split('_', 1)[1]}"
            else:
                new_audio_filename = f"{new_id}.m4a"
                
            if '_' in artwork_filename:
                new_artwork_filename = f"{new_id}_{artwork_filename.split('_', 1)[1]}"
            else:
                new_artwork_filename = f"{new_id}.jpg"
                
            new_audio_abs = os.path.join(AUDIO_DIR, new_audio_filename)
            new_artwork_abs = os.path.join(ARTWORK_DIR, new_artwork_filename)

            if os.path.exists(old_audio_abs):
                os.rename(old_audio_abs, new_audio_abs)
            
            if os.path.exists(old_artwork_abs):
                os.rename(old_artwork_abs, new_artwork_abs)

            df.at[idx, 'ID'] = new_id
            df.at[idx, 'local_preview_path'] = f"../modes/{mode}/assets/fichiers_audio/{new_audio_filename}"
            df.at[idx, 'local_artwork_path'] = f"../modes/{mode}/assets/pochettes/{new_artwork_filename}"
            
            count_shifted += 1

    df.to_json(PLAYLIST_PATH, orient="records", indent=4, force_ascii=False)
    print(f"\nTerminé ! {count_shifted} éléments ont été décalés pour boucher le trou.")

if __name__ == "__main__":
    main()
