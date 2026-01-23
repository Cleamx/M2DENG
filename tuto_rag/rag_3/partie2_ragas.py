#!/usr/bin/env python3
"""
PARTIE 2 du TP RAGOps: Évaluer avec Ragas
Calcule 4 métriques: context_precision, context_recall, faithfulness, answer_relevancy
"""
import json
import os
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy
)
from ragas.llms import LangchainLLMWrapper
from langchain_mistralai import ChatMistralAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from legal_rag.pipeline import LegalIngestionPipeline
from legal_rag.generation import LegalAnswerGenerator
from legal_rag.evaluation import GoldenSample
from dotenv import load_dotenv
import sys

# Charger les variables d'environnement depuis la racine du projet
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)


# Couleurs pour l'affichage
class Colors:
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    CYAN = '\033[96m'


def load_golden_dataset(filepath="golden_dataset.json"):
    """Charge le dataset de questions de test."""
    print("📚 Chargement du golden dataset...")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    samples = [GoldenSample(**item) for item in data]
    print(f"  ✅ {len(samples)} questions chargées\n")
    return samples


def prepare_ragas_dataset(samples, pipeline, generator):
    """
    ÉTAPE 5 : Préparer les données pour Ragas.
    
    Pour chaque question:
    1. Lancer le RAG (recherche + génération)
    2. Récupérer les documents trouvés
    3. Récupérer la réponse générée
    4. Mettre tout dans un tableau
    """
    print("=" * 80)
    print("  ÉTAPE 5: PRÉPARATION DES DONNÉES POUR RAGAS")
    print("=" * 80)
    print("\n🔄 Exécution du RAG sur chaque question...\n")
    
    # Tableau vide
    data = {
        'question': [],
        'contexts': [],      # Les documents trouvés
        'answer': [],        # La réponse générée
        'ground_truth': []   # La réponse attendue
    }
    
    # Pour chaque question
    for i, sample in enumerate(samples, 1):
        print(f"[{i}/{len(samples)}] {sample.query[:60]}...")
        
        try:
            # 1. Recherche
            results = pipeline.search(sample.query, n_results=5)
            
            # 2. Génération
            answer = generator.generate_answer(sample.query, results)
            
            # 3. Ajout au tableau
            data['question'].append(sample.query)
            data['contexts'].append(results['documents'][0] if results['documents'] else [])
            data['answer'].append(answer)
            data['ground_truth'].append(sample.ground_truth)
            
            print(f"  ✅ OK\n")
            
        except Exception as e:
            print(f"  ❌ Erreur: {e}\n")
            # Valeurs par défaut
            data['question'].append(sample.query)
            data['contexts'].append([])
            data['answer'].append("Erreur")
            data['ground_truth'].append(sample.ground_truth)
    
    # Conversion pour Ragas
    dataset = Dataset.from_dict(data)
    print(f"✅ Dataset Ragas préparé: {len(dataset)} entrées\n")
    
    return dataset


