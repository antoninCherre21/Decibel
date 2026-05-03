import subprocess
import sys
import os

def main():
    # Liste des scripts à exécuter dans l'ordre
    scripts = [
        "scripts/0_recherche_API.py",
        "scripts/1_download.py",
        "scripts/2_Vérification_csv.py",
        "scripts/3_generer_qrcodes.py",
        "scripts/4_generer_cartes_musique.py",
        "scripts/5_generer_planche_impression.py"
    ]

    # On s'assure d'être à la racine du projet
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    print("Début du processus global Decibel...")
    
    for script in scripts:
        print(f"\n{'='*60}")
        print(f"▶ Lancement de : {script}")
        print(f"{'='*60}\n")
        
        # Exécution du script avec l'exécutable Python actuel
        result = subprocess.run([sys.executable, script])
        
        # Vérification si le script s'est bien terminé
        if result.returncode != 0:
            print(f"\n❌ Erreur rencontrée lors de l'exécution de {script}.")
            print("Arrêt du processus global.")
            sys.exit(result.returncode)
            
        print(f"\n✅ {script} terminé avec succès.")

    print(f"\n{'='*60}")
    print("🎉 Tous les scripts ont été exécutés avec succès !")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
