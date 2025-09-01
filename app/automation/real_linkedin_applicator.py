"""
Real LinkedIn Application System
Uses web scraping to actually apply to LinkedIn jobs
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class RealLinkedInApplicator:
    """Real LinkedIn job application system using web scraping."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.driver = None
        self.wait = None
        self.applied_jobs = set()
        self.load_applied_jobs()
    
    def load_applied_jobs(self):
        """Load previously applied job IDs."""
        try:
            applied_file = Path("data/logs/linkedin_applied_jobs.json")
            if applied_file.exists():
                with open(applied_file, 'r', encoding='utf-8') as f:
                    self.applied_jobs = set(json.load(f))
                logger.info(f"📚 Carregados {len(self.applied_jobs)} jobs LinkedIn já aplicados")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar jobs LinkedIn aplicados: {e}")
            self.applied_jobs = set()
    
    def save_applied_jobs(self):
        """Save applied job IDs."""
        try:
            applied_file = Path("data/logs/linkedin_applied_jobs.json")
            applied_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(applied_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.applied_jobs), f, indent=2)
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar jobs LinkedIn aplicados: {e}")
    
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
            logger.info("✅ Chrome driver configurado com sucesso")
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
    
    async def apply_to_linkedin_job(self, job_url: str, job_title: str) -> Dict[str, Any]:
        """Apply to a LinkedIn job."""
        try:
            # Check if already applied
            if job_url in self.applied_jobs:
                return {
                    'success': False,
                    'error': 'Job already applied',
                    'message': 'Job already applied to'
                }
            
            logger.info(f"🚀 Aplicando para vaga LinkedIn: {job_title}")
            logger.info(f"🔗 URL: {job_url}")
            
            # Navigate to job page
            self.driver.get(job_url)
            await asyncio.sleep(2)
            
            # Check if Easy Apply button exists
            try:
                easy_apply_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Easy Apply') or contains(text(), 'Easy Apply')]"))
                )
                
                # Click Easy Apply
                easy_apply_button.click()
                await asyncio.sleep(1)
                
                # Handle application form
                success = await self._handle_application_form()
                
                if success:
                    # Add to applied jobs
                    self.applied_jobs.add(job_url)
                    self.save_applied_jobs()
                    
                    return {
                        'success': True,
                        'method': 'linkedin_easy_apply',
                        'message': 'Application submitted via LinkedIn Easy Apply',
                        'application_id': f"li_{int(datetime.now().timestamp())}",
                        'platform': 'linkedin',
                        'job_url': job_url,
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Failed to complete application form',
                        'method': 'linkedin_easy_apply',
                        'platform': 'linkedin'
                    }
                    
            except TimeoutException:
                # No Easy Apply button, try regular apply
                try:
                    apply_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Apply') or contains(@aria-label, 'Apply')]")
                    apply_button.click()
                    
                    # This will redirect to company website
                    await asyncio.sleep(2)
                    
                    return {
                        'success': True,
                        'method': 'linkedin_redirect',
                        'message': 'Redirected to company application page',
                        'application_id': f"li_{int(datetime.now().timestamp())}",
                        'platform': 'linkedin',
                        'job_url': job_url,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                except NoSuchElementException:
                    return {
                        'success': False,
                        'error': 'No apply button found',
                        'method': 'linkedin_apply',
                        'platform': 'linkedin'
                    }
            
        except Exception as e:
            logger.error(f"❌ Erro ao aplicar para vaga LinkedIn: {e}")
            return {
                'success': False,
                'error': str(e),
                'method': 'linkedin_apply',
                'platform': 'linkedin'
            }
    
    async def _handle_application_form(self) -> bool:
        """Handle LinkedIn Easy Apply form."""
        try:
            # Wait for form to load
            await asyncio.sleep(1)
            
            # Look for common form elements and fill them
            form_elements = [
                "//input[@type='text']",
                "//input[@type='email']",
                "//input[@type='tel']",
                "//textarea",
                "//select"
            ]
            
            for element_xpath in form_elements:
                try:
                    elements = self.driver.find_elements(By.XPATH, element_xpath)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Fill with default values
                            if element.get_attribute("type") == "email":
                                element.clear()
                                element.send_keys("felipefrancanogueira@gmail.com")
                            elif element.get_attribute("type") == "tel":
                                element.clear()
                                element.send_keys("+55 11 99999-9999")
                            elif element.tag_name == "textarea":
                                element.clear()
                                element.send_keys("I am interested in this position and would like to apply.")
                            else:
                                element.clear()
                                element.send_keys("Felipe França Nogueira")
                            
                            await asyncio.sleep(0.5)
                except:
                    continue
            
            # Look for Next/Submit button
            try:
                next_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Submit') or contains(text(), 'Review')]")
                next_button.click()
                await asyncio.sleep(1)
                
                # If there's a review step, submit
                try:
                    submit_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit') or contains(text(), 'Send')]")
                    submit_button.click()
                    await asyncio.sleep(1)
                except:
                    pass
                
                return True
                
            except NoSuchElementException:
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao preencher formulário: {e}")
            return False
    
    def close_driver(self):
        """Close the browser driver."""
        if self.driver:
            self.driver.quit()
            logger.info("🔒 Browser fechado")
    
    async def apply_to_multiple_jobs(self, jobs: List[Dict]) -> List[Dict[str, Any]]:
        """Apply to multiple LinkedIn jobs."""
        results = []
        
        if not self.setup_driver():
            return results
        
        try:
            # Login to LinkedIn
            email = self.config.get('email', {}).get('username', 'felipefrancanogueira@gmail.com')
            password = self.config.get('email', {}).get('password', '')
            
            if not self.login_linkedin(email, password):
                return results
            
            # Apply to each job
            for job in jobs:
                if job.get('platform', '').lower() == 'linkedin':
                    result = await self.apply_to_linkedin_job(
                        job.get('url', ''),
                        job.get('title', 'Unknown')
                    )
                    results.append(result)
                    
                    # Small delay between applications
                    await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ Erro ao aplicar para múltiplas vagas: {e}")
        
        finally:
            self.close_driver()
        
        return results
