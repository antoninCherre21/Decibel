import pandas as pd
import os

csv_file = "decibel_playlist.csv"
df = pd.read_csv(csv_file)

def safe_filename(name):
    return "".join([c for c in str(name) if c.isalnum() or c in [' ', '-', '_']]).strip().replace(' ', '_')

changes_made = 0

for index, row in df.iterrows():
    music_id = row['ID']
    if pd.isna(music_id):
        continue
    music_id = int(music_id)
    
    titre = safe_filename(row.get('Titre', f"titre_{index}"))
    artiste = safe_filename(row.get('Artiste', f"artiste_{index}"))
    
    expected_audio_filename = f"{music_id}_{titre}_{artiste}.m4a"
    expected_artwork_filename = f"{music_id}_{titre}_{artiste}.jpg"
    
    expected_audio_path = f"./fichiers_audio/{expected_audio_filename}"
    expected_artwork_path = f"./pochettes/{expected_artwork_filename}"
    
    current_audio_path = str(row.get('local_preview_path'))
    current_artwork_path = str(row.get('local_artwork_path'))
    
    # Correction Audio
    if current_audio_path != expected_audio_path and current_audio_path != "nan":
        if os.path.exists(current_audio_path):
            os.rename(current_audio_path, expected_audio_path)
            print(f"Renommé (Audio) : {current_audio_path} -> {expected_audio_path}")
        df.at[index, 'local_preview_path'] = expected_audio_path
        changes_made += 1
        
    # Correction Artwork
    if current_artwork_path != expected_artwork_path and current_artwork_path != "nan":
        if os.path.exists(current_artwork_path):
            os.rename(current_artwork_path, expected_artwork_path)
            print(f"Renommé (Artwork) : {current_artwork_path} -> {expected_artwork_path}")
        df.at[index, 'local_artwork_path'] = expected_artwork_path
        changes_made += 1

    # Verification existence
    if not os.path.exists(expected_audio_path) and pd.notna(row.get('preview_url_itunes')) and str(row.get('preview_url_itunes')).startswith('http'):
        print(f"⚠️ Fichier audio manquant : {expected_audio_path}")
    if not os.path.exists(expected_artwork_path) and pd.notna(row.get('artwork_url_itunes')) and str(row.get('artwork_url_itunes')).startswith('http'):
        print(f"⚠️ Fichier artwork manquant : {expected_artwork_path}")

if changes_made > 0:
    df.to_csv(csv_file, index=False)
    print(f"✅ Terminé. {changes_made} chemins corrigés dans {csv_file}.")
else:
    print("✅ Tout est déjà cohérent.")
