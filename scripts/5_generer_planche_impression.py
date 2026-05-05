from PIL import Image
import os
import json
import argparse

def generate_pdf():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="music", help="Mode de jeu")
    args = parser.add_argument() if False else parser.parse_args()
    
    mode = args.mode
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INPUT_DIR = os.path.join(BASE_DIR, "modes", mode, "exports", "cartes")
    EXPORTS_DIR = os.path.join(BASE_DIR, "modes", mode, "exports")
    
    # Fichier de suivi : liste des IDs de cartes déjà placées sur des planches
    TRACKING_FILE = os.path.join(EXPORTS_DIR, "planches_suivi.json")

    # Format A4 à 300 DPI
    A4_WIDTH = 2480
    A4_HEIGHT = 3508

    # Taille des cartes (8x8 cm à 300 DPI -> ~945 px)
    CARD_SIZE = 945
    CARDS_PER_ROW = 2
    CARDS_PER_COL = 3
    CARDS_PER_PAGE = CARDS_PER_ROW * CARDS_PER_COL  # 6

    MARGIN_X = (A4_WIDTH - (CARDS_PER_ROW * CARD_SIZE)) // 2
    MARGIN_Y = (A4_HEIGHT - (CARDS_PER_COL * CARD_SIZE)) // 2

    if not os.path.exists(INPUT_DIR):
        print(f"Erreur : Le dossier {INPUT_DIR} n'existe pas.")
        return

    # --- 1. Charger le suivi des planches déjà générées ---
    already_placed_ids = set()
    tracking_data = {"planches": []}
    
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
            tracking_data = json.load(f)
        for planche in tracking_data.get("planches", []):
            for card_id in planche.get("card_ids", []):
                already_placed_ids.add(card_id)
        print(f"Suivi chargé : {len(already_placed_ids)} cartes déjà placées sur {len(tracking_data['planches'])} planches existantes.")
    else:
        print("Aucun suivi existant. Toutes les cartes disponibles seront placées.")

    # --- 2. Récupérer les fichiers de cartes disponibles ---
    files = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith(".png")])
    
    # On regroupe par carte (ID)
    cards = {}
    for f in files:
        parts = f.split("_")
        if len(parts) >= 3:
            try:
                card_id = int(parts[0])
                type_face = parts[1]  # "recto" ou "verso"
                if card_id not in cards:
                    cards[card_id] = {}
                cards[card_id][type_face] = os.path.join(INPUT_DIR, f)
            except ValueError:
                pass

    # --- 3. Filtrer : garder seulement les cartes qui ont recto ET verso, et pas encore placées ---
    new_card_ids = sorted([
        card_id for card_id in cards
        if "recto" in cards[card_id] and "verso" in cards[card_id]
        and card_id not in already_placed_ids
    ])
    
    if not new_card_ids:
        print("✅ Toutes les cartes sont déjà présentes sur des planches. Rien à générer.")
        return
    
    print(f"-> {len(new_card_ids)} nouvelles cartes à placer sur des planches.")

    # --- 4. Générer les nouvelles planches ---
    pages_generated = []
    planche_counter = len(tracking_data["planches"]) + 1  # Continuer la numérotation

    # On traite par lot de 6 cartes (2 colonnes x 3 lignes)
    for i in range(0, len(new_card_ids), CARDS_PER_PAGE):
        chunk = new_card_ids[i:i + CARDS_PER_PAGE]
        planche_name_base = f"planche_{planche_counter:03d}"

        # --- PAGE RECTO ---
        page_recto = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
        
        for pos, card_id in enumerate(chunk):
            img = Image.open(cards[card_id]['recto']).resize((CARD_SIZE, CARD_SIZE))
            col = pos % CARDS_PER_ROW
            row = pos // CARDS_PER_ROW
            x = MARGIN_X + col * CARD_SIZE
            y = MARGIN_Y + row * CARD_SIZE
            page_recto.paste(img, (x, y))
        
        # --- PAGE VERSO (MIROIR pour impression recto-verso) ---
        page_verso = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
        
        for pos, card_id in enumerate(chunk):
            img = Image.open(cards[card_id]['verso']).resize((CARD_SIZE, CARD_SIZE))
            col_recto = pos % CARDS_PER_ROW
            row_recto = pos // CARDS_PER_ROW
            col_verso = (CARDS_PER_ROW - 1) - col_recto  # Miroir horizontal
            
            x = MARGIN_X + col_verso * CARD_SIZE
            y = MARGIN_Y + row_recto * CARD_SIZE
            page_verso.paste(img, (x, y))

        # Sauvegarde du PDF de la planche (1 PDF = 1 feuille A4 recto/verso = 2 pages)
        output_pdf = os.path.join(EXPORTS_DIR, f"{planche_name_base}.pdf")
        page_recto.save(
            output_pdf,
            save_all=True,
            append_images=[page_verso],
            resolution=300
        )
        
        pages_generated.append(output_pdf)
        
        # Enregistrement dans le suivi
        tracking_data["planches"].append({
            "planche": planche_counter,
            "fichier": f"{planche_name_base}.pdf",
            "card_ids": chunk
        })
        
        print(f"  ✅ Planche {planche_counter} générée ({len(chunk)} cartes) -> {planche_name_base}.pdf")
        planche_counter += 1

    # --- 5. Sauvegarder le fichier de suivi mis à jour ---
    with open(TRACKING_FILE, 'w', encoding='utf-8') as f:
        json.dump(tracking_data, f, indent=4, ensure_ascii=False)

    print(f"\n🎉 Terminé ! {len(pages_generated)} nouvelles planches générées dans '{EXPORTS_DIR}'.")
    print(f"Suivi mis à jour dans '{TRACKING_FILE}'.")

if __name__ == "__main__":
    generate_pdf()
