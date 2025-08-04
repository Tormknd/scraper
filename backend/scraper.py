#!/usr/bin/env python3
from __future__ import annotations
import os, json, time, logging, pathlib
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlsplit, urlunsplit, quote
from dataclasses import dataclass, field
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry
from dotenv import load_dotenv
from openai import OpenAI

try:
    load_dotenv()
except Exception as e:
    pass
    
MODEL       = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
API_KEY     = os.getenv("OPENAI_API_KEY")
TIMEOUT     = 10
RETRIES     = 3
PAUSE_IMG   = 0.4
MAX_TOKENS  = 8_000
CONVERSATION_MAX_TOKENS = 12_000

IMG_DIR     = pathlib.Path(__file__).with_name("images")
IMG_DIR.mkdir(exist_ok=True)

@dataclass
class ConversationMessage:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ConversationSession:
    session_id: str
    messages: List[ConversationMessage] = field(default_factory=list)
    current_url: Optional[str] = None
    website_analysis: Optional[Dict] = None
    extraction_schema: Optional[Dict] = None
    
    def add_message(self, role: str, content: str):
        self.messages.append(ConversationMessage(role=role, content=content))
        self._trim_conversation()
    
    def _trim_conversation(self):
        if len(self.messages) <= 20:
            return
            
        total_tokens = 0
        for msg in self.messages:
            total_tokens += len(msg.content.split()) * 1.3
            
        if total_tokens > CONVERSATION_MAX_TOKENS:
            system_messages = [msg for msg in self.messages if msg.role == "system"]
            other_messages = [msg for msg in self.messages if msg.role != "system"]
            
            self.messages = system_messages + other_messages[-18:]
    
    def get_messages_for_api(self) -> List[Dict[str, str]]:
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]

conversation_sessions: Dict[str, ConversationSession] = {}

WEBSITE_ANALYSIS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "analyze_website",
        "description": "Analyze the type and content of a website",
        "parameters": {
            "type": "object",
            "properties": {
                "website_type": {
                    "type": "string",
                    "enum": ["ecommerce", "blog", "news", "portfolio", "corporate", "social_media", "other"],
                    "description": "The type of website"
                },
                "description": {"type": "string", "description": "Brief description of the website"},
                "available_data": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Types of data available on the website"
                },
                "suggested_extractions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Suggested data extraction strategies"
                },
                "content_quality": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Quality of content available for extraction"
                },
                "technical_complexity": {
                    "type": "string",
                    "enum": ["simple", "moderate", "complex"],
                    "description": "Technical complexity of the website"
                }
            },
            "required": ["website_type", "description", "available_data"]
        }
    }
}

EXTRACTION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "extract_data",
        "description": "Extract structured data from the website",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "price": {"type": "string"},
                            "img": {"type": "string"},
                            "description": {"type": "string"},
                            "url": {"type": "string"},
                            "category": {"type": "string"},
                            "rating": {"type": "string"},
                            "availability": {"type": "string"}
                        }
                    }
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "total_items": {"type": "integer"},
                        "website_type": {"type": "string"},
                        "extraction_method": {"type": "string"},
                        "content_quality": {"type": "string"}
                    }
                }
            },
            "required": ["items"]
        }
    }
}

class ScraperError(RuntimeError):
    pass

def create_conversation_session(session_id: str) -> ConversationSession:
    session = ConversationSession(session_id=session_id)
    
    system_message = """Tu es un assistant spécialisé dans l'analyse et l'extraction de données web. Tu peux:

1. Analyser des sites web pour déterminer leur type et les données disponibles
2. Extraire des données structurées selon les exigences de l'utilisateur
3. Répondre aux questions sur le scraping et l'extraction de données

Utilise les fonctions disponibles pour analyser et extraire les données. Sois précis et utile dans tes réponses."""

    session.add_message("system", system_message)
    conversation_sessions[session_id] = session
    return session

def get_or_create_session(session_id: str) -> ConversationSession:
    if session_id not in conversation_sessions:
        return create_conversation_session(session_id)
    return conversation_sessions[session_id]

