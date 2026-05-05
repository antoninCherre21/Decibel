"""
utils.py — Fonctions utilitaires partagées entre tous les scripts Décibel.
Usage : from utils import get_paths, load_json, save_json, log_error
"""
import os
import json


def get_paths(mode: str) -> dict:
    """
    Retourne un dictionnaire de tous les chemins importants pour un mode donné.
    Usage : paths = get_paths("music")
    """
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mode_dir = os.path.join(base, "modes", mode)
    return {
        "base": base,
        "mode_dir": mode_dir,
        "db": os.path.join(mode_dir, "db.json"),
        "genres": os.path.join(mode_dir, "genres.json"),
        "to_add": os.path.join(mode_dir, "to_add.json"),
        "errors": os.path.join(mode_dir, "erreurs.txt"),
        "ignored_errors": os.path.join(mode_dir, "erreurs_ignorees.txt"),
        "stats": os.path.join(mode_dir, "stats.json"),
        "prov": os.path.join(base, "scripts", f"{mode}_playlist_prov.json"),
        "assets": os.path.join(mode_dir, "assets"),
        "audio": os.path.join(mode_dir, "assets", "fichiers_audio"),
        "pochettes": os.path.join(mode_dir, "assets", "pochettes"),
        "exports": os.path.join(mode_dir, "exports"),
        "qrcodes": os.path.join(mode_dir, "exports", "qrcodes"),
        "cartes": os.path.join(mode_dir, "exports", "cartes"),
        "planches_suivi": os.path.join(mode_dir, "exports", "planches_suivi.json"),
        "img": os.path.join(mode_dir, "img"),  # Ressources statiques du mode (templates, logos)
    }


def load_json(filepath: str, default=None):
    """
    Charge un fichier JSON. Retourne `default` si le fichier est absent ou vide.
    """
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return default if default is not None else []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️  Erreur lecture JSON ({filepath}): {e}")
        return default if default is not None else []


def save_json(data, filepath: str):
    """
    Sauvegarde des données Python en JSON formaté (indent=4, UTF-8).
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def log_error(message: str, errors_path: str):
    """
    Ajoute une erreur dans le fichier d'erreurs du mode.
    """
    os.makedirs(os.path.dirname(errors_path), exist_ok=True)
    with open(errors_path, 'a', encoding='utf-8') as f:
        f.write(message + "\n")


def safe_filename(name: str) -> str:
    """
    Nettoie un nom pour l'utiliser comme nom de fichier.
    """
    return "".join([c for c in str(name) if c.isalnum() or c in [' ', '-', '_']]).strip().replace(' ', '_')


def get_available_modes() -> list:
    """
    Détecte automatiquement les modes disponibles dans le dossier modes/.
    Fonctionne que le script soit appelé depuis la racine ou depuis scripts/.
    """
    # Cherche le dossier modes/ depuis le script courant
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)  # remonte d'un niveau (scripts/ -> racine)
    modes_dir = os.path.join(base_dir, "modes")
    if not os.path.isdir(modes_dir):
        return ["music"]
    return sorted([
        d for d in os.listdir(modes_dir)
        if os.path.isdir(os.path.join(modes_dir, d)) and not d.startswith('.')
    ])


def get_mode_arg() -> str:
    """
    Parse l'argument --mode depuis la ligne de commande.
    Détecte automatiquement les modes disponibles et les affiche dans le --help.
    """
    import argparse
    modes = get_available_modes()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        type=str,
        default=modes[0] if modes else "music",
        choices=modes,
        help=f"Mode de jeu. Disponibles : {', '.join(modes)}"
    )
    return parser.parse_args().mode
