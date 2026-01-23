#!/usr/bin/env python3
"""
PARTIE 3 du TP RAGOps: LLM Judge
Évalue les réponses du RAG avec un LLM selon 3 critères:
- Fidélité (pas d'hallucination)
- Clarté (compréhensibilité)
- Complétude (exhaustivité)
"""
import json
import os
import pandas as pd
from legal_rag.pipeline import LegalIngestionPipeline
from legal_rag.generation import LegalAnswerGenerator
from legal_rag.evaluation import GoldenSample, LLMJudge


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


def evaluate_with_llm_judge(samples, pipeline, generator, judge):
    """
    ÉTAPE 8 : Évaluer avec LLM Judge.
    
    Pour chaque question:
    1. Lancer le RAG
    2. Évaluer la réponse avec le LLM Judge (3 critères)
    3. Collecter les scores
    """
    print("=" * 80)
    print("  ÉTAPE 8: ÉVALUATION AVEC LLM JUDGE")
    print("=" * 80)
    print("\n📊 Critères d'évaluation:")
    print("  1. Fidélité    : La réponse est-elle basée sur les documents?")
    print("  2. Clarté      : La réponse est-elle compréhensible?")
    print("  3. Complétude  : La réponse couvre-t-elle tous les aspects?")
    print("\n⏳ Évaluation en cours...\n")
    
    results = []
    
    for i, sample in enumerate(samples, 1):
        print(f"[{i}/{len(samples)}] {sample.query[:70]}...")
        
        try:
            # 1. Recherche
            search_results = pipeline.search(sample.query, n_results=5)
            
            # 2. Génération
            answer = generator.generate_answer(sample.query, search_results)
            
            # 3. Préparation du contexte pour le juge
            context_docs = search_results['documents'][0] if search_results['documents'] else []
            
            # 4. Évaluation avec LLM Judge (scores sur 10)
            evaluation = judge.judge_answer(
                query=sample.query,
                answer=answer,
                contexts=context_docs
            )
            
            # Conversion scores /10 vers /5 pour affichage
            fid_5 = evaluation.get('fidelite', 0) / 2
            cla_5 = evaluation.get('clarte', 0) / 2
            comp_5 = evaluation.get('completude', 0) / 2
            moy_5 = evaluation.get('note_globale', 0) / 2
            
            # 5. Ajout aux résultats
            results.append({
                'question': sample.query,
                'difficulty': sample.metadata.get('difficulty', 'unknown'),
                'answer': answer,
                'ground_truth': sample.ground_truth,
                'fidelite': fid_5,
                'clarte': cla_5,
                'completude': comp_5,
                'score_moyen': moy_5,
                'justification': evaluation.get('explication', '')
            })
            
            # Affichage des scores
            fid = evaluation['fidelite']
            cla = evaluation['clarte']
            comp = evaluation['completude']
            moy = evaluation['score_moyen']
            
            color = Colors.GREEN if moy >= 4.0 else Colors.WARNING if moy >= 3.0 else Colors.FAIL
            print(f"  {color}Scores: Fidélité={fid}/5 | Clarté={cla}/5 | Complétude={comp}/5 | Moyenne={moy:.1f}/5{Colors.ENDC}\n")
            
        except Exception as e:
            print(f"  ❌ Erreur: {e}\n")
            results.append({
                'question': sample.query,
                'difficulty': sample.metadata.get('difficulty', 'unknown'),
                'answer': "Erreur",
                'ground_truth': sample.ground_truth,
                'fidelite': 0,
                'clarte': 0,
                'completude': 0,
                'score_moyen': 0,
                'justification': str(e)
            })
    
    print(f"✅ Évaluation terminée: {len(results)} réponses évaluées\n")
    return results


