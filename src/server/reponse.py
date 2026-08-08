from dotenv import load_dotenv
import os
from groq import Groq, RateLimitError
import time
from .query_search import QuerySearch

load_dotenv()

class Generation:
    # Handles LLM response generation using Groq free api
    
    def __init__(self):
        groq_key = os.getenv("GROQ_KEY", "")
        self.client = Groq(api_key=groq_key) if groq_key else None
        self.pipeline = QuerySearch()

    def question_subject(self, query):
        if not self.client:
            return "AUCUNE"

        category_names = self.pipeline.get_category_names()

        if not category_names:
            category_names = ["aucune"]

        name_list = ", ".join(category_names)
        
        prompt = f"""
                Voici une liste de catégories juridiques : {name_list}

                Question de l'utilisateur : {query}

                À quelle catégorie de cette liste cette question correspond-elle le mieux ?
                Réponds UNIQUEMENT avec le nom exact d'une catégorie de la liste, copié tel quel.
                Si aucune catégorie ne correspond clairement, réponds uniquement : AUCUNE
            """
            
        try:
            model_response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query}
                ],
                model="llama-3.1-8b-instant"
            )

            return model_response.choices[0].message.content
        except RateLimitError:
            return "Rate"
        except Exception as e:
            print(f"[REPONSE ERROR] question_subject: {e}")
            return "AUCUNE"
              
    def prompt_augmentation(self, query):
        # Generate an answer based on retrieved documents directly using vector search
        search_res = self.pipeline.query_search_db(query)

        if not search_res or not search_res[0]:
            return "Aucune information pertinente trouvée dans la base de données.", None

        response, results = search_res
        context_text = "\n\n---\n\n".join(response)

        if not self.client:
            return "Erreur: Clé GROQ_KEY absente dans la configuration du serveur.", results

        prompt = f"""
                Tu es un assistant qui répond uniquement à partir des documents suivants.
                N'ajoute aucune information, supposition ou connaissance extérieure.
                Si les documents ne contiennent pas suffisamment d'information pour répondre complètement,
                répond exactement : "Aucune information pertinente trouvée dans les documents."

                Règles à suivre :
                1. Utilise exclusivement les faits présents dans les documents ci-dessous, sans dire :"selon les documents fournis"
                2. Si une idée ou phrase ne provient pas clairement des documents, NE L'ÉCRIS PAS.
                3. Si la réponse ne peut pas être déduite directement des documents, réponds exactement :
                "Aucune information pertinente trouvée dans les documents."
                4. Ne fais aucun raisonnement ou hypothèse non soutenu par les documents.

                Ta tâche :
                - Lis attentivement les documents suivants :
                {context_text}

                - Puis, réponds strictement à la question ci-dessous.
                - Si la réponse n'est pas clairement présente ou déductible des documents, réponds uniquement :
                "Aucune information pertinente trouvée dans les documents."

                Ta réponse finale :
        """
        
        try:
            model_response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query}
                ],
                model="llama-3.1-8b-instant"
            )

            return model_response.choices[0].message.content, results

        except RateLimitError:
            return "rate", results
        except Exception as e:
            print(f"[LLM ERROR]: {e}")
            return "error", results