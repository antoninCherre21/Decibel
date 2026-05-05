import requests
import os
import shutil
from utils import get_mode_arg, get_paths, load_json, save_json, safe_filename


def search_artwork():
    mode = get_mode_arg()
    paths = get_paths(mode)
    print(f"--- Recherche de Pochette iTunes et Mise à jour ({mode.upper()}) ---")

    songs = load_json(paths["db"], default=[])
    if not songs:
        print(f"Base de données vide : {paths['db']}")
        return

    recherche = input("Rechercher dans votre playlist (Titre ou Artiste) : ").strip().lower()
    matches = [s for s in songs if recherche in str(s.get('Titre', '')).lower() or recherche in str(s.get('Artiste', '')).lower()]

    if not matches:
        print("Aucune musique trouvée dans votre playlist.")
        return

    print("\nMusiques trouvées dans votre playlist :")
    for i, s in enumerate(matches):
        print(f"[{i+1}] {s['Titre']} - {s['Artiste']} (ID: {s.get('ID', '?')})")

    choix = input("\nChoisissez le numéro de la musique à modifier (ou 'q' pour quitter) : ")
    if choix.lower() == 'q':
        return

    try:
        idx = int(choix) - 1
        if not (0 <= idx < len(matches)):
            print("Choix invalide.")
            return
    except ValueError:
        print("Entrée invalide.")
        return

    selected = matches[idx]
    titre = selected['Titre']
    artiste = selected['Artiste']
    song_id = selected.get('ID', 'unknown')
    original_idx = songs.index(selected)

    print(f"\nRecherche de pochettes sur iTunes pour : {titre} - {artiste}...")

    url = "https://itunes.apple.com/search"
    params = {"term": f"{titre} {artiste}", "media": "music", "entity": "song", "limit": 20}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json().get("results", [])
    except requests.RequestException as e:
        print(f"Erreur lors de la requête API : {e}")
        return

    if not results:
        print("Aucun résultat trouvé sur iTunes.")
        return

    temp_dir = os.path.join(paths["base"], "temp_pochettes")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    choices = []
    print("\nRésultats trouvés :")
    for i, item in enumerate(results):
        artwork_url_100 = item.get("artworkUrl100")
        if not artwork_url_100:
            continue
        artwork_url_hq = artwork_url_100.replace("100x100bb.jpg", "600x600bb.jpg")
        try:
            img_resp = requests.get(artwork_url_hq)
            img_resp.raise_for_status()
            filepath = os.path.join(temp_dir, f"temp_{i+1}.jpg")
            with open(filepath, "wb") as f:
                f.write(img_resp.content)
            print(f"[{i+1}] {item.get('trackName')} - {item.get('artistName')} (Album: {item.get('collectionName')})")
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

                local_path = selected.get('local_artwork_path', '')
                if not local_path:
                    t_clean = safe_filename(str(titre))
                    a_clean = safe_filename(str(artiste))
                    local_path = f"../modes/{mode}/assets/pochettes/{song_id}_{t_clean}_{a_clean}.jpg"
                    songs[original_idx]['local_artwork_path'] = local_path

                target_filepath = os.path.join(paths["base"], local_path.replace('../', ''))
                os.makedirs(os.path.dirname(target_filepath), exist_ok=True)
                shutil.copy(temp_filepath, target_filepath)
                print(f"\n[+] Pochette remplacée : {target_filepath}")

                songs[original_idx]['artwork_url_itunes'] = new_url
                save_json(songs, paths["db"])
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
