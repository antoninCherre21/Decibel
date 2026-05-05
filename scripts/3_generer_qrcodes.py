import qrcode
import os
from PIL import Image, ImageDraw
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from utils import get_mode_arg, get_paths, load_json

# Correspondance nom de couleur (depuis genres.json) → valeur RGB
COLORS_RGB = {
    'bleu':   (66, 135, 245),
    'violet': (155, 89, 182),
    'vert':   (39, 174, 96),
    'orange': (230, 126, 34),
    'rose':   (236, 64, 122),
    'noir':   (45, 52, 54),
}


def creer_logo_custom(size=500, color=(0, 0, 0)):
    """Crée un logo circulaire avec un triangle play."""
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img, 'RGBA')
    center = size // 2
    border_thickness = size // 15
    draw.ellipse([0, 0, size, size], fill=(255, 255, 255, 255))
    margin = border_thickness
    fill_color = color + (255,)
    draw.ellipse([margin, margin, size - margin, size - margin], fill=fill_color)
    triangle_height = size // 2.5
    triangle_width = size // 3
    offset_x = size // 100
    point_haut = (center - triangle_width // 2 + offset_x, center - triangle_height // 2)
    point_bas = (center - triangle_width // 2 + offset_x, center + triangle_height // 2)
    point_pointe = (center + triangle_width // 1.5 + offset_x, center)
    draw.polygon([point_haut, point_bas, point_pointe], fill=(255, 255, 255, 255))
    return img


def main():
    mode = get_mode_arg()
    paths = get_paths(mode)
    os.makedirs(paths["qrcodes"], exist_ok=True)

    # Trouver le dernier ID généré
    max_id_generated = -1
    for filename in os.listdir(paths["qrcodes"]):
        if filename.startswith("qr_") and filename.endswith(".png"):
            try:
                card_id = int(filename.split("_")[1])
                max_id_generated = max(max_id_generated, card_id)
            except (ValueError, IndexError):
                pass

    print(f"Dernier QR code généré : ID {max_id_generated}. Génération à partir de l'ID {max_id_generated + 1}.")

    songs = load_json(paths["db"], default=[])
    if not songs:
        print(f"Base de données vide : {paths['db']}")
        return

    # Mapping genre ID (int) → couleur RGB, construit depuis genres.json
    genre_colors_map = {}  # { genre_id (int) : (R, G, B) }
    genres = load_json(paths["genres"], default=[])
    for g in genres:
        try:
            gid = int(g['id'])  # genres.json stocke les IDs en string → cast int
            color_name = g.get('Couleur', 'noir')
            genre_colors_map[gid] = COLORS_RGB.get(color_name, COLORS_RGB['noir'])
        except (ValueError, KeyError):
            pass

    # Filtrer les nouvelles musiques
    new_songs = [s for s in songs if isinstance(s.get('ID'), (int, float)) and int(s['ID']) > max_id_generated]
    print(f"-> {len(new_songs)} QR Code(s) à générer (sur {len(songs)} total).")

    if not new_songs:
        print("Rien à générer.")
        return

    print("Début de la génération des QR Codes...")

    for i, song in enumerate(new_songs):
        song_id = int(song['ID'])
        try:
            # --- QR Code ---
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=1
            )
            qr.add_data(f"{mode}_{song_id}")
            qr.make(fit=True)

            difficulte = str(song.get('Difficulté', ''))
            if difficulte == 'Difficile':
                # QR rouge pour les chansons difficiles
                c_mask = SolidFillColorMask(front_color=(255, 0, 0), back_color=(255, 255, 255))
                logo_color_rgb = COLORS_RGB['noir']
            else:
                c_mask = SolidFillColorMask(front_color=(0, 0, 0), back_color=(255, 255, 255))
                try:
                    genre_id = int(song.get('Genre', -1))
                    logo_color_rgb = genre_colors_map.get(genre_id, COLORS_RGB['noir'])
                except (ValueError, TypeError):
                    logo_color_rgb = COLORS_RGB['noir']

            qr_img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
                color_mask=c_mask
            ).convert('RGB')

            # --- Logo ---
            qr_width, qr_height = qr_img.size
            logo_size = int(qr_width * 0.25)
            logo_img = creer_logo_custom(size=600, color=logo_color_rgb)
            logo_resized = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            pos_x = (qr_width - logo_size) // 2
            pos_y = (qr_height - logo_size) // 2
            qr_img.paste(logo_resized, (pos_x, pos_y), mask=logo_resized)

            # --- Sauvegarde ---
            titre_safe = "".join(x for x in str(song.get('Titre', f'track_{song_id}')) if x.isalnum() or x in [' ', '-', '_']).strip()[:50]
            filename = f"qr_{song_id}_{titre_safe}.png"
            qr_img.save(os.path.join(paths["qrcodes"], filename))

            if i % 50 == 0:
                print(f"Progression : {i+1}/{len(new_songs)}")

        except Exception as e:
            print(f"Erreur sur {song.get('Titre', song_id)} : {e}")

    print(f"\nTerminé ! Les QR codes sont dans '{paths['qrcodes']}'.")


if __name__ == "__main__":
    main()