import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from .config import mistral_client


@dataclass
class GoldenSample:
    query: str
    ground_truth: str
    metadata: Optional[Dict] = None

    def to_dict(self):
        return asdict(self)


class SyntheticDatasetGenerator:

    def __init__(self):

        self.model = "mistral-large-latest"
        print("🧪 Générateur de questions de test initialisé (Evol-Instruct)")

    def extract_facts(self, document_text: str, max_facts: int = 5) -> List[str]:

        prompt = f"""Extrait {max_facts} informations clés de ce document juridique.

        Document: {document_text[:2000]}

        Format JSON: {{"facts": ["info 1", "info 2", ...]}}"""

        try:
            response = mistral_client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            facts = result.get("facts", [])
            print(f"   ✅ {len(facts)} informations extraites")
            return facts

        except Exception as e:
            print(f"   ❌ Erreur extraction: {e}")
            return []

    def generate_question(self, fact: str) -> str:
        prompt = f"""Crée une question SIMPLE à partir de cette information.

        Information: {fact}

        Question simple:"""

        try:
            response = mistral_client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )

            question = response.choices[0].message.content.strip()
            return question

        except Exception as e:
            print(f"   ❌ Erreur génération question: {e}")
            return ""

    def evolve_question(self, simple_question: str) -> str:
        prompt = f"""Rends cette question plus complexe en ajoutant du raisonnement. La question ne doit pas dépasser une phrase.

        Question simple: {simple_question}

        Question complexe (nécessite analyse et compréhension):"""

        try:
            response = mistral_client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )

            complex_question = response.choices[0].message.content.strip()
            return complex_question

        except Exception as e:
            print(f"   ❌ Erreur évolution question: {e}")
            return simple_question

    def generate_answer(self, document_text: str, question: str) -> str:

        prompt = f"""Réponds à cette question selon le document (2-3 phrases max).

        Document: {document_text[:2000]}

        Question: {question}

        Réponse:"""

        try:
            response = mistral_client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )

            answer = response.choices[0].message.content.strip()
            return answer

        except Exception as e:
            print(f"   ❌ Erreur génération réponse: {e}")
            return ""


class LLMJudge:

    def __init__(self):
        self.model = "mistral-large-latest"
        print("⚖️  LLM Judge initialisé")

    def judge_answer(self, query: str, answer: str, contexts: List[str]) -> Dict:

        contexts_text = "\n\n---\n\n".join(contexts[:3])

        prompt = f"""Note cette réponse sur 3 critères (0-10):

        1. FIDÉLITÉ: Basée sur les documents ?
        2. CLARTÉ: Bien écrite ?
        3. COMPLÉTUDE: Toutes les infos ?

        DOCUMENTS: 
        {contexts_text}

        QUESTION: {query}

        RÉPONSE: {answer}

        Format JSON:
        {{
            "fidelite": <0-10>,
            "clarte": <0-10>,
            "completude": <0-10>,
            "note_globale": <moyenne>,
            "explication": "..."
        }}
        """

        try:
            response = mistral_client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            scores = json.loads(response.choices[0].message.content)
            return scores

        except Exception as e:
            print(f"   ❌ Erreur jugement: {e}")
            return {
                "fidelite": 0,
                "clarte": 0,
                "completude": 0,
                "note_globale": 0,
                "explication": f"Erreur: {e}"
            }
