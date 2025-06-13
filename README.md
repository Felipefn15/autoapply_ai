# AutoApply.AI 🤖

Sistema automatizado de busca e candidatura para vagas de tecnologia.

## 🎯 Funcionalidades

- **Busca de Vagas**: Busca automática em múltiplas plataformas (LinkedIn, Indeed, etc.)
- **Match com Perfil**: Análise de compatibilidade com seu perfil profissional
- **Candidatura Automática**: Aplicação automática via plataforma ou email
- **Análise de Resultados**: Relatórios detalhados das candidaturas

## 📁 Estrutura do Projeto

```
autoapply_ai/
├── app/                    # Código principal
│   ├── automation/        # Automação de candidaturas
│   ├── job_search/       # Busca de vagas
│   └── main.py          # Script principal
├── config/               # Configurações
│   └── config.yaml      # Arquivo de configuração
├── data/                # Dados e resultados
│   ├── applications/    # Logs de candidaturas
│   ├── matches/         # Vagas compatíveis
│   ├── analysis/        # Relatórios de análise
│   └── resumes/        # Seu currículo
├── scripts/             # Scripts de execução
│   ├── search_jobs.py   # Busca de vagas
│   ├── match_jobs.py    # Match de perfil
│   ├── apply_jobs.py    # Candidaturas
│   └── analyze_jobs.py  # Análise
├── templates/           # Templates
│   ├── cover_letter.txt # Carta de apresentação
│   └── email_signature.txt # Assinatura de email
├── requirements.txt     # Dependências
└── README.md           # Este arquivo
```

## 🚀 Como Usar

1. **Preparação**:
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/autoapply_ai.git
cd autoapply_ai

# Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt
```

2. **Configuração**:
- Coloque seu currículo em `data/resumes/resume.pdf`
- Configure suas preferências em `config/config.yaml`:
  - Palavras-chave de busca
  - Habilidades requeridas
  - Faixa salarial
  - Configurações de email
  - etc.

3. **Execução**:
```bash
python app/main.py
```

4. **Opções do Menu**:
- 1: Buscar Vagas
- 2: Combinar Vagas com Perfil
- 3: Candidatar-se às Vagas
- 4: Visualizar Análise de Vagas
- 5: Executar Fluxo Completo
- 6: Sair

## ⚙️ Configuração

O arquivo `config/config.yaml` contém todas as configurações necessárias:

```yaml
# Exemplo de configuração
job_search:
  platforms:
    linkedin:
      enabled: true
      keywords: ["software engineer", "python", "react"]
      locations: ["Remote", "São Paulo"]

  matching:
    required_skills: ["python", "git", "react"]
    min_score: 0.3
    salary_range:
      min: 18000
      max: 55000
```

## 📊 Resultados

Os resultados são salvos em diferentes diretórios:

- `data/applications/`: Logs detalhados de cada candidatura
- `data/matches/`: Vagas que combinam com seu perfil
- `data/analysis/`: Relatórios e análises

## 🔒 Segurança

- Nunca compartilhe seu `config.yaml` com credenciais
- Use variáveis de ambiente para dados sensíveis
- Mantenha suas chaves de API seguras

## 📝 Logs

O sistema mantém logs detalhados:
- Status de cada candidatura (🟢 sucesso, 🔴 falha, 🟡 pulado)
- Motivos de falha ou rejeição
- Estatísticas de sucesso
- Tempo de processamento

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.