def chat_with_ai(session_id: str, user_message: str, tools: Optional[List] = None) -> str:
    session = get_or_create_session(session_id)
    session.add_message("user", user_message)
    
    client = OpenAI(api_key=API_KEY)
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=session.get_messages_for_api(),
            tools=tools,
            tool_choice="auto" if tools else None,
            max_tokens=MAX_TOKENS,
            temperature=0.1
        )
        
        message = response.choices[0].message
        session.add_message("assistant", message.content or "")
        
        if message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call.function.name == "analyze_website":
                    args = json.loads(tool_call.function.arguments)
                    session.website_analysis = args
                    session.current_url = user_message.split()[-1] if user_message.split() else None
                    
                    analysis_response = f"J'ai analysé le site web. Voici ce que j'ai trouvé:\n\n"
                    analysis_response += f"**Type de site:** {args.get('website_type', 'Inconnu')}\n"
                    analysis_response += f"**Description:** {args.get('description', 'Aucune description')}\n"
                    analysis_response += f"**Données disponibles:** {', '.join(args.get('available_data', []))}\n"
                    analysis_response += f"**Qualité du contenu:** {args.get('content_quality', 'Inconnue')}\n"
                    analysis_response += f"**Complexité technique:** {args.get('technical_complexity', 'Inconnue')}\n\n"
                    analysis_response += f"**Suggestions d'extraction:**\n"
                    for suggestion in args.get('suggested_extractions', []):
                        analysis_response += f"- {suggestion}\n"
                    
                    session.add_message("assistant", analysis_response)
                    return analysis_response
                
                elif tool_call.function.name == "extract_data":
                    args = json.loads(tool_call.function.arguments)
                    session.extraction_schema = args
                    
                    extraction_response = f"J'ai extrait {len(args.get('items', []))} éléments du site web.\n\n"
                    extraction_response += f"**Méthode d'extraction:** {args.get('metadata', {}).get('extraction_method', 'Standard')}\n"
                    extraction_response += f"**Qualité du contenu:** {args.get('metadata', {}).get('content_quality', 'Standard')}\n\n"
                    extraction_response += "**Données extraites:**\n"
                    for i, item in enumerate(args.get('items', [])[:5], 1):
                        extraction_response += f"{i}. {item.get('title', 'Sans titre')}"
                        if item.get('price'):
                            extraction_response += f" - {item['price']}"
                        extraction_response += "\n"
                    
                    if len(args.get('items', [])) > 5:
                        extraction_response += f"\n... et {len(args.get('items', [])) - 5} autres éléments."
                    
                    session.add_message("assistant", extraction_response)
                    return extraction_response
        
        return message.content or "Je n'ai pas pu traiter votre demande."
        
    except Exception as e:
        error_msg = f"Erreur lors de la communication avec l'IA: {str(e)}"
        session.add_message("assistant", error_msg)
        return error_msg

