#!/usr/bin/env python3
"""
Script de test avec observabilité LangSmith.

Ce script instrumente le RAG avec @traceable pour tracer:
- Les recherches dans ChromaDB
- Les générations avec Mistral
- Le pipeline complet

Puis affiche les performances dans LangSmith.
"""
import os
from langsmith import traceable
from legal_rag.pipeline import LegalIngestionPipeline
from legal_rag.generation import LegalAnswerGenerator


# Couleurs
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class TracedLegalRAG:
    """
    Wrapper du RAG avec traçabilité LangSmith.
    
    Chaque méthode est décorée avec @traceable pour capturer:
    - Les entrées/sorties
    - Les temps d'exécution
    - Les erreurs éventuelles
    """
    
    def __init__(self, collection_name: str = "legal_corpus_m2_tp", retriever_type: str = "recursive"):
        """Initialisation du pipeline tracé."""
        self.pipeline = LegalIngestionPipeline(
            collection_name=collection_name,
            retriever_type=retriever_type
        )
        self.generator = LegalAnswerGenerator()
        print(f"✅ Pipeline RAG initialisé (mode: {retriever_type})")
    
    @traceable(name="Retrieval")
    def search_documents(self, query: str, n_results: int = 5):
        """
        Recherche dans ChromaDB (TRACÉ).
        
        LangSmith va capturer:
        - Le query
        - Le nombre de résultats
        - Le temps d'exécution
        - Les documents trouvés
        """
        print(f"🔍 Recherche: '{query[:60]}...'")
        results = self.pipeline.search(query, n_results=n_results)
        
        num_docs = len(results['documents'][0]) if results['documents'] else 0
        print(f"   ✅ {num_docs} documents trouvés")
        
        return results
    
    @traceable(name="Generation")
    def generate_answer(self, query: str, contexts: list):
        """
        Génération avec Mistral (TRACÉ).
        
        LangSmith va capturer:
        - Le query
        - Les contextes utilisés
        - La réponse générée
        - Le temps d'exécution
        """
        print(f"🤖 Génération de la réponse...")
        
        # Créer un objet results compatible
        results = {
            'documents': [contexts],
            'ids': [[f"doc_{i}" for i in range(len(contexts))]],
            'metadatas': [[{} for _ in contexts]],
            'distances': [[0.0 for _ in contexts]]
        }
        
        answer = self.generator.generate_answer(query, results)
        print(f"   ✅ Réponse générée ({len(answer)} caractères)")
        
        return answer
    
    @traceable(name="RAG_Query")
    def full_rag_query(self, query: str):
        """
        Pipeline RAG complet (TRACÉ).
        
        Cette trace parent contiendra deux traces enfants:
        1. Retrieval
        2. Generation
        
        Permet de voir le temps total et la décomposition.
        """
        print(f"\n{Colors.CYAN}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}🎯 Query: {query}{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*80}{Colors.ENDC}\n")
        
        # 1. Recherche
        results = self.search_documents(query)
        contexts = results['documents'][0] if results['documents'] else []
        
        # 2. Génération
        answer = self.generate_answer(query, contexts)
        
        return {
            'query': query,
            'answer': answer,
            'num_contexts': len(contexts),
            'contexts': contexts[:2]  # Limiter pour l'affichage
        }


def configure_langsmith():
    """
    Configure LangSmith pour le traçage.
    
    Variables d'environnement nécessaires:
    - LANGCHAIN_TRACING_V2: "true"
    - LANGCHAIN_API_KEY: Votre clé API
    - LANGCHAIN_PROJECT: Nom du projet
    """
    # Vérifier si déjà configuré dans .env
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv("LANGCHAIN_API_KEY"):
        print(f"\n{Colors.WARNING}⚠️  Configuration LangSmith manquante{Colors.ENDC}")
        print("\nPour activer le traçage LangSmith:")
        print("1. Créez un compte sur: https://smith.langchain.com/")
        print("2. Récupérez votre clé API")
        print("3. Ajoutez dans votre fichier .env:")
        print("   LANGCHAIN_TRACING_V2=true")
        print("   LANGCHAIN_API_KEY=votre_cle_ici")
        print("   LANGCHAIN_PROJECT=TP-RAGOps")
        print("\n4. Relancez ce script\n")
        return False
    
    # Configuration explicite
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "TP-RAGOps")
    
    print(f"{Colors.GREEN}✅ LangSmith configuré{Colors.ENDC}")
    print(f"   Projet: {os.environ['LANGCHAIN_PROJECT']}")
    print(f"   Visualisez vos traces sur: https://smith.langchain.com/\n")
    
    return True