def analyze_results(results):
    """
    ÉTAPE 9 : Analyser les résultats.
    
    Affiche:
    - Scores moyens globaux
    - Répartition par difficulté
    - Points forts/faibles
    """
    print("=" * 80)
    print("  ÉTAPE 9: ANALYSE DES RÉSULTATS")
    print("=" * 80 + "\n")
    
    df = pd.DataFrame(results)
    
    # Scores moyens globaux
    print(f"{Colors.BOLD}📊 SCORES MOYENS GLOBAUX{Colors.ENDC}")
    print("=" * 80)
    
    avg_fidelite = df['fidelite'].mean()
    avg_clarte = df['clarte'].mean()
    avg_completude = df['completude'].mean()
    avg_global = df['score_moyen'].mean()
    
    def format_score(score, label):
        color = Colors.GREEN if score >= 4.0 else Colors.WARNING if score >= 3.0 else Colors.FAIL
        emoji = "✅" if score >= 4.0 else "⚠️ " if score >= 3.0 else "❌"
        return f"{label:15} : {color}{score:.2f}/5.00 {emoji}{Colors.ENDC}"
    
    print(format_score(avg_fidelite, "Fidélité"))
    print(format_score(avg_clarte, "Clarté"))
    print(format_score(avg_completude, "Complétude"))
    print("-" * 80)
    print(format_score(avg_global, "MOYENNE GLOBALE"))
    
    # Répartition par difficulté
    print(f"\n{Colors.BOLD}📈 SCORES PAR DIFFICULTÉ{Colors.ENDC}")
    print("=" * 80)
    
    for difficulty in ['easy', 'medium', 'hard']:
        subset = df[df['difficulty'] == difficulty]
        if len(subset) > 0:
            avg = subset['score_moyen'].mean()
            count = len(subset)
            color = Colors.GREEN if avg >= 4.0 else Colors.WARNING if avg >= 3.0 else Colors.FAIL
            print(f"{difficulty.capitalize():8} ({count:2} questions) : {color}{avg:.2f}/5.00{Colors.ENDC}")
    
    # Point faible
    print(f"\n{Colors.BOLD}🔍 DIAGNOSTIC{Colors.ENDC}")
    print("=" * 80)
    
    criterias = {
        'Fidélité': avg_fidelite,
        'Clarté': avg_clarte,
        'Complétude': avg_completude
    }
    
    min_criteria = min(criterias, key=criterias.get)
    min_score = criterias[min_criteria]
    
    print(f"{Colors.WARNING}📌 Critère le plus faible:{Colors.ENDC}")
    print(f"   {min_criteria}: {min_score:.2f}/5.00\n")
    
    # Recommandations
    recommendations = {
        'Fidélité': [
            "Problème: Le RAG génère des hallucinations",
            "Actions:",
            "  • Améliorer la pertinence des documents récupérés",
            "  • Ajouter des instructions au prompt pour rester fidèle au contexte",
            "  • Réduire la température du LLM"
        ],
        'Clarté': [
            "Problème: Les réponses sont confuses ou mal structurées",
            "Actions:",
            "  • Améliorer le prompt de génération",
            "  • Demander des réponses plus structurées",
            "  • Utiliser des exemples (few-shot)"
        ],
        'Complétude': [
            "Problème: Les réponses sont incomplètes",
            "Actions:",
            "  • Augmenter K (nombre de documents récupérés)",
            "  • Améliorer le chunking (taille des fragments)",
            "  • Vérifier que les documents contiennent bien l'information"
        ]
    }
    
    print(f"{Colors.CYAN}💡 Recommandations:{Colors.ENDC}")
    for line in recommendations[min_criteria]:
        print(f"   {line}")
    
    # Pires exemples
    print(f"\n{Colors.BOLD}❌ 3 PIRES RÉPONSES{Colors.ENDC}")
    print("=" * 80)
    
    worst = df.nsmallest(3, 'score_moyen')
    for idx, row in worst.iterrows():
        print(f"\nQuestion: {row['question'][:100]}...")
        print(f"Score: {row['score_moyen']:.1f}/5.00 | Difficulté: {row['difficulty']}")
        print(f"Justification: {row['justification'][:200]}...")
    
    # Meilleures exemples
    print(f"\n{Colors.BOLD}✅ 3 MEILLEURES RÉPONSES{Colors.ENDC}")
    print("=" * 80)
    
    best = df.nlargest(3, 'score_moyen')
    for idx, row in best.iterrows():
        print(f"\nQuestion: {row['question'][:100]}...")
        print(f"Score: {row['score_moyen']:.1f}/5.00 | Difficulté: {row['difficulty']}")
        print(f"Justification: {row['justification'][:200]}...")
    
    return df


def save_results(results, df):
    """Sauvegarde les résultats."""
    print("\n" + "=" * 80)
    print(f"  💾 SAUVEGARDE DES RÉSULTATS")
    print("=" * 80 + "\n")
    
    # JSON complet
    with open("llm_judge_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("✅ Résultats détaillés: llm_judge_results.json")
    
    # CSV pour analyse
    df.to_csv("llm_judge_results.csv", index=False, encoding="utf-8")
    print("✅ Tableau CSV: llm_judge_results.csv")
    
    # Résumé
    summary = {
        'scores_moyens': {
            'fidelite': float(df['fidelite'].mean()),
            'clarte': float(df['clarte'].mean()),
            'completude': float(df['completude'].mean()),
            'global': float(df['score_moyen'].mean())
        },
        'par_difficulte': {
            difficulty: {
                'count': int(len(df[df['difficulty'] == difficulty])),
                'score_moyen': float(df[df['difficulty'] == difficulty]['score_moyen'].mean())
            }
            for difficulty in ['easy', 'medium', 'hard']
            if len(df[df['difficulty'] == difficulty]) > 0
        }
    }
    
    with open("llm_judge_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("✅ Résumé: llm_judge_summary.json\n")


def main():
    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}  PARTIE 3: ÉVALUATION AVEC LLM JUDGE{Colors.ENDC}")
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
    judge = LLMJudge()
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
    
    # ÉTAPE 8: Évaluer avec LLM Judge
    results = evaluate_with_llm_judge(samples, pipeline, generator, judge)
    
    # ÉTAPE 9: Analyser les résultats
    df = analyze_results(results)
    
    # Sauvegarde
    save_results(results, df)
    
    print("=" * 80)
    print(f"{Colors.GREEN}{Colors.BOLD}✅ PARTIE 3 TERMINÉE{Colors.ENDC}")
    print("=" * 80 + "\n")
    print(f"{Colors.CYAN}📝 Fichiers générés:{Colors.ENDC}")
    print("  • llm_judge_results.json (détails)")
    print("  • llm_judge_results.csv (tableau)")
    print("  • llm_judge_summary.json (résumé)\n")


if __name__ == "__main__":
    main()