def _fetch(url: str) -> str:
    session = requests.Session()
    retry_strategy = Retry(total=RETRIES, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    response = session.get(url, timeout=TIMEOUT, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    response.raise_for_status()
    return response.text

async def _advanced_smart_scrape(url: str, requirements: str = "") -> Dict[str, Any]:
    try:
        from advanced_scraper import AdvancedScraper
        scraper = AdvancedScraper()
        
        use_js=True
        max_pages=5
        
        scraped_content = await scraper.scrape_advanced(url, use_js=use_js, max_pages=max_pages)
        
        content_for_ai = f"URL: {url}\n\n"
        
        content_for_ai += f"Titre: {scraped_content.title}\n"
        content_for_ai += f"Description: {scraped_content.meta_description}\n\n"
        
        content_for_ai += f"Contenu principal:\n{scraped_content.main_content[:5000]}\n\n"
        
        if scraped_content.structured_data:
            content_for_ai += "Données structurées:\n"
            for key, value in scraped_content.structured_data.items():
                if isinstance(value, list) and len(value) > 0:
                    content_for_ai += f"{key}: {len(value)} éléments\n"
                elif isinstance(value, dict):
                    content_for_ai += f"{key}: {len(value)} propriétés\n"
                else:
                    content_for_ai += f"{key}: {value}\n"
            content_for_ai += "\n"
        
        if scraped_content.metadata:
            content_for_ai += "Métadonnées:\n"
            for key, value in scraped_content.metadata.items():
                content_for_ai += f"{key}: {value}\n"
            content_for_ai += "\n"
        
        for i, img in enumerate(scraped_content.images[:10]):
            content_for_ai += f"Image {i+1}: {img.get('src', 'N/A')} - {img.get('alt', 'Sans description')}\n"
        
        for i, link in enumerate(scraped_content.links[:15]):
            content_for_ai += f"Lien {i+1}: {link.get('href', 'N/A')} - {link.get('text', 'Sans texte')}\n"
        
        return {
            'main_page': {
                'url': url,
                'title': scraped_content.title,
                'content': scraped_content.main_content,
                'structured_data': scraped_content.structured_data,
                'metadata': scraped_content.metadata,
                'images': scraped_content.images,
                'links': scraped_content.links
            },
            'additional_pages': [],
            'total_pages_scraped': 1,
            'extraction_method': 'advanced',
            'content_for_ai': content_for_ai
        }
        
    except Exception as e:
        raise ScraperError(f"Advanced scraping failed: {e}")

async def _basic_smart_scrape(url: str, requirements: str = "") -> Dict[str, Any]:
    html = _fetch(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    title = soup.find('title')
    title_text = title.get_text().strip() if title else "Sans titre"
    
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    description = meta_desc.get('content', '') if meta_desc else ""
    
    structured_data = _extract_structured_data(html)
    
    relevant_pages = []
    if requirements:
        keywords = requirements.lower().split()
        links = soup.find_all('a', href=True)
    
    for link in links:
        link_text = link.get_text().strip().lower()
        link_url = link.get('href', '')
        
        is_relevant = any(keyword in link_text for keyword in keywords)
        
        if is_relevant and link_url.startswith(url):
            relevant_pages.append({
                'url': link_url,
                'text': link_text
            })
    
    for i, page in enumerate(relevant_pages[:3]):
        try:
            page_html = _fetch(page['url'])
            page_soup = BeautifulSoup(page_html, 'html.parser')
            page['content'] = _extract_text_content(page_html)
        except Exception as e:
            pass
    
    content_for_ai = f"URL: {url}\nTitre: {title_text}\nDescription: {description}\n\n"
    content_for_ai += f"Contenu principal:\n{_extract_text_content(html)[:3000]}\n\n"
    
    if structured_data:
        content_for_ai += "Données structurées:\n"
        for key, value in structured_data.items():
            content_for_ai += f"{key}: {value}\n"
        content_for_ai += "\n"
    
    return {
        'main_page': {
            'url': url,
            'title': title_text,
            'content': _extract_text_content(html),
            'structured_data': structured_data,
            'metadata': {'description': description}
        },
        'additional_pages': relevant_pages,
        'total_pages_scraped': 1 + len(relevant_pages),
        'extraction_method': 'basic',
        'content_for_ai': content_for_ai
    }

def _smart_scrape(url: str, requirements: str = "") -> Dict[str, Any]:
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_advanced_smart_scrape(url, requirements))
        loop.close()
        return result
    except Exception as e:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(_basic_smart_scrape(url, requirements))
            loop.close()
            return result
        except Exception as e2:
        return _basic_smart_scrape_sync(url, requirements)

def _basic_smart_scrape_sync(url: str, requirements: str = "") -> Dict[str, Any]:
    html = _fetch(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    title = soup.find('title')
    title_text = title.get_text().strip() if title else "Sans titre"
    
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    description = meta_desc.get('content', '') if meta_desc else ""
    
    structured_data = _extract_structured_data(html)
    
    relevant_pages = []
    if requirements:
        keywords = requirements.lower().split()
        links = soup.find_all('a', href=True)
        
        for link in links:
            link_text = link.get_text().strip().lower()
            link_url = link.get('href', '')
            
            is_relevant = any(keyword in link_text for keyword in keywords)
            
            if is_relevant and link_url.startswith(url):
                relevant_pages.append({
                    'url': link_url,
                    'text': link_text
                })
        
        for i, page in enumerate(relevant_pages[:3]):
            try:
                page_html = _fetch(page['url'])
                page_soup = BeautifulSoup(page_html, 'html.parser')
                page['content'] = _extract_text_content(page_html)
            except Exception as e:
                pass
    
    content_for_ai = f"URL: {url}\nTitre: {title_text}\nDescription: {description}\n\n"
    content_for_ai += f"Contenu principal:\n{_extract_text_content(html)[:3000]}\n\n"
    
    if structured_data:
        content_for_ai += "Données structurées:\n"
        for key, value in structured_data.items():
            content_for_ai += f"{key}: {value}\n"
        content_for_ai += "\n"
    
    return {
        'main_page': {
            'url': url,
            'title': title_text,
            'content': _extract_text_content(html),
            'structured_data': structured_data,
            'metadata': {'description': description}
        },
        'additional_pages': relevant_pages,
        'total_pages_scraped': 1 + len(relevant_pages),
        'extraction_method': 'basic',
        'content_for_ai': content_for_ai
    }

def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        tag.decompose()
    
    for tag in soup.find_all(True):
        if tag.name in ['div', 'p', 'span'] and not tag.get_text().strip():
            tag.decompose()
    
    return str(soup)

def _extract_text_content(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'menu']):
        tag.decompose()
    
    for tag in soup.find_all(True):
        if tag.name in ['div', 'p', 'span'] and not tag.get_text().strip():
            tag.decompose()
    
    main_content_selectors = [
        'main', 'article', '.content', '.main-content', '.post-content', 
        '.entry-content', '#content', '#main', '.container', '.wrapper'
    ]
    
    main_content = ""
    for selector in main_content_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text().strip()
            if len(text) > 50:
                main_content += text + "\n\n"
    
    if not main_content:
        main_content = soup.get_text()
    
    lines = [line.strip() for line in main_content.split('\n') if line.strip()]
    return '\n'.join(lines)

def _extract_links_and_navigation(html: str, base_url: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    
    nav_links = soup.find_all(['nav', 'menu', '.navigation', '.nav', '.menu'])
    for nav in nav_links:
            for link in nav.find_all('a', href=True):
            text = link.get_text().strip()
            href = link.get('href', '')
            
            if text and len(text) > 2:
                if not href.startswith('http'):
                        href = urljoin(base_url, href)
                    
                    links.append({
                        'text': text,
                    'href': href,
                        'type': 'navigation'
                    })
    
    content_links = soup.find_all('a', href=True)
    nav_texts = {link['text'] for link in links}
    
    for link in content_links:
        text = link.get_text().strip()
        href = link.get('href', '')
        
        if text and len(text) > 2 and text not in nav_texts:
            if not href.startswith('http'):
                href = urljoin(base_url, href)
            
                links.append({
                    'text': text,
                'href': href,
                    'type': 'content'
                })
    
    return links[:20]

def _extract_structured_data(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, 'html.parser')
    structured_data = {}
    
    title = soup.find('title')
    if title:
        structured_data['title'] = title.get_text().strip()
    
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        structured_data['description'] = meta_desc.get('content', '')
    
    headings = []
    for i in range(1, 7):
        for h in soup.find_all(f'h{i}'):
            headings.append({
                    'level': i,
                'text': h.get_text().strip()
                })
    if headings:
        structured_data['headings'] = headings[:10]
    
    lists = []
    for ul in soup.find_all(['ul', 'ol']):
        items = [li.get_text().strip() for li in ul.find_all('li')]
        if items:
            lists.append({
                'type': ul.name,
                'items': items[:10]
            })
    if lists:
        structured_data['lists'] = lists[:5]
    
    return structured_data

def _truncate_tokens(text: str) -> str:
    words = text.split()
    if len(words) > MAX_TOKENS // 2:
        return ' '.join(words[:MAX_TOKENS // 2]) + "..."
        return text

def _sanitize_url(url: str) -> str:
    parsed = urlsplit(url)
    if not parsed.scheme:
        url = 'https://' + url
    return url

def _download_image(url: str) -> str:
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        
        filename = quote(url.split('/')[-1].split('?')[0], safe='')
        if not filename or '.' not in filename:
            filename = f"image_{int(time.time())}.jpg"
        
        dest = IMG_DIR / filename
        with open(dest, 'wb') as f:
            f.write(response.content)

            time.sleep(PAUSE_IMG)
        return f"/images/{dest.name}"
    except Exception as e:
        return url

def _dedup(items: List[Dict]) -> List[Dict]:
    seen = set()
    uniq = []
    
    for i, item in enumerate(items):
        key = f"{item.get('title', '')}{item.get('price', '')}{item.get('img', '')}"
        key = key.lower().strip()
        
        if key and key not in seen:
            seen.add(key)
            uniq.append(item)
    
    return uniq

def analyze_website(session_id: str, url: str) -> Dict:
    session = get_or_create_session(session_id)
    session.current_url = url
    
    try:
        scraped_data = _smart_scrape(url)
        content_for_ai = scraped_data.get('content_for_ai', '')
        
        client = OpenAI(api_key=API_KEY)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Analyze this website and determine its type, available data, and extraction strategies."},
                {"role": "user", "content": content_for_ai}
            ],
            tools=[WEBSITE_ANALYSIS_SCHEMA],
            tool_choice={"type": "function", "function": {"name": "analyze_website"}},
            max_tokens=MAX_TOKENS,
            temperature=0.1
        )
        
        tool_call = response.choices[0].message.tool_calls[0]
        analysis = json.loads(tool_call.function.arguments)
        
        session.website_analysis = analysis
        
        ai_response = f"J'ai analysé le site web {url}. "
        ai_response += f"C'est un site de type {analysis.get('website_type', 'inconnu')}. "
        ai_response += f"Les données disponibles incluent: {', '.join(analysis.get('available_data', []))}. "
        ai_response += f"Je recommande: {', '.join(analysis.get('suggested_extractions', []))}"
        
        return {
            "success": True,
            "analysis": analysis,
            "ai_response": ai_response
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ai_response": f"Erreur lors de l'analyse: {str(e)}"
        }

def extract_data_with_requirements(session_id: str, requirements: str) -> Dict:
    session = get_or_create_session(session_id)
    
    if not session.current_url:
        return {
            "success": False,
            "error": "Aucune URL analysée. Utilisez d'abord 'analyze <url>'",
            "ai_response": "Veuillez d'abord analyser un site web avec 'analyze <url>'"
        }
    
    try:
        scraped_data = _smart_scrape(session.current_url, requirements)
        
        content_for_ai = scraped_data.get('content_for_ai', '')
        content_for_ai = _truncate_tokens(content_for_ai)
        
        extraction_prompt = f"""Extrait les données suivantes du site web selon ces exigences: {requirements}

Contenu du site:
{content_for_ai}

Extrait les données demandées et retourne-les dans un format structuré."""

        client = OpenAI(api_key=API_KEY)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Extract structured data from the website content according to the user's requirements."},
                {"role": "user", "content": extraction_prompt}
            ],
            tools=[EXTRACTION_SCHEMA],
            tool_choice={"type": "function", "function": {"name": "extract_data"}},
            max_tokens=MAX_TOKENS,
            temperature=0.1
        )
        
        tool_call = response.choices[0].message.tool_calls[0]
        extraction_result = json.loads(tool_call.function.arguments)
        
        session.extraction_schema = extraction_result
        
        for item in extraction_result.get('items', []):
            if 'img' in item and item['img']:
                item['img_local'] = _download_image(item['img'])
        
        extraction_result['items'] = _dedup(extraction_result.get('items', []))
        
        ai_response = f"J'ai extrait {len(extraction_result.get('items', []))} éléments selon vos exigences: {requirements}. "
        ai_response += f"Méthode d'extraction: {scraped_data.get('extraction_method', 'standard')}. "
        ai_response += f"Pages analysées: {scraped_data.get('total_pages_scraped', 1)}"
        
        return {
            "success": True,
            "data": extraction_result,
            "ai_response": ai_response
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ai_response": f"Erreur lors de l'extraction: {str(e)}"
        }

def chat_message(session_id: str, message: str) -> str:
        return chat_with_ai(session_id, message)

def get_conversation_history(session_id: str) -> List[Dict]:
    session = get_or_create_session(session_id)
    return [
        {
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat()
        }
        for msg in session.messages
    ]

def get_help_info() -> Dict:
    return {
        "commands": {
            "analyze <url>": "Analyse un site web et détermine son type et les données disponibles",
            "extract <requirements>": "Extrait des données selon vos exigences spécifiques",
            "chat <message>": "Pose une question à l'IA sur le scraping ou l'extraction",
            "help": "Affiche cette aide",
            "clear": "Efface l'écran"
        },
        "examples": {
            "analyze https://example.com": "Analyse le site example.com",
            "extract produits avec prix et images": "Extrait les produits avec leurs prix et images",
            "extract articles de blog": "Extrait les articles de blog",
            "chat comment extraire les prix?": "Demande de l'aide sur l'extraction des prix"
        }
    }

def scrape(url: str) -> Dict[str, List[Dict[str, str]]]:
    try:
        url = _sanitize_url(url)
        html = _fetch(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        items = []
        
        for product in soup.find_all(['div', 'article', 'li'], class_=lambda x: x and any(word in x.lower() for word in ['product', 'item', 'card', 'article'])):
            title_elem = product.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', '.title', '.name'])
            price_elem = product.find(class_=lambda x: x and any(word in x.lower() for word in ['price', 'cost', 'amount']))
            img_elem = product.find('img')
            
            title = title_elem.get_text().strip() if title_elem else ""
            price = price_elem.get_text().strip() if price_elem else ""
            img_url = img_elem.get('src', '') if img_elem else ""
            
            if title:
                if img_url and not img_url.startswith('http'):
                    img_url = urljoin(url, img_url)
                
                item = {
                    'title': title,
                    'price': price,
                    'img': img_url
                }
                
                if img_url:
                    item['img_local'] = _download_image(img_url)
                
                items.append(item)
        
        items = _dedup(items)
        
        return {"items": items}
        
    except Exception as e:
        return {"items": [], "error": str(e)}
