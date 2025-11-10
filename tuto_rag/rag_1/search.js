import { promises as fs } from 'fs';
import { GoogleGenerativeAI } from '@google/generative-ai';
import dotenv from 'dotenv';
dotenv.config();

const genAI = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY);
const embeddingModel = genAI.getGenerativeModel({ model: "text-embedding-004" });
const chatModel = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

function cosineSimilarity(vecA, vecB) {
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }

  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
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

async function searchSimilarChunks(question, topK = 3) {
  try {
    const data = await fs.readFile('database.json', 'utf-8');
    const database = JSON.parse(data);
    const questionEmbedding = await generateEmbedding(question);

    const similarities = database.map(chunk => ({
      ...chunk,
      similarity: cosineSimilarity(questionEmbedding, chunk.embedding)
    }));

    similarities.sort((a, b) => b.similarity - a.similarity);

    const topResults = similarities.slice(0, topK);

    console.log(`   ✅ Top ${topK} chunks les plus pertinents:\n`);
    topResults.forEach((result, index) => {
      console.log(`   ${index + 1}. Similarité: ${result.similarity.toFixed(4)}`);
      console.log(`      Texte: ${result.text.substring(0, 80)}...\n`);
    });

    return topResults;

  } catch (error) {
    console.error('❌ Erreur lors de la recherche:', error.message);
    throw error;
  }
}


async function generateAnswer(question, context) {
  try {
    const prompt = `
    Tu es un assistant qui répond aux questions en te basant uniquement sur le contexte fourni.

    CONTEXTE:
    ${context}

    QUESTION: ${question}

    Réponds à la question en te basant UNIQUEMENT sur le contexte ci-dessus. Si l'information n'est pas dans le contexte,
    dis-le clairement.
    `;

    const result = await chatModel.generateContent(prompt);
    const answer = result.response.text();

    return answer;

  } catch (error) {
    console.error('❌ Erreur lors de la génération:', error.message);
    throw error;
  }
}

async function askRAG(question) {
  try {

    const relevantChunks = await searchSimilarChunks(question, 3);

    const context = relevantChunks
      .map((chunk, index) => `[${index + 1}] ${chunk.text}`)
      .join('\n\n');

    const answer = await generateAnswer(question, context);

    return {
      question,
      answer,
      sources: relevantChunks
    };

  } catch (error) {
    console.error('❌ Erreur:', error.message);
    throw error;
  }
}

export { askRAG };

if (import.meta.url === `file://${process.argv[1]}`) {
  const question = "Parle moi de l'ia et spotify";
  askRAG(question);
}