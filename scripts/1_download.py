import requests
import os
import time
from utils import get_mode_arg, get_paths, load_json, save_json, safe_filename


def download_file(url, filepath):
    """Télécharge un fichier depuis une URL. Retourne True si succès."""
    if not url or not str(url).startswith("http"):
        return False
    if os.path.exists(filepath):
        return True
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            time.sleep(0.1)
            return True
        else:
            print(f"Erreur HTTP {response.status_code} pour {url}")
    except Exception as e:
        print(f"Erreur lors du téléchargement de {url}: {e}")
    return False


def get_max_id(db: list) -> int:
    """Retourne l'ID maximum dans la base de données."""
    if not db:
        return 0
    try:
        return max(int(song.get('ID', 0)) for song in db)
    except (ValueError, TypeError):
        return 0


def main():
    mode = get_mode_arg()
    paths = get_paths(mode)

    os.makedirs(paths["audio"], exist_ok=True)
    os.makedirs(paths["pochettes"], exist_ok=True)

    queue = load_json(paths["prov"], default=[])
    if not queue:
        print(f"Le fichier {paths['prov']} est vide ou absent. Rien à télécharger.")
        return

    db = load_json(paths["db"], default=[])
    current_max_id = get_max_id(db)

    COLUMNS_ORDER = ['ID', 'Date_Ajout', 'Date_Sortie', 'Titre', 'Artiste', 'Genre',
                     'Difficulté', 'preview_url_itunes', 'artwork_url_itunes',
                     'local_preview_path', 'local_artwork_path']

    remaining = []

    for item in queue:
        titre = safe_filename(item.get('Titre', 'titre_inconnu'))
        artiste = safe_filename(item.get('Artiste', 'artiste_inconnu'))
        audio_url = item.get('preview_url_itunes', '')
        artwork_url = item.get('artwork_url_itunes', '')

        new_id = current_max_id + 1
        local_audio_path = ""
        local_artwork_path = ""

        # --- Téléchargement audio ---
        if audio_url and str(audio_url).startswith("http"):
            audio_filename = f"{new_id}_{titre}_{artiste}.m4a"
            audio_path = os.path.join(paths["audio"], audio_filename)
            if download_file(audio_url, audio_path):
                local_audio_path = f"../modes/{mode}/assets/fichiers_audio/{audio_filename}"
            else:
                print(f"⚠️ Échec téléchargement audio pour {item.get('Titre')}.")
        else:
            print(f"⚠️ URL audio invalide ou manquante pour {item.get('Titre')}.")

        # --- Téléchargement pochette ---
        if artwork_url and str(artwork_url).startswith("http"):
            artwork_filename = f"{new_id}_{titre}_{artiste}.jpg"
            artwork_path = os.path.join(paths["pochettes"], artwork_filename)
            if download_file(artwork_url, artwork_path):
                local_artwork_path = f"../modes/{mode}/assets/pochettes/{artwork_filename}"
            else:
                print(f"⚠️ Échec téléchargement pochette pour {item.get('Titre')}.")
        else:
            print(f"⚠️ URL pochette invalide ou manquante pour {item.get('Titre')}.")

        # --- Ajout à la DB si les deux fichiers sont OK ---
        if local_audio_path and local_artwork_path:
            new_entry = {col: item.get(col, "") for col in COLUMNS_ORDER}
            new_entry['ID'] = new_id
            new_entry['local_preview_path'] = local_audio_path
            new_entry['local_artwork_path'] = local_artwork_path

            db.append(new_entry)
            save_json(db, paths["db"])

            current_max_id = new_id
            print(f"✅ Ajouté à la base finale (ID {new_id}) : {item.get('Titre')}")
        else:
            print(f"❌ Échec pour : {item.get('Titre')}. Laissé en attente.")
            remaining.append(item)

    save_json(remaining, paths["prov"])
    downloaded = len(queue) - len(remaining)
    print(f"\nTéléchargements terminés. {downloaded} musique(s) basculée(s) vers db.json.")
    if remaining:
        print(f"Il reste {len(remaining)} musique(s) en échec dans le fichier provisoire.")


if __name__ == "__main__":
    main()
