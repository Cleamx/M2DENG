# RAG Chat Application

Application de chat utilisant la technologie RAG (Retrieval-Augmented Generation) avec Google Generative AI.

## 🚀 Démarrage

### 1. Installer les dépendances (si ce n'est pas déjà fait)
```bash
npm install
```

### 2. Configurer les variables d'environnement
Créez un fichier `.env` avec votre clé API Google :
```
GOOGLE_API_KEY=votre_clé_api_ici
```

### 3. Indexer vos documents (si ce n'est pas déjà fait)
```bash
npm run index
```

### 4. Lancer le serveur
```bash
npm start
```

Le serveur démarre sur http://localhost:3000

### 5. Utiliser l'application
Ouvrez votre navigateur et allez sur http://localhost:3000

## 📁 Structure du projet

- `server.js` - Serveur Express avec l'API
- `search.js` - Logique RAG (recherche et génération de réponses)
- `index.js` - Script d'indexation des documents
- `public/` - Interface web (HTML, CSS, JS)
  - `index.html` - Page principale
  - `style.css` - Styles de l'interface
  - `app.js` - Logique frontend
- `database.json` - Base de données vectorielle

## 🔌 API Endpoints

### POST /ask
Pose une question au système RAG.

**Body:**
```json
{
  "question": "Votre question ici"
}
```

**Réponse:**
```json
{
  "success": true,
  "question": "Votre question",
  "answer": "La réponse générée",
  "sources": [
    {
      "text": "Extrait du document",
      "similarity": 0.85
    }
  ]
}
```

### GET /health
Vérifier l'état du serveur.

## 🛠️ Scripts disponibles

- `npm start` - Démarre le serveur web
- `npm run index` - Indexe les documents
- `npm run search` - Test la recherche en ligne de commande
