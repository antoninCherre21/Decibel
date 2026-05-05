import pandas as pd
import qrcode
import os
import argparse
from PIL import Image, ImageDraw
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask

# ==========================================
# PARTIE 1 : FONCTION DE GÉNÉRATION DU LOGO
# ==========================================
COLORS_RGB = {
    'bleu': (66, 135, 245),
    'violet': (155, 89, 182),
    'vert': (39, 174, 96),
    'orange': (230, 126, 34),
    'rose': (236, 64, 122),
    'noir': (45, 52, 54)
}

def creer_logo_custom(size=500, color=(0, 0, 0)):
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

# ==========================================
# PARTIE 2 : SCRIPT PRINCIPAL
# ==========================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="music", help="Mode de jeu")
    args = parser.add_argument() if False else parser.parse_args()
    
    mode = args.mode
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, "modes", mode, "db.json")
    GENRES_PATH = os.path.join(BASE_DIR, "modes", mode, "genres.json")
    OUTPUT_DIR = os.path.join(BASE_DIR, "modes", mode, "exports", "qrcodes")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    max_id_generated = -1
    for filename in os.listdir(OUTPUT_DIR):
        if filename.startswith("qr_") and filename.endswith(".png"):
            try:
                music_id = int(filename.split("_")[1])
                if music_id > max_id_generated:
                    max_id_generated = music_id
            except (ValueError, IndexError):
                pass

    print(f"Dernier QR code généré : ID {max_id_generated}. Génération à partir de l'ID {max_id_generated + 1}.")

    if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0:
        print(f"ERREUR : Le fichier {DB_PATH} n'a pas été trouvé ou est vide.")
        return

    try:
        df = pd.read_json(DB_PATH)
        print(f"Fichier JSON chargé : {len(df)} lignes trouvées.")
    except Exception as e:
        print(f"Erreur lecture JSON: {e}")
        return

    genre_colors_map = {}
    if os.path.exists(GENRES_PATH):
        try:
            df_genres = pd.read_json(GENRES_PATH)
            for _, row_g in df_genres.iterrows():
                genre_colors_map[row_g['id']] = row_g.get('Couleur', 'noir')
            print("Couleurs des genres chargées.")
        except Exception as e:
            print(f"Erreur chargement genres : {e}")

    df = df[pd.notna(df['ID'])]
    df_filtered = df[df['ID'].astype(int) > max_id_generated]
    print(f"-> {len(df_filtered)} QR Codes à générer (sur {len(df)} total).")
    df = df_filtered

    if df.empty:
        print("Rien à générer.")
        return

    print("Début de la génération des QR Codes...")

    for index, row in df.iterrows():
        if 'ID' in row and pd.notna(row['ID']):
            music_id = int(row['ID'])
            try:
                qr = qrcode.QRCode(
                    version=None, 
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=10,
                    border=1
                )
                qr_data = f"{mode}_{music_id}"
                qr.add_data(qr_data)
                qr.make(fit=True)
                
                difficulte = str(row.get('Difficulté'))
                if difficulte == 'Difficile':
                    c_mask = SolidFillColorMask(front_color=(255, 0, 0), back_color=(255, 255, 255))
                    logo_color_rgb = (0, 0, 0)
                else:
                    c_mask = SolidFillColorMask(front_color=(0, 0, 0), back_color=(255, 255, 255))
                    try:
                        genre_id = int(row.get('Genre', -1))
                        color_name = genre_colors_map.get(genre_id, 'noir')
                        logo_color_rgb = COLORS_RGB.get(color_name, (0, 0, 0))
                    except:
                        logo_color_rgb = (0, 0, 0)

                qr_img = qr.make_image(
                    image_factory=StyledPilImage,
                    module_drawer=RoundedModuleDrawer(),
                    color_mask=c_mask
                ).convert('RGB')
                
                qr_width, qr_height = qr_img.size
                logo_size = int(qr_width * 0.25) 
                
                logo_img = creer_logo_custom(size=600, color=logo_color_rgb)
                logo_resized = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                
                pos_x = (qr_width - logo_size) // 2
                pos_y = (qr_height - logo_size) // 2
                
                qr_img.paste(logo_resized, (pos_x, pos_y), mask=logo_resized)

                titre_safe = "".join(x for x in str(row.get('Titre', f'track_{music_id}')) if x.isalnum() or x in [' ', '-', '_']).strip()
                titre_safe = titre_safe[:50] 
                
                filename = f"qr_{music_id}_{titre_safe}.png"
                qr_img.save(os.path.join(OUTPUT_DIR, filename))
                
                if index % 50 == 0:
                    print(f"Progression : {index}/{len(df)}")
                
            except Exception as e:
                 print(f"Erreur sur la ligne {index} : {e}")

    print(f"\nTerminé ! Les QR codes sont dans le dossier '{OUTPUT_DIR}'.")

if __name__ == "__main__":
    main()