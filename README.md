# AutoApply.AI - Sistema de Aplicação Automática para Vagas

Sistema completo para busca, matching e aplicação automática de vagas com geração de logs CSV detalhados.

## 🚀 Funcionalidades

- **Busca Automática**: Busca vagas em múltiplas plataformas (LinkedIn, WeWorkRemotely, Remotive, etc.)
- **Matching Inteligente**: Compara vagas com seu perfil usando algoritmos de matching
- **Aplicação Automática**: Aplica automaticamente para vagas com melhor match
- **Logging Completo**: Gera logs CSV detalhados de todas as operações
- **Relatórios**: Cria relatórios de performance e analytics

## 📋 Pré-requisitos

- Python 3.8+
- pip
- Virtual environment (recomendado)

## 🛠️ Instalação

1. **Clone o repositório:**
```bash
git clone <repository-url>
cd autoapply_ai
```

2. **Crie e ative o ambiente virtual:**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

## ⚙️ Configuração

1. **Configure o arquivo `config/config.yaml`:**
```yaml
personal:
  name: "Seu Nome"
  email: "seu@email.com"
  skills:
    - "python"
    - "react"
    - "javascript"
    - "node.js"
  
search:
  keywords:
    - "software engineer"
    - "developer"
    - "python"
    - "react"
  
application:
  max_applications_per_session: 5
  delay_between_applications: 1
```

2. **Configure o arquivo `config/profile.yaml`:**
```yaml
personal_info:
  name: "Seu Nome"
  email: "seu@email.com"
  phone: "+55 11 99999-9999"
  location: "São Paulo, SP"
  
experience:
  years: 5
  skills:
    - "Python"
    - "React"
    - "JavaScript"
    - "Node.js"
    - "Docker"
    - "AWS"
  
education:
  degree: "Bacharel em Ciência da Computação"
  institution: "Universidade XYZ"
  
languages:
  - "Português (Nativo)"
  - "Inglês (Fluente)"
  - "Espanhol (Intermediário)"
```

## 🚀 Como Usar

### Execução Simples

Para executar o sistema completo com uma única linha de comando:

```bash
source venv/bin/activate && PYTHONPATH=. python3 autoapply.py
```

### Execução Detalhada

Para executar cada etapa separadamente:

1. **Buscar vagas:**
```bash
source venv/bin/activate && PYTHONPATH=. python3 scripts/search_jobs.py
```

2. **Fazer matching:**
```bash
source venv/bin/activate && PYTHONPATH=. python3 scripts/match_jobs.py
```

3. **Aplicar para vagas:**
```bash
source venv/bin/activate && PYTHONPATH=. python3 scripts/apply_jobs.py
```

### Visualizar Logs

Para visualizar os logs e relatórios gerados:

```bash
source venv/bin/activate && PYTHONPATH=. python3 view_logs.py
```

## 📊 Logs e Relatórios

O sistema gera automaticamente os seguintes arquivos:

### Arquivos CSV Gerados

1. **`autoapply_report_YYYYMMDD_HHMMSS.csv`** - Relatório detalhado com:
   - Data/Hora de cada operação
   - Tipo (BUSCA ou CANDIDATURA)
   - Plataforma
   - Título da vaga
   - Empresa
   - URL da vaga
   - Método de aplicação
   - Status
   - Score de match
   - Duração
   - Erros (se houver)
   - Detalhes adicionais

2. **`autoapply_summary_YYYYMMDD_HHMMSS.csv`** - Resumo executivo com:
   - Métricas gerais (total de vagas, candidaturas, taxa de sucesso)
   - Breakdown por plataforma
   - Estatísticas de performance

### Estrutura de Diretórios

```
data/logs/
├── autoapply_report_*.csv          # Relatórios detalhados
├── autoapply_summary_*.csv         # Resumos executivos
├── sessions/                       # Logs de sessões
├── applications/                   # Logs de aplicações
├── searches/                       # Logs de buscas
└── reports/                        # Relatórios em texto
```

## 🔧 Plataformas Suportadas

- **LinkedIn** - Vagas corporativas
- **WeWorkRemotely** - Vagas remotas
- **Remotive** - Vagas remotas e freelancer
- **AngelList/Wellfound** - Startups
- **HackerNews** - Vagas da comunidade tech
- **InfoJobs** - Vagas brasileiras
- **Catho** - Vagas brasileiras

## 📈 Métricas e Analytics

O sistema rastreia automaticamente:

- **Performance de Busca**: Vagas encontradas por plataforma
- **Taxa de Match**: Percentual de vagas que correspondem ao perfil
- **Taxa de Sucesso**: Percentual de aplicações bem-sucedidas
- **Tempo de Execução**: Duração de cada operação
- **Erros e Falhas**: Logs detalhados de problemas

## 🛡️ Segurança e Boas Práticas

- **Rate Limiting**: Delays entre requisições para evitar bloqueios
- **User-Agent Rotation**: Headers de navegador realistas
- **Error Handling**: Tratamento robusto de erros
- **Logging Seguro**: Logs sem informações sensíveis

## 🔍 Troubleshooting

### Problemas Comuns

1. **Erro de conexão com plataformas:**
   - Verifique sua conexão com a internet
   - Algumas plataformas podem ter proteções anti-bot

2. **Poucas vagas encontradas:**
   - Ajuste as keywords no `config.yaml`
   - Verifique se as plataformas estão funcionando

3. **Erro de importação:**
   - Certifique-se de que o ambiente virtual está ativo
   - Verifique se todas as dependências foram instaladas

### Logs de Debug

Para logs mais detalhados, adicione ao início do script:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Exemplo de Saída

```
🚀 AUTOAPPLY.AI - Sistema de Aplicação Automática
============================================================
📋 1. Carregando configurações...
   ✅ Configurações carregadas
📊 2. Inicializando sistema de logging...
   ✅ Sessão iniciada: session_20250901_114307
🔍 3. Iniciando busca de vagas...
   📊 Total de vagas encontradas: 64
🎯 4. Fazendo matching das vagas...
   📊 Vagas com match: 52

🏆 TOP 5 VAGAS COM MELHOR MATCH:
1. Senior Data Engineer
   Score: 40.0%
   URL: https://remotive.com/remote-jobs/...

📝 5. Aplicando para vagas...
📄 Aplicação 1/5
   Vaga: Senior Data Engineer
   Empresa: Unknown
   Score: 40.0%
   ✅ Aplicação simulada com sucesso

📊 6. Finalizando sessão e gerando relatório...

============================================================
📈 RELATÓRIO FINAL
============================================================
📊 Total de vagas encontradas: 64
🎯 Vagas com match: 52
📝 Aplicações realizadas: 5
✅ Aplicações bem-sucedidas: 5
❌ Aplicações falharam: 0
📈 Taxa de sucesso: 100.0%
📁 Logs salvos em: data/logs/
📊 CSV Detalhado: data/logs/autoapply_report_20250901_114328.csv
📈 CSV Resumo: data/logs/autoapply_summary_20250901_114328.csv

🎉 Sistema AutoApply.AI executado com sucesso!
📊 Os arquivos CSV com logs completos foram gerados automaticamente.
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para dúvidas ou problemas:
- Abra uma issue no GitHub
- Consulte a documentação
- Verifique os logs gerados pelo sistema

---

**AutoApply.AI** - Automatize sua busca por vagas e maximize suas chances de conseguir a vaga dos sonhos! 🚀