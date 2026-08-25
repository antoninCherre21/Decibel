from PIL import Image, ImageDraw, ImageFont
import os
import argparse
import textwrap
from utils import get_paths, load_json

def get_fonts(base_path):
    font_path_title = os.path.join(base_path, "fonts", "COOPBL.TTF")
    font_path_desc = os.path.join(base_path, "fonts", "KeeponTruckin.ttf")
    
    try:
        title_font = ImageFont.truetype(font_path_title, size=70)
    except IOError:
        title_font = ImageFont.load_default(size=50)
        
    try:
        # On utilise une taille plus petite pour la description
        desc_font = ImageFont.truetype(font_path_title, size=40)
    except IOError:
        desc_font = ImageFont.load_default(size=30)
        
    return title_font, desc_font

def draw_text_centered(draw, text, font, y_pos, image_width, fill="black"):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    x_pos = (image_width - text_w) / 2
    draw.text((x_pos, y_pos), text, font=font, fill=fill)

def generate_versos(paths, copies_per_card=2):
    db_path = paths["db_chances"]
    cartes_dir = paths["cartes_chances"]
    logos_dir = os.path.join(paths["img"], "logos_cartesChances")
    
    os.makedirs(cartes_dir, exist_ok=True)
    cards_data = load_json(db_path, default=[])
    
    if not cards_data:
        print(f"Aucune donnée dans {db_path}.")
        return []
        
    title_font, desc_font = get_fonts(paths["base"])
    CARD_W = 803
    CARD_H = 1092
    generated_files = []
    
    print("-> Génération des versos des Cartes Chances...")
    for card in cards_data:
        cid = card["id"]
        titre = card["titre"]
        desc = card["description"]
        logo_file = card.get("logo", "")
        
        # Création de l'image (fond blanc)
        img = Image.new("RGB", (CARD_W, CARD_H), "white")
        draw = ImageDraw.Draw(img)
        
        # Titre (en haut)
        draw_text_centered(draw, titre, title_font, 120, CARD_W, fill=(18, 22, 45)) # Bleu Décibel
        
        # Logo (au centre)
        if logo_file:
            logo_path = os.path.join(logos_dir, logo_file)
            if os.path.exists(logo_path):
                try:
                    logo_img = Image.open(logo_path).convert("RGBA")
                    # Redimensionner le logo (max 400x400)
                    logo_img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                    lx = (CARD_W - logo_img.width) // 2
                    ly = (CARD_H - logo_img.height) // 2 - 50 # Un peu plus haut que le centre exact
                    img.paste(logo_img, (lx, ly), logo_img)
                except Exception as e:
                    print(f"Erreur avec le logo {logo_file}: {e}")
            else:
                print(f"Attention: logo {logo_file} introuvable.")
                
        # Description (en bas, multiligne)
        margin = 80
        max_width = CARD_W - (margin * 2)
        chars_per_line = int(max_width / 20)
        wrapped_text = textwrap.fill(desc, width=chars_per_line)
        
        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=desc_font, align="center")
        text_h = bbox[3] - bbox[1]
        y_pos = CARD_H - 180 - text_h
        
        draw.multiline_text((CARD_W/2, y_pos), wrapped_text, font=desc_font, fill="black", anchor="ma", align="center")
        
        # Sauvegarde
        out_filename = f"verso_chance_{cid:03d}.png"
        out_path = os.path.join(cartes_dir, out_filename)
        img.save(out_path)
        
        # Ajouter à la liste selon le nombre d'exemplaires souhaité
        for _ in range(copies_per_card):
            generated_files.append(out_path)
            
    print(f"✅ {len(cards_data)} cartes chances générées (x{copies_per_card} exemplaires = {len(generated_files)} cartes totales).")
    return generated_files

def draw_crop_marks(draw, x_positions, y_positions, width, height, margin_x, margin_y):
    """Dessine des traits de coupe en croix dans les marges."""
    color = (180, 180, 180)  # Gris clair
    for x in x_positions:
        draw.line([(x, 0), (x, margin_y - 20)], fill=color, width=2)
        draw.line([(x, height), (x, height - margin_y + 20)], fill=color, width=2)
    for y in y_positions:
        draw.line([(0, y), (margin_x - 20, y)], fill=color, width=2)
        draw.line([(width, y), (width - margin_x + 20, y)], fill=color, width=2)

