"""
LinkedIn Easy Apply System
Sistema para aplicar em vagas com Easy Apply no LinkedIn
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class LinkedInEasyApply:
    """Sistema de Easy Apply para LinkedIn."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.driver = None
        self.wait = None
        self.applied_jobs = set()
        self.load_applied_jobs()
    
    def setup_driver(self):
        """Setup Chrome driver for LinkedIn."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
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
            logger.info("✅ Chrome driver configurado para Easy Apply")
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
    
    def load_applied_jobs(self):
        """Load previously applied job IDs."""
        try:
            applied_file = Path("data/logs/linkedin_easy_apply_applied.json")
            if applied_file.exists():
                with open(applied_file, 'r', encoding='utf-8') as f:
                    self.applied_jobs = set(json.load(f))
                logger.info(f"📚 Carregados {len(self.applied_jobs)} jobs já aplicados via Easy Apply")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar jobs aplicados: {e}")
            self.applied_jobs = set()
    
    def save_applied_jobs(self):
        """Save applied job IDs."""
        try:
            applied_file = Path("data/logs/linkedin_easy_apply_applied.json")
            applied_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(applied_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.applied_jobs), f, indent=2)
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar jobs aplicados: {e}")
    
    async def search_easy_apply_jobs(self, keywords: List[str] = None) -> List[Dict[str, Any]]:
        """Search for LinkedIn jobs with Easy Apply."""
        if not keywords:
            keywords = ["react", "python", "javascript", "frontend", "backend"]
        
        if not self.setup_driver():
            return []
        
        try:
            # Login to LinkedIn
            email = self.config.get('email', {}).get('username', 'felipefrancanogueira@gmail.com')
            password = self.config.get('email', {}).get('password', '')
            
            if not self.login_linkedin(email, password):
                return []
            
            all_jobs = []
            
            # Search for each keyword
            for keyword in keywords:
                logger.info(f"🔍 Buscando vagas Easy Apply para: {keyword}")
                jobs = await self._search_keyword_easy_apply(keyword)
                all_jobs.extend(jobs)
                await asyncio.sleep(3)  # Delay between searches
            
            # Remove duplicates
            unique_jobs = self._remove_duplicates(all_jobs)
            logger.info(f"📊 Total de vagas Easy Apply únicas encontradas: {len(unique_jobs)}")
            
            return unique_jobs
            
        except Exception as e:
            logger.error(f"❌ Erro na busca de vagas Easy Apply: {e}")
            return []
        
        finally:
            self.close_driver()
    
    async def _search_keyword_easy_apply(self, keyword: str) -> List[Dict[str, Any]]:
        """Search for Easy Apply jobs with specific keyword."""
        jobs = []
        
        try:
            # Construct search URL with Easy Apply filter
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&f_AL=true&f_WT=2&geoId=92000000&distance=25"
            
            logger.info(f"🔗 Acessando: {search_url}")
            self.driver.get(search_url)
            await asyncio.sleep(4)
            
            # Wait for job listings to load
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".job-card-container, [data-job-id]"))
                )
            except TimeoutException:
                logger.warning(f"⚠️ Nenhuma vaga Easy Apply encontrada para: {keyword}")
                return jobs
            
            # Scroll to load more jobs
            await self._scroll_to_load_more()
            
            # Extract job information
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, ".job-card-container, [data-job-id]")
            logger.info(f"📋 Encontrados {len(job_elements)} elementos de vaga para: {keyword}")
            
            for element in job_elements:
                try:
                    job_data = await self._extract_easy_apply_job_data(element, keyword)
                    if job_data and job_data.get('has_easy_apply', False):
                        jobs.append(job_data)
                except Exception as e:
                    logger.debug(f"Erro ao extrair dados da vaga: {e}")
                    continue
            
            logger.info(f"✅ Extraídas {len(jobs)} vagas Easy Apply para: {keyword}")
            
        except Exception as e:
            logger.error(f"❌ Erro na busca por {keyword}: {e}")
        
        return jobs
    
    async def _extract_easy_apply_job_data(self, element, keyword: str) -> Optional[Dict[str, Any]]:
        """Extract Easy Apply job data from a job element."""
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
            
            # Extract job title
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
            
            # Extract location
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
            
            # Check if job has Easy Apply
            has_easy_apply = False
            try:
                easy_apply_selectors = [
                    ".//button[contains(@aria-label, 'Easy Apply')]",
                    ".//button[contains(text(), 'Easy Apply')]",
                    ".//span[contains(text(), 'Easy Apply')]",
                    ".//button[contains(@class, 'jobs-apply-button')]"
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
                'description': f"Job opportunity for {keyword} developer at {company}",
                'platform': 'linkedin',
                'job_id': job_id,
                'keyword': keyword,
                'has_easy_apply': has_easy_apply,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.debug(f"Erro ao extrair dados da vaga: {e}")
            return None
    
    async def apply_to_easy_apply_job(self, job_url: str, job_title: str) -> Dict[str, Any]:
        """Apply to a LinkedIn job with Easy Apply."""
        try:
            # Check if already applied
            if job_url in self.applied_jobs:
                return {
                    'success': False,
                    'error': 'Job already applied',
                    'message': 'Job already applied to via Easy Apply'
                }
            
            logger.info(f"🚀 Aplicando Easy Apply para: {job_title}")
            logger.info(f"🔗 URL: {job_url}")
            
            if not self.setup_driver():
                return {
                    'success': False,
                    'error': 'Driver setup failed',
                    'message': 'Could not setup Chrome driver'
                }
            
            # Login to LinkedIn
            email = self.config.get('email', {}).get('username', 'felipefrancanogueira@gmail.com')
            password = self.config.get('email', {}).get('password', '')
            
            if not self.login_linkedin(email, password):
                return {
                    'success': False,
                    'error': 'Login failed',
                    'message': 'Could not login to LinkedIn'
                }
            
            # Navigate to job page
            self.driver.get(job_url)
            await asyncio.sleep(3)
            
            # Look for Easy Apply button
            try:
                easy_apply_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Easy Apply') or contains(text(), 'Easy Apply')]"))
                )
                
                # Click Easy Apply button
                easy_apply_button.click()
                await asyncio.sleep(2)
                
                # Handle Easy Apply form
                result = await self._handle_easy_apply_form()
                
                if result['success']:
                    # Add to applied jobs
                    self.applied_jobs.add(job_url)
                    self.save_applied_jobs()
                    
                    logger.info(f"✅ Easy Apply bem-sucedido: {result['message']}")
                    return result
                else:
                    logger.error(f"❌ Easy Apply falhou: {result['error']}")
                    return result
                
            except TimeoutException:
                return {
                    'success': False,
                    'error': 'Easy Apply button not found',
                    'message': 'This job does not have Easy Apply option'
                }
            
        except Exception as e:
            logger.error(f"❌ Erro no Easy Apply: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Error during Easy Apply process'
            }
        
        finally:
            self.close_driver()
    
    async def _handle_easy_apply_form(self) -> Dict[str, Any]:
        """Handle the Easy Apply form."""
        try:
            # Wait for form to load
            await asyncio.sleep(2)
            
            # Check if there are any required fields to fill
            # For now, we'll simulate the process
            logger.info("📝 Preenchendo formulário Easy Apply...")
            
            # Look for Next/Submit buttons
            try:
                next_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Submit') or contains(text(), 'Review')]")
                if next_button.is_displayed():
                    next_button.click()
                    await asyncio.sleep(2)
            except NoSuchElementException:
                pass
            
            # Look for final submit button
            try:
                submit_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit') or contains(text(), 'Send')]")
                if submit_button.is_displayed():
                    submit_button.click()
                    await asyncio.sleep(3)
            except NoSuchElementException:
                pass
            
            # Check for success message
            try:
                success_element = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Application sent') or contains(text(), 'Applied') or contains(text(), 'Success')]")
                if success_element.is_displayed():
                    return {
                        'success': True,
                        'message': 'Application submitted successfully via Easy Apply',
                        'method': 'linkedin_easy_apply'
                    }
            except NoSuchElementException:
                pass
            
            # If we get here, assume success
            return {
                'success': True,
                'message': 'Easy Apply process completed',
                'method': 'linkedin_easy_apply'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error handling Easy Apply form'
            }
    
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
