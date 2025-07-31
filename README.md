# 🤖 Scraper-LLM - Extracteur Web Intelligent

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15.4+-black.svg)](https://nextjs.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-purple.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Scraper-LLM** est une application qui combine la puissance de l'IA (OpenAI) avec le web scraping pour extraire automatiquement des données structurées de n'importe quel site web. L'application utilise l'intelligence artificielle pour comprendre le contenu des pages et extraire intelligemment les produits, images et prix.

## ✨ Fonctionnalités Principales

- 🧠 **Extraction Intelligente** : Utilise GPT-4o-mini pour analyser et extraire les données pertinentes
- 🖼️ **Téléchargement d'Images** : Télécharge automatiquement les images et les stocke localement
- 🎯 **Extraction Structurée** : Retourne des données JSON organisées (titre, prix, image)
- 🌐 **Interface Web Moderne** : Interface terminal interactive inspirée de vzlabs.ai
- ⚡ **Performance Optimisée** : Gestion des erreurs, retry automatique, déduplication
- 🔒 **Sécurité** : Validation des URLs, gestion des timeouts, sanitisation

## 🏗️ Architecture

```
ScrapingTest/
├── backend/                 # API FastAPI
│   ├── main.py             # Serveur FastAPI
│   ├── scraper.py          # Logique de scraping avec OpenAI
│   ├── requirements.txt    # Dépendances Python
│   └── images/             # Images téléchargées
└── frontend/               # Interface Next.js
    ├── src/app/page.tsx    # Interface terminal
    ├── package.json        # Dépendances Node.js
    └── components/         # Composants UI
```

## 🚀 Installation et Configuration

### Prérequis

- **Python 3.8+**
- **Node.js 18+**
- **Clé API OpenAI** (gratuite ou payante)

### 1. Cloner le Repository

```bash
git clone https://github.com/Tormknd/scraper.git
cd scraper
```

### 2. Configuration du Backend

```bash
cd backend

# Installer les dépendances Python
pip install -r requirements.txt

# Configurer les variables d'environnement
cp env.example .env
```

Éditez le fichier `.env` :
```env
OPENAI_API_KEY=sk-votre-clé-api-openai
# Optionnel : changer le modèle OpenAI
# OPENAI_MODEL=gpt-4o-mini
```

### 3. Configuration du Frontend

```bash
cd ../frontend

# Installer les dépendances Node.js
npm install
```

## 🎮 Utilisation

### Démarrage des Services

**Terminal 1 - Backend :**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend :**
```bash
cd frontend
npm run dev
```

L'application sera accessible sur `http://localhost:3000`

### Interface Terminal

L'interface propose une expérience terminal interactive avec les commandes suivantes :

```bash
# Afficher l'aide
help

# Scraper une URL
scrap https://example.com

# Effacer l'écran
clear

# Navigation dans l'historique
↑ / ↓  # Naviguer dans les 10 dernières commandes
```

### Exemple d'Utilisation

1. Ouvrez `http://localhost:3000`
2. Tapez `scrap https://www.example-ecommerce.com`
3. L'IA analyse la page et extrait automatiquement :
   - Les titres des produits
   - Les prix (si disponibles)
   - Les images (téléchargées localement)
4. Les résultats s'affichent en JSON et les images dans une galerie

## 🔧 Configuration Avancée

### Variables d'Environnement

| Variable | Description | Défaut |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Clé API OpenAI (requise) | - |
| `OPENAI_MODEL` | Modèle OpenAI à utiliser | `gpt-4o-mini` |

### Paramètres de Performance

Dans `backend/scraper.py` :
```python
TIMEOUT     = 10        # Timeout HTTP (secondes)
RETRIES     = 3         # Nombre de tentatives
PAUSE_IMG   = 0.4       # Pause entre téléchargements d'images
MAX_TOKENS  = 11_000    # Limite de tokens pour OpenAI
```

## 📊 Format des Données

L'API retourne un JSON structuré :

```json
{
  "items": [
    {
      "title": "Nom du produit",
      "price": "29.99 €",
      "img": "https://example.com/image.jpg",
      "img_local": "/images/image.jpg"
    }
  ]
}
```

## 🛠️ API Endpoints

### POST `/scrape`

Extrait les données d'une URL donnée.

**Requête :**
```json
{
  "url": "https://example.com"
}
```

**Réponse :**
```json
{
  "items": [
    {
      "title": "Produit 1",
      "price": "19.99 €",
      "img": "https://example.com/img1.jpg",
      "img_local": "/images/img1.jpg"
    }
  ]
}
```

## 🔍 Fonctionnalités Techniques

### Intelligence Artificielle
- **Modèle** : GPT-4o-mini (optimisé pour la vitesse et le coût)
- **Prompt** : Analyse du HTML pour extraire les éléments pertinents
- **Schéma** : Structure JSON prédéfinie pour la cohérence

### Gestion des Images
- **Téléchargement automatique** vers le dossier `backend/images/`
- **Déduplication** basée sur les URLs d'images
- **Support multi-format** : JPEG, PNG, WebP, AVIF, GIF
- **Fallback** : URL distante si téléchargement échoue

### Robustesse
- **Retry automatique** pour les erreurs HTTP 5xx
- **Timeout configurable** pour éviter les blocages
- **Gestion d'erreurs** complète avec messages explicites
- **Sanitisation des URLs** pour éviter les injections

## 🎨 Interface Utilisateur

L'interface s'inspire des terminaux modernes avec :
- **Design sombre** pour réduire la fatigue oculaire
- **Typographie monospace** pour l'aspect technique
- **Animations fluides** avec Framer Motion
- **Galerie d'images** responsive
- **Navigation clavier** complète

## 🚨 Gestion des Erreurs

L'application gère automatiquement :
- **Erreurs réseau** : Retry avec backoff exponentiel
- **Timeouts** : Limite configurable pour éviter les blocages
- **Erreurs OpenAI** : Messages d'erreur explicites
- **Images manquantes** : Fallback vers URL distante
- **HTML malformé** : Nettoyage automatique avec BeautifulSoup

## 📈 Performance

- **Extraction rapide** : Optimisé pour les sites e-commerce
- **Cache d'images** : Évite les téléchargements redondants
- **Limite de tokens** : Contrôle des coûts OpenAI
- **Concurrence** : Gestion asynchrone des requêtes

## 🔒 Sécurité

- **Validation des URLs** : Vérification du format et du protocole
- **Sanitisation** : Encodage des caractères spéciaux
- **User-Agent** : Identification claire du bot
- **Rate limiting** : Pause entre les téléchargements d'images

## 🤝 Contribution

Les contributions sont les bienvenues ! Voici comment contribuer :

1. **Fork** le projet
2. **Créez** une branche pour votre fonctionnalité
3. **Commitez** vos changements
4. **Poussez** vers la branche
5. **Ouvrez** une Pull Request

### Améliorations Suggérées

- [ ] Support de l'authentification pour les sites protégés
- [ ] Extraction de données plus complexes (avis, descriptions)
- [ ] Interface d'administration pour gérer les extractions
- [ ] Support de l'export vers CSV/Excel
- [ ] Intégration avec d'autres modèles d'IA

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- **OpenAI** pour l'accès à leurs modèles d'IA
- **FastAPI** pour le framework backend performant
- **Next.js** pour l'interface utilisateur moderne
- **BeautifulSoup** pour le parsing HTML robuste

## 📞 Support

Pour toute question ou problème :
- **Issues GitHub** : [Créer une issue](https://github.com/Tormknd/scraper/issues)
- **Email** : [Votre email]

---

**Scraper-LLM** - Transformez n'importe quel site web en données structurées avec l'intelligence artificielle ! 🚀 