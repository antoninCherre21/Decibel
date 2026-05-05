import os
import sys
import argparse
from collections import Counter
from utils import get_paths, load_json, save_json


GENRE_MAP = {
    "Pop": 1, "Hip Hop": 3, "Metal": 2, "Electro": 4,
    "Chanson Française": 1, "Variété Française": 1,
    "Indie Folk": 2, "Alternative": 2, "Country": 1,
    "Latin Pop": 5, "Latin": 5, "Eurodance": 1, "New Wave": 1,
    "Punk Rock": 2, "Britpop": 2, "Afrobeats": 5, "Afro-House": 5,
    "Synthpop": 4, "Folk": 1, "Folk Rock": 2, "Nu Metal": 2,
    "Pop Rock": 1, "Pop Urbaine": 3, "Reggaeton": 5, "Salsa": 5,
    "Rap Français": 3, "Rap": 3, "R&B": 3, "Soul": 5, "Funk": 5,
    "Disco": 1, "Jazz": 5, "Gospel": 5, "Blues": 5,
    "Rock": 2, "Hard Rock": 2, "Grunge": 2, "Punk": 2,
    "Rock and Roll": 2, "K-Pop": 1, "Raï": 5, "Dance": 4,
    "Comédie Musicale": 1, "Rap Celtique": 3,
    "Hip Hop/Country": 3, "Hip Hop/Rock": 3, "Soul/Pop": 5,
    "A cappella": 1, "Rap Parodie": 3,
    "Yé-yé": 1, "Disco/Funk": 5, "Zouk": 5
}


def load_genre_mapping(genres_path: str) -> dict:
    """Charge la carte des genres depuis genres.json et la fusionne avec GENRE_MAP."""
    mapping = dict(GENRE_MAP)  # Copie du mapping par défaut
    genres = load_json(genres_path, default=[])
    for g in genres:
        gid = g.get('id')
        if g.get('Famille de Genre'):
            mapping[g['Famille de Genre'].strip()] = gid
        subs = str(g.get('Sous-genres', '')).split(',')
        for sub in subs:
            sub = sub.strip()
            if sub:
                mapping[sub] = gid
    return mapping


def map_genre(genre, genre_map: dict, errors: list) -> int:
    """Convertit un genre textuel en ID numérique."""
    if genre is None or str(genre).strip() == "":
        return genre
    s_genre = str(genre).strip()
    if s_genre.isdigit():
        return int(s_genre)
    # Recherche exacte puis insensible à la casse
    if s_genre in genre_map:
        return genre_map[s_genre]
    for k, v in genre_map.items():
        if k.lower() == s_genre.lower():
            return v
    errors.append(f"Erreur Genre Inconnu: {s_genre}")
    return s_genre


