from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
import os
from utils import get_mode_arg, get_paths, load_json

MOIS_FR = {
    1: 'janvier', 2: 'fevrier', 3: 'mars', 4: 'avril', 5: 'mai', 6: 'juin',
    7: 'juillet', 8: 'aout', 9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'decembre'
}

# Zooms spécifiques à certains titres : stockés ici en attendant de migrer vers db.json
ZOOMS_SPECIFIQUES = {
    ("Take on Me", "a-ha"): {"ratio": 1.15},
    ("Stayin' Alive", "Bee Gees"): {"ratio": 1.15, "y_offset": -38},
    ("Like a Rolling Stone", "Bob Dylan"): {"ratio": 1.28, "y_offset": 30},
    ("Harley Davidson", "Brigitte Bardot"): {"ratio": 1.15},
    ("Blue Suede Shoes", "The Rolling Stones"): {"ratio": 1.15},
    ("Est-ce que tu viens pour les vacances ?", "David et Jonathan"): {"ratio": 1.15},
    ("Il jouait du piano debout", "France Gall"): {"ratio": 1.10},
    ("Conmigo", "Kendji Girac"): {"ratio": 1.10},
    ("Andalouse", "Kendji Girac"): {"ratio": 1.10},
    ("U Can't Touch This", "MC Hammer"): {"ratio": 1.05},
    ("Celebration", "Kool & The Gang"): {"ratio": 1.10},
    ("Nuit sauvage", "Les Avions"): {"ratio": 1.10},
    ("Walk on the Wild Side", "Lou Reed"): {"ratio": 1.10},
    ("Wonderwall", "Oasis"): {"ratio": 1.07},
    ("Counting Stars", "OneRepublic"): {"ratio": 1.10},
    ("L'École est finie", "Sheila"): {"ratio": 1.10},
    ("Bitter Sweet Symphony", "The Verve"): {"ratio": 1.15},
    ("Je veux", "Zaz"): {"ratio": 1.10},
    ("Autobahn", "Kraftwerk"): {"ratio": 1.10},
    ("Derrière le Brouillard", "Grand Corps Malade & Louane"): {"ratio": 1.15},
    ("Steal My Girl", "One Direction"): {"ratio": 1.08},
}


