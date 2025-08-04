#!/usr/bin/env python3

import asyncio
import time
import random
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
import logging
from dataclasses import dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

try:
    from newspaper import Article, Config
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False

try:
    from readability import Document
    READABILITY_AVAILABLE = True
except ImportError:
    READABILITY_AVAILABLE = False

try:
    import extruct
    EXTRUCT_AVAILABLE = True
except ImportError:
    EXTRUCT_AVAILABLE = False

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    import undetected_chromedriver as uc
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError as e:
    SELENIUM_AVAILABLE = False
except Exception as e:
    SELENIUM_AVAILABLE = False

try:
    from requests_html import HTMLSession
    REQUESTS_HTML_AVAILABLE = True
except ImportError:
    REQUESTS_HTML_AVAILABLE = False

@dataclass
class ScrapedContent:
    url: str
    title: str
    meta_description: str
    main_content: str
    structured_data: Dict[str, Any]
    images: List[Dict[str, str]]
    links: List[Dict[str, str]]
    metadata: Dict[str, Any]
    raw_html: str
    rendered_html: Optional[str] = None
    extraction_method: str = "basic"

class AdvancedScraper:
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def _setup_session(self):
        retry_strategy = requests.adapters.Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    async def scrape_advanced(self, url: str, use_js: bool = True, max_pages: int = 5) -> ScrapedContent:
        self._setup_session()
        
        html = await self._fetch_with_fallback(url, use_js)
        
        scraped_content = await self._extract_with_multiple_methods(url, html)
        
        if max_pages > 1:
            additional_content = await self._scrape_additional_pages(url, html, max_pages)
            if additional_content:
                scraped_content.main_content += "\n\n" + additional_content
        
        return scraped_content
    
    async def _fetch_with_fallback(self, url: str, use_js: bool) -> str:
        methods = []
        
        if use_js:
            if PLAYWRIGHT_AVAILABLE:
                methods.append(("Playwright", self._fetch_with_playwright))
            if SELENIUM_AVAILABLE:
                methods.append(("Selenium", self._fetch_with_selenium))
            if REQUESTS_HTML_AVAILABLE:
                methods.append(("Requests-HTML", self._fetch_with_requests_html))
        
        methods.append(("Requests", self._fetch_with_requests))
        
        js_heavy_sites = ['news.ycombinator.com', 'reddit.com', 'twitter.com', 'facebook.com']
        is_js_heavy = any(site in url for site in js_heavy_sites)
        
        if is_js_heavy and SELENIUM_AVAILABLE:
            methods.insert(0, ("Selenium", self._fetch_with_selenium))
        
        for method_name, method_func in methods:
            try:
                if asyncio.iscoroutinefunction(method_func):
                    html = await method_func(url)
                else:
                    html = method_func(url)
                
                if html and len(html) > 1000:
                    return html
            except Exception as e:
                continue
        
        raise Exception("All fetching methods failed")
    
    async def _fetch_with_playwright(self, url: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            await page.wait_for_timeout(random.randint(1000, 3000))
            
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            
            html = await page.content()
            await browser.close()
            return html
    
    def _fetch_with_selenium(self, url: str) -> str:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"--user-agent={self.ua.random}")
        
        try:
            driver = webdriver.Chrome(options=options)
        except:
            driver = uc.Chrome(options=options)
        
        try:
            driver.get(url)
            time.sleep(random.uniform(2, 4))
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            if "news.ycombinator.com" in url:
                time.sleep(3)
                
                articles = driver.find_elements("css selector", ".athing")
                if len(articles) > 0:
                    pass
            
            html = driver.page_source
            driver.quit()
            return html
        except Exception as e:
            driver.quit()
            raise e
    
    def _fetch_with_requests_html(self, url: str) -> str:
        session = HTMLSession()
        response = session.get(url)
        response.html.render(timeout=20)
        return response.html.html
    
    def _fetch_with_requests(self, url: str) -> str:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    
    async def _extract_with_multiple_methods(self, url: str, html: str) -> ScrapedContent:
        soup = BeautifulSoup(html, 'html.parser')
        
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ""
        
        main_content = ""
        structured_data = {}
        metadata = {}
        
        if NEWSPAPER_AVAILABLE:
            try:
                article = Article(url)
                article.download(input_html=html)
                article.parse()
                main_content = article.text
                metadata['newspaper'] = {
                    'authors': article.authors,
                    'publish_date': str(article.publish_date) if article.publish_date else None,
                    'top_image': article.top_image,
                    'meta_img': article.meta_img,
                    'tags': article.tags,
                    'meta_keywords': article.meta_keywords
                }
            except Exception as e:
                pass
        
        if not main_content and READABILITY_AVAILABLE:
            try:
                doc = Document(html)
                main_content = doc.summary()
            except Exception as e:
                pass
        
        if EXTRUCT_AVAILABLE:
            try:
                structured_data = extruct.extract(html, url)
            except Exception as e:
                pass
        
        if not main_content:
            main_content = self._extract_basic_content(html)
        
        metadata.update(self._extract_enhanced_metadata(html))
        images = self._extract_images(url, html)
        links = self._extract_links(url, html)
        
        return ScrapedContent(
            url=url,
            title=title_text,
            meta_description=description,
            main_content=main_content,
            structured_data=structured_data,
            images=images,
            links=links,
            metadata=metadata,
            raw_html=html,
            extraction_method="advanced"
        )
    
    def _extract_with_newspaper(self, url: str, html: str) -> Dict[str, str]:
        if not NEWSPAPER_AVAILABLE:
            return {}
        
        try:
            article = Article(url)
            article.download(input_html=html)
            article.parse()
            return {
                'text': article.text,
                'title': article.title,
                'authors': article.authors,
                'publish_date': str(article.publish_date) if article.publish_date else None,
                'top_image': article.top_image,
                'meta_img': article.meta_img,
                'tags': article.tags,
                'meta_keywords': article.meta_keywords
            }
        except Exception as e:
            return {}
    
    def _extract_with_readability(self, html: str) -> str:
        if not READABILITY_AVAILABLE:
            return ""
        
        try:
            doc = Document(html)
            return doc.summary()
        except Exception as e:
            return ""
    
    def _extract_structured_data(self, url: str, html: str) -> Dict[str, Any]:
        if not EXTRUCT_AVAILABLE:
            return {}
        
        try:
            return extruct.extract(html, url)
        except Exception as e:
            return {}
    
    def _extract_enhanced_metadata(self, html: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {}
        
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name', meta.get('property', ''))
            content = meta.get('content', '')
            if name and content:
                metadata[name] = content
        
        open_graph = {}
        for meta in soup.find_all('meta', property=lambda x: x and x.startswith('og:')):
            property_name = meta.get('property', '').replace('og:', '')
            content = meta.get('content', '')
            if property_name and content:
                open_graph[property_name] = content
        
        if open_graph:
            metadata['open_graph'] = open_graph
        
        twitter_cards = {}
        for meta in soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')}):
            name = meta.get('name', '').replace('twitter:', '')
            content = meta.get('content', '')
            if name and content:
                twitter_cards[name] = content
        
        if twitter_cards:
            metadata['twitter_cards'] = twitter_cards
        
        json_ld = []
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                json_ld.append(data)
            except:
                continue
        
        if json_ld:
            metadata['json_ld'] = json_ld
        
        return metadata
    
    def _extract_images(self, base_url: str, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, 'html.parser')
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            
            if src:
                if not src.startswith('http'):
                    src = urljoin(base_url, src)
                
                parent_tag = img.parent.name if img.parent else ''
                
                images.append({
                    'src': src,
                    'alt': alt,
                    'parent_tag': parent_tag
                })
        
        return images[:20]
    
    def _extract_links(self, base_url: str, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text().strip()
            
            if href and text:
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                
                link_type = self._determine_link_type(href, text)
                
                links.append({
                    'href': href,
                    'text': text,
                    'type': link_type
                })
        
        return links[:30]
    
    def _determine_link_type(self, url: str, text: str) -> str:
        url_lower = url.lower()
        text_lower = text.lower()
        
        if any(word in url_lower for word in ['contact', 'about', 'team']):
            return 'contact'
        elif any(word in url_lower for word in ['product', 'item', 'buy', 'shop']):
            return 'product'
        elif any(word in url_lower for word in ['article', 'post', 'blog', 'news']):
            return 'article'
        elif any(word in url_lower for word in ['login', 'signup', 'register']):
            return 'auth'
        else:
            return 'general'
    
    def _extract_basic_content(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
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
    
    async def _scrape_additional_pages(self, base_url: str, main_html: str, max_pages: int) -> str:
        soup = BeautifulSoup(main_html, 'html.parser')
        additional_content = []
        
        links = soup.find_all('a', href=True)
        relevant_links = []
        
        for link in links:
            href = link.get('href', '')
            text = link.get_text().strip().lower()
            
            if not href.startswith('http'):
                href = urljoin(base_url, href)
            
            if href.startswith(base_url) and len(text) > 3:
                skip_words = ['contact', 'about', 'privacy', 'terms', 'login', 'signup']
                if not any(word in text for word in skip_words):
                    relevant_links.append((href, text))
        
        for i, (url, text) in enumerate(relevant_links[:max_pages-1]):
            try:
                html = await self._fetch_with_fallback(url, use_js=False)
                content = self._extract_basic_content(html)
                if content:
                    additional_content.append(f"=== {text} ===\n{content}")
                
                await asyncio.sleep(random.uniform(1, 2))
            except Exception as e:
                continue
        
        return "\n\n".join(additional_content)

advanced_scraper = AdvancedScraper() 