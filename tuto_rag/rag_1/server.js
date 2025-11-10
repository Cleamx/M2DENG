import express from 'express';
import cors from 'cors';
import { askRAG } from './search.js';

const app = express();
const PORT = 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public')); // Servir les fichiers statiques depuis le dossier 'public'

// Endpoint pour poser une question au RAG
app.post('/ask', async (req, res) => {
  try {
    const { question } = req.body;

    if (!question || question.trim() === '') {
      return res.status(400).json({
        error: 'La question ne peut pas être vide'
      });
    }

    console.log(`📩 Question reçue: ${question}`);

    // Appeler la fonction RAG
    const result = await askRAG(question);

    // Retourner la réponse
    res.json({
      success: true,
      question: result.question,
      answer: result.answer,
      sources: result.sources.map(s => ({
        text: s.text,
        similarity: s.similarity
      }))
    });

  } catch (error) {
    console.error('❌ Erreur serveur:', error);
    res.status(500).json({
      success: false,
      error: 'Une erreur est survenue lors du traitement de votre question'
    });
  }
});

// Route pour vérifier que le serveur fonctionne
app.get('/health', (req, res) => {
  res.json({ status: 'OK', message: 'Le serveur RAG fonctionne correctement' });
});

// Démarrer le serveur
app.listen(PORT, () => {
  console.log('🚀 Serveur RAG démarré');
  console.log(`📡 API disponible sur http://localhost:${PORT}`);
  console.log(`🌐 Interface web sur http://localhost:${PORT}`);
  console.log('='.repeat(60));
});
