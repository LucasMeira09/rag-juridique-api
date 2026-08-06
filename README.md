# Semantic Search System for Legal Texts
This project implements a semantic search pipeline (RAG) using ChromaDB and SentenceTransformers to index and query legal documents.
> **New here?** Check out the [Quick Start Guide](docs/QUICKSTART.md)
## Features
- **PDF -> TXT Conversion**: Automatically extracts text from your PDFs
- **Smart Indexing**: Splits and indexes your documents with embeddings
- **Semantic Search**: Finds relevant passages even without exact keywords
- **Elegant Display**: Formatted results with relevance scores
- **REST API**: API interface with FastAPI for frontend integration
- **Avoids Duplicates**: Doesn't index the same content twice
## Prerequisites
- Python 3.8 or higher
- pip
## Quick Installation
### With Make (recommended)
```bash
# Install all dependencies
make install
# Activate the virtual environment
source venv/bin/activate
# Run the script
make run
```
### Manual installation
```bash
# Create a virtual environment
python3 -m venv venv
# Activate the environment
source venv/bin/activate
# Install dependencies
pip install -r requirements.txt
```
## Project Structure
```
formation-ai-/
├── src/                  # Code source de l'application
│   ├── bridge.py         # API FastAPI
│   ├── reponse.py        # Logique de generation de reponse
│   ├── traitement.py     # Pipeline RAG (Indexation & Recherche)
│   ├── scrap.py          # Scraper web
│   └── pdf_to_txt.py     # Convertisseur PDF vers TXT
├── data/                 # Donnees de l'application
│   ├── raw_pdfs/         # PDFs sources
│   ├── clean_data/       # Fichiers TXT indexes
│   ├── chroma_db/        # Base de donnees vectorielle
│   └── base_dechets.json # Base de connaissances JSON
├── docs/                 # Documentation
│   ├── EXEMPLES.md
│   └── QUICKSTART.md
├── requirements.txt      # Dependances
├── Makefile              # Automatisation
└── README.md             # Ce fichier
```

## Usage
### Step 1: Convert PDFs to TXT (optional)
1. Place your PDF files in the `data/raw_pdfs/` folder
2. Run the conversion:
```bash
make convert-pdf
# or
python -m src.pdf_to_txt
```
### Step 2: Semantic Search (CLI)
The `src/traitement.py` script allows you to query the database.
**Interactive mode:**
```bash
make run
# or
python -m src.traitement
```
**Single query:**
```bash
make query QUERY="which authority is responsible?"
# or
python -m src.traitement "which authority is responsible?"
```
### Step 3: Launch the API (Backend)
To use the application via a web interface or another client:
```bash
uvicorn src.bridge:app --reload
```
The API will be accessible at `http://127.0.0.1:8000`.
## Available Make Commands
- `make install` - Complete installation
- `make convert-pdf` - Converts PDFs to TXT
- `make run` - Interactive CLI mode
- `make query QUERY="..."` - CLI search
- `make clean` - Cleanup
- `make reset-db` - Database reset
## Main Dependencies
- **chromadb**: Vector database
- **sentence-transformers**: Embedding generation
- **fastapi**: API framework
- **pypdf**: PDF extraction
## Documentation
- [Search examples](docs/EXEMPLES.md)
- [Getting started guide](docs/QUICKSTART.md)
## Special mention 
-Tekno-Family -->https://teknofamily.be/
## OUR TEAM!!!
- https://github.com/LucasMeira09
- https://github.com/16050
