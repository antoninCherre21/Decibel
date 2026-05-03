import pandas as pd
import requests
import time
import time
import os
import datetime

# Configuration des fichiers
SOURCE_FILE = "./musiques_a_ajouter.csv"
COMPLETED_FILE = "./scripts/decibel_playlist_prov.csv"

def get_itunes_info(artist, title):
    """Recherche les infos sur iTunes API"""
    search_url = "https://itunes.apple.com/search"
    # Nettoyage basique pour améliorer la recherche
    term = f"{artist} {title}".replace(" ft.", "").replace(" feat.", "")
    params = {"term": term, "entity": "song", "limit": 1}
    
    try:
        response = requests.get(search_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["resultCount"] > 0:
                result = data["results"][0]
                # On récupère la date complète (YYYY-MM-DD)
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
    if not os.path.exists(SOURCE_FILE):
        print(f"Erreur: Le fichier source '{SOURCE_FILE}' est introuvable.")
        return

    # Chargement du fichier source
    df_source = pd.read_csv(SOURCE_FILE)
    print(f"Chargement de {len(df_source)} titres à traiter depuis {SOURCE_FILE}...")

    # Sleep for user convenience
    time.sleep(1)

    # On travaille sur une liste d'index pour pouvoir modifier le dataframe source sans casser la boucle
    indices = list(df_source.index)

    for i in indices:
        # Vérification si la ligne existe toujours (au cas où)
        if i not in df_source.index:
            continue
            
        row = df_source.loc[i]
        artiste = row['Artiste']
        titre = row['Titre']
        # Gestion propre de la date CSV (peut être int ou float ou str)
        # On nettoie pour n'avoir que l'année en string pour la comparaison
        date_csv_raw = str(row['Date']).replace('.0', '').strip()
        # Si la date CSV est juste une année (ex: 1984), on l'utilise pour comparer
        year_csv = date_csv_raw[:4]
        
        print(f"\n--- Traitement : {titre} - {artiste} (CSV: {date_csv_raw}) ---")
        
        info = get_itunes_info(artiste, titre)
        
        if info:
            date_itunes_full = info['release_date'] # YYYY-MM-DD
            year_itunes = date_itunes_full[:4]
            
            final_date = date_itunes_full
            
            # 1. Vérification de l'année
            # Si l'année CSV diffère de l'année iTunes
            if year_itunes != year_csv:
                print(f"⚠️  CONFLIT D'ANNÉE détecté !")
                print(f"   1. CSV (Votre date) : {date_csv_raw}")
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
            else:
                # Si les années correspondent, on vérifie si le jour est le 1er du mois (souvent une date par défaut)
                if date_itunes_full.endswith("-01"):
                    print(f"⚠️  DATE PAR DÉFAUT SUSPECTE (Jour 01) détectée !")
                    print(f"   1. Garder CSV ({date_csv_raw})")
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
                else:
                    final_date = date_itunes_full
            
            # 2. Préparation de la ligne complète
            new_row = row.to_dict()
            new_row['preview_url_itunes'] = info['preview_url']
            new_row['artwork_url_itunes'] = info['artwork_url']
            
            # Mise à jour des dates
            new_row['Date_Ajout'] = datetime.date.today().strftime("%Y-%m-%d")
            new_row['Date_Sortie'] = final_date
            
            # Suppression de l'ancienne colonne Date si elle existe dans le row source
            if 'Date' in new_row:
                del new_row['Date']
            
            # 3. Sauvegarde dans le fichier complet (Append mode)
            # On force l'ordre des colonnes pour correspondre au fichier de destination
            # Ordre attendu : Date_Ajout, Date_Sortie, Titre, Artiste, Genre, Difficulté, preview_url_itunes, artwork_url_itunes
            columns_order = ['Date_Ajout', 'Date_Sortie', 'Titre', 'Artiste', 'Genre', 'Difficulté', 'preview_url_itunes', 'artwork_url_itunes']
            
            df_complete_row = pd.DataFrame([new_row])
            
            # Réorganisation des colonnes (et ajout des manquantes si besoin)
            for col in columns_order:
                if col not in df_complete_row.columns:
                    df_complete_row[col] = ""
            
            df_complete_row = df_complete_row[columns_order]

            # On écrit l'en-tête seulement si le fichier n'existe pas
            header_mode = not os.path.exists(COMPLETED_FILE)
            df_complete_row.to_csv(COMPLETED_FILE, mode='a', header=header_mode, index=False)
            
            # 4. Suppression de la ligne dans le fichier source et sauvegarde
            df_source = df_source.drop(i)
            df_source.to_csv(SOURCE_FILE, index=False)
            
            print(f"✅ Ajouté avec date : {final_date}")
            
        else:
            print("❌ Introuvable sur iTunes (ou erreur). Laissé dans la liste de travail.")
        
        # Pause pour respecter l'API Apple
        time.sleep(0.5)

    print(f"\nTraitement terminé ! Les éléments restants dans '{SOURCE_FILE}' sont ceux en échec.")

if __name__ == "__main__":
    main()