import pandas as pd
import os
from collections import Counter

# Définition des chemins relatifs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYLIST_PATH = os.path.join(BASE_DIR, "../decibel_playlist.csv")
GENRES_PATH = os.path.join(BASE_DIR, "../tri_genres_musiques.csv")
ERRORS_PATH = os.path.join(BASE_DIR, "../erreurs.txt")
IGNORED_ERRORS_PATH = os.path.join(BASE_DIR, "../erreurs_ignorees.txt")
STATS_PATH = os.path.join(BASE_DIR, "../statistiques.csv")

def load_genre_mapping():
    mapping = {}
    if not os.path.exists(GENRES_PATH):
        print(f"Erreur: {GENRES_PATH} introuvable.")
        return mapping
    
    try:
        df_genres = pd.read_csv(GENRES_PATH)
        for _, row in df_genres.iterrows():
            genre_id = row['id']
            # Map the family name
            if pd.notna(row['Famille de Genre']):
                mapping[row['Famille de Genre'].strip()] = genre_id
            # Map sub-genres
            if pd.notna(row['Sous-genres']):
                subs = row['Sous-genres'].split(',')
                for sub in subs:
                    mapping[sub.strip()] = genre_id
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier de genres: {e}")

    # Ajouts manuels pour correspondre aux données actuelles si absents du fichier de mapping
    # Ces mappings sont déduits logiquement des familles
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

def verify_and_correct():
    errors = []
    if not os.path.exists(PLAYLIST_PATH):
        print(f"Erreur: {PLAYLIST_PATH} introuvable.")
        return

    try:
        df = pd.read_csv(PLAYLIST_PATH)
    except Exception as e:
        print(f"Erreur lors de la lecture de la playlist: {e}")
        return

    genre_map = load_genre_mapping()
    
    # 1. Check Date Duplicates (YYYY-MM-DD)
    # On extrait YYYY-MM-DD
    df['YearMonthDay'] = df['Date_Sortie'].apply(lambda x: str(x)[:10] if pd.notna(x) else "Unknown")
    
    # On compte les occurrences de chaque YearMonthDay
    date_counts = Counter(df['YearMonthDay'])
    duplicates_date = [date for date, count in date_counts.items() if count > 1 and date != "Unknown"]
    
    if duplicates_date:
        for date in duplicates_date:
            rows = df[df['YearMonthDay'] == date]
            items = [f"{row['Titre']} - {row['Artiste']}" for _, row in rows.iterrows()]
            # On limite l'affichage à 5 titres pour ne pas surcharger
            items_str = ", ".join(items[:5]) + ("..." if len(items) > 5 else "")
            errors.append(f"Erreur Doublon Date ({date}): {items_str}")

    # 1b. Check ID Duplicates
    if 'ID' in df.columns:
        id_counts = Counter(df['ID'])
        duplicates_id = [id_val for id_val, count in id_counts.items() if count > 1]
        if duplicates_id:
            for id_val in duplicates_id:
                rows = df[df['ID'] == id_val]
                items = [f"{row['Titre']} - {row['Artiste']}" for _, row in rows.iterrows()]
                items_str = ", ".join(items[:3]) + ("..." if len(items) > 3 else "")
                errors.append(f"Erreur Doublon ID ({id_val}): {items_str}")

    # 2. Check Title Duplicates
    title_counts = Counter(df['Titre'])
    duplicates_title = [title for title, count in title_counts.items() if count > 1]
    if duplicates_title:
        for title in duplicates_title:
            artists = df[df['Titre'] == title]['Artiste'].tolist()
            artists_str = " et ".join(artists)
            errors.append(f"Erreur Doublon Titre: {title} (par {artists_str})")

    # 3. Check Artist Limits (>5)
    artist_counts = Counter(df['Artiste'])
    limits_artist = [artist for artist, count in artist_counts.items() if count > 5]
    if limits_artist:
        for artist in limits_artist:
            errors.append(f"Erreur Limite Artiste (>5): {artist} ({artist_counts[artist]} titres)")

    # 3b. Check Duplicate URLs (Artwork & Preview)
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

    # 4. Genre Verification and Correction
    def map_genre(genre):
        if pd.isna(genre):
            return genre
        s_genre = str(genre).strip()
        
        # Si c'est déjà un chiffre, on le garde (en int)
        if s_genre.isdigit():
            return int(s_genre)
        
        # Essai correspondance exacte
        if s_genre in genre_map:
            return genre_map[s_genre]
        
        # Essai insensible à la casse
        for k, v in genre_map.items():
            if k.lower() == s_genre.lower():
                return v
        
        # Si non trouvé, on signale l'erreur et on garde l'original
        errors.append(f"Erreur Genre Inconnu: {s_genre}")
        return s_genre

    # On applique le mapping
    df['Genre_ID'] = df['Genre'].apply(map_genre)
    
    # On met à jour la colonne Genre avec les IDs
    df['Genre'] = df['Genre_ID']
    
    # Lecture des erreurs ignorées
    ignored_errors = set()
    if os.path.exists(IGNORED_ERRORS_PATH):
        with open(IGNORED_ERRORS_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    ignored_errors.add(line)

    # Filtrage des erreurs
    final_errors = [err for err in errors if err not in ignored_errors]

    # Sauvegarde des erreurs
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

    # 5. Statistics
    stats = []
    
    # Stats par Année
    df['Year'] = df['Date_Sortie'].apply(lambda x: str(x)[:4] if pd.notna(x) else "Unknown")
    year_counts = df['Year'].value_counts().sort_index()
    for year, count in year_counts.items():
        stats.append({'Type': 'Année', 'Valeur': year, 'Nombre': count})

    # Stats par Décennie
    def get_decade(year):
        if year == "Unknown" or not year.isdigit(): return "Unknown"
        return str(int(year) // 10 * 10) + "s"
    
    df['Decade'] = df['Year'].apply(get_decade)
    decade_counts = df['Decade'].value_counts().sort_index()
    for dec, count in decade_counts.items():
        stats.append({'Type': 'Décennie', 'Valeur': dec, 'Nombre': count})

    # Stats par Genre ID
    genre_counts = df['Genre'].value_counts()
    for g, count in genre_counts.items():
        stats.append({'Type': 'Genre ID', 'Valeur': g, 'Nombre': count})

    # Stats par Difficulté
    if 'Difficulté' in df.columns:
        diff_counts = df['Difficulté'].value_counts()
        for d, count in diff_counts.items():
            stats.append({'Type': 'Difficulté', 'Valeur': d, 'Nombre': count})

    # Sauvegarde des Statistiques
    df_stats = pd.DataFrame(stats)
    df_stats.to_csv(STATS_PATH, index=False)
    print(f"Statistiques sauvegardées dans {STATS_PATH}")
    
    # Sauvegarde du fichier corrigé (avec les IDs de genre)
    # On nettoie les colonnes temporaires
    df_final = df.drop(columns=['YearMonthDay', 'Genre_ID', 'Year', 'Decade'])
    df_final.to_csv(PLAYLIST_PATH, index=False)
    print(f"Fichier {PLAYLIST_PATH} mis à jour avec les IDs de genre.")
    
    return final_errors

if __name__ == "__main__":
    import sys
    final_errors = verify_and_correct()
    # Si le tableau n'est pas vide (erreurs trouvées), on sort avec un code d'erreur 1
    if final_errors:
        print("\n❌ Vérification échouée : des erreurs ont été trouvées (voir erreurs.txt).")
        sys.exit(1)
    else:
        print("\n✅ Vérification réussie : aucune erreur.")
        sys.exit(0)