def main():
    mode = get_mode_arg()
    paths = get_paths(mode)
    base = paths["base"]

    os.makedirs(paths["cartes"], exist_ok=True)

    songs = load_json(paths["db"], default=[])
    if not songs:
        print(f"Base de données vide : {paths['db']}")
        return

    # Trouver le dernier ID généré
    max_id_generated = -1
    for filename in os.listdir(paths["cartes"]):
        if "recto" in filename or "verso" in filename:
            try:
                card_id = int(filename.split("_")[0])
                max_id_generated = max(max_id_generated, card_id)
            except (ValueError, IndexError):
                pass

    print(f"Dernière carte générée : ID {max_id_generated}. Génération à partir de l'ID {max_id_generated + 1}.")
    new_songs = [s for s in songs if isinstance(s.get('ID'), (int, float)) and int(s['ID']) > max_id_generated]
    print(f"-> {len(new_songs)} carte(s) à générer.")

    if not new_songs:
        print("Rien à générer.")
        return

    CARD_SIZE = (945, 945)
    CENTRE_X = CARD_SIZE[0] // 2
    CENTRE_Y = CARD_SIZE[1] // 2

    font_path = os.path.join(base, "fonts", "KeeponTruckin.ttf")
    font_path_title = os.path.join(base, "fonts", "COOPBL.TTF")

    # Chercher l'image recto : modes/<mode>/img/ en priorité, puis fallbacks historiques
    def find_recto(filename):
        candidates = [
            os.path.join(paths["img"], filename),       # ✅ chemin canonique
            os.path.join(base, "webapp", "img", filename),  # ancien emplacement webapp
            os.path.join(base, "img", filename),        # ancien emplacement racine
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return candidates[0]  # retourne le chemin canonique même si absent (fallback blanc)

    recto_img_path = find_recto("recto_carteExtrait.png")
    recto_chance_path = find_recto("recto_carteChance.png")

    for song in new_songs:
        song_id = int(song['ID'])
        titre = str(song.get('Titre', f'track_{song_id}'))
        artiste = str(song.get('Artiste', ''))
        titre_safe = "".join(x for x in titre if x.isalnum() or x in [' ', '-', '_']).strip()[:50]

        # --- RECTO ---
        try:
            recto = Image.open(recto_img_path).convert("RGBA").resize(CARD_SIZE)
        except Exception:
            recto = Image.new("RGBA", CARD_SIZE, (255, 255, 255, 255))

        qr_path = os.path.join(paths["qrcodes"], f"qr_{song_id}_{titre_safe}.png")
        if os.path.exists(qr_path):
            QR_SIZE = 280  # Taille réduite pour économiser de la place / esthétique
            qr_img = Image.open(qr_path).convert("RGBA").resize((QR_SIZE, QR_SIZE))
            recto.paste(qr_img, (CARD_SIZE[0]//2 - QR_SIZE//2, CARD_SIZE[1]//2 - QR_SIZE//2), qr_img)
        recto.save(os.path.join(paths["cartes"], f"{song_id}_recto_{titre_safe}.png"))

        # --- VERSO ---
        # local_artwork_path peut être "./pochettes/fichier.jpg" (relatif au mode)
        # ou "../modes/music/assets/pochettes/fichier.jpg" (ancien format).
        # On extrait le basename et on utilise paths["pochettes"] pour construire
        # le chemin absolu correct : modes/<mode>/assets/pochettes/
        pochette_filename = os.path.basename(str(song.get('local_artwork_path', '')))
        pochette_path = os.path.join(paths["pochettes"], pochette_filename)

        try:
            pochette = Image.open(pochette_path).convert("RGBA")
        except Exception as e:
            print(f"Pochette introuvable pour {titre}, ignorée. ({e})")
            continue

        target_w, target_h = CARD_SIZE
        img_w, img_h = pochette.size
        ratio = max(target_w / img_w, target_h / img_h)
        y_offset = 0

        # Appliquer les zooms spécifiques depuis db.json (champ optionnel) ou la table de fallback
        zoom_override = song.get('zoom')
        if zoom_override:
            ratio *= float(zoom_override)
            y_offset = int(song.get('y_offset', 0))
        else:
            key = (titre, artiste)
            if key in ZOOMS_SPECIFIQUES:
                spec = ZOOMS_SPECIFIQUES[key]
                ratio *= spec.get("ratio", 1.0)
                y_offset = spec.get("y_offset", 0)

        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)
        pochette = pochette.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2 + y_offset
        pochette = pochette.crop((left, top, left + target_w, top + target_h))

        verso = pochette
        draw = ImageDraw.Draw(verso)

        try:
            date_obj = datetime.strptime(str(song.get('Date_Sortie', ''))[:10], '%Y-%m-%d')
            annee_str = str(date_obj.year)
            jour_mois_str = f"{date_obj.day} {MOIS_FR[date_obj.month]}"
        except Exception:
            annee_str = "????"
            jour_mois_str = ""

        try:
            font_annee = ImageFont.truetype(font_path, size=220)
            font_date = ImageFont.truetype(font_path, size=60)
            font_texte = ImageFont.truetype(font_path_title, size=45)
        except IOError:
            font_annee = ImageFont.load_default(size=200)
            font_date = ImageFont.load_default(size=50)
            font_texte = ImageFont.load_default(size=40)

        band_thickness = 15
        y_band_top = CENTRE_Y - 250
        y_band_bottom = CENTRE_Y + 90

        blur_box = (0, y_band_top + band_thickness, CARD_SIZE[0], y_band_bottom)
        region = verso.crop(blur_box)
        region = region.filter(ImageFilter.GaussianBlur(radius=3))
        verso.paste(region, blur_box)

        draw.rectangle([(0, y_band_top), (CARD_SIZE[0], y_band_top + band_thickness)], fill="white")
        draw.rectangle([(0, y_band_bottom), (CARD_SIZE[0], y_band_bottom + band_thickness)], fill="white")

        overlay = Image.new('RGBA', CARD_SIZE, (255, 255, 255, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_overlay.rectangle([(0, y_band_top + band_thickness), (CARD_SIZE[0], y_band_bottom)], fill=(255, 255, 255, 30))

        padding = 15
        try:
            bbox_titre = draw.textbbox((CENTRE_X, 720), titre, font=font_texte, anchor="mm")
            draw_overlay.rectangle((bbox_titre[0]-padding, bbox_titre[1]-padding, bbox_titre[2]+padding, bbox_titre[3]+padding), fill=(255, 255, 255, 200))
            bbox_artiste = draw.textbbox((CENTRE_X, 780), artiste, font=font_texte, anchor="mm")
            draw_overlay.rectangle((bbox_artiste[0]-padding, bbox_artiste[1]-padding, bbox_artiste[2]+padding, bbox_artiste[3]+padding), fill=(255, 255, 255, 200))
        except Exception:
            pass

        verso = Image.alpha_composite(verso, overlay)
        draw = ImageDraw.Draw(verso)

        y_frise = CENTRE_Y - 90
        draw.text((CENTRE_X, y_frise), annee_str, fill="black", font=font_annee, anchor="mm", stroke_width=8, stroke_fill="white")
        draw.text((CENTRE_X, y_frise + 90), jour_mois_str, fill="black", font=font_date, anchor="mt", stroke_width=5, stroke_fill="white")
        draw.text((CENTRE_X, 720), titre, fill="black", font=font_texte, anchor="mm", stroke_width=3, stroke_fill="white")
        draw.text((CENTRE_X, 780), artiste, fill="black", font=font_texte, anchor="mm", stroke_width=3, stroke_fill="white")

        verso.save(os.path.join(paths["cartes"], f"{song_id}_verso_{titre_safe}.png"))
        print(f"Carte {song_id} terminée.")


if __name__ == "__main__":
    main()