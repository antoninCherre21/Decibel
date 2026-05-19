from PIL import Image, ImageDraw
import os
import argparse
from utils import get_paths, load_json, save_json


def generate_pdf():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="music", help="Mode de jeu")
    args = parser.parse_args()

    mode = args.mode
    paths = get_paths(mode)
    INPUT_DIR = paths["cartes"]
    PLANCHES_DIR = paths["planches_extraits"]
    TRACKING_FILE = paths["planches_suivi"]

    os.makedirs(PLANCHES_DIR, exist_ok=True)

    A4_WIDTH = 2480
    A4_HEIGHT = 3508
    CARD_SIZE = 945
    CARDS_PER_ROW = 2
    CARDS_PER_COL = 3
    CARDS_PER_PAGE = CARDS_PER_ROW * CARDS_PER_COL

    # Paramètres de coupe (en mm, convertis en pixels @ 300 DPI)
    DPI = 300
    MM_TO_PX = DPI / 25.4
    SPACING = int(5 * MM_TO_PX)  # 5 mm d'espace entre les cartes
    BLEED = int(1 * MM_TO_PX)    # 1 mm de "rogne" (coupe à l'intérieur de la carte)

    # Calcul des marges avec espacement
    TOTAL_W = (CARDS_PER_ROW * CARD_SIZE) + (CARDS_PER_ROW - 1) * SPACING
    TOTAL_H = (CARDS_PER_COL * CARD_SIZE) + (CARDS_PER_COL - 1) * SPACING
    MARGIN_X = (A4_WIDTH - TOTAL_W) // 2
    MARGIN_Y = (A4_HEIGHT - TOTAL_H) // 2

    if not os.path.exists(INPUT_DIR):
        print(f"Erreur : Le dossier {INPUT_DIR} n'existe pas.")
        return

    # --- Suivi des planches déjà générées ---
    tracking_data = load_json(TRACKING_FILE, default={"planches": []})
    already_placed_ids = set()
    for planche in tracking_data.get("planches", []):
        for card_id in planche.get("card_ids", []):
            already_placed_ids.add(card_id)

    if already_placed_ids:
        print(f"Suivi chargé : {len(already_placed_ids)} cartes déjà placées sur {len(tracking_data['planches'])} planche(s).")
    else:
        print("Aucun suivi existant. Toutes les cartes disponibles seront placées.")

    # --- Récupération et regroupement des fichiers ---
    files = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith(".png")])
    cards = {}
    for f in files:
        parts = f.split("_")
        if len(parts) >= 3:
            try:
                card_id = int(parts[0])
                type_face = parts[1]
                if card_id not in cards:
                    cards[card_id] = {}
                cards[card_id][type_face] = os.path.join(INPUT_DIR, f)
            except ValueError:
                pass

    new_card_ids = sorted([
        cid for cid in cards
        if "recto" in cards[cid] and "verso" in cards[cid]
        and cid not in already_placed_ids
    ])

    if not new_card_ids:
        print("✅ Toutes les cartes sont déjà présentes sur des planches. Rien à générer.")
        return

    print(f"-> {len(new_card_ids)} nouvelle(s) carte(s) à placer sur des planches.")

    # --- Génération ---
    planche_counter = len(tracking_data["planches"]) + 1

    def draw_crop_marks(draw, x_positions, y_positions, length=60):
        """Dessine des traits de coupe en croix dans les marges."""
        color = (180, 180, 180)  # Gris clair
        # Traits verticaux
        for x in x_positions:
            draw.line([(x, 0), (x, MARGIN_Y - 20)], fill=color, width=2)
            draw.line([(x, A4_HEIGHT), (x, A4_HEIGHT - MARGIN_Y + 20)], fill=color, width=2)
        # Traits horizontaux
        for y in y_positions:
            draw.line([(0, y), (MARGIN_X - 20, y)], fill=color, width=2)
            draw.line([(A4_WIDTH, y), (A4_WIDTH - MARGIN_X + 20, y)], fill=color, width=2)

    for i in range(0, len(new_card_ids), CARDS_PER_PAGE):
        chunk = new_card_ids[i:i + CARDS_PER_PAGE]
        planche_name_base = f"planche_{planche_counter:03d}"

        # Échantillonner la couleur de fond du premier recto pour le fond de la planche
        bg_color = (18, 22, 45) # Défaut (bleu Décibel)
        try:
            sample_img = Image.open(cards[chunk[0]]['recto']).convert("RGB")
            bg_color = sample_img.getpixel((10, 10))
        except:
            pass

        page_recto = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
        draw_r = ImageDraw.Draw(page_recto)
        BORDER_OUT = int(3 * MM_TO_PX) # Marge de sécurité de 3mm autour de la carte

        for pos, cid in enumerate(chunk):
            img = Image.open(cards[cid]['recto']).resize((CARD_SIZE, CARD_SIZE))
            col = pos % CARDS_PER_ROW
            row = pos // CARDS_PER_ROW
            x = MARGIN_X + col * (CARD_SIZE + SPACING)
            y = MARGIN_Y + row * (CARD_SIZE + SPACING)
            
            # Dessiner une bordure de couleur de 3mm pour la sécurité de coupe
            draw_r.rectangle([x - BORDER_OUT, y - BORDER_OUT, x + CARD_SIZE + BORDER_OUT, y + CARD_SIZE + BORDER_OUT], fill=bg_color)
            
            page_recto.paste(img, (x, y))

        page_verso = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
        draw_v = ImageDraw.Draw(page_verso)
        
        # Coordonnées des coupes (incluant la rogne de 1mm)
        x_cuts = []
        y_cuts = []

        for pos, cid in enumerate(chunk):
            img = Image.open(cards[cid]['verso']).resize((CARD_SIZE, CARD_SIZE))
            col_recto = pos % CARDS_PER_ROW
            row_recto = pos // CARDS_PER_ROW
            col_verso = (CARDS_PER_ROW - 1) - col_recto
            
            x = MARGIN_X + col_verso * (CARD_SIZE + SPACING)
            y = MARGIN_Y + row_recto * (CARD_SIZE + SPACING)
            page_verso.paste(img, (x, y))

            # On mémorise les positions des bords pour les traits de coupe (avec rogne)
            if row_recto == 0: # Colonnes
                x_cuts.append(x + BLEED)
                x_cuts.append(x + CARD_SIZE - BLEED)
            if col_verso == 0: # Lignes
                y_cuts.append(y + BLEED)
                y_cuts.append(y + CARD_SIZE - BLEED)

        # Dessiner les aides à la découpe sur le verso
        draw_crop_marks(draw_v, sorted(list(set(x_cuts))), sorted(list(set(y_cuts))))

        output_pdf = os.path.join(PLANCHES_DIR, f"{planche_name_base}.pdf")
        page_recto.save(output_pdf, save_all=True, append_images=[page_verso], resolution=300)

        tracking_data["planches"].append({
            "planche": planche_counter,
            "fichier": f"{planche_name_base}.pdf",
            "card_ids": chunk
        })

        print(f"  ✅ Planche {planche_counter} générée ({len(chunk)} cartes) -> {planche_name_base}.pdf")
        planche_counter += 1

    save_json(tracking_data, TRACKING_FILE)
    print(f"\n🎉 Terminé ! Planches dans '{PLANCHES_DIR}'. Suivi mis à jour.")


if __name__ == "__main__":
    generate_pdf()
