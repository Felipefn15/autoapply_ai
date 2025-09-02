"""
LinkedIn Post Analyzer
Sistema para analisar posts de contratação e determinar como se inscrever
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
from pathlib import Path
import re
import requests
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class LinkedInPostAnalyzer:
    """Sistema para analisar posts de contratação no LinkedIn."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.driver = None
        self.wait = None
        self.analyzed_posts = set()
        self.load_analyzed_posts()
        
        # Keywords para identificar posts de contratação
        self.hiring_keywords = [
            'hiring', 'contratando', 'vaga', 'job', 'oportunidade', 'trabalho',
            'desenvolvedor', 'developer', 'programador', 'engenheiro', 'engineer',
            'frontend', 'backend', 'fullstack', 'react', 'python', 'javascript',
            'candidatar', 'aplicar', 'apply', 'cv', 'curriculum', 'resume'
        ]
        
        # Padrões para identificar emails
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'contato@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            r'rh@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            r'vagas@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        ]
        
        # Padrões para identificar URLs de aplicação
        self.application_url_patterns = [
            r'https?://[^\s]+',
            r'www\.[^\s]+',
            r'linkedin\.com/in/[^\s]+',
            r'bit\.ly/[^\s]+',
            r'tinyurl\.com/[^\s]+'
        ]
    
    def setup_driver(self):
        """Setup Chrome driver for LinkedIn."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Add user agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 15)
            logger.info("✅ Chrome driver configurado para análise de posts")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar Chrome driver: {e}")
            return False
    
    def login_linkedin(self, email: str, password: str) -> bool:
        """Login to LinkedIn."""
        try:
            logger.info("🔐 Fazendo login no LinkedIn...")
            
            # Go to LinkedIn login page
            self.driver.get("https://www.linkedin.com/login")
            
            # Wait for email field
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.clear()
            email_field.send_keys(email)
            
            # Wait for password field
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "global-nav"))
            )
            
            logger.info("✅ Login no LinkedIn realizado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro no login LinkedIn: {e}")
            return False
    
    def load_analyzed_posts(self):
        """Load previously analyzed post IDs."""
        try:
            analyzed_file = Path("data/logs/linkedin_analyzed_posts.json")
            if analyzed_file.exists():
                with open(analyzed_file, 'r', encoding='utf-8') as f:
                    self.analyzed_posts = set(json.load(f))
                logger.info(f"📚 Carregados {len(self.analyzed_posts)} posts já analisados")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar posts analisados: {e}")
            self.analyzed_posts = set()
    
    def save_analyzed_posts(self):
        """Save analyzed post IDs."""
        try:
            analyzed_file = Path("data/logs/linkedin_analyzed_posts.json")
            analyzed_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(analyzed_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.analyzed_posts), f, indent=2)
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar posts analisados: {e}")
    
    async def search_hiring_posts(self, keywords: List[str] = None) -> List[Dict[str, Any]]:
        """Search for hiring posts on LinkedIn."""
        if not keywords:
            keywords = ["react", "python", "javascript", "frontend", "backend", "fullstack"]
        
        if not self.setup_driver():
            return []
        
        try:
            # Login to LinkedIn
            email = self.config.get('email', {}).get('username', 'felipefrancanogueira@gmail.com')
            password = self.config.get('email', {}).get('password', '')
            
            if not self.login_linkedin(email, password):
                return []
            
            all_posts = []
            
            # Search for each keyword
            for keyword in keywords:
                logger.info(f"🔍 Buscando posts de contratação para: {keyword}")
                posts = await self._search_keyword_posts(keyword)
                all_posts.extend(posts)
                await asyncio.sleep(3)  # Delay between searches
            
            # Remove duplicates
            unique_posts = self._remove_duplicate_posts(all_posts)
            logger.info(f"📊 Total de posts únicos encontrados: {len(unique_posts)}")
            
            return unique_posts
            
        except Exception as e:
            logger.error(f"❌ Erro na busca de posts: {e}")
            return []
        
        finally:
            self.close_driver()
    
    async def _search_keyword_posts(self, keyword: str) -> List[Dict[str, Any]]:
        """Search for hiring posts with specific keyword."""
        posts = []
        
        try:
            # Construct search URL for posts
            search_url = f"https://www.linkedin.com/search/results/content/?keywords=%22{keyword}%22%20AND%20hiring%20AND%20(Brazil%20OR%20Brasil%20OR%20Latam%20OR%20%22Latin%20America%22)&origin=FACETED_SEARCH&sortBy=%22date_posted%22"
            
            logger.info(f"🔗 Acessando: {search_url}")
            self.driver.get(search_url)
            await asyncio.sleep(4)
            
            # Wait for posts to load
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-shared-update-v2, .occludable-update"))
                )
            except TimeoutException:
                logger.warning(f"⚠️ Nenhum post encontrado para: {keyword}")
                return posts
            
            # Scroll to load more posts
            await self._scroll_to_load_more_posts()
            
            # Extract post information
            post_elements = self.driver.find_elements(By.CSS_SELECTOR, ".feed-shared-update-v2, .occludable-update")
            logger.info(f"📋 Encontrados {len(post_elements)} posts para: {keyword}")
            
            for element in post_elements:
                try:
                    post_data = await self._extract_post_data(element, keyword)
                    if post_data and self._is_hiring_post(post_data['content']):
                        posts.append(post_data)
                except Exception as e:
                    logger.debug(f"Erro ao extrair dados do post: {e}")
                    continue
            
            logger.info(f"✅ Extraídos {len(posts)} posts de contratação para: {keyword}")
            
        except Exception as e:
            logger.error(f"❌ Erro na busca por {keyword}: {e}")
        
        return posts
    
    async def _extract_post_data(self, element, keyword: str) -> Optional[Dict[str, Any]]:
        """Extract post data from a post element."""
        try:
            # Extract post content
            content = ""
            try:
                content_element = element.find_element(By.CSS_SELECTOR, ".feed-shared-text, .break-words")
                content = content_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Extract author name
            author = "Unknown Author"
            try:
                author_element = element.find_element(By.CSS_SELECTOR, ".feed-shared-actor__name, .update-components-actor__name")
                author = author_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Extract post URL
            post_url = ""
            try:
                link_element = element.find_element(By.CSS_SELECTOR, "a[href*='/posts/']")
                post_url = link_element.get_attribute("href")
            except NoSuchElementException:
                pass
            
            # Extract post ID from URL
            post_id = ""
            if post_url:
                post_id = post_url.split("/posts/")[-1].split("/")[0] if "/posts/" in post_url else ""
            
            # Extract timestamp
            timestamp = ""
            try:
                time_element = element.find_element(By.CSS_SELECTOR, ".feed-shared-actor__sub-description, .update-components-actor__sub-description")
                timestamp = time_element.text.strip()
            except NoSuchElementException:
                pass
            
            return {
                'post_id': post_id,
                'author': author,
                'content': content,
                'url': post_url,
                'timestamp': timestamp,
                'keyword': keyword,
                'extraction_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.debug(f"Erro ao extrair dados do post: {e}")
            return None
    
    def _is_hiring_post(self, content: str) -> bool:
        """Check if post is about hiring."""
        if not content:
            return False
        
        content_lower = content.lower()
        
        # Check for hiring keywords
        hiring_count = sum(1 for keyword in self.hiring_keywords if keyword.lower() in content_lower)
        
        # Must have at least 2 hiring-related keywords
        return hiring_count >= 2
    
    async def analyze_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a post to determine how to apply."""
        try:
            post_id = post_data.get('post_id', '')
            content = post_data.get('content', '')
            
            # Check if already analyzed
            if post_id in self.analyzed_posts:
                return {
                    'already_analyzed': True,
                    'post_id': post_id,
                    'message': 'Post already analyzed'
                }
            
            logger.info(f"🔍 Analisando post: {post_data.get('author', 'Unknown')}")
            logger.info(f"📝 Conteúdo: {content[:200]}...")
            
            # Extract application information
            analysis_result = {
                'post_id': post_id,
                'author': post_data.get('author', ''),
                'content': content,
                'url': post_data.get('url', ''),
                'analysis_timestamp': datetime.now().isoformat(),
                'application_method': None,
                'application_details': {},
                'confidence': 0
            }
            
            # Extract emails
            emails = self._extract_emails(content)
            if emails:
                analysis_result['application_method'] = 'email'
                analysis_result['application_details']['emails'] = emails
                analysis_result['confidence'] = 0.8
                logger.info(f"📧 Emails encontrados: {emails}")
            
            # Extract URLs
            urls = self._extract_urls(content)
            if urls:
                if analysis_result['application_method'] is None:
                    analysis_result['application_method'] = 'website'
                analysis_result['application_details']['urls'] = urls
                analysis_result['confidence'] = max(analysis_result['confidence'], 0.7)
                logger.info(f"🔗 URLs encontradas: {urls}")
            
            # Extract phone numbers
            phones = self._extract_phones(content)
            if phones:
                analysis_result['application_details']['phones'] = phones
                logger.info(f"📞 Telefones encontrados: {phones}")
            
            # Extract job requirements
            requirements = self._extract_requirements(content)
            if requirements:
                analysis_result['application_details']['requirements'] = requirements
                logger.info(f"📋 Requisitos encontrados: {requirements}")
            
            # If no clear application method, try to infer from content
            if analysis_result['application_method'] is None:
                analysis_result['application_method'] = self._infer_application_method(content)
                analysis_result['confidence'] = 0.5
            
            # Mark as analyzed
            self.analyzed_posts.add(post_id)
            self.save_analyzed_posts()
            
            logger.info(f"✅ Análise concluída: {analysis_result['application_method']} (confiança: {analysis_result['confidence']})")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Erro na análise do post: {e}")
            return {
                'error': str(e),
                'post_id': post_data.get('post_id', ''),
                'application_method': None
            }
    
    def _extract_emails(self, content: str) -> List[str]:
        """Extract email addresses from content."""
        emails = []
        for pattern in self.email_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            emails.extend(matches)
        
        # Remove duplicates and filter out common false positives
        unique_emails = list(set(emails))
        filtered_emails = [email for email in unique_emails if not self._is_false_positive_email(email)]
        
        return filtered_emails
    
    def _extract_urls(self, content: str) -> List[str]:
        """Extract URLs from content."""
        urls = []
        for pattern in self.application_url_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            urls.extend(matches)
        
        # Remove duplicates and filter out common false positives
        unique_urls = list(set(urls))
        filtered_urls = [url for url in unique_urls if not self._is_false_positive_url(url)]
        
        return filtered_urls
    
    def _extract_phones(self, content: str) -> List[str]:
        """Extract phone numbers from content."""
        phone_patterns = [
            r'\(\d{2}\)\s?\d{4,5}-?\d{4}',
            r'\d{2}\s?\d{4,5}-?\d{4}',
            r'\+55\s?\d{2}\s?\d{4,5}-?\d{4}'
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, content)
            phones.extend(matches)
        
        return list(set(phones))
    
    def _extract_requirements(self, content: str) -> List[str]:
        """Extract job requirements from content."""
        requirements = []
        
        # Common requirement patterns
        requirement_patterns = [
            r'requisitos?:?\s*([^.]*)',
            r'experiência:?\s*([^.]*)',
            r'conhecimento:?\s*([^.]*)',
            r'habilidades:?\s*([^.]*)'
        ]
        
        for pattern in requirement_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            requirements.extend(matches)
        
        return requirements
    
    def _infer_application_method(self, content: str) -> str:
        """Infer application method from content."""
        content_lower = content.lower()
        
        # Check for email-related keywords
        email_keywords = ['email', 'e-mail', 'contato', 'enviar', 'mandar']
        if any(keyword in content_lower for keyword in email_keywords):
            return 'email'
        
        # Check for website-related keywords
        website_keywords = ['site', 'website', 'aplicar', 'candidatar', 'inscrever']
        if any(keyword in content_lower for keyword in website_keywords):
            return 'website'
        
        # Default to email
        return 'email'
    
    def _is_false_positive_email(self, email: str) -> bool:
        """Check if email is a false positive."""
        false_positives = [
            'example.com', 'test.com', 'sample.com', 'placeholder.com',
            'linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com'
        ]
        
        return any(fp in email.lower() for fp in false_positives)
    
    def _is_false_positive_url(self, url: str) -> bool:
        """Check if URL is a false positive."""
        false_positives = [
            'linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com',
            'youtube.com', 'google.com', 'example.com'
        ]
        
        return any(fp in url.lower() for fp in false_positives)
    
    async def _scroll_to_load_more_posts(self):
        """Scroll to load more posts."""
        try:
            # Scroll down multiple times to load more posts
            for i in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(2)
        except Exception as e:
            logger.debug(f"Erro no scroll: {e}")
    
    def _remove_duplicate_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate posts based on post_id."""
        seen_ids = set()
        unique_posts = []
        
        for post in posts:
            post_id = post.get('post_id')
            if post_id and post_id not in seen_ids:
                seen_ids.add(post_id)
                unique_posts.append(post)
        
        return unique_posts
    
    def close_driver(self):
        """Close the browser driver."""
        if self.driver:
            self.driver.quit()
            logger.info("🔒 Browser fechado")
