"""LinkedIn scraper for both job posts and feed posts."""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from loguru import logger
from playwright.async_api import Page, Browser, async_playwright

class LinkedInScraper:
    """Scraper for LinkedIn jobs and posts."""
    
    def __init__(self, config: Dict):
        """Initialize the scraper with configuration."""
        self.config = config
        self.browser = None
        self.context = None
        self.page = None
        
    async def setup(self):
        """Set up the browser and login to LinkedIn."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        # Login to LinkedIn
        await self._login()
        
    async def _login(self):
        """Login to LinkedIn using credentials from config."""
        try:
            await self.page.goto('https://www.linkedin.com/login')
            await self.page.fill('input[name="session_key"]', self.config['linkedin']['email'])
            await self.page.fill('input[name="session_password"]', self.config['linkedin']['password'])
            await self.page.click('button[type="submit"]')
            await self.page.wait_for_load_state('networkidle')
            
            logger.info("Successfully logged in to LinkedIn")
        except Exception as e:
            logger.error(f"Failed to login to LinkedIn: {e}")
            raise
            
    async def search_feed_posts(self, keywords: List[str], days_back: int = 7) -> List[Dict]:
        """Search LinkedIn feed for job-related posts."""
        posts = []
        
        try:
            # Go to LinkedIn feed
            await self.page.goto('https://www.linkedin.com/feed/')
            await self.page.wait_for_load_state('networkidle')
            
            # Scroll and collect posts
            last_height = await self.page.evaluate('document.body.scrollHeight')
            posts_seen = set()
            
            while len(posts) < 100:  # Limit to 100 posts
                # Extract posts
                new_posts = await self._extract_feed_posts()
                for post in new_posts:
                    if post['url'] not in posts_seen and self._is_job_post(post['text'], keywords):
                        posts_seen.add(post['url'])
                        posts.append(post)
                
                # Scroll down
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(2)  # Wait for new content to load
                
                # Check if we've reached the bottom
                new_height = await self.page.evaluate('document.body.scrollHeight')
                if new_height == last_height:
                    break
                last_height = new_height
                
        except Exception as e:
            logger.error(f"Error searching LinkedIn feed: {e}")
            
        return posts
        
    async def _extract_feed_posts(self) -> List[Dict]:
        """Extract posts from the current feed page."""
        posts = []
        
        # Get all post elements
        post_elements = await self.page.query_selector_all('div.feed-shared-update-v2')
        
        for element in post_elements:
            try:
                # Get post URL
                url_element = await element.query_selector('a.app-aware-link')
                url = await url_element.get_attribute('href') if url_element else None
                
                # Get post text
                text_element = await element.query_selector('div.feed-shared-update-v2__description')
                text = await text_element.inner_text() if text_element else ""
                
                # Get author info
                author_element = await element.query_selector('span.feed-shared-actor__name')
                author = await author_element.inner_text() if author_element else ""
                
                # Get author profile URL
                profile_element = await element.query_selector('a.feed-shared-actor__container-link')
                profile_url = await profile_element.get_attribute('href') if profile_element else None
                
                if url and text:
                    posts.append({
                        'url': urljoin('https://www.linkedin.com', url),
                        'text': text,
                        'author': author,
                        'author_profile': urljoin('https://www.linkedin.com', profile_url) if profile_url else None,
                        'source': 'linkedin_feed',
                        'posted_at': datetime.now().isoformat(),  # We could parse the actual post date if needed
                    })
                    
            except Exception as e:
                logger.error(f"Error extracting post data: {e}")
                continue
                
        return posts
        
    def _is_job_post(self, text: str, keywords: List[str]) -> bool:
        """Check if a post is job-related based on its text and keywords."""
        text_lower = text.lower()
        
        # Job-related phrases
        job_phrases = [
            'hiring',
            'job opening',
            'job opportunity',
            'looking for',
            'position',
            'role',
            'vacancy',
            'vagas',
            'oportunidade',
            'contratando',
        ]
        
        # Check for job phrases
        has_job_phrase = any(phrase in text_lower for phrase in job_phrases)
        
        # Check for keywords
        has_keyword = any(keyword.lower() in text_lower for keyword in keywords)
        
        return has_job_phrase and has_keyword
        
    async def cleanup(self):
        """Clean up resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close() 