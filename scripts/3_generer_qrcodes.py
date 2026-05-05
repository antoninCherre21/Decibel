import pandas as pd
import qrcode
import os
import shutil
from PIL import Image, ImageDraw
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask

# ==========================================
# PARTIE 1 : FONCTION DE GÉNÉRATION DU LOGO
# ==========================================
# Mapping des couleurs (Nom FR -> RGB)
# Couleurs adoucies (moins "flashy")
COLORS_RGB = {
    'bleu': (66, 135, 245),   # Bleu doux
    'violet': (155, 89, 182), # Violet améthyste
    'vert': (39, 174, 96),    # Vert émeraude
    'orange': (230, 126, 34), # Orange carotte
    'rose': (236, 64, 122),   # Rose framboise doux
    'noir': (45, 52, 54)      # Noir anthracite
}

def creer_logo_custom(size=500, color=(0, 0, 0)):
    """
    Crée un logo carré transparent contenant :
    1. Un cercle blanc (pour la bordure)
    2. Un cercle de couleur (fond)
    3. Un triangle 'play' blanc au centre
    """
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img, 'RGBA')
    
    center = size // 2
    border_thickness = size // 15  
    
    # Cercle blanc (bordure)
    draw.ellipse([0, 0, size, size], fill=(255, 255, 255, 255))
    
    # Cercle de couleur (fond)
    margin = border_thickness
    # On ajoute le canal Alpha (255) à la couleur RGB
    fill_color = color + (255,)
    draw.ellipse([margin, margin, size - margin, size - margin], fill=fill_color)
    
    # Triangle Play
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

csv_path = "./decibel_playlist.csv"
output_dir = "qrcodes_finaux"

# Ne plus nettoyer le dossier, on veut garder les anciens
os.makedirs(output_dir, exist_ok=True)

# Trouver le dernier ID généré
max_id_generated = -1
for filename in os.listdir(output_dir):
    if filename.startswith("qr_") and filename.endswith(".png"):
        try:
            music_id = int(filename.split("_")[1])
            if music_id > max_id_generated:
                max_id_generated = music_id
        except (ValueError, IndexError):
            pass

print(f"Dernier QR code généré : ID {max_id_generated}. Génération à partir de l'ID {max_id_generated + 1}.")

try:
    df = pd.read_csv(csv_path)
    print(f"Fichier CSV chargé : {len(df)} lignes trouvées.")
except FileNotFoundError:
    print(f"ERREUR : Le fichier {csv_path} n'a pas été trouvé.")
    exit()

# Chargement des genres et couleurs
genre_colors_map = {}
try:
    df_genres = pd.read_csv("tri_genres_musiques.csv")
    # On crée un dictionnaire {id_genre: couleur_nom}
    for _, row_g in df_genres.iterrows():
        genre_colors_map[row_g['id']] = row_g['Couleur']
    print("Couleurs des genres chargées.")
except Exception as e:
    print(f"Erreur chargement genres : {e}")

# Filtrage du DataFrame pour ne prendre que les nouveaux
df = df[pd.notna(df['ID'])]
df_filtered = df[df['ID'].astype(int) > max_id_generated]
print(f"-> {len(df_filtered)} musiques à générer (sur {len(df)} total).")
df = df_filtered


print("Début de la génération des QR Codes...")

for index, row in df.iterrows():
    if 'ID' in row and pd.notna(row['ID']):
        music_id = int(row['ID'])
        try:
            # A. Création du QR Code (Style Arrondi)
            qr = qrcode.QRCode(
                version=None, 
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=1
            )
            qr_data = f"music_{music_id}"
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Détermination de la couleur en fonction de la difficulté
            if str(row.get('Difficulté')) == 'Difficile':
                # Rouge pour Difficile
                c_mask = SolidFillColorMask(front_color=(255, 0, 0), back_color=(255, 255, 255))
            else:
                # Noir pour les autres (Facile, Moyen)
                c_mask = SolidFillColorMask(front_color=(0, 0, 0), back_color=(255, 255, 255))

            # Utilisation du style "Rounded" (Arrondi)
            qr_img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
                color_mask=c_mask
            ).convert('RGB')
            
            # B. Collage du logo
            qr_width, qr_height = qr_img.size
            
            # Taille du logo : 25%
            logo_size = int(qr_width * 0.25) 
            
            # Détermination de la couleur du logo
            logo_color_rgb = (0, 0, 0) # Noir par défaut
            
            if str(row.get('Difficulté')) == 'Difficile':
                logo_color_rgb = (0, 0, 0) # Noir si Difficile
            else:
                # Récupération de la couleur du genre
                genre_id = row.get('Genre')
                # Le genre peut être un int ou str, on gère
                try:
                    genre_id = int(genre_id)
                    color_name = genre_colors_map.get(genre_id, 'noir')
                    logo_color_rgb = COLORS_RGB.get(color_name, (0, 0, 0))
                except:
                    logo_color_rgb = (0, 0, 0)

            # Génération du logo spécifique
            logo_img = creer_logo_custom(size=600, color=logo_color_rgb)
            logo_resized = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            pos_x = (qr_width - logo_size) // 2
            pos_y = (qr_height - logo_size) // 2
            
            # Collage avec masque de transparence
            qr_img.paste(logo_resized, (pos_x, pos_y), mask=logo_resized)

            # C. Sauvegarde
            # Nom de fichier : qr_{music_id}_{titre_simplifié}.png
            titre_safe = "".join(x for x in str(row.get('Titre', f'track_{music_id}')) if x.isalnum() or x in [' ', '-', '_']).strip()
            # Limite la longueur du nom de fichier pour éviter les erreurs système
            titre_safe = titre_safe[:50] 
            
            filename = f"qr_{music_id}_{titre_safe}.png"
            qr_img.save(os.path.join(output_dir, filename))
            
            if index % 50 == 0:
                print(f"Progression : {index}/{len(df)}")
            
        except Exception as e:
             print(f"Erreur sur la ligne {index} : {e}")

print(f"\nTerminé ! Les QR codes sont dans le dossier '{output_dir}'.")