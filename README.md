# Systeme de Recherche Semantique pour Textes Juridiques

Ce projet implemente un pipeline de recherche semantique (RAG) utilisant ChromaDB et SentenceTransformers pour indexer et interroger des documents juridiques.

> **Nouveau ?** Consultez le [Guide de demarrage rapide](docs/QUICKSTART.md)

## Fonctionnalites

- **Conversion PDF -> TXT** : Extrait automatiquement le texte de vos PDFs
- **Indexation intelligente** : Decoupe et indexe vos documents avec des embeddings
- **Recherche semantique** : Trouve les passages pertinents meme sans mots-cles exacts
- **Affichage elegant** : Resultats formates avec scores de pertinence
- **API REST** : Interface API avec FastAPI pour integration frontend
- **Evite les doublons** : N'indexe pas deux fois le meme contenu

## Prerequis

- Python 3.8 ou superieur
- pip

## Installation rapide

### Avec Make (recommande)

```bash
# Installer toutes les dependances
make install

# Activer l'environnement virtuel
source venv/bin/activate

# Executer le script
make run
```

### Installation manuelle

```bash
# Creer un environnement virtuel
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate

# Installer les dependances
pip install -r requirements.txt
```

## Structure du projet

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

## Utilisation

### Etape 1 : Convertir les PDFs en TXT (optionnel)

1. Placez vos fichiers PDF dans le dossier `data/raw_pdfs/`
2. Lancez la conversion :

```bash
make convert-pdf
# ou
python -m src.pdf_to_txt
```

### Etape 2 : Recherche semantique (CLI)

Le script `src/traitement.py` permet d'interroger la base de donnees.

**Mode interactif :**
```bash
make run
# ou
python -m src.traitement
```

**Requete unique :**
```bash
make query QUERY="quelle autorite est responsable ?"
# ou
python -m src.traitement "quelle autorite est responsable ?"
```

### Etape 3 : Lancer l'API (Backend)

Pour utiliser l'application via une interface web ou un autre client :

```bash
uvicorn src.bridge:app --reload
```
L'API sera accessible sur `http://127.0.0.1:8000`.

## Commandes Make disponibles

- `make install` - Installation complete
- `make convert-pdf` - Convertit les PDFs en TXT
- `make run` - Mode interactif CLI
- `make query QUERY="..."` - Recherche CLI
- `make clean` - Nettoyage
- `make reset-db` - Reinitialisation de la base de donnees

## Dependances principales

- **chromadb** : Base de donnees vectorielle
- **sentence-transformers** : Generation d'embeddings
- **fastapi** : Framework API
- **pypdf** : Extraction PDF

## Documentation

- [Exemples de recherche](docs/EXEMPLES.md)
- [Guide de demarrage](docs/QUICKSTART.md)

## OUR TEAM!!!

- https://github.com/LucasMeira09
- https://github.com/16050
- 
