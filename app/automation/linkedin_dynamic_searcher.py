"""
LinkedIn Dynamic Searcher
Sistema para buscar vagas dinamicamente no LinkedIn
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path
import re
import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class LinkedInDynamicSearcher:
    """Sistema para buscar vagas dinamicamente no LinkedIn."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.driver = None
        self.wait = None
        self.found_jobs = []
        
        # Keywords for dynamic search
        self.search_keywords = [
            'react', 'python', 'javascript', 'frontend', 'backend', 
            'fullstack', 'nodejs', 'typescript', 'vue', 'angular',
            'java', 'spring', 'django', 'flask', 'express'
        ]
        
        # Job titles variations
        self.job_titles = [
            'developer', 'engineer', 'programmer', 'analyst',
            'specialist', 'consultant', 'architect', 'lead'
        ]
        
        # Locations for Brazil
        self.locations = [
            'Brazil', 'São Paulo', 'Rio de Janeiro', 'Belo Horizonte',
            'Brasília', 'Curitiba', 'Porto Alegre', 'Salvador',
            'Fortaleza', 'Recife', 'Manaus', 'Remote'
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
            
            # Set timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            self.wait = WebDriverWait(self.driver, 20)
            logger.info("✅ Chrome driver configurado para busca dinâmica")
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
    
    async def search_jobs_dynamically(self, max_jobs: int = 50) -> List[Dict[str, Any]]:
        """Search for jobs dynamically using various search combinations."""
        if not self.setup_driver():
            return []
        
        try:
            # Login to LinkedIn
            email = self.config.get('linkedin', {}).get('email', 'felipefrancanogueira@gmail.com')
            password = self.config.get('linkedin', {}).get('password', '')
            
            if not self.login_linkedin(email, password):
                return []
            
            all_jobs = []
            
            # Generate search combinations
            search_combinations = self._generate_search_combinations()
            
            for i, (keyword, location) in enumerate(search_combinations):
                if len(all_jobs) >= max_jobs:
                    break
                
                logger.info(f"🔍 Busca {i+1}/{len(search_combinations)}: {keyword} em {location}")
                jobs = await self._search_combination(keyword, location)
                all_jobs.extend(jobs)
                
                # Delay between searches
                await asyncio.sleep(random.uniform(2, 4))
            
            # Remove duplicates
            unique_jobs = self._remove_duplicates(all_jobs)
            logger.info(f"📊 Total de vagas únicas encontradas: {len(unique_jobs)}")
            
            return unique_jobs[:max_jobs]
            
        except Exception as e:
            logger.error(f"❌ Erro na busca dinâmica: {e}")
            return []
        
        finally:
            self.close_driver()
    
    def _generate_search_combinations(self) -> List[tuple]:
        """Generate search keyword and location combinations."""
        combinations = []
        
        # Primary combinations (most relevant) - High priority
        primary_keywords = ['react', 'python', 'javascript', 'frontend', 'backend', 'fullstack']
        primary_locations = ['Remote', 'Worldwide', 'United States', 'Canada']
        
        for keyword in primary_keywords:
            for location in primary_locations:
                combinations.append((keyword, location))
        
        # Secondary combinations (more diverse) - Medium priority
        secondary_keywords = ['nodejs', 'typescript', 'vue', 'angular', 'java', 'django', 'flask']
        secondary_locations = ['Europe', 'Brazil', 'São Paulo', 'Rio de Janeiro']
        
        for keyword in secondary_keywords:
            for location in secondary_locations:
                combinations.append((keyword, location))
        
        # Tertiary combinations (specialized) - Lower priority
        tertiary_keywords = ['spring', 'express', 'mongodb', 'postgresql', 'aws', 'docker', 'kubernetes']
        tertiary_locations = ['Belo Horizonte', 'Brasília', 'Curitiba', 'Porto Alegre']
        
        for keyword in tertiary_keywords:
            for location in tertiary_locations:
                combinations.append((keyword, location))
        
        # Random combinations for variety
        for _ in range(15):
            keyword = random.choice(self.search_keywords)
            location = random.choice(self.locations)
            combinations.append((keyword, location))
        
        # Shuffle to avoid predictable patterns
        random.shuffle(combinations)
        
        return combinations
    
    async def _search_combination(self, keyword: str, location: str) -> List[Dict[str, Any]]:
        """Search for jobs with specific keyword and location combination."""
        jobs = []
        
        try:
            # Construct optimized search URL with better filters
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location={location}&f_WT=2&f_AL=true&f_JT=F&f_E=2%2C3%2C4&sortBy=DD"
            
            logger.info(f"🔗 Acessando: {search_url}")
            self.driver.get(search_url)
            await asyncio.sleep(3)
            
            # Wait for job listings to load
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".job-card-container, [data-job-id]"))
                )
            except TimeoutException:
                logger.warning(f"⚠️ Nenhuma vaga encontrada para: {keyword} em {location}")
                return jobs
            
            # Scroll to load more jobs
            await self._scroll_to_load_more()
            
            # Extract job information
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, ".job-card-container, [data-job-id]")
            logger.info(f"📋 Encontrados {len(job_elements)} elementos de vaga para: {keyword} em {location}")
            
            for element in job_elements:
                try:
                    job_data = await self._extract_job_data(element, keyword, location)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.debug(f"Erro ao extrair dados da vaga: {e}")
                    continue
            
            logger.info(f"✅ Extraídas {len(jobs)} vagas para: {keyword} em {location}")
            
        except Exception as e:
            logger.error(f"❌ Erro na busca por {keyword} em {location}: {e}")
        
        return jobs
    
    async def _extract_job_data(self, element, keyword: str, location: str) -> Optional[Dict[str, Any]]:
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
            
            # Extract job title with improved selectors
            title = "Unknown Title"
            try:
                title_selectors = [
                    "a[data-control-name='job_card_click']",
                    ".job-card-list__title",
                    "h3 a",
                    ".job-card-container__link",
                    ".job-card-container__title",
                    ".job-card-list__title-link",
                    "a[href*='/jobs/view/']"
                ]
                for selector in title_selectors:
                    try:
                        title_element = element.find_element(By.CSS_SELECTOR, selector)
                        title = title_element.text.strip()
                        if title and len(title) > 3:  # Ensure we have a meaningful title
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract company name
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
            
            # Extract job location
            job_location = location
            try:
                location_selectors = [
                    ".job-card-container__metadata-item",
                    ".job-card-list__metadata-item",
                    ".job-card-container__metadata-wrapper"
                ]
                for selector in location_selectors:
                    try:
                        location_element = element.find_element(By.CSS_SELECTOR, selector)
                        job_location = location_element.text.strip()
                        if job_location:
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
            
            # Check if job has Easy Apply with improved detection
            has_easy_apply = False
            try:
                easy_apply_selectors = [
                    ".//button[contains(@aria-label, 'Easy Apply')]",
                    ".//button[contains(text(), 'Easy Apply')]",
                    ".//span[contains(text(), 'Easy Apply')]",
                    ".//button[contains(@class, 'jobs-apply-button')]",
                    ".//button[contains(@class, 'jobs-apply-button--top-card')]",
                    ".//button[contains(@class, 'jobs-apply-button--footer')]",
                    ".//button[contains(@data-control-name, 'jobdetails_topcard_inapply')]",
                    ".//button[contains(@data-control-name, 'jobdetails_topcard_apply')]"
                ]
                for selector in easy_apply_selectors:
                    try:
                        easy_apply_element = element.find_element(By.XPATH, selector)
                        if easy_apply_element.is_displayed():
                            has_easy_apply = True
                            break
                    except:
                        continue
                
                # Also check for Easy Apply text in the element
                if not has_easy_apply:
                    element_text = element.text.lower()
                    if 'easy apply' in element_text or 'aplicação rápida' in element_text:
                        has_easy_apply = True
                        
            except:
                pass
            
            return {
                'title': title,
                'company': company,
                'location': job_location,
                'url': job_url,
                'description': description,
                'platform': 'linkedin',
                'job_id': job_id,
                'keyword': keyword,
                'search_location': location,
                'has_easy_apply': has_easy_apply,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.debug(f"Erro ao extrair dados da vaga: {e}")
            return None
    
    async def _scroll_to_load_more(self):
        """Scroll to load more job listings."""
        try:
            # Scroll down multiple times to load more jobs
            for i in range(3):
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