def run_ragas_evaluation(dataset):
    """
    ÉTAPE 6 : Lancer l'évaluation Ragas.
    
    Calcule 4 métriques:
    - context_precision: Qualité des documents (pertinents?)
    - context_recall: Couverture (tous les docs nécessaires?)
    - faithfulness: Pas d'hallucinations?
    - answer_relevancy: Réponse claire et pertinente?
    """
    print("=" * 80)
    print("  ÉTAPE 6: ÉVALUATION RAGAS")
    print("=" * 80)
    print("\n📊 Métriques:")
    print("  1. context_precision  : Qualité Retriever")
    print("  2. context_recall     : Couverture Retriever")
    print("  3. faithfulness       : Pas d'hallucination")
    print("  4. answer_relevancy   : Pertinence réponse")
    
    print("\n⚙️ Configuration de Ragas avec Mistral AI...")
    
    # Récupérer la clé Mistral (compatible avec config.py qui utilise "key")
    mistral_api_key = os.getenv("key") or os.getenv("MISTRAL_API_KEY")
    
    if not mistral_api_key:
        print("❌ Clé API Mistral introuvable dans .env")
        print("   Vérifiez que 'key=...' ou 'MISTRAL_API_KEY=...' existe dans .env")
        return None
    
    print(f"  ✅ Clé API trouvée: {mistral_api_key[:8]}...")
    
    try:
        # Configuration du LLM Mistral pour Ragas
        mistral_llm = ChatMistralAI(
            model="mistral-large-latest",
            api_key=mistral_api_key,
            temperature=0.0
        )
        
        # Wrapper pour Ragas
        ragas_llm = LangchainLLMWrapper(mistral_llm)
        
        # Embeddings locaux (HuggingFace)
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        print("  ✅ Mistral AI configuré\n")
        print("⏳ Évaluation en cours (peut prendre 5-10 minutes)...\n")
        
        # Évaluation avec le LLM et embeddings personnalisés
        result = evaluate(
            dataset,
            metrics=[
                context_precision,
                context_recall,
                faithfulness,
                answer_relevancy
            ],
            llm=ragas_llm,
            embeddings=embeddings
        )
        return result
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'évaluation: {e}")
        import traceback
        traceback.print_exc()
        return None


def display_results(result):
    """ÉTAPE 7 : Afficher et interpréter les résultats."""
    if not result:
        return None
    
    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}  RÉSULTATS RAGAS{Colors.ENDC}")
    print("=" * 80 + "\n")
    
    # Récupérer les scores (result est un objet EvaluationResult avec attributs)
    scores = {
        'context_precision': getattr(result, 'context_precision', 0),
        'context_recall': getattr(result, 'context_recall', 0),
        'faithfulness': getattr(result, 'faithfulness', 0),
        'answer_relevancy': getattr(result, 'answer_relevancy', 0)
    }
    
    # Affichage formaté
    print(f"Qualité Retriever    : {scores['context_precision']:.2f}", end="")
    if scores['context_precision'] >= 0.80:
        print(f" {Colors.GREEN}✅ Excellent{Colors.ENDC}")
    elif scores['context_precision'] >= 0.60:
        print(f" {Colors.WARNING}⚠️  Correct{Colors.ENDC}")
    else:
        print(f" {Colors.FAIL}❌ À améliorer{Colors.ENDC}")
    
    print(f"Couverture Retriever : {scores['context_recall']:.2f}", end="")
    if scores['context_recall'] >= 0.80:
        print(f" {Colors.GREEN}✅ Excellent{Colors.ENDC}")
    elif scores['context_recall'] >= 0.60:
        print(f" {Colors.WARNING}⚠️  Correct{Colors.ENDC}")
    else:
        print(f" {Colors.FAIL}❌ À améliorer{Colors.ENDC}")
    
    print(f"Pas d'hallucination  : {scores['faithfulness']:.2f}", end="")
    if scores['faithfulness'] >= 0.80:
        print(f" {Colors.GREEN}✅ Excellent{Colors.ENDC}")
    elif scores['faithfulness'] >= 0.60:
        print(f" {Colors.WARNING}⚠️  Correct{Colors.ENDC}")
    else:
        print(f" {Colors.FAIL}❌ À améliorer{Colors.ENDC}")
    
    print(f"Pertinence réponse   : {scores['answer_relevancy']:.2f}", end="")
    if scores['answer_relevancy'] >= 0.80:
        print(f" {Colors.GREEN}✅ Excellent{Colors.ENDC}")
    elif scores['answer_relevancy'] >= 0.60:
        print(f" {Colors.WARNING}⚠️  Correct{Colors.ENDC}")
    else:
        print(f" {Colors.FAIL}❌ À améliorer{Colors.ENDC}")
    
    # Note moyenne
    avg = sum(scores.values()) / len(scores)
    print(f"\n{Colors.BOLD}Note moyenne : {avg:.2f}{Colors.ENDC}")
    
    # Diagnostic
    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}  DIAGNOSTIC{Colors.ENDC}")
    print("=" * 80 + "\n")
    
    min_metric = min(scores, key=scores.get)
    min_score = scores[min_metric]
    
    print(f"{Colors.WARNING}📌 Point faible principal:{Colors.ENDC}")
    print(f"   {min_metric}: {min_score:.2f}\n")
    
    # Recommandations
    recommendations = {
        'context_precision': [
            "Votre RAG trouve trop de documents inutiles",
            "Actions:",
            "  • Améliorer le tri des résultats (réduire K)",
            "  • Ajouter un re-ranking",
            "  • Utiliser un meilleur modèle d'embedding"
        ],
        'context_recall': [
            "Votre RAG manque des documents importants",
            "Actions:",
            "  • Augmenter K (chercher plus de documents)",
            "  • Améliorer le découpage (chunks plus petits)",
            "  • Utiliser un retriever hybride"
        ],
        'faithfulness': [
            "Votre RAG invente des informations",
            "Actions:",
            "  • Améliorer le prompt du générateur (plus strict)",
            "  • Demander de citer les sources",
            "  • Réduire la température du modèle"
        ],
        'answer_relevancy': [
            "Vos réponses sont trop longues ou hors-sujet",
            "Actions:",
            "  • Demander des réponses plus courtes",
            "  • Améliorer le format du prompt",
            "  • Ajouter des contraintes de longueur"
        ]
    }
    
    for line in recommendations[min_metric]:
        print(line)
    
    # Sauvegarder
    print("\n" + "=" * 80)
    print("💾 Sauvegarde des résultats...")
    
    results_data = {
        'scores': {k: float(v) for k, v in scores.items()},
        'moyenne': float(avg),
        'point_faible': min_metric
    }
    
    with open("ragas_results.json", "w", encoding="utf-8") as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)
    
    print("✅ Résultats sauvegardés dans ragas_results.json")
    
    return scores


