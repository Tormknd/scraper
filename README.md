# 🤖 Scraper-LLM - Extracteur Web Intelligent

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15.4+-black.svg)](https://nextjs.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-purple.svg)](https://openai.com/)

> **Scraper-LLM** est une application révolutionnaire qui combine l'intelligence artificielle (OpenAI) avec des techniques avancées de web scraping pour extraire automatiquement des données structurées de n'importe quel site web. L'application utilise l'IA pour comprendre le contenu des pages et extraire intelligemment les produits, images, prix et informations pertinentes.

## ✨ Fonctionnalités Principales

- 🧠 **Extraction Intelligente** : Utilise GPT-4o-mini pour analyser et extraire les données pertinentes
- 🖼️ **Téléchargement d'Images** : Télécharge automatiquement les images et les stocke localement
- 🎯 **Extraction Structurée** : Retourne des données JSON organisées (titre, prix, image, description)
- ⚡ **Performance Optimisée** : Gestion des erreurs, retry automatique, déduplication
- 🔒 **Sécurité Avancée** : Validation des URLs, gestion des timeouts, sanitisation
- 🌐 **Rendu JavaScript** : Support des sites dynamiques avec Playwright et Selenium
- 📰 **Extraction de Contenu** : Algorithmes de lisibilité pour un contenu de qualité
- 🏷️ **Données Structurées** : Extraction des métadonnées Schema.org, Open Graph, etc.

## 🏗️ Architecture

```
ScrapingTest/
├── backend/                 # API FastAPI
│   ├── main.py             # Serveur FastAPI principal
│   ├── scraper.py          # Scraper de base avec OpenAI
│   ├── advanced_scraper.py # Scraper avancé avec multiples méthodes
│   ├── requirements.txt    # Dépendances Python
│   ├── env.example         # Configuration d'environnement
│   └── images/             # Images téléchargées
└── frontend/               # Interface Next.js
    ├── src/app/page.tsx    # Interface terminal interactive
    ├── package.json        # Dépendances Node.js
    └── components/         # Composants UI
```

## 🚀 Installation Rapide

### Prérequis

- **Python 3.8+**
- **Node.js 18+**
- **Clé API OpenAI** (gratuite ou payante)

### 1. Cloner et Installer

```bash
# Cloner le repository
git clone https://github.com/Tormknd/scraper.git
cd scraper

# Configuration du backend
cd backend
pip install -r requirements.txt

# Configuration du frontend
cd ../frontend
npm install
```

### 2. Configuration

```bash
# Dans le dossier backend
cp env.example .env
```

Éditez le fichier `backend/.env` :
```env
OPENAI_API_KEY=sk-votre-clé-api-openai
# Optionnel : changer le modèle OpenAI
# OPENAI_MODEL=gpt-4o-mini
```

### 3. Démarrer l'Application

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

🎉 **L'application est maintenant accessible sur `http://localhost:3000`**

## 🎮 Utilisation Simple

### Interface Terminal Interactive

1. Ouvrez `http://localhost:3000`
2. Utilisez les commandes suivantes :

```bash
# Afficher l'aide
help

# Scraper une URL (méthode de base)
scrap https://example.com

# Scraper avec méthode avancée
scrap-advanced https://example.com

# Effacer l'écran
clear

# Navigation dans l'historique
↑ / ↓  # Naviguer dans les 10 dernières commandes
```

### Exemples d'Utilisation

#### Scraping de Base
```bash
scrap https://www.amazon.fr/dp/B08N5WRWNW
```
Extrait automatiquement :
- Titres des produits
- Prix
- Images (téléchargées localement)
- Descriptions

#### Scraping Avancé
```bash
scrap-advanced https://www.lemonde.fr
```
Utilise des méthodes avancées :
- Rendu JavaScript
- Extraction de contenu principal
- Métadonnées structurées
- Images haute qualité

## 🔧 Fonctionnalités Avancées

### Méthodes d'Extraction

Le scraper avancé utilise plusieurs méthodes en cascade :

1. **Playwright** : Rendu JavaScript complet
2. **Selenium** : Automatisation navigateur
3. **Requests-HTML** : Rendu JavaScript léger
4. **Newspaper3k** : Extraction de contenu journalistique
5. **Readability** : Algorithmes de lisibilité
6. **Extruct** : Données structurées (Schema.org, Open Graph)

### Configuration Avancée

Dans `backend/advanced_scraper.py` :
```python
# Paramètres de performance
TIMEOUT = 30              # Timeout HTTP (secondes)
MAX_PAGES = 5             # Nombre max de pages à scraper
USE_JS = True             # Activer le rendu JavaScript
RETRIES = 3               # Nombre de tentatives
```

## 📊 Formats de Données

### Scraping de Base
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

### Scraping Avancé
```json
{
  "url": "https://example.com",
  "title": "Titre de la page",
  "meta_description": "Description meta",
  "main_content": "Contenu principal extrait",
  "structured_data": {
    "schema_org": [...],
    "open_graph": {...},
    "twitter_cards": {...}
  },
  "images": [
    {
      "src": "https://example.com/img.jpg",
      "alt": "Description",
      "local_path": "/images/img.jpg"
    }
  ],
  "links": [...],
  "metadata": {
    "language": "fr",
    "author": "Auteur",
    "published_date": "2024-01-01"
  }
}
```

## 🛠️ API Endpoints

### POST `/scrape` - Scraping de Base
```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### POST `/scrape-advanced` - Scraping Avancé
```bash
curl -X POST "http://localhost:8000/scrape-advanced" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "use_js": true, "max_pages": 3}'
```

### POST `/extract` - Extraction de Contenu
```bash
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## 🎯 Cas d'Usage

