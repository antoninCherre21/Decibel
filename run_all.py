import subprocess
import sys
import os


def detect_modes(base_dir: str) -> list:
    """Détecte automatiquement les modes disponibles dans le dossier modes/."""
    modes_dir = os.path.join(base_dir, "modes")
    if not os.path.isdir(modes_dir):
        return []
    return sorted([
        d for d in os.listdir(modes_dir)
        if os.path.isdir(os.path.join(modes_dir, d)) and not d.startswith('.')
    ])


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    print("=" * 60)
    print(" Bienvenue dans le processus global Décibel")
    print("=" * 60)

    modes_disponibles = detect_modes(base_dir)

    if not modes_disponibles:
        print("❌ Aucun mode trouvé dans le dossier 'modes/'. Abandon.")
        sys.exit(1)

    print("\nModes disponibles :")
    for i, m in enumerate(modes_disponibles):
        print(f"  {i+1}. {m}")

    choix = input("\nEntrez le numéro du mode à générer (défaut: 1) : ").strip()
    mode = modes_disponibles[0]
    if choix.isdigit() and 1 <= int(choix) <= len(modes_disponibles):
        mode = modes_disponibles[int(choix) - 1]

    print(f"\n🚀 Lancement du processus pour le mode : {mode.upper()}")

    scripts = [
        "scripts/0_recherche_API.py",
        "scripts/1_download.py",
        "scripts/2_Verification_BDD.py",
        "scripts/3_generer_qrcodes.py",
        "scripts/4_generer_cartes_musique.py",
        "scripts/5_generer_planche_impression.py"
    ]

    for script in scripts:
        print(f"\n{'=' * 60}")
        print(f"▶ Lancement de : {script}")
        print(f"{'=' * 60}\n")

        result = subprocess.run([sys.executable, script, "--mode", mode])

        if result.returncode != 0:
            if "2_Verification_BDD.py" in script:
                print(f"\n❌ Arrêt : des erreurs ont été détectées dans la base de données !")
                print(f"   -> Consultez 'modes/{mode}/erreurs.txt' pour les détails.")
                print(f"   -> Pour ignorer une erreur, copiez la ligne exacte dans 'modes/{mode}/erreurs_ignorees.txt'.")
                print(f"   -> Pour corriger manuellement, éditez 'modes/{mode}/db.json'.")
            else:
                print(f"\n❌ Erreur rencontrée lors de l'exécution de {script}.")

            print("\nArrêt du processus global.")
            sys.exit(result.returncode)

        print(f"\n✅ {script} terminé avec succès.")

    print(f"\n{'=' * 60}")
    print("🎉 Tous les scripts ont été exécutés avec succès !")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