def run_traced_queries(rag):
    """Exécute quelques requêtes avec traçage."""
    
    queries = [
        "Quel est le dispositif de l'arrêt?",
        "Qui sont les parties dans cette affaire?",
        "Quelle est la date de l'arrêt?"
    ]
    
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  EXÉCUTION DE REQUÊTES TRACÉES{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    for i, query in enumerate(queries, 1):
        print(f"\n{Colors.BLUE}[{i}/{len(queries)}]{Colors.ENDC}")
        result = rag.full_rag_query(query)
        
        print(f"\n{Colors.GREEN}Réponse:{Colors.ENDC}")
        print(f"{result['answer'][:300]}...")
        print(f"\n{Colors.CYAN}Contextes utilisés: {result['num_contexts']}{Colors.ENDC}")


def analyze_performance():
    """Affiche des conseils pour analyser les performances."""
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  ANALYSE DES PERFORMANCES{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}📊 Comment analyser vos traces:{Colors.ENDC}\n")
    
    print("1. Ouvrez LangSmith:")
    print(f"   {Colors.CYAN}https://smith.langchain.com/{Colors.ENDC}\n")
    
    print("2. Cliquez sur votre projet 'TP-RAGOps'\n")
    
    print("3. Vous verrez les traces avec:")
    print("   • Timeline des étapes")
    print("   • Temps d'exécution de chaque composant")
    print("   • Entrées/sorties détaillées\n")
    
    print(f"{Colors.BOLD}🔍 Questions à se poser:{Colors.ENDC}\n")
    
    print("❓ Quelle étape est la plus lente?")
    print("   • Retrieval devrait être < 500ms")
    print("   • Generation peut prendre 1-3s\n")
    
    print("❓ Y a-t-il des erreurs cachées?")
    print("   • Vérifiez les traces en rouge\n")
    
    print("❓ Les contextes sont-ils pertinents?")
    print("   • Regardez les documents récupérés\n")
    
    print(f"{Colors.BOLD}⚡ Optimisations possibles:{Colors.ENDC}\n")
    
    print("Si Retrieval est lent (> 1s):")
    print("   • Réduire la taille du corpus")
    print("   • Optimiser les embeddings")
    print("   • Utiliser un index sur GPU\n")
    
    print("Si Generation est lent (> 5s):")
    print("   • Passer à mistral-small")
    print("   • Réduire le nombre de tokens générés")
    print("   • Activer le streaming\n")


def main():
    """Fonction principale."""
    print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  TP RAGOps - Observabilité avec LangSmith{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    # Configuration LangSmith
    if not configure_langsmith():
        print(f"{Colors.WARNING}⚠️  Continuez sans traçage LangSmith{Colors.ENDC}")
        print(f"{Colors.WARNING}   (Les requêtes fonctionneront mais ne seront pas tracées){Colors.ENDC}\n")
    
    # Vérifier que la collection existe
    print("🔍 Vérification de la collection...")
    try:
        from legal_rag.config import chroma_client
        collection = chroma_client.get_collection("legal_corpus_m2_tp")
        count = collection.count()
        
        if count == 0:
            print(f"\n{Colors.FAIL}❌ La collection est vide!{Colors.ENDC}")
            print("   Indexez d'abord vos documents avec: python main.py")
            return
        
        print(f"✅ Collection trouvée: {count} documents indexés\n")
        
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Collection non trouvée!{Colors.ENDC}")
        print(f"   Erreur: {e}")
        print("   Indexez d'abord vos documents avec: python main.py")
        return
    
    # Initialiser le RAG tracé
    print("🚀 Initialisation du RAG tracé...")
    rag = TracedLegalRAG()
    
    # Exécuter des requêtes
    run_traced_queries(rag)
    
    # Guide d'analyse
    analyze_performance()
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}✅ TRAÇAGE TERMINÉ{Colors.ENDC}")
    print(f"{Colors.GREEN}Consultez vos traces sur: https://smith.langchain.com/{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
