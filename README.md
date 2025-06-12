# AutoApply.AI

AutoApply.AI é uma ferramenta automatizada de busca e aplicação para vagas de emprego que ajuda você a encontrar e se candidatar a oportunidades relevantes de forma eficiente.

## Funcionalidades

- **Busca Inteligente de Vagas**: Pesquisa vagas em múltiplas plataformas (atualmente suportando Remotive e WeWorkRemotely)
- **Correspondência Baseada em IA**: Utiliza o LLM da GROQ para avaliar a compatibilidade das vagas com seu currículo
- **Candidaturas Automatizadas**: Aplica automaticamente para vagas que atendem aos seus critérios
- **Preferências Configuráveis**: Personalize sua busca de emprego com preferências detalhadas
- **Acompanhamento de Progresso**: Mantenha o controle de suas candidaturas e correspondências

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/yourusername/autoapply_ai.git
cd autoapply_ai
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale o pacote:
```bash
pip install -e .
```

4. Configure suas variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas chaves de API e preferências
```

## Configuração

### Variáveis de Ambiente

O sistema pode ser configurado através de variáveis de ambiente. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```bash
# API Configuration
GROQ_API_KEY=your_groq_api_key

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SENDER_EMAIL=your_email@gmail.com
SENDER_NAME="Your Name"
USE_APP_PASSWORD=true
EMAIL_SIGNATURE="Best regards,\nYour Name"

# Platform Credentials
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password
INDEED_EMAIL=your_indeed_email
INDEED_PASSWORD=your_indeed_password

# Application Settings
RESUME_PATH=data/resume.pdf
DEBUG_MODE=false
```

#### Notas sobre Configuração de Email:

1. Para Gmail:
   - Use `smtp.gmail.com` como servidor SMTP
   - Porta 587 para TLS
   - Você precisa gerar uma "App Password" nas configurações de segurança do Google
   - Defina `USE_APP_PASSWORD=true`

2. Para outros provedores:
   - Ajuste `SMTP_SERVER` e `SMTP_PORT` conforme necessário
   - Use suas credenciais normais
   - Defina `USE_APP_PASSWORD=false`

3. Assinatura de Email:
   - Opcional, mas recomendado
   - Use `\n` para quebras de linha
   - Inclua seu nome e informações de contato

Crie um arquivo de configuração (`config.json`) com suas preferências:

```json
{
  "technical": {
    "role_type": "Engenheiro de Software",
    "seniority_level": "Sênior",
    "primary_skills": ["Python", "JavaScript", "React"],
    "secondary_skills": ["Node.js", "TypeScript"],
    "min_experience_years": 5,
    "max_experience_years": 15,
    "preferred_stack": ["Python", "React", "Node.js"]
  },
  "work_preferences": {
    "remote_only": true,
    "accept_hybrid": false,
    "accept_contract": true,
    "accept_fulltime": true,
    "accept_parttime": false,
    "preferred_languages": ["English", "Portuguese"],
    "preferred_timezones": ["UTC-3", "UTC-4", "UTC-5"]
  },
  "location": {
    "country": "Brasil",
    "city": "São Paulo",
    "state": "SP",
    "timezone": "UTC-3",
    "willing_to_relocate": false,
    "preferred_countries": ["EUA", "Canadá"]
  },
  "salary": {
    "min_salary_usd": 120000,
    "preferred_currency": "USD",
    "require_salary_range": true,
    "accept_equity": true,
    "min_equity_percent": 0.1
  },
  "application": {
    "max_applications_per_day": 10,
    "blacklisted_companies": [],
    "preferred_companies": [],
    "cover_letter_required": true,
    "follow_up_days": 7
  },
  "api": {
    "groq_api_key": "sua-chave-api-aqui",
    "groq_model": "llama3-70b-8192",
    "groq_temperature": 0.3,
    "groq_max_tokens": 1000,
    "groq_rate_limit": 10
  }
}
```

## Uso

### Buscar Vagas

```bash
autoapply search caminho/do/seu/curriculo.pdf --platform remotive --limit 10
```

### Candidatar-se às Vagas

```bash
autoapply apply caminho/do/seu/curriculo.pdf --platform remotive --limit 5 --min-score 0.8
```

### Configurar Preferências

```bash
autoapply configure --config caminho/do/config.json
```

## Estrutura do Projeto

O projeto está organizado nos seguintes diretórios principais:

- `app/` - Código fonte da aplicação e lógica de negócio
  - `automation/` - Código relacionado à automação
  - `matching/` - Algoritmos e lógica de correspondência
  - `job_search/` - Funcionalidade de busca de vagas
  - `resume/` - Processamento e gerenciamento de currículos
  - `cli/` - Ferramentas de interface de linha de comando
  - `autoapply/` - Módulos principais da aplicação

- `config/` - Arquivos de configuração
  - `.isort.cfg` - Configuração de ordenação de imports Python
  - `pytest.ini` - Configuração do PyTest

- `data/` - Armazenamento de dados e recursos
  - Listagens de vagas
  - Modelos de currículo
  - Dados de treinamento

- `logs/` - Logs da aplicação
  - Logs de erro
  - Logs de atividade
  - Informações de depuração

- `tests/` - Suite de testes e recursos de teste

## Desenvolvimento

1. Instale as dependências de desenvolvimento:
```bash
pip install -e ".[dev]"
```

2. Execute os testes:
```bash
pytest
```

3. Formate o código:
```bash
black src tests
isort src tests
```

## Contribuindo

1. Faça um fork do repositório
2. Crie uma branch para sua feature
3. Faça suas alterações
4. Execute os testes
5. Envie um pull request

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

## Agradecimentos

- [GROQ](https://groq.com/) por sua poderosa API de LLM
- [Remotive](https://remotive.com/) e [WeWorkRemotely](https://weworkremotely.com/) pelas listagens de vagas
- Todos os contribuidores e usuários do AutoApply.AI 