#!/usr/bin/env python3
"""
LinkedIn Ultimate Smart Easy Apply System
Sistema definitivo que preenche TODOS os campos dos formulários automaticamente
"""

import asyncio
import logging
import random
import time
import re
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Optional, Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

class LinkedInUltimateSmartApply:
    """Sistema definitivo de Easy Apply que preenche TODOS os campos automaticamente."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.driver = None
        self.wait = None
        self.applied_jobs = set()
        self.resume_data = {}
        self.load_applied_data()
        self.load_resume_data()
        
        # Credenciais
        self.email = config.get('linkedin', {}).get('email', '')
        self.password = config.get('linkedin', {}).get('password', '')
        
        logger.info(f"📧 Email LinkedIn: {self.email}")
        logger.info(f"🚀 Sistema Ultimate Smart Easy Apply Inicializado")
    
    def load_applied_data(self):
        """Load previously applied job IDs."""
        try:
            applied_file = Path("data/logs/linkedin_ultimate_applied.json")
            if applied_file.exists():
                with open(applied_file, 'r', encoding='utf-8') as f:
                    self.applied_jobs = set(json.load(f))
                logger.info(f"📚 Carregados {len(self.applied_jobs)} jobs já aplicados")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar dados: {e}")
            self.applied_jobs = set()
    
    def save_applied_data(self):
        """Save applied job IDs."""
        try:
            applied_file = Path("data/logs/linkedin_ultimate_applied.json")
            applied_file.parent.mkdir(parents=True, exist_ok=True)
            with open(applied_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.applied_jobs), f, indent=2)
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar dados: {e}")
    
    def load_resume_data(self):
        """Load resume data from profile.yaml."""
        try:
            import yaml
            
            # Load profile data
            profile_path = Path("config/profile.yaml")
            if profile_path.exists():
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile_data = yaml.safe_load(f)
                
                # Extract data from profile
                personal = profile_data.get('personal', {})
                experience = profile_data.get('experience', {})
                skills = profile_data.get('skills_list', [])
                salary = profile_data.get('salary', {})
                custom_questions = profile_data.get('application_preferences', {}).get('custom_questions', {})
                
                self.resume_data = {
                    'name': personal.get('name', 'Felipe França Nogueira'),
                    'email': personal.get('email', 'felipefrancanogueira@gmail.com'),
                    'phone': personal.get('phone', '+5521969689811'),
                    'location': personal.get('location', 'Rio de Janeiro, Brasil'),
                    'linkedin': personal.get('linkedin', 'https://linkedin.com/in/felipefrancanogueira'),
                    'github': personal.get('github', 'https://github.com/Felipefn15'),
                    'cpf': personal.get('cpf', '166.546.297-36').replace('.', '').replace('-', ''),
                    'years_of_experience': experience.get('years', 7),
                    'current_role': experience.get('current_role', 'Full-stack Developer'),
                    'current_company': experience.get('current_company', 'Originate'),
                    'salary_expectation': str(salary.get('min_monthly', 4000)),
                    'salary_currency': salary.get('currency', 'USD'),
                    'skills': skills,
                    'core_technologies': profile_data.get('core_technologies', []),
                    'education': profile_data.get('education', []),
                    'certifications': profile_data.get('certifications', []),
                    'custom_questions': custom_questions,
                    'preferences': profile_data.get('preferences', {}),
                    'achievements': profile_data.get('application_preferences', {}).get('highlight_achievements', [])
                }
                
                logger.info(f"📄 Perfil carregado: {self.resume_data['name']}")
                logger.info(f"💼 Experiência: {self.resume_data['years_of_experience']} anos")
                logger.info(f"🛠️ Skills: {len(self.resume_data['skills'])} tecnologias")
                logger.info(f"💰 Salário: ${self.resume_data['salary_expectation']} {self.resume_data['salary_currency']}")
                
            else:
                logger.warning("⚠️ Arquivo profile.yaml não encontrado, usando dados padrão")
                self._load_default_data()
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar perfil: {e}")
            self._load_default_data()
    
    def _load_default_data(self):
        """Load default data if profile loading fails."""
        self.resume_data = {
            'name': 'Felipe França Nogueira',
            'email': 'felipefrancanogueira@gmail.com',
            'phone': '+5521969689811',
            'location': 'Rio de Janeiro, Brasil',
            'linkedin': 'https://linkedin.com/in/felipefrancanogueira',
            'github': 'https://github.com/Felipefn15',
            'cpf': '16654629736',
            'years_of_experience': 7,
            'current_role': 'Full-stack Developer',
            'current_company': 'Originate',
            'salary_expectation': '4000',
            'salary_currency': 'USD',
            'skills': ['React', 'TypeScript', 'Node.js', 'Python', 'Next.js'],
            'core_technologies': ['JavaScript', 'React', 'React Native', 'Next.js', 'Node.js'],
            'education': [],
            'certifications': [],
            'custom_questions': {},
            'preferences': {},
            'achievements': []
        }
    
    def setup_driver(self):
        """Setup Chrome driver with advanced options."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            self.wait = WebDriverWait(self.driver, 20)
            
            logger.info("✅ Chrome driver configurado com anti-detecção avançada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar driver: {e}")
            return False
    
    def login_linkedin(self) -> bool:
        """Login to LinkedIn."""
        try:
            logger.info("🔐 Fazendo login no LinkedIn...")
            
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(3)
            
            # Fill email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.clear()
            email_field.send_keys(self.email)
            
            # Fill password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Click login
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            time.sleep(5)
            
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                logger.info("✅ Login realizado com sucesso")
                return True
            else:
                logger.error("❌ Login falhou")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no login: {e}")
            return False
    
    async def search_and_apply_jobs(self, max_applications: int = 2) -> Dict[str, Any]:
        """Search for and apply to Easy Apply jobs with ultimate form filling."""
        try:
            if not self.setup_driver():
                return {'success': False, 'error': 'Driver setup failed'}
            
            if not self.login_linkedin():
                return {'success': False, 'error': 'Login failed'}
            
            # Search for Easy Apply jobs
            search_url = "https://www.linkedin.com/jobs/search/?keywords=software%20engineer&location=Remote&f_WT=2&f_AL=true&f_JT=F&f_E=2%2C3%2C4&sortBy=DD"
            self.driver.get(search_url)
            time.sleep(5)
            
            # Wait for job listings
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".job-card-container"))
                )
            except TimeoutException:
                logger.warning("⚠️ Nenhuma vaga encontrada")
                return {'success': False, 'error': 'No jobs found'}
            
            applications = 0
            successful_applications = 0
            
            # Process jobs one by one
            for i in range(max_applications):
                try:
                    logger.info(f"🔄 Processando vaga {i+1}/{max_applications}")
                    
                    # Re-find job cards each time
                    job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
                    if i >= len(job_cards):
                        logger.info("ℹ️ Não há mais vagas disponíveis")
                        break
                    
                    # Click on job card
                    job_cards[i].click()
                    time.sleep(3)
                    
                    # Get job details
                    job_title = self._get_job_title()
                    company = self._get_company_name()
                    job_url = self.driver.current_url
                    
                    if not job_title or not company:
                        logger.warning(f"⚠️ Dados incompletos da vaga {i+1}")
                        continue
                    
                    logger.info(f"🚀 Vaga {i+1}: {job_title} - {company}")
                    
                    # Check if already applied
                    if job_url in self.applied_jobs:
                        logger.info(f"ℹ️ Já aplicado para: {job_title}")
                        continue
                    
                    # Try to apply with ultimate form filling
                    result = await self._ultimate_apply_to_job(job_title, company, job_url)
                    applications += 1
                    
                    if result['success']:
                        successful_applications += 1
                        self.applied_jobs.add(job_url)
                        logger.info(f"✅ Aplicação bem-sucedida: {job_title}")
                    else:
                        logger.info(f"❌ Aplicação falhou: {job_title} - {result.get('error', 'Unknown error')}")
                    
                    # Wait between applications
                    await asyncio.sleep(random.uniform(5, 8))
                    
                except Exception as e:
                    logger.error(f"❌ Erro na vaga {i+1}: {e}")
                    continue
            
            # Save data
            self.save_applied_data()
            
            logger.info(f"📊 Total de aplicações: {applications}")
            logger.info(f"✅ Aplicações bem-sucedidas: {successful_applications}")
            
            return {
                'success': True,
                'total_applications': applications,
                'successful_applications': successful_applications,
                'failed_applications': applications - successful_applications
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na busca e aplicação: {e}")
            return {'success': False, 'error': str(e)}
        
        finally:
            self.close_driver()
    
    async def _ultimate_apply_to_job(self, job_title: str, company: str, job_url: str) -> Dict[str, Any]:
        """Ultimate apply to job with complete form filling."""
        try:
            # Look for Easy Apply button
            easy_apply_button = self._find_easy_apply_button()
            
            if not easy_apply_button:
                return {
                    'success': False,
                    'error': 'Easy Apply button not found',
                    'message': 'This job does not have Easy Apply option'
                }
            
            # Click Easy Apply button
            easy_apply_button.click()
            time.sleep(3)
            
            # Handle the application form with ultimate filling
            result = await self._handle_ultimate_application_form()
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao aplicar para {job_title}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Error during application process'
            }
    
    def _find_easy_apply_button(self) -> Optional[Any]:
        """Find Easy Apply button."""
        selectors = [
            "button[aria-label*='Easy Apply']",
            "button[data-control-name*='jobdetails_topcard_inapply']",
            ".jobs-apply-button--top-card",
            ".jobs-apply-button"
        ]
        
        for selector in selectors:
            try:
                button = self.driver.find_element(By.CSS_SELECTOR, selector)
                if button.is_displayed() and button.is_enabled():
                    return button
            except:
                continue
        
        return None
    
    async def _handle_ultimate_application_form(self) -> Dict[str, Any]:
        """Handle Easy Apply form with ultimate field filling."""
        try:
            max_steps = 15
            current_step = 0
            
            while current_step < max_steps:
                time.sleep(2)
                
                # Fill all form fields with ultimate intelligence
                await self._ultimate_fill_form_fields()
                
                # Look for next/submit buttons
                next_button = self._find_next_button()
                
                if next_button:
                    button_text = next_button.text.lower()
                    aria_label = next_button.get_attribute("aria-label") or ""
                    
                    if "submit" in button_text or "submit" in aria_label or "send" in button_text:
                        # Final submit
                        next_button.click()
                        time.sleep(5)
                        
                        # Check for success
                        if self._check_application_success():
                            return {
                                'success': True,
                                'message': 'Application submitted successfully with ultimate form filling',
                                'method': 'linkedin_ultimate_smart_apply'
                            }
                        else:
                            return {
                                'success': False,
                                'error': 'Application submission failed',
                                'message': 'Could not confirm application success'
                            }
                    else:
                        # Next step
                        next_button.click()
                        current_step += 1
                        time.sleep(3)
                else:
                    # No more buttons found
                    break
            
            return {
                'success': False,
                'error': 'Form handling incomplete',
                'message': 'Could not complete the application form'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error handling application form'
            }
    
    async def _ultimate_fill_form_fields(self):
        """Ultimate intelligent form field filling."""
        try:
            # Find all input fields
            input_fields = self.driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")
            
            for field in input_fields:
                try:
                    if not field.is_displayed() or not field.is_enabled():
                        continue
                    
                    # Get field attributes
                    field_type = field.get_attribute("type") or "text"
                    field_name = field.get_attribute("name") or ""
                    field_id = field.get_attribute("id") or ""
                    field_placeholder = field.get_attribute("placeholder") or ""
                    field_aria_label = field.get_attribute("aria-label") or ""
                    field_class = field.get_attribute("class") or ""
                    
                    # Combine all field identifiers
                    field_identifiers = f"{field_name} {field_id} {field_placeholder} {field_aria_label} {field_class}".lower()
                    
                    # Skip if field already has value
                    current_value = field.get_attribute("value") or ""
                    if current_value.strip():
                        continue
                    
                    # Determine what to fill based on field identifiers
                    value_to_fill = self._get_ultimate_field_value(field_identifiers, field_type)
                    
                    if value_to_fill:
                        # Clear and fill field
                        field.clear()
                        field.send_keys(value_to_fill)
                        logger.info(f"📝 Preenchido: {field_identifiers[:50]} = {value_to_fill}")
                        time.sleep(0.5)
                        
                except Exception as e:
                    logger.debug(f"Erro ao preencher campo: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Erro ao preencher formulário: {e}")
    
    def _get_ultimate_field_value(self, field_identifiers: str, field_type: str) -> Optional[str]:
        """Get ultimate appropriate value for form field."""
        
        # CPF field - CRITICAL
        if "cpf" in field_identifiers:
            return self.resume_data.get('cpf', '12345678901')
        
        # Salary expectation - CRITICAL
        if any(word in field_identifiers for word in ["salar", "pretensão", "expectativa", "valor", "salary"]):
            return self.resume_data.get('salary_expectation', '4000')
        
        # Years of experience fields - CRITICAL
        if any(word in field_identifiers for word in ["anos", "years", "experiência", "experience"]):
            if "node" in field_identifiers or "node.js" in field_identifiers:
                return "5"  # 5 years Node.js experience
            elif "python" in field_identifiers:
                return "7"  # 7 years Python experience
            elif "react" in field_identifiers:
                return "6"  # 6 years React experience
            elif "javascript" in field_identifiers:
                return "7"  # 7 years JavaScript experience
            elif "flutter" in field_identifiers:
                return "2"  # 2 years Flutter experience
            elif "vue" in field_identifiers:
                return "3"  # 3 years Vue experience
            elif "java" in field_identifiers:
                return "4"  # 4 years Java experience
            elif "django" in field_identifiers:
                return "5"  # 5 years Django experience
            elif "flask" in field_identifiers:
                return "4"  # 4 years Flask experience
            else:
                return str(self.resume_data.get('years_of_experience', 5))
        
        # Phone number
        if any(word in field_identifiers for word in ["phone", "telefone", "celular", "mobile"]):
            return self.resume_data.get('phone', '+55 11 99999-9999')
        
        # Email
        if "email" in field_identifiers:
            return self.resume_data.get('email', 'felipefrancanogueira@gmail.com')
        
        # Name
        if any(word in field_identifiers for word in ["name", "nome", "full name"]):
            return self.resume_data.get('name', 'Felipe França Nogueira')
        
        # Location
        if any(word in field_identifiers for word in ["location", "localização", "cidade", "city"]):
            return self.resume_data.get('location', 'São Paulo, SP')
        
        # LinkedIn URL
        if "linkedin" in field_identifiers:
            return "https://www.linkedin.com/in/felipefrancanogueira"
        
        # GitHub URL
        if "github" in field_identifiers:
            return "https://github.com/felipefrancanogueira"
        
        # Portfolio/Website
        if any(word in field_identifiers for word in ["portfolio", "website", "site", "url"]):
            return "https://felipefrancanogueira.dev"
        
        # Cover letter/Message
        if any(word in field_identifiers for word in ["cover", "message", "mensagem", "carta"]):
            return self._generate_cover_letter()
        
        # Availability
        if any(word in field_identifiers for word in ["availability", "disponibilidade", "when can you start"]):
            return "I can start immediately"
        
        # Notice period
        if any(word in field_identifiers for word in ["notice", "aviso", "period"]):
            return "2 weeks"
        
        # Visa status
        if any(word in field_identifiers for word in ["visa", "work permit", "authorization"]):
            return "I have the right to work in Brazil"
        
        # Why are you interested in this role?
        if any(word in field_identifiers for word in ["why", "interested", "motivation", "por que"]):
            custom_questions = self.resume_data.get('custom_questions', {})
            return custom_questions.get('why_leave', "I am passionate about software development and this role aligns perfectly with my skills and career goals.")
        
        # What makes you a good fit?
        if any(word in field_identifiers for word in ["good fit", "qualify", "suitable", "adequado"]):
            achievements = self.resume_data.get('achievements', [])
            if achievements:
                return achievements[0]  # Use first achievement
            return "My extensive experience in full-stack development, AI integration, and team leadership make me an ideal candidate for this position."
        
        # Availability/Start date
        if any(word in field_identifiers for word in ["availability", "disponibilidade", "when can you start", "start date"]):
            custom_questions = self.resume_data.get('custom_questions', {})
            return custom_questions.get('start_date', "I can start within 4 weeks of accepting an offer.")
        
        # Text fields that might need generic responses
        if field_type in ["text", "textarea"] and not field.get_attribute("value"):
            # Check if it's a required field by looking for asterisk or required attribute
            if "*" in field_identifiers or "required" in field_identifiers:
                return "See resume for details"
        
        return None
    
    def _generate_cover_letter(self) -> str:
        """Generate a personalized cover letter using profile data."""
        name = self.resume_data.get('name', 'Felipe França Nogueira')
        experience = self.resume_data.get('years_of_experience', 7)
        current_role = self.resume_data.get('current_role', 'Full-stack Developer')
        current_company = self.resume_data.get('current_company', 'Originate')
        skills = self.resume_data.get('core_technologies', ['React', 'TypeScript', 'Node.js'])
        achievements = self.resume_data.get('achievements', [])
        
        # Use custom questions if available
        custom_questions = self.resume_data.get('custom_questions', {})
        why_leave = custom_questions.get('why_leave', 'I am interested in opportunities that allow me to further develop my expertise in AI integration and modern web technologies while working on impactful projects.')
        start_date = custom_questions.get('start_date', 'I can start within 4 weeks of accepting an offer.')
        
        return f"""Dear Hiring Manager,

I am {name}, a {current_role} with {experience} years of experience in {', '.join(skills[:3])}. Currently working at {current_company}, I am excited about this opportunity and believe my skills align perfectly with your requirements.

{why_leave}

{start_date}

I have a strong background in full-stack development, AI integration, and team leadership. I am passionate about creating innovative solutions and would love to discuss how I can contribute to your team.

Best regards,
{name}"""
    
    def _find_next_button(self) -> Optional[Any]:
        """Find next/submit button."""
        selectors = [
            "button[aria-label*='Continue to next step']",
            "button[aria-label*='Review your application']",
            "button[aria-label*='Submit application']",
            "button[data-control-name*='continue_unify']",
            "button[data-control-name*='submit_unify']",
            "button[aria-label*='Submit']",
            "button[aria-label*='Send']",
            "button[aria-label*='Review']",
            "button[aria-label*='Next']"
        ]
        
        for selector in selectors:
            try:
                button = self.driver.find_element(By.CSS_SELECTOR, selector)
                if button.is_displayed() and button.is_enabled():
                    return button
            except:
                continue
        
        return None
    
    def _check_application_success(self) -> bool:
        """Check if application was successful."""
        success_indicators = [
            "Application sent",
            "Applied",
            "Success",
            "Thank you",
            "Application submitted",
            "Aplicação enviada",
            "Candidatura enviada"
        ]
        
        for indicator in success_indicators:
            try:
                element = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{indicator}')]")
                if element.is_displayed():
                    return True
            except:
                continue
        
        return False
    
    def _get_job_title(self) -> str:
        """Get job title from current page."""
        try:
            selectors = [
                "h1.job-title",
                ".job-details-jobs-unified-top-card__job-title",
                "h1",
                ".jobs-unified-top-card__job-title"
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    title = element.text.strip()
                    if title:
                        return title
                except:
                    continue
            
            return "Unknown Title"
        except:
            return "Unknown Title"
    
    def _get_company_name(self) -> str:
        """Get company name from current page."""
        try:
            selectors = [
                ".job-details-jobs-unified-top-card__company-name a",
                ".jobs-unified-top-card__company-name a",
                ".job-details-jobs-unified-top-card__company-name",
                ".jobs-unified-top-card__company-name"
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    company = element.text.strip()
                    if company:
                        return company
                except:
                    continue
            
            return "Unknown Company"
        except:
            return "Unknown Company"
    
    def close_driver(self):
        """Close the driver."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🔒 Driver fechado")
            except:
                pass

async def main():
    """Main function for testing."""
    from app.main import load_config
    
    config = load_config()
    applicator = LinkedInUltimateSmartApply(config)
    
    try:
        result = await applicator.search_and_apply_jobs(max_applications=1)
        logger.info(f"🎯 Resultado: {result}")
    except Exception as e:
        logger.error(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    asyncio.run(main())