def main():
    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}  PARTIE 2: ÉVALUATION AVEC RAGAS{Colors.ENDC}")
    print("=" * 80 + "\n")
    
    # Vérifier les prérequis
    if not os.path.exists("golden_dataset.json"):
        print(f"{Colors.FAIL}❌ Fichier golden_dataset.json non trouvé!{Colors.ENDC}")
        print("   Exécutez d'abord: python etape2_generer_questions.py")
        return
    
    # Charger le dataset
    samples = load_golden_dataset()
    
    # Initialiser le pipeline
    print("🔧 Initialisation du pipeline RAG...")
    pipeline = LegalIngestionPipeline(
        collection_name="legal_corpus_m2_tp",
        retriever_type="recursive"
    )
    generator = LegalAnswerGenerator()
    print()
    
    # Vérifier la collection
    try:
        from legal_rag.config import chroma_client
        collection = chroma_client.get_collection("legal_corpus_m2_tp")
        count = collection.count()
        if count == 0:
            print(f"{Colors.FAIL}❌ Collection vide!{Colors.ENDC}")
            return
        print(f"✅ Collection: {count} documents indexés\n")
    except:
        print(f"{Colors.FAIL}❌ Collection non trouvée!{Colors.ENDC}")
        return
    
    # ÉTAPE 5: Préparer les données
    dataset = prepare_ragas_dataset(samples, pipeline, generator)
    
    # ÉTAPE 6: Lancer l'évaluation
    result = run_ragas_evaluation(dataset)
    
    # ÉTAPE 7: Afficher les résultats
    if result:
        scores = display_results(result)
    
    print("\n" + "=" * 80)
    print(f"{Colors.GREEN}{Colors.BOLD}✅ PARTIE 2 TERMINÉE{Colors.ENDC}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
