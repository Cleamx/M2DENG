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
from legal_rag.pipeline import LegalIngestionPipeline
from legal_rag.generation import LegalAnswerGenerator
from legal_rag.evaluation import GoldenSample, LLMJudge


# Couleurs pour l'affichage
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def load_golden_dataset(filepath: str = "golden_dataset.json"):
    """Charge le dataset de questions de test."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    samples = [GoldenSample(**item) for item in data]
    print(f"✅ {len(samples)} questions chargées")
    return samples


def prepare_ragas_dataset(samples, pipeline, generator):
    """
    Prépare le dataset au format Ragas en exécutant le RAG.
    
    Format attendu:
    {
        'question': [...],
        'contexts': [...],      # Documents trouvés
        'answer': [...],        # Réponse générée
        'ground_truth': [...]   # Réponse attendue
    }
    """
    print(f"\n{'='*80}")
    print("🔄 EXÉCUTION DU RAG SUR LES QUESTIONS DE TEST")
    print(f"{'='*80}\n")
    
    data = {
        'question': [],
        'contexts': [],
        'answer': [],
        'ground_truth': []
    }
    
    for i, sample in enumerate(samples, 1):
        print(f"[{i}/{len(samples)}] {sample.query[:80]}...")
        
        try:
            # 1. Recherche
            results = pipeline.search(sample.query, n_results=5)
            
            # 2. Génération
            answer = generator.generate_answer(sample.query, results)
            
            # 3. Extraction des contextes
            contexts = results['documents'][0] if results['documents'] else []
            
            # 4. Ajout au dataset
            data['question'].append(sample.query)
            data['contexts'].append(contexts)
            data['answer'].append(answer)
            data['ground_truth'].append(sample.ground_truth)
            
            print(f"   ✅ Traité")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            # Ajouter des valeurs par défaut pour éviter les erreurs
            data['question'].append(sample.query)
            data['contexts'].append([])
            data['answer'].append("Erreur lors de la génération")
            data['ground_truth'].append(sample.ground_truth)
    
    # Conversion pour Ragas
    dataset = Dataset.from_dict(data)
    print(f"\n✅ Dataset Ragas préparé: {len(dataset)} entrées")
    
    return dataset


def run_ragas_evaluation(dataset):
    """
    Lance l'évaluation Ragas avec les 4 métriques.
    
    Métriques:
    - context_precision: Qualité des documents trouvés (pertinents?)
    - context_recall: Couverture (tous les documents nécessaires?)
    - faithfulness: Pas d'hallucinations?
    - answer_relevancy: Réponse claire et pertinente?
    """
    print(f"\n{'='*80}")
    print("📊 ÉVALUATION RAGAS EN COURS...")
    print(f"{'='*80}\n")
    
    print("🔍 Métriques utilisées:")
    print("   1. context_precision: Qualité Retriever (documents pertinents?)")
    print("   2. context_recall: Couverture Retriever (tous les docs nécessaires?)")
    print("   3. faithfulness: Pas d'hallucinations?")
    print("   4. answer_relevancy: Pertinence de la réponse")
    
    print("\n⏳ Évaluation en cours (cela peut prendre quelques minutes)...\n")
    
    try:
        result = evaluate(
            dataset,
            metrics=[
                context_precision,
                context_recall,
                faithfulness,
                answer_relevancy
            ]
        )
        
        return result
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'évaluation: {e}")
        return None


def display_results(result):
    """Affiche les résultats formatés."""
    if not result:
        return
    
    print(f"\n{'='*80}")
    print(f"{Colors.BOLD}📊 RÉSULTATS RAGAS{Colors.ENDC}")
    print(f"{'='*80}\n")
    
    # Récupérer les scores
    scores = {
        'context_precision': result.get('context_precision', 0),
        'context_recall': result.get('context_recall', 0),
        'faithfulness': result.get('faithfulness', 0),
        'answer_relevancy': result.get('answer_relevancy', 0)
    }
    
    # Affichage avec couleurs
    for metric, score in scores.items():
        # Déterminer la couleur selon le score
        if score >= 0.80:
            color = Colors.GREEN
            status = "✅ Excellent"
        elif score >= 0.60:
            color = Colors.WARNING
            status = "⚠️  Correct"
        else:
            color = Colors.FAIL
            status = "❌ À améliorer"
        
        # Noms lisibles
        names = {
            'context_precision': 'Qualité Retriever',
            'context_recall': 'Couverture Retriever',
            'faithfulness': 'Pas d\'hallucination',
            'answer_relevancy': 'Pertinence réponse'
        }
        
        print(f"{color}{names[metric]:25s} : {score:.2f} {status}{Colors.ENDC}")
    
    # Note moyenne
    avg_score = sum(scores.values()) / len(scores)
    print(f"\n{Colors.BOLD}Note moyenne : {avg_score:.2f}{Colors.ENDC}")
    
    return scores


def diagnostic(scores):
    """Fournit un diagnostic et des recommandations."""
    print(f"\n{'='*80}")
    print(f"{Colors.BOLD}🔍 DIAGNOSTIC ET RECOMMANDATIONS{Colors.ENDC}")
    print(f"{'='*80}\n")
    
    # Trouver le score le plus faible
    min_metric = min(scores, key=scores.get)
    min_score = scores[min_metric]
    
    print(f"{Colors.WARNING}📌 Point faible principal:{Colors.ENDC}")
    print(f"   {min_metric}: {min_score:.2f}\n")
    
    # Recommandations selon la métrique
    recommendations = {
        'context_precision': [
            "🔹 Votre Retriever trouve trop de documents inutiles",
            "   Actions possibles:",
            "   • Améliorer le tri des résultats (top-k plus petit)",
            "   • Ajouter un re-ranking des documents",
            "   • Utiliser un meilleur modèle d'embedding",
            "   • Affiner le découpage des chunks"
        ],
        'context_recall': [
            "🔹 Votre Retriever manque des documents importants",
            "   Actions possibles:",
            "   • Augmenter K (chercher dans plus de documents)",
            "   • Améliorer le découpage (chunks plus petits)",
            "   • Vérifier la qualité des embeddings",
            "   • Utiliser un retriever hybride (dense + sparse)"
        ],
        'faithfulness': [
            "🔹 Votre RAG invente des informations (hallucinations)",
            "   Actions possibles:",
            "   • Améliorer le prompt du générateur (plus strict)",
            "   • Demander explicitement de citer les sources",
            "   • Réduire la température du modèle",
            "   • Filtrer mieux les documents non pertinents"
        ],
        'answer_relevancy': [
            "🔹 Vos réponses sont trop longues ou hors-sujet",
            "   Actions possibles:",
            "   • Demander des réponses plus courtes et ciblées",
            "   • Améliorer le prompt (format structuré)",
            "   • Utiliser un modèle plus précis",
            "   • Ajouter des contraintes de longueur"
        ]
    }
    
    for line in recommendations[min_metric]:
        print(line)
    
    print(f"\n{Colors.BOLD}📋 TABLEAU DE BORD:{Colors.ENDC}")
    print("\nNote | Votre Score | Bon ou Mauvais | Action")
    print("-" * 60)
    
    for metric, score in scores.items():
        status = "Excellent ✅" if score >= 0.80 else ("Correct ⚠️" if score >= 0.60 else "À améliorer ❌")
        action = "Continuer" if score >= 0.80 else "Optimiser"
        print(f"{metric:20s} | {score:.2f}        | {status:15s} | {action}")


def test_llm_judge(samples, pipeline, generator, judge):
    """Teste le LLM Judge sur quelques exemples."""
    print(f"\n{'='*80}")
    print(f"{Colors.BOLD}⚖️  TEST DU LLM JUDGE{Colors.ENDC}")
    print(f"{'='*80}\n")
    
    # Prendre les 3 premières questions
    for i, sample in enumerate(samples[:3], 1):
        print(f"\n{Colors.CYAN}--- Question {i} ---{Colors.ENDC}")
        print(f"Q: {sample.query}\n")
        
        # Exécuter le RAG
        results = pipeline.search(sample.query, n_results=3)
        answer = generator.generate_answer(sample.query, results)
        contexts = results['documents'][0] if results['documents'] else []
        
        print(f"{Colors.BLUE}Réponse générée:{Colors.ENDC}")
        print(f"{answer[:200]}...\n")
        
        # Noter avec le juge
        scores = judge.judge_answer(sample.query, answer, contexts)
        
        print(f"{Colors.GREEN}Notes du juge:{Colors.ENDC}")
        print(f"   Fidélité:    {scores['fidelite']}/10")
        print(f"   Clarté:      {scores['clarte']}/10")
        print(f"   Complétude:  {scores['completude']}/10")
        print(f"   Note globale: {scores['note_globale']}/10")
        print(f"\n   {Colors.WARNING}Explication:{Colors.ENDC} {scores['explication']}")


def main():
    """Fonction principale."""
    print(f"\n{'='*80}")
    print(f"{Colors.HEADER}{Colors.BOLD}  TP RAGOps & Métrologie - Évaluation avec Ragas{Colors.ENDC}")
    print(f"{'='*80}\n")
    
    # Vérifier les prérequis
    if not os.path.exists("golden_dataset.json"):
        print(f"{Colors.FAIL}❌ Fichier golden_dataset.json non trouvé!{Colors.ENDC}")
        print("   Exécutez d'abord: python generate_questions.py")
        return
    
    if not os.path.exists(".env"):
        print(f"{Colors.FAIL}❌ Fichier .env non trouvé!{Colors.ENDC}")
        print("   Créez un fichier .env avec votre MISTRAL_API_KEY")
        return
    
    # Charger le dataset
    print("📚 Chargement du golden dataset...")
    samples = load_golden_dataset()
    
    # Initialiser le pipeline
    print("\n🔧 Initialisation du pipeline RAG...")
    pipeline = LegalIngestionPipeline(
        collection_name="legal_corpus_m2_tp",
        retriever_type="recursive"  # Ou "parent-child"
    )
    generator = LegalAnswerGenerator()
    
    # Vérifier si la collection existe
    try:
        collection = pipeline.chroma_client.get_collection("legal_corpus_m2_tp")
        count = collection.count()
        if count == 0:
            print(f"\n{Colors.WARNING}⚠️  La collection est vide!{Colors.ENDC}")
            print("   Indexez d'abord vos documents avec: python main.py")
            return
        print(f"✅ Collection trouvée: {count} documents indexés")
    except:
        print(f"\n{Colors.WARNING}⚠️  Collection non trouvée!{Colors.ENDC}")
        print("   Indexez d'abord vos documents avec: python main.py")
        return
    
    # PARTIE 2: Évaluation Ragas
    dataset = prepare_ragas_dataset(samples, pipeline, generator)
    result = run_ragas_evaluation(dataset)
    
    if result:
        scores = display_results(result)
        diagnostic(scores)
    
    # PARTIE 3: LLM Judge
    print(f"\n{Colors.BOLD}Voulez-vous tester le LLM Judge? (y/n){Colors.ENDC}")
    try:
        response = input().strip().lower()
        if response == 'y':
            judge = LLMJudge()
            test_llm_judge(samples, pipeline, generator, judge)
    except:
        pass
    
    # Sauvegarde des résultats
    if result:
        print(f"\n{'='*80}")
        print("💾 Sauvegarde des résultats...")
        
        results_data = {
            'scores': {
                'context_precision': float(result.get('context_precision', 0)),
                'context_recall': float(result.get('context_recall', 0)),
                'faithfulness': float(result.get('faithfulness', 0)),
                'answer_relevancy': float(result.get('answer_relevancy', 0))
            },
            'moyenne': sum(scores.values()) / len(scores)
        }
        
        with open("ragas_results.json", "w", encoding="utf-8") as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        print("✅ Résultats sauvegardés dans ragas_results.json")
    
    print(f"\n{'='*80}")
    print(f"{Colors.GREEN}{Colors.BOLD}✅ ÉVALUATION TERMINÉE{Colors.ENDC}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
