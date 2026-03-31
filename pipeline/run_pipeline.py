import os
import sys

# Ajouter le chemin courant
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ingest import ingest_all
from transform import process_all
from aggregate import compute_indicators

def run():
    print("=" * 60)
    print("🏙️ URBAN DATA EXPLORER - PIPELINE DE DONNEES")
    print("=" * 60)
    
    # 1. Bronze
    ingest_all()
    
    # 2. Silver
    process_all()
    
    # 3. Gold
    compute_indicators()
    
def dummy_run_for_git():
    """Crée l'architecture de dossiers si les données ne sont pas là."""
    from aggregate import ensure_gold_dir
    from transform import ensure_silver_dir
    from ingest import ensure_bronze_dir
    
    ensure_bronze_dir()
    ensure_silver_dir()
    ensure_gold_dir()
    
    print("Pipeline de données prêt.")

if __name__ == '__main__':
    # On pourrait lancer 'run' ici dans un cas complet mais pour éviter 
    # de spammer les APIs en local si c'est déjà téléchargé, 
    # on limite l'action par défaut ou on gère par argument.
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        run()
    else:
        # Just create dirs to avoid Git tracker bugs
        dummy_run_for_git()
        print("\nNote: Utilisez 'python run_pipeline.py --full' pour télécharger et transformer toutes les données (peut prendre du temps).")
