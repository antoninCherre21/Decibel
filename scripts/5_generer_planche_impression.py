from PIL import Image
import os
import math

# Configuration
INPUT_DIR = "./cartes_musiques"
OUTPUT_FILE = "planches_impression.pdf"

# Format A4 à 300 DPI
A4_WIDTH = 2480
A4_HEIGHT = 3508
DPI = 300

# Taille des cartes (8x8 cm à 300 DPI -> ~945 px)
CARD_SIZE = 945
MARGIN_X = (A4_WIDTH - (2 * CARD_SIZE)) // 2
MARGIN_Y = (A4_HEIGHT - (3 * CARD_SIZE)) // 2

def generate_pdf():
    if not os.path.exists(INPUT_DIR):
        print(f"Erreur : Le dossier {INPUT_DIR} n'existe pas.")
        return

    # Récupération des fichiers
    files = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith(".png")])
    
    # On regroupe par carte (index)
    cards = {}
    for f in files:
        parts = f.split("_")
        if len(parts) >= 3:
            index = int(parts[0])
            type_face = parts[1] # "recto" ou "verso"
            
            if index not in cards:
                cards[index] = {}
            cards[index][type_face] = os.path.join(INPUT_DIR, f)

    sorted_indexes = sorted(cards.keys())
    print(f"{len(sorted_indexes)} cartes trouvées.")

    pages = []

    # On traite par lot de 6 cartes (2 colonnes x 3 lignes)
    chunk_size = 6
    for i in range(0, len(sorted_indexes), chunk_size):
        chunk = sorted_indexes[i:i + chunk_size]
        
        # --- PAGE RECTO ---
        page_recto = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
        
        # Positions :
        # 0 1
        # 2 3
        # 4 5
        
        for pos, card_idx in enumerate(chunk):
            if "recto" in cards[card_idx]:
                img = Image.open(cards[card_idx]['recto']).resize((CARD_SIZE, CARD_SIZE))
                
                col = pos % 2
                row = pos // 2
                
                x = MARGIN_X + col * CARD_SIZE
                y = MARGIN_Y + row * CARD_SIZE
                
                page_recto.paste(img, (x, y))
        
        pages.append(page_recto)

        # --- PAGE VERSO (MIROIR) ---
        # Pour que le recto et le verso coïncident à l'impression :
        # La carte en haut à gauche du recto (Col 0) doit avoir son verso en haut à DROITE (Col 1)
        # La carte en haut à droite du recto (Col 1) doit avoir son verso en haut à GAUCHE (Col 0)
        
        page_verso = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
        
        for pos, card_idx in enumerate(chunk):
            if "verso" in cards[card_idx]:
                img = Image.open(cards[card_idx]['verso']).resize((CARD_SIZE, CARD_SIZE))
                
                col_recto = pos % 2
                row_recto = pos // 2
                
                # INVERSION DE LA COLONNE (Miroir)
                # Si col_recto est 0 -> col_verso doit être 1
                # Si col_recto est 1 -> col_verso doit être 0
                col_verso = 1 - col_recto
                
                x = MARGIN_X + col_verso * CARD_SIZE
                y = MARGIN_Y + row_recto * CARD_SIZE
                
                page_verso.paste(img, (x, y))
        
        pages.append(page_verso)
        print(f"Page {len(pages)//2} générée (Recto + Verso).")

    if pages:
        pages[0].save(OUTPUT_FILE, save_all=True, append_images=pages[1:])
        print(f"\nTerminé ! Fichier généré : {OUTPUT_FILE}")
    else:
        print("Aucune page générée.")

if __name__ == "__main__":
    generate_pdf()
