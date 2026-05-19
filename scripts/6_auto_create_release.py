#!/usr/bin/env python3
"""
6_auto_create_release.py — Crée/met à jour les Releases GitHub Décibel.

Usage:
    python scripts/6_auto_create_release.py --mode music
    python scripts/6_auto_create_release.py --mode music --dry-run
    python scripts/6_auto_create_release.py --all-modes   # Met à jour le pack global tous modes
"""

import os
import sys
import zipfile
import subprocess
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import get_paths, load_json, save_json, get_available_modes

GITHUB_REPO = "antoninCherre21/Decibel"
WEBAPP_URL = "https://antonincherre21.github.io/Decibel/"


# ─────────────────────────── Helpers ────────────────────────────

def check_gh():
    """Vérifie que gh CLI est installé et authentifié."""
    try:
        r = subprocess.run(["gh", "auth", "status"], capture_output=True)
        if r.returncode != 0:
            print("❌  gh CLI non authentifié. Lancez : gh auth login")
            sys.exit(1)
    except FileNotFoundError:
        print("❌  gh CLI introuvable. Installez-le : https://cli.github.com/")
        sys.exit(1)


def make_zip(pdf_paths, zip_path):
    """Crée un ZIP contenant les PDFs donnés (noms de fichiers seulement, pas de sous-dossiers)."""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for p in pdf_paths:
            if os.path.exists(p):
                zf.write(p, os.path.basename(p))
    size_mb = os.path.getsize(zip_path) / 1_048_576
    print(f"   📦 ZIP créé : {os.path.basename(zip_path)} ({size_mb:.1f} Mo, {len(pdf_paths)} PDF)")
    return zip_path


def release_exists(tag):
    r = subprocess.run(
        ["gh", "release", "view", tag, "--repo", GITHUB_REPO],
        capture_output=True
    )
    return r.returncode == 0


def publish_release(tag, title, notes, assets, update=False, latest=False, dry_run=False):
    """Crée ou met à jour une Release GitHub."""
    if dry_run:
        action = "màj" if update else "création"
        print(f"   [DRY-RUN] {action} release → {tag}")
        return True

    if update and release_exists(tag):
        # Mettre à jour titre + notes
        subprocess.run([
            "gh", "release", "edit", tag,
            "--repo", GITHUB_REPO,
            "--title", title,
            "--notes", notes,
        ], capture_output=True)
        # Remplacer les assets
        r = subprocess.run(
            ["gh", "release", "upload", tag, "--repo", GITHUB_REPO, "--clobber"] + assets,
            capture_output=True, text=True
        )
    else:
        flags = ["--latest"] if latest else ["--latest=false"]
        r = subprocess.run(
            ["gh", "release", "create", tag,
             "--repo", GITHUB_REPO,
             "--title", title,
             "--notes", notes] + flags + assets,
            capture_output=True, text=True
        )

    if r.returncode != 0:
        print(f"   ⚠️  Erreur : {r.stderr.strip()}")
        return False
    return True


# ─────────────────────────── Notes ──────────────────────────────

def notes_pack(mode, pack_num, new_cards, new_planches):
    planche_list = "\n".join(f"- `{p['fichier']}`" for p in new_planches)
    return f"""## 🎵 Pack {pack_num} — Mode {mode.capitalize()}

**{new_cards} nouvelles cartes** ajoutées dans ce pack.

### Contenu
- {len(new_planches)} planche(s) PDF — format A4, recto/verso, 6 cartes par page
{planche_list}

### Utilisation
Imprimez uniquement ces planches pour compléter votre collection existante.
→ [Guide d'impression](https://github.com/{GITHUB_REPO}#%EF%B8%8F-comment-imprimer-ses-cartes-)

### Jouer
🌐 {WEBAPP_URL}
"""