def verify_and_correct(mode: str) -> list:
    paths = get_paths(mode)

    errors = []
    songs = load_json(paths["db"], default=[])
    if not songs:
        print(f"Base de données vide ou absente : {paths['db']}")
        return []

    genre_map = load_genre_mapping(paths["genres"])

    # --- Vérification des doublons de date ---
    date_counts = Counter(str(s.get('Date_Sortie', ''))[:10] for s in songs)
    for date, count in date_counts.items():
        if count > 1 and date and date != "Unknown":
            items = [f"{s['Titre']} - {s['Artiste']}" for s in songs if str(s.get('Date_Sortie', ''))[:10] == date]
            errors.append(f"Erreur Doublon Date ({date}): {', '.join(items[:5])}{'...' if len(items) > 5 else ''}")

    # --- Vérification des doublons d'ID ---
    id_counts = Counter(s.get('ID') for s in songs)
    for id_val, count in id_counts.items():
        if count > 1:
            items = [f"{s['Titre']} - {s['Artiste']}" for s in songs if s.get('ID') == id_val]
            errors.append(f"Erreur Doublon ID ({id_val}): {', '.join(items[:3])}{'...' if len(items) > 3 else ''}")

    # --- Vérification des doublons de titre ---
    title_counts = Counter(s.get('Titre') for s in songs)
    for title, count in title_counts.items():
        if count > 1:
            artists = [s['Artiste'] for s in songs if s.get('Titre') == title]
            errors.append(f"Erreur Doublon Titre: {title} (par {' et '.join(artists)})")

    # --- Limite d'artiste (> 5 titres) ---
    artist_counts = Counter(s.get('Artiste') for s in songs)
    for artist, count in artist_counts.items():
        if count > 5:
            errors.append(f"Erreur Limite Artiste (>5): {artist} ({count} titres)")

    # --- Doublons d'URL artwork ---
    artwork_counts = Counter(s.get('artwork_url_itunes') for s in songs if s.get('artwork_url_itunes'))
    for url, count in artwork_counts.items():
        if count > 1:
            items = [f"{s['Titre']} - {s['Artiste']}" for s in songs if s.get('artwork_url_itunes') == url]
            errors.append(f"Erreur Doublon Artwork URL iTunes: {', '.join(items[:3])}{'...' if len(items) > 3 else ''}")

    # --- Doublons d'URL preview ---
    preview_counts = Counter(s.get('preview_url_itunes') for s in songs if s.get('preview_url_itunes'))
    for url, count in preview_counts.items():
        if count > 1:
            items = [f"{s['Titre']} - {s['Artiste']}" for s in songs if s.get('preview_url_itunes') == url]
            errors.append(f"Erreur Doublon Preview URL iTunes: {', '.join(items[:3])}{'...' if len(items) > 3 else ''}")

    # --- Normalisation des genres ---
    for song in songs:
        song['Genre'] = map_genre(song.get('Genre'), genre_map, errors)

    # --- Filtrage des erreurs ignorées ---
    ignored_errors = set()
    if os.path.exists(paths["ignored_errors"]):
        with open(paths["ignored_errors"], 'r', encoding='utf-8') as f:
            ignored_errors = {line.strip() for line in f if line.strip()}

    final_errors = [e for e in errors if e not in ignored_errors]

    # --- Écriture du rapport d'erreurs ---
    with open(paths["errors"], 'w', encoding='utf-8') as f:
        f.write("--- RAPPORT D'ERREURS ---\n")
        f.write("Pour ignorer une erreur, copiez-collez la ligne exacte dans 'erreurs_ignorees.txt'.\n")
        f.write("-" * 50 + "\n\n")
        if not final_errors:
            f.write("Aucune erreur détectée (ou toutes les erreurs sont ignorées).\n")
        else:
            f.write("\n".join(final_errors) + "\n")

    print(f"Rapport d'erreurs : {paths['errors']}")
    masked = len(errors) - len(final_errors)
    if masked > 0:
        print(f"({masked} erreur(s) masquée(s) via erreurs_ignorees.txt)")

    # --- Calcul des statistiques ---
    stats = []
    year_counts = Counter(str(s.get('Date_Sortie', ''))[:4] for s in songs)
    for year, count in sorted(year_counts.items()):
        stats.append({'Type': 'Année', 'Valeur': year, 'Nombre': count})

    decade_counts = Counter(
        (str(int(str(s.get('Date_Sortie', ''))[:4]) // 10 * 10) + "s"
         if str(s.get('Date_Sortie', ''))[:4].isdigit() else "Unknown")
        for s in songs
    )
    for dec, count in sorted(decade_counts.items()):
        stats.append({'Type': 'Décennie', 'Valeur': dec, 'Nombre': count})

    genre_counts = Counter(s.get('Genre') for s in songs)
    for g, count in genre_counts.items():
        stats.append({'Type': 'Genre ID', 'Valeur': g, 'Nombre': count})

    diff_counts = Counter(s.get('Difficulté') for s in songs if s.get('Difficulté'))
    for d, count in diff_counts.items():
        stats.append({'Type': 'Difficulté', 'Valeur': d, 'Nombre': count})

    save_json(stats, paths["stats"])
    print(f"Statistiques sauvegardées : {paths['stats']}")

    # --- Sauvegarde de la DB mise à jour (genres normalisés) ---
    save_json(songs, paths["db"])
    print(f"Fichier {paths['db']} mis à jour avec les IDs de genre.")

    return final_errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="music")
    args = parser.parse_args()

    final_errors = verify_and_correct(args.mode)
    if final_errors:
        print("\n❌ Vérification échouée : des erreurs ont été trouvées (voir erreurs.txt).")
        sys.exit(1)
    else:
        print("\n✅ Vérification réussie : aucune erreur.")
        sys.exit(0)
