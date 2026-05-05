import pandas as pd
import requests
import time
import os
import datetime
import argparse

def get_itunes_info(artist, title):
    """Recherche les infos sur iTunes API"""
    search_url = "https://itunes.apple.com/search"
    term = f"{artist} {title}".replace(" ft.", "").replace(" feat.", "")
    params = {"term": term, "entity": "song", "limit": 1}
    
    try:
        response = requests.get(search_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["resultCount"] > 0:
                result = data["results"][0]
                release_date = result.get("releaseDate", "")[:10]
                return {
                    "preview_url": result.get("previewUrl"),
                    "artwork_url": result.get("artworkUrl100").replace("100x100bb", "600x600bb"),
                    "release_date": release_date
                }
    except Exception as e:
        print(f"Erreur connexion pour {title}: {e}")
    return None

def main():
    parser = argparse.ArgumentParser(description="Recherche API iTunes")
    parser.add_argument("--mode", type=str, default="music", help="Mode de jeu (ex: music, movies)")
    args = parser.add_argument() if False else parser.parse_args()
    
    mode = args.mode
    SOURCE_FILE = f"./modes/{mode}/to_add.json"
    COMPLETED_FILE = f"./scripts/{mode}_playlist_prov.json"

    if not os.path.exists(SOURCE_FILE):
        print(f"Erreur: Le fichier source '{SOURCE_FILE}' est introuvable.")
        return

    # Chargement du fichier source JSON
    try:
        df_source = pd.read_json(SOURCE_FILE)
    except Exception as e:
        print(f"Le fichier {SOURCE_FILE} est vide ou invalide.")
        return

    print(f"Chargement de {len(df_source)} titres à traiter depuis {SOURCE_FILE}...")
    time.sleep(1)

    indices = list(df_source.index)

    for i in indices:
        if i not in df_source.index:
            continue
            
        row = df_source.loc[i]
        artiste = row.get('Artiste', '')
        titre = row.get('Titre', '')
        date_csv_raw = str(row.get('Date', '')).replace('.0', '').strip()
        year_csv = date_csv_raw[:4]
        
        print(f"\n--- Traitement : {titre} - {artiste} (JSON: {date_csv_raw}) ---")
        
        info = get_itunes_info(artiste, titre)
        
        if info:
            date_itunes_full = info['release_date']
            year_itunes = date_itunes_full[:4]
            final_date = date_itunes_full
            
            if year_itunes != year_csv and year_csv:
                print(f"⚠️  CONFLIT D'ANNÉE détecté !")
                print(f"   1. JSON (Votre date) : {date_csv_raw}")
                print(f"   2. iTunes (Meilleur résultat) : {date_itunes_full}")
                print(f"   3. Saisir manuellement")
                
                while True:
                    choix = input("   -> Quel choix (1/2/3) ? ")
                    if choix == '1':
                        final_date = date_csv_raw
                        break
                    elif choix == '2':
                        final_date = date_itunes_full
                        break
                    elif choix == '3':
                        final_date = input("   -> Entrez la date : ")
                        break
            elif date_itunes_full.endswith("-01"):
                print(f"⚠️  DATE PAR DÉFAUT SUSPECTE (Jour 01) détectée !")
                print(f"   1. Garder JSON ({date_csv_raw})")
                print(f"   2. Garder iTunes ({date_itunes_full})")
                print(f"   3. Saisir manuellement")
                
                while True:
                    choix_jour = input("   -> Quel choix (1/2/3) ? ")
                    if choix_jour == '1':
                        final_date = date_csv_raw
                        break
                    elif choix_jour == '2':
                        final_date = date_itunes_full
                        break
                    elif choix_jour == '3':
                        final_date = input("   -> Entrez la date (YYYY-MM-DD) : ")
                        break
            
            new_row = row.to_dict()
            new_row['preview_url_itunes'] = info['preview_url']
            new_row['artwork_url_itunes'] = info['artwork_url']
            new_row['Date_Ajout'] = datetime.date.today().strftime("%Y-%m-%d")
            new_row['Date_Sortie'] = final_date
            
            if 'Date' in new_row:
                del new_row['Date']
            
            # Sauvegarde dans le fichier prov
            columns_order = ['Date_Ajout', 'Date_Sortie', 'Titre', 'Artiste', 'Genre', 'Difficulté', 'preview_url_itunes', 'artwork_url_itunes']
            
            # Load existing prov JSON or create new
            if os.path.exists(COMPLETED_FILE) and os.path.getsize(COMPLETED_FILE) > 0:
                df_prov = pd.read_json(COMPLETED_FILE)
            else:
                df_prov = pd.DataFrame(columns=columns_order)
                
            df_new_row = pd.DataFrame([new_row])
            for col in columns_order:
                if col not in df_new_row.columns:
                    df_new_row[col] = ""
            df_new_row = df_new_row[columns_order]
            
            df_prov = pd.concat([df_prov, df_new_row], ignore_index=True)
            df_prov.to_json(COMPLETED_FILE, orient="records", indent=4, force_ascii=False)
            
            df_source = df_source.drop(i)
            df_source.to_json(SOURCE_FILE, orient="records", indent=4, force_ascii=False)
            
            print(f"✅ Ajouté avec date : {final_date}")
        else:
            print("❌ Introuvable sur iTunes (ou erreur). Laissé dans la liste de travail.")
        
        time.sleep(0.5)

    print(f"\nTraitement terminé ! Les éléments restants dans '{COMPLETED_FILE}' sont ceux en échec.")

if __name__ == "__main__":
    main()