import pandas as pd
import os

# Définition des chemins relatifs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYLIST_PATH = os.path.join(BASE_DIR, "../decibel_playlist.csv")
AUDIO_DIR = os.path.join(BASE_DIR, "../fichiers_audio")
ARTWORK_DIR = os.path.join(BASE_DIR, "../pochettes")

def main():
    if not os.path.exists(PLAYLIST_PATH):
        print(f"Erreur: {PLAYLIST_PATH} introuvable.")
        return

    try:
        df = pd.read_csv(PLAYLIST_PATH)
    except Exception as e:
        print(f"Erreur lors de la lecture du CSV: {e}")
        return

    try:
        id_to_delete = int(input("Entrez l'ID de la musique à supprimer : "))
    except ValueError:
        print("Veuillez entrer un nombre valide.")
        return

    if id_to_delete not in df['ID'].values:
        print(f"L'ID {id_to_delete} n'existe pas dans la base de données.")
        return

    # Récupérer les infos de la musique à supprimer
    row_to_delete = df[df['ID'] == id_to_delete].iloc[0]
    print(f"\nVous allez supprimer : {row_to_delete['Titre']} - {row_to_delete['Artiste']}")
    confirm = input("Êtes-vous sûr ? Cette action est irréversible (o/n) : ")
    
    if confirm.lower() != 'o':
        print("Annulation.")
        return

    print(f"\nSuppression des fichiers pour l'ID {id_to_delete}...")
    
    # 1. Supprimer les fichiers physiques (audio et pochette) de la musique ciblée
    audio_path = os.path.join(BASE_DIR, "..", str(row_to_delete['local_preview_path']).replace('./', ''))
    artwork_path = os.path.join(BASE_DIR, "..", str(row_to_delete['local_artwork_path']).replace('./', ''))
    
    if os.path.exists(audio_path):
        os.remove(audio_path)
        print(f" - Supprimé : {os.path.basename(audio_path)}")
    
    if os.path.exists(artwork_path):
        os.remove(artwork_path)
        print(f" - Supprimé : {os.path.basename(artwork_path)}")

    # 2. Retirer la ligne du DataFrame
    df = df[df['ID'] != id_to_delete].reset_index(drop=True)

    # 3. Décaler tous les IDs suivants et renommer les fichiers
    print("Décalage des IDs suivants et renommage des fichiers...")
    
    count_shifted = 0
    # On itère sur le dataframe directement
    for idx in range(len(df)):
        current_id = df.at[idx, 'ID']
        
        if current_id > id_to_delete:
            new_id = current_id - 1
            
            old_audio_rel = str(df.at[idx, 'local_preview_path'])
            old_artwork_rel = str(df.at[idx, 'local_artwork_path'])
            
            old_audio_abs = os.path.join(BASE_DIR, "..", old_audio_rel.replace('./', ''))
            old_artwork_abs = os.path.join(BASE_DIR, "..", old_artwork_rel.replace('./', ''))
            
            # Déterminer les nouveaux noms de fichiers en remplaçant juste l'ID au début
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

            # Renommer physiquement
            if os.path.exists(old_audio_abs):
                os.rename(old_audio_abs, new_audio_abs)
            
            if os.path.exists(old_artwork_abs):
                os.rename(old_artwork_abs, new_artwork_abs)

            # Mettre à jour le DataFrame
            df.at[idx, 'ID'] = new_id
            df.at[idx, 'local_preview_path'] = f"./fichiers_audio/{new_audio_filename}"
            df.at[idx, 'local_artwork_path'] = f"./pochettes/{new_artwork_filename}"
            
            count_shifted += 1

    # 4. Sauvegarder le CSV final
    df.to_csv(PLAYLIST_PATH, index=False)
    print(f"\nTerminé ! {count_shifted} musiques ont été décalées pour boucher le trou.")

if __name__ == "__main__":
    main()
