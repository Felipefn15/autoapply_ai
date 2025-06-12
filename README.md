# AutoApply.AI 🚀

Sistema automatizado para busca e aplicação em vagas remotas ao redor do mundo, com foco em profissionais de tecnologia do Brasil.

## 🎯 Funcionalidades

- **Análise de Currículo**
  - Extração automática de PDF e TXT
  - Detecção inteligente de habilidades
  - Categorização de experiências
  - Suporte a múltiplos idiomas

- **Busca de Vagas**
  - Vagas 100% remotas globais
  - Múltiplas plataformas (LinkedIn, Indeed, Remotive, etc.)
  - Filtros inteligentes por:
    - Faixa salarial
    - Fuso horário compatível
    - Requisitos de idioma
    - Tipo de contrato
    - Benefícios oferecidos

- **Matching Inteligente**
  - Análise de compatibilidade com IA
  - Pontuação de match por vaga
  - Sugestões de melhorias no currículo
  - Priorização de vagas mais adequadas

## 🛠️ Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/autoapply_ai.git
cd autoapply_ai
```

2. Crie e ative o ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure o arquivo `.env`:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

## ⚙️ Configuração

O arquivo `.env` permite personalizar:

- **Localização**
  - País e cidade base
  - Fuso horário local

- **Preferências de Trabalho**
  - Faixa salarial desejada (USD)
  - Tipos de contrato aceitos
  - Idiomas de preferência
  - Empresas favoritas/bloqueadas

- **Preferências Técnicas**
  - Anos de experiência
  - Nível de senioridade
  - Habilidades principais
  - Habilidades secundárias

## 🚀 Uso

1. Coloque seu currículo em PDF ou TXT na pasta `data/resumes/`

2. Execute o sistema:
```bash
python app/main.py
```

3. Os resultados serão salvos em:
  - `data/output/`: Vagas encontradas e análises
  - `data/cache/`: Cache de currículos processados

## 📊 Estrutura do Projeto

```
autoapply_ai/
├── app/
│   ├── resume/         # Análise de currículos
│   ├── job_search/     # Busca de vagas
│   ├── matching/       # Match currículo-vaga
│   └── automation/     # Automação de aplicações
├── data/
│   ├── resumes/       # Currículos
│   ├── cache/         # Cache
│   └── output/        # Resultados
└── tests/             # Testes
```

## 🔍 Plataformas Suportadas

- LinkedIn
- Indeed
- Remotive
- We Work Remotely (em breve)
- Stack Overflow Jobs (em breve)

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, leia nosso guia de contribuição antes de submeter mudanças.

## 📝 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## ⚠️ Aviso Legal

Este projeto é para fins educacionais e de automação pessoal. Use com responsabilidade e respeite os termos de serviço de cada plataforma de emprego. 