import requests
import os
import shutil
import pandas as pd
import argparse

def clean_filename(name):
    return "".join([c for c in str(name) if c.isalnum() or c in [' ', '-', '_']]).strip().replace(' ', '_')

def search_artwork():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="music", help="Mode de jeu")
    args = parser.add_argument() if False else parser.parse_args()
    
    mode = args.mode
    print(f"--- Recherche de Pochette iTunes et Mise à jour ({mode.upper()}) ---")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "modes", mode, "db.json")
    
    if not os.path.exists(db_path):
        print(f"Erreur : Impossible de trouver {db_path}")
        return
        
    try:
        df = pd.read_json(db_path)
    except Exception as e:
        print(f"Erreur lecture JSON: {e}")
        return
    
    recherche = input("Rechercher dans votre playlist (Titre ou Artiste) : ").strip().lower()
    
    matches = df[df['Titre'].str.lower().str.contains(recherche, na=False) | 
                 df['Artiste'].str.lower().str.contains(recherche, na=False)]
                 
    if matches.empty:
        print("Aucune musique trouvée dans votre playlist.")
        return
        
    print("\nMusiques trouvées dans votre playlist :")
    for i, (idx, row) in enumerate(matches.iterrows()):
        print(f"[{i+1}] {row['Titre']} - {row['Artiste']} (ID: {row.get('ID', '?')})")
        
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
    song_id = selected_row.get('ID', 'unknown')
    original_idx = selected_row.name
    
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

    temp_dir = os.path.join(base_dir, "temp_pochettes")
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
                
                local_path = df.at[original_idx, 'local_artwork_path']
                if pd.isna(local_path) or str(local_path).strip() == "":
                    titre_clean = clean_filename(str(titre).replace(" ", "_"))
                    artiste_clean = clean_filename(str(artiste).replace(" ", "_"))
                    local_path = f"../modes/{mode}/assets/pochettes/{song_id}_{titre_clean}_{artiste_clean}.jpg"
                    df.at[original_idx, 'local_artwork_path'] = local_path
                
                target_filepath = os.path.join(base_dir, str(local_path).replace('../', ''))
                os.makedirs(os.path.dirname(target_filepath), exist_ok=True)
                
                shutil.copy(temp_filepath, target_filepath)
                print(f"\n[+] Pochette remplacée : {target_filepath}")
                
                df.at[original_idx, 'artwork_url_itunes'] = new_url
                df.to_json(db_path, orient="records", indent=4, force_ascii=False)
                print("[+] Base de données JSON mise à jour avec succès.")
                
                break
            else:
                print("Numéro invalide.")
        except ValueError:
            print("Entrée invalide.")

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    search_artwork()