def notes_complet(mode, total_cards, nb_planches, date_str):
    return f"""## 🎵 Pack Complet — Mode {mode.capitalize()}

Ce pack contient **la totalité des cartes** du mode, toujours à jour.

### Contenu
- **{total_cards} cartes** au total
- {nb_planches} planches PDF (A4, recto/verso, 6 cartes par page)
- Mis à jour le : {date_str}

> ⚠️ Ce pack est remplacé à chaque ajout. Pour ne télécharger que les nouveautés, utilisez les packs incrémentiaux (`{mode}-pack-XXX`).

### Imprimer
→ [Guide d'impression](https://github.com/{GITHUB_REPO}#%EF%B8%8F-comment-imprimer-ses-cartes-)

### Jouer
🌐 {WEBAPP_URL}
"""


def notes_all(modes_summary, date_str):
    lines = "\n".join(f"- **{m}** : {c} cartes" for m, c in modes_summary)
    total = sum(c for _, c in modes_summary)
    return f"""## 🎮 Pack Global — Tous les Modes

Ce pack regroupe **tous les modes de jeu** en un seul téléchargement.

### Contenu
{lines}
**Total : {total} cartes**
- Mis à jour le : {date_str}

### Imprimer
→ [Guide d'impression](https://github.com/{GITHUB_REPO}#%EF%B8%8F-comment-imprimer-ses-cartes-)

### Jouer
🌐 {WEBAPP_URL}
"""


# ─────────────────────────── Core ───────────────────────────────

def process_mode(mode, dry_run=False, complete_only=False):
    """Traite un mode : pack incrémental + pack complet."""
    paths = get_paths(mode)
    planches_dir = paths.get("planches_extraits", os.path.join(paths["planches"], "extraits"))
    planches_chances_dir = paths.get("planches_chances", os.path.join(paths["planches"], "chances"))
    tracking = load_json(paths["planches_suivi"], default={"planches": [], "release_packs": []})
    all_planches = tracking.get("planches", [])
    release_packs = tracking.get("release_packs", [])

    # IDs déjà publiés dans un pack
    published_ids = {pid for pack in release_packs for pid in pack.get("planche_ids", [])}

    available = []       # (meta_dict, pdf_path)
    new_planches = []

    for p in all_planches:
        pdf_path = os.path.join(planches_dir, p["fichier"])
        if os.path.exists(pdf_path):
            available.append((p, pdf_path))
            if p["planche"] not in published_ids:
                new_planches.append((p, pdf_path))

    total_cards = sum(len(p[0].get("card_ids", [])) for p in available)
    new_cards = sum(len(p[0].get("card_ids", [])) for p in new_planches)
    date_str = datetime.now().strftime("%d/%m/%Y")

    print(f"\n{'─'*50}")
    print(f"  Mode : {mode.upper()}")
    print(f"  Planches disponibles  : {len(available)} ({total_cards} cartes)")
    print(f"  Nouvelles non publiées: {len(new_planches)} ({new_cards} cartes)")

    # ── Pack incrémental ──────────────────────────────────────
    if not complete_only and new_planches:
        pack_num = len(release_packs) + 1
        tag = f"{mode}-pack-{pack_num:03d}"
        title = f"🎵 {mode.capitalize()} — Pack {pack_num} (+{new_cards} cartes · {date_str})"
        zip_path = os.path.join(planches_dir, f"pack_{pack_num:03d}_{mode}.zip")
        make_zip([p[1] for p in new_planches], zip_path)

        print(f"\n  ▶ Création release incrémentale : {tag}")
        ok = publish_release(tag, title,
                             notes_pack(mode, pack_num, new_cards, [p[0] for p in new_planches]),
                             [zip_path], update=False, dry_run=dry_run)
        if ok and not dry_run:
            tracking["release_packs"].append({
                "pack": pack_num,
                "tag": tag,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "planche_ids": [p[0]["planche"] for p in new_planches],
                "cards_count": new_cards,
            })
            save_json(tracking, paths["planches_suivi"])
            print(f"  ✅ Pack {pack_num} publié → {tag}")
    elif not complete_only:
        print("\n  ℹ️  Aucune nouvelle planche → pas de pack incrémental.")

    # ── Pack complet ──────────────────────────────────────────
    if available:
        tag_c = f"{mode}-complet"
        title_c = f"🎵 {mode.capitalize()} — Pack Complet ({total_cards} cartes)"
        zip_c = os.path.join(paths["planches"], f"pack_complet_{mode}.zip")
        
        all_pdfs = [p[1] for p in available]
        # Ajouter les planches chances s'il y en a
        if os.path.exists(planches_chances_dir):
            for f in os.listdir(planches_chances_dir):
                if f.endswith(".pdf"):
                    all_pdfs.append(os.path.join(planches_chances_dir, f))
                    
        make_zip(all_pdfs, zip_c)

        print(f"\n  ▶ Mise à jour pack complet : {tag_c}")
        ok = publish_release(tag_c, title_c,
                             notes_complet(mode, total_cards, len(available), date_str),
                             [zip_c], update=True, dry_run=dry_run)
        if ok:
            print(f"  ✅ Pack complet mis à jour → {tag_c}")

    return mode, total_cards, [p[1] for p in available]


