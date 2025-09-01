"""
Real LinkedIn Job Searcher
Searches for real LinkedIn jobs using web scraping
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class RealLinkedInSearcher:
    """Real LinkedIn job searcher using web scraping."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.driver = None
        self.wait = None
        self.found_jobs = []
    
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
            
            self.wait = WebDriverWait(self.driver, 10)
            logger.info("✅ Chrome driver configurado para busca")
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
            email_field.send_keys(email)
            
            # Wait for password field
            password_field = self.driver.find_element(By.ID, "password")
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
    
    async def search_linkedin_jobs(self, keywords: List[str] = None) -> List[Dict[str, Any]]:
        """Search for real LinkedIn jobs."""
        if not keywords:
            keywords = ["react", "python", "javascript", "frontend", "backend", "fullstack"]
        
        all_jobs = []
        
        if not self.setup_driver():
            return all_jobs
        
        try:
            # Login to LinkedIn
            email = self.config.get('email', {}).get('username', 'felipefrancanogueira@gmail.com')
            password = self.config.get('email', {}).get('password', '')
            
            if not self.login_linkedin(email, password):
                return all_jobs
            
            # Search for each keyword
            for keyword in keywords:
                logger.info(f"🔍 Buscando vagas para: {keyword}")
                jobs = await self._search_keyword(keyword)
                all_jobs.extend(jobs)
                await asyncio.sleep(2)  # Delay between searches
            
            # Remove duplicates
            unique_jobs = self._remove_duplicates(all_jobs)
            logger.info(f"📊 Total de vagas únicas encontradas: {len(unique_jobs)}")
            
            return unique_jobs
            
        except Exception as e:
            logger.error(f"❌ Erro na busca de vagas LinkedIn: {e}")
            return all_jobs
        
        finally:
            self.close_driver()
    
    async def _search_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """Search for jobs with specific keyword."""
        jobs = []
        
        try:
            # Construct search URL based on the pattern you provided
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&f_WT=2&geoId=92000000&f_AL=true&distance=25"
            
            logger.info(f"🔗 Acessando: {search_url}")
            self.driver.get(search_url)
            await asyncio.sleep(3)
            
            # Wait for job listings to load
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".job-card-container, [data-job-id]"))
                )
            except TimeoutException:
                logger.warning(f"⚠️ Nenhuma vaga encontrada para: {keyword}")
                return jobs
            
            # Scroll to load more jobs
            await self._scroll_to_load_more()
            
            # Extract job information
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, ".job-card-container, [data-job-id]")
            logger.info(f"📋 Encontrados {len(job_elements)} elementos de vaga para: {keyword}")
            
            for element in job_elements:
                try:
                    job_data = await self._extract_job_data(element, keyword)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.debug(f"Erro ao extrair dados da vaga: {e}")
                    continue
            
            logger.info(f"✅ Extraídas {len(jobs)} vagas para: {keyword}")
            
        except Exception as e:
            logger.error(f"❌ Erro na busca por {keyword}: {e}")
        
        return jobs
    
    async def _scroll_to_load_more(self):
        """Scroll to load more job listings."""
        try:
            # Scroll down multiple times to load more jobs
            for i in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(2)
                
                # Check if "Show more" button exists and click it
                try:
                    show_more_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Show more') or contains(text(), 'Ver mais')]")
                    if show_more_button.is_displayed():
                        show_more_button.click()
                        await asyncio.sleep(2)
                except NoSuchElementException:
                    pass
        except Exception as e:
            logger.debug(f"Erro no scroll: {e}")
    
    async def _extract_job_data(self, element, keyword: str) -> Optional[Dict[str, Any]]:
        """Extract job data from a job element."""
        try:
            # Get job ID from data attribute or extract from URL
            job_id = element.get_attribute("data-job-id")
            if not job_id:
                # Try to extract from href
                try:
                    link_element = element.find_element(By.CSS_SELECTOR, "a[href*='/jobs/view/']")
                    href = link_element.get_attribute("href")
                    job_id = href.split("/jobs/view/")[-1].split("/")[0] if "/jobs/view/" in href else None
                except:
                    return None
            
            if not job_id:
                return None
            
            # Extract job title - try multiple selectors
            title = "Unknown Title"
            try:
                title_selectors = [
                    "a[data-control-name='job_card_click']",
                    ".job-card-list__title",
                    "h3 a",
                    ".job-card-container__link"
                ]
                for selector in title_selectors:
                    try:
                        title_element = element.find_element(By.CSS_SELECTOR, selector)
                        title = title_element.text.strip()
                        if title:
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract company name - try multiple selectors
            company = "Unknown Company"
            try:
                company_selectors = [
                    "h4 a",
                    ".job-card-container__company-name a",
                    ".job-card-container__company-name",
                    ".job-card-list__company-name"
                ]
                for selector in company_selectors:
                    try:
                        company_element = element.find_element(By.CSS_SELECTOR, selector)
                        company = company_element.text.strip()
                        if company:
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract location - try multiple selectors
            location = "Remote"
            try:
                location_selectors = [
                    ".job-card-container__metadata-item",
                    ".job-card-list__metadata-item",
                    ".job-card-container__metadata-wrapper"
                ]
                for selector in location_selectors:
                    try:
                        location_element = element.find_element(By.CSS_SELECTOR, selector)
                        location = location_element.text.strip()
                        if location:
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract job URL
            job_url = f"https://www.linkedin.com/jobs/view/{job_id}"
            
            # Extract description (first few lines)
            description = f"Job opportunity for {keyword} developer at {company}"
            try:
                description_selectors = [
                    ".job-card-container__description",
                    ".job-card-list__description"
                ]
                for selector in description_selectors:
                    try:
                        description_element = element.find_element(By.CSS_SELECTOR, selector)
                        description = description_element.text.strip()[:500]  # First 500 chars
                        if description:
                            break
                    except:
                        continue
            except:
                pass
            
            # Check if job has Easy Apply
            has_easy_apply = False
            try:
                easy_apply_selectors = [
                    ".//button[contains(@aria-label, 'Easy Apply')]",
                    ".//button[contains(text(), 'Easy Apply')]",
                    ".//span[contains(text(), 'Easy Apply')]"
                ]
                for selector in easy_apply_selectors:
                    try:
                        easy_apply_element = element.find_element(By.XPATH, selector)
                        has_easy_apply = True
                        break
                    except:
                        continue
            except:
                pass
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'url': job_url,
                'description': description,
                'platform': 'linkedin',
                'job_id': job_id,
                'keyword': keyword,
                'has_easy_apply': has_easy_apply,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.debug(f"Erro ao extrair dados da vaga: {e}")
            return None
    
    def _remove_duplicates(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate jobs based on job_id."""
        seen_ids = set()
        unique_jobs = []
        
        for job in jobs:
            job_id = job.get('job_id')
            if job_id and job_id not in seen_ids:
                seen_ids.add(job_id)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def close_driver(self):
        """Close the browser driver."""
        if self.driver:
            self.driver.quit()
            logger.info("🔒 Browser fechado")
    
    async def search_posts_for_hiring(self, keywords: List[str] = None) -> List[Dict[str, Any]]:
        """Search LinkedIn posts for hiring announcements."""
        if not keywords:
            keywords = ["react", "python", "javascript"]
        
        posts = []
        
        if not self.setup_driver():
            return posts
        
        try:
            # Login to LinkedIn
            email = self.config.get('email', {}).get('username', 'felipefrancanogueira@gmail.com')
            password = self.config.get('email', {}).get('password', '')
            
            if not self.login_linkedin(email, password):
                return posts
            
            for keyword in keywords:
                # Construct posts search URL based on your example
                search_url = f"https://www.linkedin.com/search/results/content/?keywords=%22{keyword}%22%20AND%20hiring%20AND%20(Brazil%20OR%20Brasil%20OR%20Latam%20OR%20%22Latin%20America%22)&origin=FACETED_SEARCH&sortBy=%22date_posted%22"
                
                logger.info(f"🔍 Buscando posts de contratação para: {keyword}")
                self.driver.get(search_url)
                await asyncio.sleep(3)
                
                # Extract posts (this would need more specific implementation)
                # For now, return empty list as posts are more complex to extract
                
        except Exception as e:
            logger.error(f"❌ Erro na busca de posts: {e}")
        
        finally:
            self.close_driver()
        
        return posts
