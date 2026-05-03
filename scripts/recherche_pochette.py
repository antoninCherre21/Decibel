import requests
import os
import shutil
import pandas as pd

def clean_filename(filename):
    return "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).strip()

def search_artwork():
    print("--- Recherche de Pochette iTunes et Mise à jour ---")
    
    csv_file = "../decibel_playlist.csv"
    if not os.path.exists(csv_file):
        csv_file = "decibel_playlist.csv"
        
    if not os.path.exists(csv_file):
        print(f"Erreur : Impossible de trouver {csv_file}")
        return
        
    df = pd.read_csv(csv_file)
    
    recherche = input("Rechercher dans votre playlist (Titre ou Artiste) : ").strip().lower()
    
    # Filtrer les musiques qui correspondent
    matches = df[df['Titre'].str.lower().str.contains(recherche, na=False) | 
                 df['Artiste'].str.lower().str.contains(recherche, na=False)]
                 
    if matches.empty:
        print("Aucune musique trouvée dans votre playlist.")
        return
        
    print("\nMusiques trouvées dans votre playlist :")
    for i, (idx, row) in enumerate(matches.iterrows()):
        print(f"[{i+1}] {row['Titre']} - {row['Artiste']} (ID: {row['ID']})")
        
    choix_musique = input("\nChoisissez le numéro de la musique à modifier (ou 'q' pour quitter) : ")
    if choix_musique.lower() == 'q':
        return
        
    try:
        choix_musique_idx = int(choix_musique) - 1
        if not (0 <= choix_musique_idx < len(matches)):
            print("Choix invalide.")
            return
    except ValueError:
        print("Entrée invalide.")
        return
        
    selected_row = matches.iloc[choix_musique_idx]
    titre = selected_row['Titre']
    artiste = selected_row['Artiste']
    song_id = selected_row['ID']
    original_idx = selected_row.name # L'index dans le dataframe original
    
    print(f"\nRecherche de pochettes sur iTunes pour : {titre} - {artiste}...")

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
        print("Aucun résultat trouvé sur iTunes.")
        return

    temp_dir = "./temp_pochettes"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    choices = []
    
    print("\nRésultats trouvés :")

    for i, item in enumerate(results):
        track_name = item.get("trackName", "Inconnu")
        artist_name = item.get("artistName", "Inconnu")
        album_name = item.get("collectionName", "Inconnu")
        
        artwork_url_100 = item.get("artworkUrl100")
        if not artwork_url_100:
            continue
            
        artwork_url_hq = artwork_url_100.replace("100x100bb.jpg", "600x600bb.jpg")
        
        try:
            img_resp = requests.get(artwork_url_hq)
            img_resp.raise_for_status()
            
            filename = f"temp_{i+1}.jpg"
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(img_resp.content)
                
            print(f"[{i+1}] {track_name} - {artist_name} (Album: {album_name})")
            
            choices.append((artwork_url_hq, filepath))
            
        except requests.RequestException:
            choices.append(None)

    while True:
        try:
            choice_str = input("\nChoisissez le numéro de la nouvelle pochette (0 pour annuler) : ")
            if choice_str == '0':
                print("Annulé.")
                break
            
            choice_idx = int(choice_str) - 1
            if 0 <= choice_idx < len(choices) and choices[choice_idx]:
                new_url, temp_filepath = choices[choice_idx]
                
                # Récupérer le chemin local depuis le CSV ou le générer
                local_path = df.at[original_idx, 'local_artwork_path']
                if pd.isna(local_path) or str(local_path).strip() == "":
                    titre_clean = clean_filename(str(titre).replace(" ", "_"))
                    artiste_clean = clean_filename(str(artiste).replace(" ", "_"))
                    local_path = f"./pochettes/{song_id}_{titre_clean}_{artiste_clean}.jpg"
                    df.at[original_idx, 'local_artwork_path'] = local_path
                
                # Remplacer le fichier
                target_filepath = os.path.join(os.path.dirname(csv_file), local_path)
                os.makedirs(os.path.dirname(target_filepath), exist_ok=True)
                
                shutil.copy(temp_filepath, target_filepath)
                print(f"\n[+] Pochette remplacée : {target_filepath}")
                
                # Mettre à jour le CSV
                df.at[original_idx, 'artwork_url_itunes'] = new_url
                df.to_csv(csv_file, index=False)
                print("[+] Base de données mise à jour avec succès.")
                
                break
            else:
                print("Numéro invalide.")
        except ValueError:
            print("Entrée invalide.")

    # Nettoyage
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    search_artwork()
