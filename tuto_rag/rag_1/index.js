const fs = require('fs').promises;
const { GoogleGenerativeAI } = require('@google/generative-ai');
require('dotenv').config();

const genAI = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY);
const embeddingModel = genAI.getGenerativeModel({ model: "text-embedding-004" });

function chunkText(text, wordsPerChunk = 50) {
  const words = text.split(/\s+/);
  const chunks = [];

  for (let i = 0; i < words.length; i += wordsPerChunk) {
    const chunk = words.slice(i, i + wordsPerChunk).join(' ');
    chunks.push(chunk);
  }

  return chunks;
}

async function generateEmbedding(text) {
  try {
    const result = await embeddingModel.embedContent(text);
    return result.embedding.values;
  } catch (error) {
    console.error('Erreur lors de la génération de l\'embedding:', error.message);
    throw error;
  }
}

async function indexDocument() {
  try {
    const texte = await fs.readFile('read-file.txt', 'utf-8');
    const chunks = chunkText(texte, 100);
    const database = [];

    for (let i = 0; i < chunks.length; i++) {
      const texte = chunks[i];

      console.log(`   Chunk ${i + 1}/${chunks.length}:`);
      console.log(`   - Génération de l'embedding...`);

      const vecteur = await generateEmbedding(texte);

      console.log(`   - Dimensions du vecteur: ${vecteur.length}`);

      database.push({
        id: `chunk_${i}`,
        text: texte,
        embedding: vecteur,
        metadata: {
          chunk_index: i,
          word_count: texte.split(/\s+/).length
        }
      });
    }
    await fs.writeFile('database.json', JSON.stringify(database, null, 2));
  } catch (error) {
    console.error('❌ Erreur:', error.message);
    console.error(error);
  }
}

indexDocument();