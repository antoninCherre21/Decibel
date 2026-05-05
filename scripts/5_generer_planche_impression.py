from PIL import Image
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
    EXPORTS_DIR = paths["exports"]
    TRACKING_FILE = paths["planches_suivi"]

    A4_WIDTH = 2480
    A4_HEIGHT = 3508
    CARD_SIZE = 945
    CARDS_PER_ROW = 2
    CARDS_PER_COL = 3
    CARDS_PER_PAGE = CARDS_PER_ROW * CARDS_PER_COL
    MARGIN_X = (A4_WIDTH - (CARDS_PER_ROW * CARD_SIZE)) // 2
    MARGIN_Y = (A4_HEIGHT - (CARDS_PER_COL * CARD_SIZE)) // 2

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

    for i in range(0, len(new_card_ids), CARDS_PER_PAGE):
        chunk = new_card_ids[i:i + CARDS_PER_PAGE]
        planche_name_base = f"planche_{planche_counter:03d}"

        page_recto = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
        for pos, cid in enumerate(chunk):
            img = Image.open(cards[cid]['recto']).resize((CARD_SIZE, CARD_SIZE))
            col = pos % CARDS_PER_ROW
            row = pos // CARDS_PER_ROW
            page_recto.paste(img, (MARGIN_X + col * CARD_SIZE, MARGIN_Y + row * CARD_SIZE))

        page_verso = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
        for pos, cid in enumerate(chunk):
            img = Image.open(cards[cid]['verso']).resize((CARD_SIZE, CARD_SIZE))
            col_recto = pos % CARDS_PER_ROW
            row_recto = pos // CARDS_PER_ROW
            col_verso = (CARDS_PER_ROW - 1) - col_recto
            page_verso.paste(img, (MARGIN_X + col_verso * CARD_SIZE, MARGIN_Y + row_recto * CARD_SIZE))

        output_pdf = os.path.join(EXPORTS_DIR, f"{planche_name_base}.pdf")
        page_recto.save(output_pdf, save_all=True, append_images=[page_verso], resolution=300)

        tracking_data["planches"].append({
            "planche": planche_counter,
            "fichier": f"{planche_name_base}.pdf",
            "card_ids": chunk
        })

        print(f"  ✅ Planche {planche_counter} générée ({len(chunk)} cartes) -> {planche_name_base}.pdf")
        planche_counter += 1

    save_json(tracking_data, TRACKING_FILE)
    print(f"\n🎉 Terminé ! Planches dans '{EXPORTS_DIR}'. Suivi mis à jour.")


if __name__ == "__main__":
    generate_pdf()
