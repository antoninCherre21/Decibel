import requests
import time
import datetime
import os
from utils import get_mode_arg, get_paths, load_json, save_json


def get_itunes_info(artist, title):
    """Recherche les infos sur iTunes API."""
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
                    "artwork_url": result.get("artworkUrl100", "").replace("100x100bb", "600x600bb"),
                    "release_date": release_date
                }
    except Exception as e:
        print(f"Erreur connexion pour {title}: {e}")
    return None


def main():
    mode = get_mode_arg()
    paths = get_paths(mode)
    SOURCE_FILE = paths["to_add"]
    COMPLETED_FILE = paths["prov"]

    if not os.path.exists(SOURCE_FILE):
        print(f"Erreur: Le fichier source '{SOURCE_FILE}' est introuvable.")
        return

    source_list = load_json(SOURCE_FILE, default=[])
    if not source_list:
        print(f"Le fichier {SOURCE_FILE} est vide. Rien à traiter.")
        return

    print(f"Chargement de {len(source_list)} titres à traiter depuis {SOURCE_FILE}...")
    time.sleep(1)

    COLUMNS_ORDER = ['Date_Ajout', 'Date_Sortie', 'Titre', 'Artiste', 'Genre', 'Difficulté', 'preview_url_itunes', 'artwork_url_itunes']
    remaining = []

    for item in source_list:
        artiste = item.get('Artiste', '')
        titre = item.get('Titre', '')
        date_raw = str(item.get('Date', '')).strip()
        year_source = date_raw[:4]

        print(f"\n--- Traitement : {titre} - {artiste} (Date source: {date_raw}) ---")

        info = get_itunes_info(artiste, titre)

        if info:
            date_itunes_full = info['release_date']
            year_itunes = date_itunes_full[:4]
            final_date = date_itunes_full

            if year_itunes != year_source and year_source:
                print(f"⚠️  CONFLIT D'ANNÉE détecté !")
                print(f"   1. Source (Votre date) : {date_raw}")
                print(f"   2. iTunes (Meilleur résultat) : {date_itunes_full}")
                print(f"   3. Saisir manuellement")
                while True:
                    choix = input("   -> Quel choix (1/2/3) ? ")
                    if choix == '1': final_date = date_raw; break
                    elif choix == '2': final_date = date_itunes_full; break
                    elif choix == '3': final_date = input("   -> Entrez la date (YYYY-MM-DD) : "); break

            elif date_itunes_full.endswith("-01"):
                print(f"⚠️  DATE PAR DÉFAUT SUSPECTE (Jour 01) détectée !")
                print(f"   1. Garder source ({date_raw})")
                print(f"   2. Garder iTunes ({date_itunes_full})")
                print(f"   3. Saisir manuellement")
                while True:
                    choix = input("   -> Quel choix (1/2/3) ? ")
                    if choix == '1': final_date = date_raw; break
                    elif choix == '2': final_date = date_itunes_full; break
                    elif choix == '3': final_date = input("   -> Entrez la date (YYYY-MM-DD) : "); break

            new_row = {col: item.get(col, "") for col in COLUMNS_ORDER}
            new_row['preview_url_itunes'] = info['preview_url']
            new_row['artwork_url_itunes'] = info['artwork_url']
            new_row['Date_Ajout'] = datetime.date.today().strftime("%Y-%m-%d")
            new_row['Date_Sortie'] = final_date

            prov_list = load_json(COMPLETED_FILE, default=[])
            prov_list.append(new_row)
            save_json(prov_list, COMPLETED_FILE)

            print(f"✅ Ajouté avec date : {final_date}")
        else:
            print(f"❌ Introuvable sur iTunes (ou erreur). Laissé dans la liste de travail.")
            remaining.append(item)

        time.sleep(0.5)

    save_json(remaining, SOURCE_FILE)
    print(f"\nTraitement terminé ! {len(source_list) - len(remaining)} musiques traitées.")
    if remaining:
        print(f"Il reste {len(remaining)} musique(s) en échec dans {SOURCE_FILE}.")


if __name__ == "__main__":
    main()