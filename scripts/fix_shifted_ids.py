import pandas as pd
import os
import glob

csv_file = "decibel_playlist.csv"
df = pd.read_csv(csv_file)

def safe_filename(name):
    return "".join([c for c in str(name) if c.isalnum() or c in [' ', '-', '_']]).strip().replace(' ', '_')

renamed_count = 0

for index, row in df.iterrows():
    music_id = row['ID']
    if pd.isna(music_id):
        continue
    music_id = int(music_id)
    
    titre = safe_filename(row.get('Titre', f"titre_{index}"))
    artiste = safe_filename(row.get('Artiste', f"artiste_{index}"))
    
    # Audio
    expected_audio = f"./fichiers_audio/{music_id}_{titre}_{artiste}.m4a"
    if not os.path.exists(expected_audio):
        matches = glob.glob(f"./fichiers_audio/*_{titre}_{artiste}.m4a")
        if len(matches) == 1:
            os.rename(matches[0], expected_audio)
            print(f"Correction ID (Audio): {matches[0]} -> {expected_audio}")
            renamed_count += 1
            
    # Pochette
    expected_artwork = f"./pochettes/{music_id}_{titre}_{artiste}.jpg"
    if not os.path.exists(expected_artwork):
        matches = glob.glob(f"./pochettes/*_{titre}_{artiste}.jpg")
        if len(matches) == 1:
            os.rename(matches[0], expected_artwork)
            print(f"Correction ID (Artwork): {matches[0]} -> {expected_artwork}")
            renamed_count += 1

print(f"Terminé. {renamed_count} fichiers renommés.")
