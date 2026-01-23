#!/usr/bin/env python3
"""
ÉTAPE 2 du TP RAGOps: Générer 15 questions de test
Stratégie Evol-Instruct: 8 easy + 5 medium + 2 hard
"""
import json
from pathlib import Path
from legal_rag.evaluation import SyntheticDatasetGenerator, GoldenSample
from legal_rag.loaders import XMLLoader, JSONLoader


def main():
    print("=" * 80)
    print("  ÉTAPE 2: GÉNÉRATION DE 15 QUESTIONS (Evol-Instruct)")
    print("=" * 80)
    
    # Charger 2-3 documents
    print("\n📚 Chargement de 2-3 documents...")
    documents = []
    corpus_dir = Path("./documents_juridiques")
    
    # Charger 2 fichiers JSON
    json_files = list(corpus_dir.glob("audience_*.json"))[:2]
    for json_file in json_files:
        loader = JSONLoader(str(json_file))
        data = loader.load()
        documents.append((json_file.name, data['raw_text']))
        print(f"  ✅ {json_file.name}")
    
    # Charger 1 fichier XML
    xml_files = list(corpus_dir.glob("DCE_*.xml"))[:1]
    for xml_file in xml_files:
        loader = XMLLoader(str(xml_file))
        data = loader.load()
        documents.append((xml_file.name, data['raw_text']))
        print(f"  ✅ {xml_file.name}")
    
    print(f"\n✅ {len(documents)} documents chargés\n")
    
    # Générer
    print("🧪 Initialisation du générateur...")
    generator = SyntheticDatasetGenerator()
    samples = []
    
    # Compteurs
    easy_count = 0
    medium_count = 0
    hard_count = 0
    
    target_easy = 8
    target_medium = 5
    target_hard = 2
    
    print(f"\n🎯 Objectif: {target_easy} easy + {target_medium} medium + {target_hard} hard = 15 questions\n")
    
    for doc_name, doc_text in documents:
        print(f"{'='*80}")
        print(f"📄 Document: {doc_name}")
        print(f"{'='*80}\n")
        
        # Extraire les faits
        print("🔍 Extraction des informations clés...")
        facts = generator.extract_facts(doc_text, max_facts=5)
        
        if not facts:
            print("  ⚠️  Aucune information extraite\n")
            continue
        
        for i, fact in enumerate(facts):
            print(f"\n--- Information {i+1}/{len(facts)} ---")
            print(f"  📌 {fact[:80]}...")
            
            # 1. Question simple (easy)
            if easy_count < target_easy:
                print("  🔹 Génération question SIMPLE...")
                simple_q = generator.generate_question(fact)
                
                if simple_q:
                    print(f"  ✅ Q: {simple_q}")
                    answer = generator.generate_answer(doc_text, simple_q)
                    
                    if answer:
                        samples.append(GoldenSample(
                            query=simple_q,
                            ground_truth=answer,
                            metadata={"difficulty": "easy", "source": doc_name}
                        ))
                        easy_count += 1
                        print(f"  ✅ Question EASY ajoutée ({easy_count}/{target_easy})")
            
            # 2. ÉVOLUTION : Question complexe (medium/hard)
            if i % 2 == 0 and medium_count < target_medium and simple_q:  # 1 question sur 2
                print("  🔸 ÉVOLUTION vers MEDIUM...")
                complex_q = generator.evolve_question(simple_q)
                
                if complex_q and complex_q != simple_q:
                    print(f"  ✅ Q: {complex_q}")
                    answer = generator.generate_answer(doc_text, complex_q)
                    
                    if answer:
                        samples.append(GoldenSample(
                            query=complex_q,
                            ground_truth=answer,
                            metadata={"difficulty": "medium", "source": doc_name}
                        ))
                        medium_count += 1
                        print(f"  ✅ Question MEDIUM ajoutée ({medium_count}/{target_medium})")
            
            # Arrêter si objectifs atteints
            if easy_count >= target_easy and medium_count >= target_medium:
                break
        
        if easy_count >= target_easy and medium_count >= target_medium:
            break
    
    # Générer 2 questions HARD à partir des medium
    print(f"\n{'='*80}")
    print("🔶 GÉNÉRATION DE 2 QUESTIONS HARD (double évolution)")
    print(f"{'='*80}\n")
    
    medium_samples = [s for s in samples if s.metadata.get("difficulty") == "medium"][:2]
    for i, sample in enumerate(medium_samples, 1):
        print(f"Question HARD {i}/2...")
        hard_q = generator.evolve_question(sample.query)
        
        if hard_q and hard_q != sample.query:
            print(f"  ✅ Q: {hard_q}")
            # Trouver le document source
            source_doc = next((doc for name, doc in documents if name == sample.metadata["source"]), "")
            answer = generator.generate_answer(source_doc, hard_q)
            
            if answer:
                samples.append(GoldenSample(
                    query=hard_q,
                    ground_truth=answer,
                    metadata={"difficulty": "hard", "source": sample.metadata["source"]}
                ))
                hard_count += 1
                print(f"  ✅ Question HARD ajoutée ({hard_count}/{target_hard})")
    
    # Sauvegarder
    print(f"\n{'='*80}")
    print("💾 SAUVEGARDE DU DATASET")
    print(f"{'='*80}\n")
    
    output_data = [sample.to_dict() for sample in samples]
    
    with open("golden_dataset.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Fichier créé: golden_dataset.json")
    print(f"\n📊 RÉSUMÉ:")
    print(f"  • Questions EASY:   {easy_count}/{target_easy}")
    print(f"  • Questions MEDIUM: {medium_count}/{target_medium}")
    print(f"  • Questions HARD:   {hard_count}/{target_hard}")
    print(f"  • TOTAL:            {len(samples)} questions")
    
    # Afficher quelques exemples
    print(f"\n📋 EXEMPLES DE QUESTIONS:")
    for difficulty in ["easy", "medium", "hard"]:
        examples = [s for s in samples if s.metadata.get("difficulty") == difficulty]
        if examples:
            print(f"\n{difficulty.upper()}:")
            print(f"  Q: {examples[0].query}")
            print(f"  R: {examples[0].ground_truth[:100]}...")
    
    print(f"\n{'='*80}")
    print("✅ ÉTAPE 2 TERMINÉE")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