### E-commerce
```bash
scrap https://www.fnac.com
scrap https://www.darty.com
scrap https://www.cdiscount.com
```

### Actualités
```bash
scrap-advanced https://www.lemonde.fr
scrap-advanced https://www.lefigaro.fr
scrap-advanced https://www.liberation.fr
```

### Blogs et Sites Web
```bash
scrap-advanced https://www.medium.com
scrap-advanced https://www.dev.to
```

## 🔍 Fonctionnalités Techniques

### Intelligence Artificielle
- **Modèle** : GPT-4o-mini (optimisé pour la vitesse et le coût)
- **Prompt** : Analyse intelligente du HTML pour extraire les éléments pertinents
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
- **Anti-détection** : User-Agents aléatoires, délais

## 🎨 Interface Utilisateur

L'interface s'inspire des terminaux modernes avec :
- **Design sombre** pour réduire la fatigue oculaire
- **Typographie monospace** pour l'aspect technique
- **Animations fluides** avec Framer Motion
- **Galerie d'images** responsive
- **Navigation clavier** complète
- **Historique des commandes** avec recherche

## 🚨 Gestion des Erreurs

L'application gère automatiquement :
- **Erreurs réseau** : Retry avec backoff exponentiel
- **Timeouts** : Limite configurable pour éviter les blocages
- **Erreurs OpenAI** : Messages d'erreur explicites
- **Images manquantes** : Fallback vers URL distante
- **HTML malformé** : Nettoyage automatique avec BeautifulSoup
- **Sites protégés** : Utilisation de méthodes alternatives

## 📈 Performance

- **Extraction rapide** : Optimisé pour les sites e-commerce
- **Cache d'images** : Évite les téléchargements redondants
- **Limite de tokens** : Contrôle des coûts OpenAI
- **Concurrence** : Gestion asynchrone des requêtes
- **Méthodes multiples** : Fallback automatique en cas d'échec

## 🔒 Sécurité

- **Validation des URLs** : Vérification du format et du protocole
- **Sanitisation** : Encodage des caractères spéciaux
- **User-Agent** : Identification claire du bot
- **Rate limiting** : Pause entre les téléchargements d'images
- **Anti-bot** : Techniques pour éviter la détection

## 🚀 Démarrage Rapide pour Test

### Test Immédiat (5 minutes)

1. **Installer les dépendances :**
```bash
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

2. **Configurer OpenAI :**
```bash
# Dans backend/.env
OPENAI_API_KEY=sk-votre-clé-api-openai
```

3. **Démarrer :**
```bash
# Terminal 1
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2  
cd frontend && npm run dev
```

4. **Tester :**
- Ouvrez `http://localhost:3000`
- Tapez : `scrap https://www.example.com`
- Admirez le résultat ! 🎉

## 📚 Ressources

- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Documentation Next.js](https://nextjs.org/docs)
- [API OpenAI](https://platform.openai.com/docs)
- [Playwright Documentation](https://playwright.dev/)

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Ajouter de nouvelles fonctionnalités
- Améliorer la documentation

---

**Scraper-LLM** - Transformez n'importe quel site web en données structurées avec l'intelligence artificielle ! 🚀

*Développé avec ❤️ en utilisant FastAPI, Next.js et OpenAI* 