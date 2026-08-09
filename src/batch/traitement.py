import chromadb 
from fastembed import TextEmbedding
import os
from pathlib import Path
import json
import unicodedata
import re
from groq import Groq, RateLimitError
from dotenv import load_dotenv
import time

load_dotenv()

# local config
# Racine du projet (2 niveaux au-dessus de src/batch/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = os.getenv("DATA_DIR", str(_PROJECT_ROOT / "data"))

CLEAN_DIR = os.path.join(DATA_DIR, "clean_data")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(DATA_DIR, "chroma_db"))


def list_files_local(directory_path):
    #  Liste tous les fichiers dans un répertoire local
    try:
        if not os.path.isdir(directory_path):
            return []
        return [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    except Exception:
        return []

def read_text_local(file_path):
    # Lit un fichier texte local et retourne son contenu
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Erreur lors de la lecture: {e}")
        return None

class RetrievalPipeline:
    def __init__(self):
        # Initialise le modèle fastembed pour les embeddings de texte
        self.model = TextEmbedding(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            threads=1,
            providers=["CPUExecutionProvider"]
        )

        groq_key = os.getenv("GROQ_KEY")
        self.client = Groq(api_key=groq_key)

        #base du projet ou ce fichier ce trouve
        self.base_dir = Path(__file__).resolve().parent
        self.project_root = self.base_dir.parent

        # Chemins locaux pour les dossiers
        self.clean_data_dir = CLEAN_DIR
        
        # Créer les dossiers si nécessaire
        os.makedirs(CLEAN_DIR, exist_ok=True)
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)
        
        print(f"Initialisation: Chargement de ChromaDB depuis {CHROMA_DB_PATH}")
        
        # Crée ou connecte une base de données Chroma persistante au chemin local
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        # Récupère ou crée une collection dans la base appelée "law_text"
        self.collection = self.chroma_client.get_or_create_collection(
            name="law_text",
            metadata={"hnsw:space": "cosine"}
        )
        self.categories_collection = self.chroma_client.get_or_create_collection(
            name="categories",
            metadata={"hnsw:space": "cosine"}
        )

    def save(self):
        # No-op — PersistentClient sauvegarde automatiquement sur disque.
        print("Sauvegarde: ChromaDB persiste automatiquement sur disque local.")

    def cleanup(self):
        # No-op — la base locale persiste sur disque.
        pass

    def find_category(self, text):
        # trouve la categorie aproximatif
        
        similarity_threshold = 0.45

        doc_embedding = list(self.model.embed([text[:3000]]))[0]

        existing_count = self.categories_collection.count()
        if existing_count > 0:
            result = self.categories_collection.query(
                query_embeddings=[doc_embedding],
                n_results= 1
            )

            if result["distances"][0]:
                best_distance = result["distances"][0][0]
                best_category = result["metadatas"][0][0]["name"]
                if best_distance <= similarity_threshold:
                    return best_category

        category_name = self.ask_llm_for_new_category_name(text)

        if category_name == "Rate":
            time.sleep(60)


        category_name = category_name.strip().lower()
        category_name = unicodedata.normalize('NFKD', category_name).encode('ascii', 'ignore').decode('ascii')
        
        category_id = re.sub(r'\s+', '_', category_name)
        self.categories_collection.add(
            ids=[category_id],
            embeddings=[doc_embedding],
            metadatas=[{"name" : category_name}]
        )

        return category_name

    def ask_llm_for_new_category_name(self, text):

        prompt = f"""
            Tu catégorises des documents juridiques liés aux déchets.
            Donne UNE SEULE catégorie courte (2 à 4 mots, en français) qui résume
            le sujet juridique de cet extrait. Pas de phrase, pas d'explication.

            Extrait :
            {text[:1500]}

            Réponds uniquement par le nom de la catégorie.
        """

        try:
                
            model_response = self.client.chat.completions.create(
                messages=[
                    {
                        "role" : "user",
                        "content" : prompt
                    }
                ],
                model="llama-3.1-8b-instant"
            )

            return model_response.choices[0].message.content

        except RateLimitError as e:
            return "Rate"
        
        except Exception as e:
            return str(e)


    def chunking(self, text, chunk_size=450, overlap=50):
        # Divise un texte long en petits segments qui se chevauchent pour une meilleure qualité d'embedding
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            # si le chunk est assez grand, on le garde
            if len(chunk) >= 250:
                chunks.append(chunk)

            # Déplace la fenêtre vers l'avant, en gardant un chevauchement pour préserver le contexte
            start += chunk_size - overlap

        return chunks

    def index_text(self, file_name):
        """
        Indexe un fichier texte local
        
        Args:
            file_name: Nom du fichier dans le dossier clean_data (ex: "document.txt")
        """
        # Construit le chemin complet local
        local_file_path = os.path.join(self.clean_data_dir, file_name)
        
        # Lit le contenu du fichier texte local
        text_law = read_text_local(local_file_path)
        if text_law is None:
            print(f"Erreur: Impossible de lire {file_name}.")
            return

        # Divise le texte en segments
        chunks = self.chunking(text_law)
        # Récupère le nom du fichier (sans extension) pour l'utiliser comme identifiant unique
        file_id = os.path.splitext(file_name)[0]
        # ajuster le nom
        if len(file_id) > 60:
            file_id = file_id[0:60]+"..."
        #essaye de recuperer la date
        pattern = r"(janv|fevr|mars|avr|mai|juin|juil|aout|sept|oct|nov|dec)[\s\-]+[0-9]{4}"
        # essaye de trouve une date au debut du texte
        match = re.search(pattern, text_law[:100], re.IGNORECASE)
        # si match = True return la date recupere
        if match:
            date = match.group(0)
        else:
            date="unknow"
        # Récupère les identifiants de documents existants dans la collection Chroma pour éviter les doublons
        existing_ids = set(self.collection.get()["ids"])
        new_chunks = 0
        
        idx = len(existing_ids)

        # Boucle sur tous les segments du fichier
        for i, chunk in enumerate(chunks):
            idx += 1
            # Crée un identifiant unique pour chaque segment basé sur le nom du fichier et son index
            chunk_id = f"{file_id}_chunk_{i}" 
            # recupere la categorie
            category = self.find_category(chunk)     
            # Passe ce segment s'il est déjà indexé
            if chunk_id in existing_ids:
                continue
            
            # Génère un embedding pour le segment à l'aide du modèle
            embedding = list(self.model.embed([chunk]))[0]
            # Ajoute le segment, son embedding et ses métadonnées (chemin du fichier) à la collection
            self.collection.add(
                ids=[chunk_id],
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[{"source": file_id, "categorie": category, "date": date, "chunk_id":idx}]
            )
            new_chunks += 1

if __name__ == "__main__":
    # Initialise le pipeline de recherche
    retrieval_pipeline = RetrievalPipeline()
    
    try:
        # Parcourt tous les fichiers texte dans le dossier 'clean_data' local et les indexe
        file_list = list_files_local(retrieval_pipeline.clean_data_dir)
        
        if not file_list:
            print(f"Aucun fichier trouvé dans {retrieval_pipeline.clean_data_dir}/")
            print("Assurez-vous que les fichiers ont été traités par scrap.py.")
        else:
            print(f"Trouvé {len(file_list)} fichier(s) à indexer dans {retrieval_pipeline.clean_data_dir}/")
            for file_name in file_list:
                print(f"Indexation de: {file_name}")
                retrieval_pipeline.index_text(file_name)
        
        # Sauvegarde (no-op, PersistentClient persiste automatiquement)
        retrieval_pipeline.save()
        
    finally:
        # Nettoyage (no-op en local)
        retrieval_pipeline.cleanup()
