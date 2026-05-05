import os
from utils import get_mode_arg, get_paths, load_json, save_json, safe_filename


def main():
    mode = get_mode_arg()
    paths = get_paths(mode)

    songs = load_json(paths["db"], default=[])
    if not songs:
        print(f"Erreur: {paths['db']} introuvable ou vide.")
        return

    try:
        id_to_delete = int(input("Entrez l'ID de l'élément à supprimer : "))
    except ValueError:
        print("Veuillez entrer un nombre valide.")
        return

    target = next((s for s in songs if int(s.get('ID', -1)) == id_to_delete), None)
    if not target:
        print(f"L'ID {id_to_delete} n'existe pas dans la base de données.")
        return

    print(f"\nVous allez supprimer : {target.get('Titre')} - {target.get('Artiste')}")
    confirm = input("Êtes-vous sûr ? Cette action est irréversible (o/n) : ")
    if confirm.lower() != 'o':
        print("Annulation.")
        return

    print(f"\nSuppression des fichiers pour l'ID {id_to_delete}...")
    base = paths["base"]

    for field in ('local_preview_path', 'local_artwork_path'):
        rel = str(target.get(field, '')).replace('../', '')
        if rel:
            abs_path = os.path.join(base, rel)
            if os.path.exists(abs_path):
                os.remove(abs_path)
                print(f" - Supprimé : {os.path.basename(abs_path)}")

    # Retirer l'entrée
    songs = [s for s in songs if int(s.get('ID', -1)) != id_to_delete]

    # Décaler les IDs suivants et renommer les fichiers
    print("Décalage des IDs suivants et renommage des fichiers...")
    count_shifted = 0

    for song in songs:
        current_id = int(song.get('ID', 0))
        if current_id <= id_to_delete:
            continue

        new_id = current_id - 1

        for field, asset_dir in [('local_preview_path', paths["audio"]), ('local_artwork_path', paths["pochettes"])]:
            old_rel = str(song.get(field, '')).replace('../', '')
            if not old_rel:
                continue
            old_abs = os.path.join(base, old_rel)
            old_filename = os.path.basename(old_abs)

            if '_' in old_filename:
                new_filename = f"{new_id}_{old_filename.split('_', 1)[1]}"
            else:
                ext = os.path.splitext(old_filename)[1]
                new_filename = f"{new_id}{ext}"

            new_abs = os.path.join(asset_dir, new_filename)
            if os.path.exists(old_abs):
                os.rename(old_abs, new_abs)

            # Mettre à jour le chemin dans l'entrée
            sub_folder = "fichiers_audio" if "audio" in field else "pochettes"
            song[field] = f"../modes/{mode}/assets/{sub_folder}/{new_filename}"

        song['ID'] = new_id
        count_shifted += 1

    save_json(songs, paths["db"])
    print(f"\nTerminé ! {count_shifted} élément(s) décalé(s) pour boucher le trou.")


if __name__ == "__main__":
    main()
