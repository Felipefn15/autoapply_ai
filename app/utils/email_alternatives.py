import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import requests
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

class EmailAlternatives:
    """Alternative email services to replace SendGrid."""
    
    def __init__(self, config_path: str = "config/credentials.yaml"):
        self.config = self._load_config(config_path)
        self.current_provider = None
        self.providers = self._initialize_providers()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from credentials file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return {}
    
    def _initialize_providers(self) -> Dict[str, Dict]:
        """Initialize all available email providers."""
        providers = {}
        
        # Gmail SMTP
        if self.config.get('email', {}).get('gmail'):
            providers['gmail'] = {
                'type': 'smtp',
                'host': 'smtp.gmail.com',
                'port': 587,
                'username': self.config['email']['gmail'].get('username'),
                'password': self.config['email']['gmail'].get('password'),
                'enabled': True
            }
        
        # Outlook/Hotmail SMTP
        if self.config.get('email', {}).get('outlook'):
            providers['outlook'] = {
                'type': 'smtp',
                'host': 'smtp-mail.outlook.com',
                'port': 587,
                'username': self.config['email']['outlook'].get('username'),
                'password': self.config['email']['outlook'].get('password'),
                'enabled': True
            }
        
        # ProtonMail SMTP
        if self.config.get('email', {}).get('protonmail'):
            providers['protonmail'] = {
                'type': 'smtp',
                'host': '127.0.0.1',
                'port': 1025,
                'username': self.config['email']['protonmail'].get('username'),
                'password': self.config['email']['protonmail'].get('password'),
                'enabled': True
            }
        
        # Resend.com (Free tier: 3,000 emails/month)
        if self.config.get('email', {}).get('resend'):
            providers['resend'] = {
                'type': 'api',
                'api_key': self.config['email']['resend'].get('api_key'),
                'base_url': 'https://api.resend.com',
                'enabled': True
            }
        
        # Mailgun (Free tier: 5,000 emails/month for 3 months)
        if self.config.get('email', {}).get('mailgun'):
            providers['mailgun'] = {
                'type': 'api',
                'api_key': self.config['email']['mailgun'].get('api_key'),
                'domain': self.config['email']['mailgun'].get('domain'),
                'base_url': 'https://api.mailgun.net/v3',
                'enabled': True
            }
        
        # Brevo (Free tier: 300 emails/day)
        if self.config.get('email', {}).get('brevo'):
            providers['brevo'] = {
                'type': 'api',
                'api_key': self.config['email']['brevo'].get('api_key'),
                'base_url': 'https://api.brevo.com/v3',
                'enabled': True
            }
        
        # Local SMTP (for testing)
        providers['local'] = {
            'type': 'smtp',
            'host': 'localhost',
            'port': 1025,
            'username': None,
            'password': None,
            'enabled': True
        }
        
        return providers
    
    def get_available_providers(self) -> List[str]:
        """Get list of available email providers."""
        return [name for name, config in self.providers.items() if config.get('enabled')]
    
    def select_provider(self, provider_name: str = None) -> bool:
        """Select an email provider to use."""
        if provider_name and provider_name in self.providers:
            self.current_provider = provider_name
            logger.info(f"Selected email provider: {provider_name}")
            return True
        
        # Auto-select first available provider
        available = self.get_available_providers()
        if available:
            self.current_provider = available[0]
            logger.info(f"Auto-selected email provider: {self.current_provider}")
            return True
        
        logger.error("No email providers available")
        return False
    
    async def send_email(self, to_email: str, subject: str, body: str, 
                        html_body: str = None, attachments: List[Dict] = None) -> bool:
        """Send email using the selected provider."""
        if not self.current_provider:
            if not self.select_provider():
                return False
        
        provider_config = self.providers[self.current_provider]
        
        try:
            if provider_config['type'] == 'smtp':
                return await self._send_smtp_email(provider_config, to_email, subject, body, html_body, attachments)
            elif provider_config['type'] == 'api':
                return await self._send_api_email(provider_config, to_email, subject, body, html_body, attachments)
            else:
                logger.error(f"Unknown provider type: {provider_config['type']}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email via {self.current_provider}: {str(e)}")
            # Try to fallback to another provider
            return await self._fallback_to_other_provider(to_email, subject, body, html_body, attachments)
    
    async def _send_smtp_email(self, provider_config: Dict, to_email: str, subject: str, 
                              body: str, html_body: str = None, attachments: List[Dict] = None) -> bool:
        """Send email via SMTP."""
        try:
            msg = MIMEMultipart()
            msg['From'] = provider_config['username']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['data'])
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f"attachment; filename= {attachment['filename']}")
                    msg.attach(part)
            
            # Create SMTP connection
            context = ssl.create_default_context()
            
            with smtplib.SMTP(provider_config['host'], provider_config['port']) as server:
                server.starttls(context=context)
                if provider_config['username'] and provider_config['password']:
                    server.login(provider_config['username'], provider_config['password'])
                server.send_message(msg)
            
            logger.info(f"Email sent successfully via SMTP ({self.current_provider})")
            return True
            
        except Exception as e:
            logger.error(f"SMTP email failed: {str(e)}")
            return False
    
    async def _send_api_email(self, provider_config: Dict, to_email: str, subject: str, 
                            body: str, html_body: str = None, attachments: List[Dict] = None) -> bool:
        """Send email via API."""
        try:
            if self.current_provider == 'resend':
                return await self._send_resend_email(provider_config, to_email, subject, body, html_body, attachments)
            elif self.current_provider == 'mailgun':
                return await self._send_mailgun_email(provider_config, to_email, subject, body, html_body, attachments)
            elif self.current_provider == 'brevo':
                return await self._send_brevo_email(provider_config, to_email, subject, body, html_body, attachments)
            else:
                logger.error(f"API provider not implemented: {self.current_provider}")
                return False
                
        except Exception as e:
            logger.error(f"API email failed: {str(e)}")
            return False
    
    async def _send_resend_email(self, provider_config: Dict, to_email: str, subject: str, 
                               body: str, html_body: str = None, attachments: List[Dict] = None) -> bool:
        """Send email via Resend API."""
        try:
            headers = {
                'Authorization': f'Bearer {provider_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'from': 'AutoApply.AI <noreply@autoapply.ai>',
                'to': [to_email],
                'subject': subject,
                'text': body
            }
            
            if html_body:
                data['html'] = html_body
            
            response = requests.post(
                f"{provider_config['base_url']}/emails",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                logger.info("Email sent successfully via Resend API")
                return True
            else:
                logger.error(f"Resend API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Resend API error: {str(e)}")
            return False
    
    async def _send_mailgun_email(self, provider_config: Dict, to_email: str, subject: str, 
                                body: str, html_body: str = None, attachments: List[Dict] = None) -> bool:
        """Send email via Mailgun API."""
        try:
            data = {
                'from': f'AutoApply.AI <noreply@{provider_config["domain"]}>',
                'to': to_email,
                'subject': subject,
                'text': body
            }
            
            if html_body:
                data['html'] = html_body
            
            response = requests.post(
                f"{provider_config['base_url']}/{provider_config['domain']}/messages",
                auth=('api', provider_config['api_key']),
                data=data
            )
            
            if response.status_code == 200:
                logger.info("Email sent successfully via Mailgun API")
                return True
            else:
                logger.error(f"Mailgun API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Mailgun API error: {str(e)}")
            return False
    
    async def _send_brevo_email(self, provider_config: Dict, to_email: str, subject: str, 
                              body: str, html_body: str = None, attachments: List[Dict] = None) -> bool:
        """Send email via Brevo API."""
        try:
            headers = {
                'api-key': provider_config['api_key'],
                'Content-Type': 'application/json'
            }
            
            data = {
                'sender': {
                    'name': 'AutoApply.AI',
                    'email': 'noreply@autoapply.ai'
                },
                'to': [{'email': to_email}],
                'subject': subject,
                'textContent': body
            }
            
            if html_body:
                data['htmlContent'] = html_body
            
            response = requests.post(
                f"{provider_config['base_url']}/smtp/email",
                headers=headers,
                json=data
            )
            
            if response.status_code == 201:
                logger.info("Email sent successfully via Brevo API")
                return True
            else:
                logger.error(f"Brevo API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Brevo API error: {str(e)}")
            return False
    
    async def _fallback_to_other_provider(self, to_email: str, subject: str, body: str, 
                                        html_body: str = None, attachments: List[Dict] = None) -> bool:
        """Try to send email using another provider if the current one fails."""
        available_providers = self.get_available_providers()
        
        for provider in available_providers:
            if provider != self.current_provider:
                logger.info(f"Trying fallback provider: {provider}")
                self.current_provider = provider
                
                if await self.send_email(to_email, subject, body, html_body, attachments):
                    return True
        
        logger.error("All email providers failed")
        return False
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all email providers."""
        status = {}
        
        for name, config in self.providers.items():
            status[name] = {
                'enabled': config.get('enabled', False),
                'type': config.get('type', 'unknown'),
                'current': name == self.current_provider
            }
        
        return status
    
    def test_provider(self, provider_name: str) -> bool:
        """Test if a specific provider is working."""
        if provider_name not in self.providers:
            return False
        
        # Simple test - try to create a connection
        provider_config = self.providers[provider_name]
        
        if provider_config['type'] == 'smtp':
            try:
                with smtplib.SMTP(provider_config['host'], provider_config['port']) as server:
                    server.starttls()
                    if provider_config['username'] and provider_config['password']:
                        server.login(provider_config['username'], provider_config['password'])
                return True
            except Exception:
                return False
        
        elif provider_config['type'] == 'api':
            # Test API key validity
            try:
                if provider_name == 'resend':
                    response = requests.get(
                        f"{provider_config['base_url']}/domains",
                        headers={'Authorization': f'Bearer {provider_config["api_key"]}'}
                    )
                    return response.status_code == 200
                # Add other API tests as needed
                return True
            except Exception:
                return False
        
        return False
