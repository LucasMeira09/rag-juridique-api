from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .reponse import Generation
from datetime import date
import time
import os

# uvicorn src.server.bridge:app --reload

app = FastAPI()

cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
if cors_origins_raw.strip() == "*":
    allow_origins = ["*"]
    allow_credentials = False
else:
    allow_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = Generation()

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Legal RAG API is running"}

class Query(BaseModel):
    query: str

@app.post("/search")
def search(data: Query):
    try:
        model_response, results = model.prompt_augmentation(data.query)

        if not results or not isinstance(results, dict) or not results.get("distances") or not results["distances"][0]:
            return {
                "results": [
                    {
                        "id": 1,
                        "title": f"Résultat pour '{data.query}'",
                        "excerpt": model_response if isinstance(model_response, str) else "Aucun résultat trouvé dans la base de données.",
                        "source": "Base de données",
                        "date": date.today().isoformat(),
                        "type": "Réponse IA",
                        "relevance": 50,
                        "link": "#"
                    }
                ]
            }

        distance = results["distances"][0][0]
        relevance = max(0, (2 - distance) / 2 * 100)
        
        metadatas = results.get("metadatas", [[]])[0]
        source = metadatas[0].get('source', 'Base de données') if metadatas and len(metadatas) > 0 else 'Base de données'
        
        if model_response == "rate":
            excerpt = "Le quota de requêtes Groq est temporairement atteint. Veuillez réessayer dans une minute."
        elif model_response == "error":
            excerpt = "Une erreur est survenue lors de l'appel à l'API LLM."
        else:
            excerpt = model_response

        return {
            "results": [
                {
                    "id": 1,
                    "title": f"Résultat pour '{data.query}'",
                    "excerpt": excerpt,
                    "source": source,
                    "date": date.today().isoformat(),
                    "type": "Réponse IA",
                    "relevance": round(relevance),
                    "link": "#"  
                }
            ]
        }
    except Exception as e:
        print(f"[API SEARCH ERROR]: {e}")
        return {
            "results": [
                {
                    "id": 1,
                    "title": f"Résultat pour '{data.query}'",
                    "excerpt": f"Erreur lors du traitement de la requête : {str(e)}",
                    "source": "Système",
                    "date": date.today().isoformat(),
                    "type": "Erreur",
                    "relevance": 0,
                    "link": "#"
                }
            ]
        }

@app.post("/admin/restart")
def trigger_restart():
    # Admin endpoint to restart the API container (called by pipeline after updates)
    import os
    import signal
    print("[ADMIN] Restart requested - shutting down to reload data...")
    os.kill(os.getpid(), signal.SIGTERM)
    return {"status": "restarting"}