def generate_planches(paths, verso_paths):
    if not verso_paths:
        return
        
    planches_dir = paths["planches_chances"]
    os.makedirs(planches_dir, exist_ok=True)
    
    A4_WIDTH = 3508  # Format Paysage
    A4_HEIGHT = 2480
    CARD_W = 803
    CARD_H = 1092
    CARDS_PER_ROW = 4
    CARDS_PER_COL = 2
    CARDS_PER_PAGE = CARDS_PER_ROW * CARDS_PER_COL
    
    DPI = 300
    MM_TO_PX = DPI / 25.4
    SPACING = int(5 * MM_TO_PX)
    BLEED = int(1 * MM_TO_PX)
    BORDER_OUT = int(3 * MM_TO_PX)
    
    TOTAL_W = (CARDS_PER_ROW * CARD_W) + (CARDS_PER_ROW - 1) * SPACING
    TOTAL_H = (CARDS_PER_COL * CARD_H) + (CARDS_PER_COL - 1) * SPACING
    MARGIN_X = (A4_WIDTH - TOTAL_W) // 2
    MARGIN_Y = (A4_HEIGHT - TOTAL_H) // 2
    
    # Chargement du recto commun
    recto_path = os.path.join(paths["img"], "recto_carteChance.png")
    if not os.path.exists(recto_path):
        print(f"Erreur : Recto introuvable à {recto_path}")
        return
        
    recto_img_orig = Image.open(recto_path).convert("RGB")
    recto_img = recto_img_orig.resize((CARD_W, CARD_H))
    
    # Couleur de fond pour le bleed du recto (échantillonnée)
    bg_color = recto_img_orig.getpixel((10, 10))
    
    print("-> Génération des planches...")
    planche_counter = 1
    
    for i in range(0, len(verso_paths), CARDS_PER_PAGE):
        chunk = verso_paths[i:i + CARDS_PER_PAGE]
        planche_name = f"planche_chances_{planche_counter:03d}.pdf"
        
        # --- PAGE RECTO ---
        page_recto = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
        draw_r = ImageDraw.Draw(page_recto)
        
        for pos in range(len(chunk)):
            col = pos % CARDS_PER_ROW
            row = pos // CARDS_PER_ROW
            x = MARGIN_X + col * (CARD_W + SPACING)
            y = MARGIN_Y + row * (CARD_H + SPACING)
            
            # Bordure de sécurité (bleed)
            draw_r.rectangle([x - BORDER_OUT, y - BORDER_OUT, x + CARD_W + BORDER_OUT, y + CARD_H + BORDER_OUT], fill=bg_color)
            page_recto.paste(recto_img, (x, y))
            
        # --- PAGE VERSO ---
        page_verso = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
        draw_v = ImageDraw.Draw(page_verso)
        
        x_cuts = []
        y_cuts = []
        
        for pos, v_path in enumerate(chunk):
            v_img = Image.open(v_path).resize((CARD_W, CARD_H))
            
            # Miroir horizontal pour l'alignement recto/verso
            col_recto = pos % CARDS_PER_ROW
            row_recto = pos // CARDS_PER_ROW
            col_verso = (CARDS_PER_ROW - 1) - col_recto
            
            x = MARGIN_X + col_verso * (CARD_W + SPACING)
            y = MARGIN_Y + row_recto * (CARD_H + SPACING)
            page_verso.paste(v_img, (x, y))
            
            if row_recto == 0:
                x_cuts.extend([x + BLEED, x + CARD_W - BLEED])
            if col_verso == 0:
                y_cuts.extend([y + BLEED, y + CARD_H - BLEED])
                
        draw_crop_marks(draw_v, sorted(list(set(x_cuts))), sorted(list(set(y_cuts))), A4_WIDTH, A4_HEIGHT, MARGIN_X, MARGIN_Y)
        
        output_pdf = os.path.join(planches_dir, planche_name)
        page_recto.save(output_pdf, save_all=True, append_images=[page_verso], resolution=300)
        
        print(f"  ✅ Planche {planche_counter} générée ({len(chunk)} cartes) -> {planche_name}")
        planche_counter += 1

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="music", help="Mode de jeu")
    args = parser.parse_args()
    
    paths = get_paths(args.mode)
    
    COPIES_PER_CARD = 2
    verso_paths = generate_versos(paths, copies_per_card=COPIES_PER_CARD)
    generate_planches(paths, verso_paths)
    
    print("\n🎉 Terminé ! Les planches de cartes chances sont prêtes.")

if __name__ == "__main__":
    main()
