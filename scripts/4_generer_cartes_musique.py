from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
import pandas as pd
import os
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="music", help="Mode de jeu")
    args = parser.add_argument() if False else parser.parse_args()
    
    mode = args.mode
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    db_path = os.path.join(project_root, "modes", mode, "db.json")
    output_dir = os.path.join(project_root, "modes", mode, "exports", "cartes")
    qr_dir = os.path.join(project_root, "modes", mode, "exports", "qrcodes")
    
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        print(f"Erreur: la base de données {db_path} est introuvable.")
        return

    try:
        df = pd.read_json(db_path)
    except Exception as e:
        print(f"Erreur lecture JSON: {e}")
        return

    max_id_generated = -1
    for filename in os.listdir(output_dir):
        if "recto" in filename or "verso" in filename:
            try:
                music_id = int(filename.split("_")[0])
                if music_id > max_id_generated:
                    max_id_generated = music_id
            except (ValueError, IndexError):
                pass

    print(f"Dernière carte générée : ID {max_id_generated}. Génération à partir de l'ID {max_id_generated + 1}.")

    df = df[pd.notna(df['ID'])]
    df = df[df['ID'].astype(int) > max_id_generated]
    print(f"-> {len(df)} cartes à générer.")
    
    CARD_SIZE = (945, 945) # 8x8cm à 300 DPI
    CENTRE_X = CARD_SIZE[0] // 2
    CENTRE_Y = CARD_SIZE[1] // 2

    font_path = os.path.join(project_root, "fonts", "KeeponTruckin.ttf")
    font_path_title = os.path.join(project_root, "fonts", "COOPBL.TTF")

    for index, row in df.iterrows():
        if 'ID' not in row or pd.isna(row['ID']):
            continue
        music_id = int(row['ID'])
        
        # --- RECTO ---
        recto_img_path = os.path.join(project_root, "webapp", "img", "recto_carteExtrait.png")
        if not os.path.exists(recto_img_path):
            recto_img_path = os.path.join(project_root, "img", "recto_carteExtrait.png") # Fallback for old path
            
        try:
            recto = Image.open(recto_img_path).convert("RGBA").resize(CARD_SIZE)
        except Exception:
            recto = Image.new("RGBA", CARD_SIZE, (255, 255, 255, 255))
        
        titre_safe = "".join(x for x in str(row['Titre']) if x.isalnum() or x in [' ', '-', '_']).strip()
        titre_safe = titre_safe[:50]
        qr_path = os.path.join(qr_dir, f"qr_{music_id}_{titre_safe}.png")
        
        if os.path.exists(qr_path):
            qr_img = Image.open(qr_path).convert("RGBA").resize((330, 330))
            recto.paste(qr_img, (CARD_SIZE[0]//2 - 165, CARD_SIZE[1]//2 - 165), qr_img)
        recto.save(os.path.join(output_dir, f"{music_id}_recto_{titre_safe}.png"))

        # --- VERSO ---
        MOIS_FR = {
            1: 'janvier', 2: 'fevrier', 3: 'mars', 4: 'avril', 5: 'mai', 6: 'juin',
            7: 'juillet', 8: 'aout', 9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'decembre'
        }
        
        pochette_raw_path = str(row.get('local_artwork_path', '')).replace('../', '')
        pochette_path = os.path.join(project_root, pochette_raw_path)
        
        try:
            pochette = Image.open(pochette_path).convert("RGBA")
        except Exception as e:
            print(f"Pochette introuvable pour {row['Titre']}, ignorée. ({e})")
            continue
        
        target_width, target_height = CARD_SIZE
        img_width, img_height = pochette.size
        
        ratio = max(target_width / img_width, target_height / img_height)

        # Zooms spécifiques hardcodés... (on les garde pour rétrocompatibilité)
        y_offset = 0
        if row['Titre'] == "Take on Me" and row['Artiste'] == "a-ha": ratio *= 1.15
        if row['Titre'] == "Stayin' Alive" and row['Artiste'] == "Bee Gees": ratio *= 1.15; y_offset = -38
        if row['Titre'] == "Like a Rolling Stone" and row['Artiste'] == "Bob Dylan": ratio *= 1.28; y_offset = +30
        if row['Titre'] == "Harley Davidson" and row['Artiste'] == "Brigitte Bardot": ratio *= 1.15
        if row['Titre'] == "Blue Suede Shoes" and row['Artiste'] == "The Rolling Stones": ratio *= 1.15
        if row['Titre'] == "Est-ce que tu viens pour les vacances ?" and row['Artiste'] == "David et Jonathan": ratio *= 1.15
        if row['Titre'] == "Il jouait du piano debout" and row['Artiste'] == "France Gall": ratio *= 1.10
        if row['Titre'] == "Conmigo" and row['Artiste'] == "Kendji Girac": ratio *= 1.10
        if row['Titre'] == "Andalouse" and row['Artiste'] == "Kendji Girac": ratio *= 1.10
        if row['Titre'] == "U Can't Touch This" and row['Artiste'] == "MC Hammer": ratio *= 1.05
        if row['Titre'] == "Celebration" and row['Artiste'] == "Kool & The Gang": ratio *= 1.10
        if row['Titre'] == "Nuit sauvage" and row['Artiste'] == "Les Avions": ratio *= 1.10
        if row['Titre'] == "Walk on the Wild Side" and row['Artiste'] == "Lou Reed": ratio *= 1.10
        if row['Titre'] == "Wonderwall" and row['Artiste'] == "Oasis": ratio *= 1.07
        if row['Titre'] == "Counting Stars" and row['Artiste'] == "OneRepublic": ratio *= 1.10
        if row['Titre'] == "L'École est finie" and row['Artiste'] == "Sheila": ratio *= 1.10
        if row['Titre'] == "Bitter Sweet Symphony" and row['Artiste'] == "The Verve": ratio *= 1.15
        if row['Titre'] == "Je veux" and row['Artiste'] == "Zaz": ratio *= 1.10
        if row['Titre'] == "Autobahn" and row['Artiste'] == "Kraftwerk": ratio *= 1.10
        if row['Titre'] == "Derrière le Brouillard" and row['Artiste'] == "Grand Corps Malade & Louane": ratio *= 1.15
        if row['Titre'] == "Steal My Girl" and row['Artiste'] == "One Direction": ratio *= 1.08

        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)

        pochette = pochette.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2 + y_offset
        right = left + target_width
        bottom = top + target_height
        
        pochette = pochette.crop((left, top, right, bottom))
        
        verso = pochette
        draw = ImageDraw.Draw(verso)

        try:
            date_obj = datetime.strptime(str(row['Date_Sortie'])[:10], '%Y-%m-%d')
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
            bbox_titre = draw.textbbox((CENTRE_X, 720), str(row.get('Titre', '')), font=font_texte, anchor="mm")
            rect_titre = (bbox_titre[0] - padding, bbox_titre[1] - padding, bbox_titre[2] + padding, bbox_titre[3] + padding)
            draw_overlay.rectangle(rect_titre, fill=(255, 255, 255, 200))
            
            bbox_artiste = draw.textbbox((CENTRE_X, 780), str(row.get('Artiste', '')), font=font_texte, anchor="mm")
            rect_artiste = (bbox_artiste[0] - padding, bbox_artiste[1] - padding, bbox_artiste[2] + padding, bbox_artiste[3] + padding)
            draw_overlay.rectangle(rect_artiste, fill=(255, 255, 255, 200))
        except Exception:
            pass
        
        verso = Image.alpha_composite(verso, overlay)
        draw = ImageDraw.Draw(verso)

        y_frise = CENTRE_Y - 90 
        draw.text((CENTRE_X, y_frise), annee_str, fill="black", font=font_annee, anchor="mm", stroke_width=8, stroke_fill="white")
        draw.text((CENTRE_X, y_frise + 90), jour_mois_str, fill="black", font=font_date, anchor="mt", stroke_width=5, stroke_fill="white")

        draw.text((CENTRE_X, 720), str(row.get('Titre', '')), fill="black", font=font_texte, anchor="mm", stroke_width=3, stroke_fill="white")
        draw.text((CENTRE_X, 780), str(row.get('Artiste', '')), fill="black", font=font_texte, anchor="mm", stroke_width=3, stroke_fill="white")

        verso.save(os.path.join(output_dir, f"{music_id}_verso_{titre_safe}.png"))
        print(f"Carte {music_id} terminée.")

if __name__ == "__main__":
    main()