def process_all_modes(dry_run=False):
    """Met à jour le pack global tous modes."""
    modes = get_available_modes()
    all_pdfs = []
    summary = []
    date_str = datetime.now().strftime("%d/%m/%Y")

    for mode in modes:
        paths = get_paths(mode)
        tracking = load_json(paths["planches_suivi"], default={"planches": []})
        planches_dir = paths.get("planches_extraits", os.path.join(paths["planches"], "extraits"))
        planches_chances_dir = paths.get("planches_chances", os.path.join(paths["planches"], "chances"))
        total = 0
        for p in tracking.get("planches", []):
            pdf_path = os.path.join(planches_dir, p["fichier"])
            if os.path.exists(pdf_path):
                all_pdfs.append(pdf_path)
                total += len(p.get("card_ids", []))
        
        if os.path.exists(planches_chances_dir):
            for f in os.listdir(planches_chances_dir):
                if f.endswith(".pdf"):
                    all_pdfs.append(os.path.join(planches_chances_dir, f))

        summary.append((mode, total))

    if not all_pdfs:
        print("❌ Aucune planche trouvée dans les modes disponibles.")
        return

    # Créer le ZIP global dans le dossier du premier mode (ou racine)
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    zip_all = os.path.join(base, "pack_complet_all_modes.zip")
    make_zip(all_pdfs, zip_all)

    total_all = sum(c for _, c in summary)
    tag = "all-complet"
    title = f"🎮 Tous les Modes — Pack Complet ({total_all} cartes)"

    print(f"\n  ▶ Mise à jour pack global : {tag}")
    ok = publish_release(tag, title,
                         notes_all(summary, date_str),
                         [zip_all], update=True, dry_run=dry_run)
    if ok:
        print(f"  ✅ Pack global mis à jour → {tag}")


# ─────────────────────────── Main ───────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Crée/met à jour les Releases GitHub Décibel"
    )
    parser.add_argument("--mode", type=str,
                        help="Mode à publier (ex: music). Omettez avec --all-modes.")
    parser.add_argument("--all-modes", action="store_true",
                        help="Met à jour le pack global tous modes uniquement.")
    parser.add_argument("--complete-only", action="store_true",
                        help="Met à jour uniquement le pack complet (pas de nouveau pack incrémental).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simule sans appeler l'API GitHub.")
    args = parser.parse_args()

    if not args.mode and not args.all_modes:
        parser.print_help()
        sys.exit(1)

    if not args.dry_run:
        check_gh()

    if args.all_modes:
        process_all_modes(dry_run=args.dry_run)
    else:
        process_mode(args.mode, dry_run=args.dry_run, complete_only=args.complete_only)

    print("\n🎉 Terminé !")


if __name__ == "__main__":
    main()
