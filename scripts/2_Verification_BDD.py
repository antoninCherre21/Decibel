import pandas as pd
import os
import sys
import argparse
from collections import Counter

def load_genre_mapping(genres_path):
    mapping = {}
    if not os.path.exists(genres_path):
        return mapping
    
    try:
        df_genres = pd.read_json(genres_path)
        for _, row in df_genres.iterrows():
            genre_id = row['id']
            if pd.notna(row.get('Famille de Genre')):
                mapping[row['Famille de Genre'].strip()] = genre_id
            if pd.notna(row.get('Sous-genres')):
                subs = str(row['Sous-genres']).split(',')
                for sub in subs:
                    mapping[sub.strip()] = genre_id
    except Exception as e:
        pass

    manual_map = {
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
        "Comédie Musicale": 1, "Rap Celtique": 3, "Afro-House": 5,
        "Hip Hop/Country": 3, "Hip Hop/Rock": 3, "Soul/Pop": 5,
        "A cappella": 1, "Rap Parodie": 3,
        "Yé-yé": 1, "Disco/Funk": 5, "Zouk": 5
    }
    for k, v in manual_map.items():
        if k not in mapping:
            mapping[k] = v
            
    return mapping

def verify_and_correct(mode):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODE_DIR = os.path.join(BASE_DIR, "modes", mode)
    PLAYLIST_PATH = os.path.join(MODE_DIR, "db.json")
    GENRES_PATH = os.path.join(MODE_DIR, "genres.json")
    ERRORS_PATH = os.path.join(MODE_DIR, "erreurs.txt")
    IGNORED_ERRORS_PATH = os.path.join(MODE_DIR, "erreurs_ignorees.txt")
    STATS_PATH = os.path.join(MODE_DIR, "stats.json")

    errors = []
    if not os.path.exists(PLAYLIST_PATH):
        print(f"Erreur: {PLAYLIST_PATH} introuvable.")
        return []

    try:
        df = pd.read_json(PLAYLIST_PATH)
    except Exception as e:
        print(f"Erreur lors de la lecture de la playlist: {e}")
        return []
    
    if df.empty:
        return []

    genre_map = load_genre_mapping(GENRES_PATH)
    
    df['YearMonthDay'] = df['Date_Sortie'].apply(lambda x: str(x)[:10] if pd.notna(x) else "Unknown")
    date_counts = Counter(df['YearMonthDay'])
    duplicates_date = [date for date, count in date_counts.items() if count > 1 and date != "Unknown"]
    
    if duplicates_date:
        for date in duplicates_date:
            rows = df[df['YearMonthDay'] == date]
            items = [f"{row['Titre']} - {row['Artiste']}" for _, row in rows.iterrows()]
            items_str = ", ".join(items[:5]) + ("..." if len(items) > 5 else "")
            errors.append(f"Erreur Doublon Date ({date}): {items_str}")

    if 'ID' in df.columns:
        id_counts = Counter(df['ID'])
        duplicates_id = [id_val for id_val, count in id_counts.items() if count > 1]
        if duplicates_id:
            for id_val in duplicates_id:
                rows = df[df['ID'] == id_val]
                items = [f"{row['Titre']} - {row['Artiste']}" for _, row in rows.iterrows()]
                items_str = ", ".join(items[:3]) + ("..." if len(items) > 3 else "")
                errors.append(f"Erreur Doublon ID ({id_val}): {items_str}")

    title_counts = Counter(df['Titre'])
    duplicates_title = [title for title, count in title_counts.items() if count > 1]
    if duplicates_title:
        for title in duplicates_title:
            artists = df[df['Titre'] == title]['Artiste'].tolist()
            artists_str = " et ".join(artists)
            errors.append(f"Erreur Doublon Titre: {title} (par {artists_str})")

    artist_counts = Counter(df['Artiste'])
    limits_artist = [artist for artist, count in artist_counts.items() if count > 5]
    if limits_artist:
        for artist in limits_artist:
            errors.append(f"Erreur Limite Artiste (>5): {artist} ({artist_counts[artist]} titres)")

    if 'artwork_url_itunes' in df.columns:
        artwork_counts = Counter(df['artwork_url_itunes'])
        duplicates_artwork = [url for url, count in artwork_counts.items() if count > 1 and pd.notna(url) and url != ""]
        if duplicates_artwork:
            for url in duplicates_artwork:
                rows = df[df['artwork_url_itunes'] == url]
                items = [f"{row['Titre']} - {row['Artiste']}" for _, row in rows.iterrows()]
                items_str = ", ".join(items[:3]) + ("..." if len(items) > 3 else "")
                errors.append(f"Erreur Doublon Artwork URL iTunes: {items_str} ({url})")

    if 'preview_url_itunes' in df.columns:
        preview_counts = Counter(df['preview_url_itunes'])
        duplicates_preview = [url for url, count in preview_counts.items() if count > 1 and pd.notna(url) and url != ""]
        if duplicates_preview:
            for url in duplicates_preview:
                rows = df[df['preview_url_itunes'] == url]
                items = [f"{row['Titre']} - {row['Artiste']}" for _, row in rows.iterrows()]
                items_str = ", ".join(items[:3]) + ("..." if len(items) > 3 else "")
                errors.append(f"Erreur Doublon Preview URL iTunes: {items_str} ({url})")

    def map_genre(genre):
        if pd.isna(genre): return genre
        s_genre = str(genre).strip()
        if s_genre.isdigit(): return int(s_genre)
        if s_genre in genre_map: return genre_map[s_genre]
        for k, v in genre_map.items():
            if k.lower() == s_genre.lower(): return v
        errors.append(f"Erreur Genre Inconnu: {s_genre}")
        return s_genre

    df['Genre_ID'] = df['Genre'].apply(map_genre)
    df['Genre'] = df['Genre_ID']
    
    ignored_errors = set()
    if os.path.exists(IGNORED_ERRORS_PATH):
        with open(IGNORED_ERRORS_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line: ignored_errors.add(line)

    final_errors = [err for err in errors if err not in ignored_errors]

    with open(ERRORS_PATH, 'w', encoding='utf-8') as f:
        f.write("--- RAPPORT D'ERREURS ---\n")
        f.write("Si une ligne est marquée comme erreur mais n'en est pas une, copiez-collez cette ligne exacte dans le fichier 'erreurs_ignorees.txt' pour la masquer.\n")
        f.write("-" * 50 + "\n\n")
        if not final_errors:
            f.write("Aucune erreur détectée (ou toutes les erreurs sont ignorées).\n")
        else:
            for err in final_errors:
                f.write(err + "\n")
                
    print(f"Erreurs sauvegardées dans {ERRORS_PATH}")
    if ignored_errors:
        masquees = len(errors) - len(final_errors)
        if masquees > 0:
            print(f"({masquees} erreurs masquées car présentes dans erreurs_ignorees.txt)")

    stats = []
    df['Year'] = df['Date_Sortie'].apply(lambda x: str(x)[:4] if pd.notna(x) else "Unknown")
    year_counts = df['Year'].value_counts().sort_index()
    for year, count in year_counts.items():
        stats.append({'Type': 'Année', 'Valeur': year, 'Nombre': count})

    def get_decade(year):
        if year == "Unknown" or not year.isdigit(): return "Unknown"
        return str(int(year) // 10 * 10) + "s"
    
    df['Decade'] = df['Year'].apply(get_decade)
    decade_counts = df['Decade'].value_counts().sort_index()
    for dec, count in decade_counts.items():
        stats.append({'Type': 'Décennie', 'Valeur': dec, 'Nombre': count})

    genre_counts = df['Genre'].value_counts()
    for g, count in genre_counts.items():
        stats.append({'Type': 'Genre ID', 'Valeur': g, 'Nombre': count})

    if 'Difficulté' in df.columns:
        diff_counts = df['Difficulté'].value_counts()
        for d, count in diff_counts.items():
            stats.append({'Type': 'Difficulté', 'Valeur': d, 'Nombre': count})

    df_stats = pd.DataFrame(stats)
    df_stats.to_json(STATS_PATH, orient="records", indent=4, force_ascii=False)
    print(f"Statistiques sauvegardées dans {STATS_PATH}")
    
    df_final = df.drop(columns=['YearMonthDay', 'Genre_ID', 'Year', 'Decade'])
    df_final.to_json(PLAYLIST_PATH, orient="records", indent=4, force_ascii=False)
    print(f"Fichier {PLAYLIST_PATH} mis à jour avec les IDs de genre.")
    
    return final_errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="music")
    args = parser.add_argument() if False else parser.parse_args()
    
    final_errors = verify_and_correct(args.mode)
    if final_errors:
        print("\n❌ Vérification échouée : des erreurs ont été trouvées (voir erreurs.txt).")
        sys.exit(1)
    else:
        print("\n✅ Vérification réussie : aucune erreur.")
        sys.exit(0)
