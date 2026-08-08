import os
import sys
import requests

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from .scrap import TextScrapper
from .traitement import RetrievalPipeline, list_files_local

def restart_api():
    """Trigger API restart via webhook to reload data"""
    try:
        print("\n[PIPELINE] Triggering API restart...")
        api_url = os.getenv("API_URL", "http://localhost:8000")
        requests.post(f"{api_url}/admin/restart", timeout=5)
        print("[PIPELINE] Restart signal sent!")
    except Exception as e:
        print(f"[PIPELINE] Warning: Failed to trigger API restart: {e}")

def run_pipeline():
    """Main pipeline orchestrator: scraping -> indexing"""
    print("="*80)
    print("   AUTOMATED PIPELINE START (SCRAP -> INDEX) ".center(80))
    print("="*80 + "\n")

    # STEP 1: SCRAPING
    print("--- STEP 1: SCRAPING & CONVERSION ---")
    
    urls = [
        "https://environnement.brussels/pro/gestion-environnementale/gerer-les-dechets/parcours-dechets-professionnels-reduire-trier-et-gerer-vos-dechets-bruxelles"
    ]
    
    total_new_files = 0
    
    for u in urls:
        print(f"\nProcessing URL: {u}")
        scrap = TextScrapper(u)
        
        scrap.download_text()
        scrap.pdf_to_txt()
        scrap.clean_text()
        scrap.clone_verifie()
        
        total_new_files += scrap.new_files_count

    print(f"\nTotal new files detected and converted: {total_new_files}")

    # STEP 2: INDEXING (CONDITIONAL)
    print("\n" + "="*80)
    if total_new_files > 0:
        print("   NEW FILES DETECTED -> STARTING INDEXATION ".center(80))
        print("="*80 + "\n")
        
        try:
            retrieval_pipeline = RetrievalPipeline()
            
            file_list = list_files_local(retrieval_pipeline.clean_data_dir)
            
            if not file_list:
                print("Warning: No files found in clean_data despite detecting new files.")
            else:
                print(f"Indexing {len(file_list)} files...")
                for file_name in file_list:
                    retrieval_pipeline.index_text(file_name)
            
            retrieval_pipeline.save()
            retrieval_pipeline.cleanup()
            
            # Trigger API restart after successful update
            restart_api()
            
            print("\n" + "="*80)
            print("   PIPELINE COMPLETED SUCCESSFULLY ".center(80))
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"\nCRITICAL ERROR DURING INDEXING: {e}")
            try:
                if 'retrieval_pipeline' in locals():
                    retrieval_pipeline.cleanup()
            except:
                pass
            sys.exit(1)
            
    else:
        print("   NO NEW FILES -> INDEXING SKIPPED ".center(80))
        print("="*80 + "\n")
        print("Pipeline completed normally without database update.")

if __name__ == "__main__":
    run_pipeline()
