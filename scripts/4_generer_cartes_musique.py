from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
import pandas as pd
import os
import shutil

df = pd.read_csv("./decibel_playlist.csv")
output_dir = "./cartes_musiques"
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir, exist_ok=True)
CARD_SIZE = (945, 945) # 8x8cm à 300 DPI
CENTRE_X = CARD_SIZE[0] // 2
CENTRE_Y = CARD_SIZE[1] // 2

# Détermination du chemin absolu vers la police
# Le script est dans /scripts, donc on remonte d'un niveau pour trouver /fonts
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
font_path = os.path.join(project_root, "fonts", "KeeponTruckin.ttf")
font_path_title = os.path.join(project_root, "fonts", "COOPBL.TTF")

for index, row in df.iterrows():
    if 'ID' not in row or pd.isna(row['ID']):
        continue
    music_id = int(row['ID'])
    # --- RECTO ---
    recto = Image.open("./img/recto_carteExtrait.png").convert("RGBA").resize(CARD_SIZE)
    
    # On doit utiliser la même logique de nommage que dans 3_generer_qrcodes.py
    titre_safe = "".join(x for x in str(row['Titre']) if x.isalnum() or x in [' ', '-', '_']).strip()
    titre_safe = titre_safe[:50]
    qr_path = f"./qrcodes_finaux/qr_{music_id}_{titre_safe}.png"
    if os.path.exists(qr_path):
        qr_img = Image.open(qr_path).convert("RGBA").resize((330, 330))
        recto.paste(qr_img, (CARD_SIZE[0]//2 - 165, CARD_SIZE[1]//2 - 165), qr_img)
    recto.save(f"{output_dir}/{music_id}_recto_{row['Titre']}.png")

    # --- VERSO ---

    # Dictionnaire pour les mois en français
    MOIS_FR = {
        1: 'janvier', 2: 'fevrier', 3: 'mars', 4: 'avril', 5: 'mai', 6: 'juin',
        7: 'juillet', 8: 'aout', 9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'decembre'
    }
    
    # Chargement pochette locale
    # local_artwork_path contient le chemin local depuis la racine, ex: ./pochettes/...
    pochette_path = os.path.join(project_root, str(row['local_artwork_path']).replace('./', ''))
    try:
        pochette = Image.open(pochette_path).convert("RGBA")
    except Exception as e:
        print(f"Pochette introuvable pour {row['Titre']}, ignorée. ({e})")
        continue
    
    # Redimensionnement intelligent (Crop-to-fill)
    # On veut remplir un carré de CARD_SIZE (945x945)
    target_width, target_height = CARD_SIZE
    img_width, img_height = pochette.size
    
    # Calcul du ratio pour redimensionner en gardant les proportions
    # On prend le max des ratios pour s'assurer que l'image couvre tout le carré
    ratio = max(target_width / img_width, target_height / img_height)

    # Zoom spécifique pour Take on Me
    if row['Titre'] == "Take on Me" and row['Artiste'] == "a-ha":
        ratio *= 1.15

    # Zoom spécifique pour Stayin' Alive
    y_offset = 0
    if row['Titre'] == "Stayin' Alive" and row['Artiste'] == "Bee Gees":
        ratio *= 1.15
        y_offset = -38 # On remonte le crop pour éviter la bande blanche en bas

    # Zoom spécifique pour Like a Rolling Stone
    if row['Titre'] == "Like a Rolling Stone" and row['Artiste'] == "Bob Dylan":
        ratio *= 1.28
        y_offset = +30

    # Zoom spécifique pour Harley Davidson
    if row['Titre'] == "Harley Davidson" and row['Artiste'] == "Brigitte Bardot":
        ratio *= 1.15

    # Zoom spécifique pour Blue Suede Shoes
    if row['Titre'] == "Blue Suede Shoes" and row['Artiste'] == "The Rolling Stones":
        ratio *= 1.15

    # Zoom spécifique pour Est-ce que tu viens pour les vacances ?
    if row['Titre'] == "Est-ce que tu viens pour les vacances ?" and row['Artiste'] == "David et Jonathan":
        ratio *= 1.15

    # Zoom spécifique pour Il jouait du piano debout
    if row['Titre'] == "Il jouait du piano debout" and row['Artiste'] == "France Gall":
        ratio *= 1.10

    # Zoom spécifique pour Conmigo
    if row['Titre'] == "Conmigo" and row['Artiste'] == "Kendji Girac":
        ratio *= 1.10

    # Zoom spécifique pour Celebration
    if row['Titre'] == "Celebration" and row['Artiste'] == "Kool & The Gang":
        ratio *= 1.10

    # Zoom spécifique pour Nuit sauvage,Les Avions
    if row['Titre'] == "Nuit sauvage" and row['Artiste'] == "Les Avions":
        ratio *= 1.10

    # Zoom spécifique pour Walk on the Wild Side
    if row['Titre'] == "Walk on the Wild Side" and row['Artiste'] == "Lou Reed":
        ratio *= 1.10

    # Zoom spécifique pour Wonderwall,Oasis
    if row['Titre'] == "Wonderwall" and row['Artiste'] == "Oasis":
        ratio *= 1.07

    # Zoom spécifique pour Counting Stars,OneRepublic
    if row['Titre'] == "Counting Stars" and row['Artiste'] == "OneRepublic":
        ratio *= 1.10

    # Zoom spécifique pour L'École est finie,Sheila
    if row['Titre'] == "L'École est finie" and row['Artiste'] == "Sheila":
        ratio *= 1.10

    # Zoom spécifique pour Bitter Sweet Symphony,The Verve
    if row['Titre'] == "Bitter Sweet Symphony" and row['Artiste'] == "The Verve":
        ratio *= 1.15

    # Zoom spécifique pour Je veux,Zaz
    if row['Titre'] == "Je veux" and row['Artiste'] == "Zaz":
        ratio *= 1.10
        
    # Zoom spécifique pour Autobahn,Kraftwerk
    if row['Titre'] == "Autobahn" and row['Artiste'] == "Kraftwerk":
        ratio *= 1.10

    new_width = int(img_width * ratio)
    new_height = int(img_height * ratio)

    pochette = pochette.resize((new_width, new_height), Image.LANCZOS)
    
    # Centrage pour le crop
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2 + y_offset
    right = left + target_width
    bottom = top + target_height
    
    pochette = pochette.crop((left, top, right, bottom))
    
    # Création du fond : PAS DE FOND BLANC (Artwork brut)
    verso = pochette
    draw = ImageDraw.Draw(verso)

    # Traitement de la date
    date_obj = datetime.strptime(row['Date_Sortie'], '%Y-%m-%d')
    annee_str = str(date_obj.year)
    # Format "14 octobre"
    jour_mois_str = f"{date_obj.day} {MOIS_FR[date_obj.month]}"

    # Chargement des Polices
    # KeeponTruckin pour Année et Date
    # COOPBL pour Titre et Artiste
    try:
        font_annee = ImageFont.truetype(font_path, size=220)
        font_date = ImageFont.truetype(font_path, size=60)
        # Utilisation de la nouvelle font pour le texte
        font_texte = ImageFont.truetype(font_path_title, size=45)
    except IOError:
        # Fallback sur la police par défaut si Arial n'est pas trouvé (moins beau)
        print("Police non trouvée, utilisation de la police par défaut.")
        font_annee = ImageFont.load_default(size=200)
        font_date = ImageFont.load_default(size=50)
        font_texte = ImageFont.load_default(size=40)

    # Dessin de la FRISE CHRONOLOGIQUE (Nouveau Design)
    # L'année est au centre (CENTRE_X, CENTRE_Y).
    
    # Dessin de la FRISE CHRONOLOGIQUE (Au CENTRE)
    # L'année est au centre de la frise.
    
    # Paramètres de la frise
    offset_annee = 280  # Espace réservé pour l'année
    y_frise = CENTRE_Y  # Retour au centre
    margin_x = 0        # Marge nulle
    
    # Dessin des BANDES BLANCHES (Encadrant Année + Date)
    
    band_thickness = 15         # Epaisseur des bandes
    
    # Bande du DESSUS (Au-dessus de l'année)
    y_band_top = CENTRE_Y - 250
    
    # Bande du DESSOUS (En dessous de la date)
    y_band_bottom = CENTRE_Y + 90

    # --- FLOU ENTRE LES BANDES ---
    # Zone à flouter
    blur_box = (0, y_band_top + band_thickness, CARD_SIZE[0], y_band_bottom)
    # On découpe la zone
    region = verso.crop(blur_box)
    # On applique le flou (Radius 3 pour un effet léger)
    region = region.filter(ImageFilter.GaussianBlur(radius=3))
    # On recolle
    verso.paste(region, blur_box)

    # Dessin des BANDES BLANCHES
    draw.rectangle([(0, y_band_top), (CARD_SIZE[0], y_band_top + band_thickness)], fill="white")
    draw.rectangle([(0, y_band_bottom), (CARD_SIZE[0], y_band_bottom + band_thickness)], fill="white")

    # FOND SEMI-TRANSPARENT ENTRE LES BANDES
    # On crée une image temporaire pour la transparence
    overlay = Image.new('RGBA', CARD_SIZE, (255, 255, 255, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    # Rectangle entre la bande du haut et la bande du bas
    # Alpha = 128 (Semi-transparent)
    draw_overlay.rectangle([(0, y_band_top + band_thickness), (CARD_SIZE[0], y_band_bottom)], fill=(255, 255, 255, 30))
    
    # FOND DYNAMIQUE POUR TITRE ET ARTISTE
    # On calcule la taille du texte pour adapter le fond
    padding = 15
    
    # Titre
    bbox_titre = draw.textbbox((CENTRE_X, 720), row['Titre'], font=font_texte, anchor="mm")
    # bbox est (left, top, right, bottom)
    rect_titre = (bbox_titre[0] - padding, bbox_titre[1] - padding, bbox_titre[2] + padding, bbox_titre[3] + padding)
    draw_overlay.rectangle(rect_titre, fill=(255, 255, 255, 200))
    
    # Artiste
    bbox_artiste = draw.textbbox((CENTRE_X, 780), row['Artiste'], font=font_texte, anchor="mm")
    rect_artiste = (bbox_artiste[0] - padding, bbox_artiste[1] - padding, bbox_artiste[2] + padding, bbox_artiste[3] + padding)
    draw_overlay.rectangle(rect_artiste, fill=(255, 255, 255, 200))
    
    # Application de l'overlay sur le verso
    verso = Image.alpha_composite(verso, overlay)
    
    # On recrée l'objet draw pour continuer à dessiner sur l'image fusionnée
    draw = ImageDraw.Draw(verso)

    # --- ANNÉE (Au centre, sur la frise) ---
    # y_frise est utilisé pour le positionnement de l'année, même sans frise
    y_frise = CENTRE_Y - 90 # Repositionnement de y_frise pour l'année
    draw.text((CENTRE_X, y_frise), annee_str, fill="black", font=font_annee, anchor="mm", stroke_width=8, stroke_fill="white")

    # --- DATE (Juste en dessous de l'année) ---
    # Date (Jour Mois)
    draw.text((CENTRE_X, y_frise + 90), jour_mois_str, fill="black", font=font_date, anchor="mt", stroke_width=5, stroke_fill="white")

    # --- TITRE & ARTISTE (Tout en BAS) ---
    # Titre
    draw.text((CENTRE_X, 720), row['Titre'], fill="black", font=font_texte, anchor="mm", stroke_width=3, stroke_fill="white")
    # Artiste (sous le titre)
    draw.text((CENTRE_X, 780), row['Artiste'], fill="black", font=font_texte, anchor="mm", stroke_width=3, stroke_fill="white")

    verso.save(f"./cartes_musiques/{music_id}_verso_{row['Titre']}.png")
    print(f"Carte {music_id} terminée.")