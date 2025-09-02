# AutoApply.AI - Sistema Contínuo e Independente

Sistema automatizado que roda em loop contínuo buscando vagas e se inscrevendo automaticamente, com integração de Groq AI para melhorar o matching e aplicações.

## 🚀 Características Principais

- **Sistema Independente**: Roda em loop contínuo sem intervenção manual
- **Integração Groq AI**: Usa inteligência artificial para melhorar matching de vagas
- **Múltiplas Plataformas**: Suporte a Remotive, WeWorkRemotely, Email, Sites Diretos e LinkedIn
- **Sistema Anti-Duplicação**: Evita aplicar para a mesma vaga múltiplas vezes
- **Monitoramento em Tempo Real**: Dashboard para acompanhar performance
- **Logs Detalhados**: Sistema completo de logging e relatórios
- **Recuperação de Erros**: Sistema robusto com retry automático

## 📋 Pré-requisitos

### Dependências do Sistema
```bash
# Python 3.8+
python --version

# Instalar dependências
pip install -r requirements.txt
```

### Configuração de API Keys (Opcional)
```bash
# Groq AI (recomendado para melhor matching)
export GROQ_API_KEY="sua_chave_groq"

# Outras configurações opcionais
export SEARCH_INTERVAL="3600"  # Intervalo em segundos
export MAX_APPLICATIONS="20"   # Máximo de aplicações por ciclo
```

## 🛠️ Instalação e Configuração

### 1. Verificar Arquivos de Configuração
Certifique-se de que os seguintes arquivos existem:
- `config/config.yaml` - Configuração principal
- `config/profile.yaml` - Perfil do usuário
- `config/continuous_config.yaml` - Configuração do sistema contínuo

### 2. Configurar Sistema Contínuo
Edite `config/continuous_config.yaml`:
```yaml
# Intervalos e Limites
search_interval: 3600  # 1 hora entre ciclos
max_applications_per_cycle: 20
max_concurrent_applications: 5
application_delay: 30  # 30 segundos entre aplicações

# Groq AI
enable_groq_ai: true
groq_model: "llama3-8b-8192"

# Plataformas
platforms:
  - "remotive"
  - "weworkremotely"
  - "email"
  - "direct"
  - "linkedin"
```

## 🚀 Como Usar

### Método 1: Script de Inicialização (Recomendado)
```bash
python start_continuous_system.py
```

Este script:
- ✅ Verifica dependências
- ✅ Valida arquivos de configuração
- ✅ Cria diretórios necessários
- ✅ Inicia o sistema com verificações

### Método 2: Inicialização Direta
```bash
python continuous_autoapply.py
```

### Método 3: Execução em Background
```bash
# Linux/Mac
nohup python continuous_autoapply.py > system.log 2>&1 &

# Windows
start /B python continuous_autoapply.py
```

## 📊 Monitoramento

### Dashboard em Tempo Real
```bash
python monitor_system.py
```

O dashboard mostra:
- 📈 Status do sistema (funcionando/problemas/erro)
- 💾 Uso de memória e CPU
- ⏱️ Tempo de execução
- 📝 Estatísticas de aplicações
- 📋 Atividade recente dos logs

### Logs e Relatórios
- **Logs contínuos**: `data/logs/continuous_autoapply.log`
- **Estatísticas finais**: `data/logs/final_stats_*.json`
- **Relatórios de aplicações**: `data/applications/`

## ⚙️ Configurações Avançadas

### Variáveis de Ambiente
```bash
# Configurações principais
export GROQ_API_KEY="gsk_..."           # Chave da API Groq
export SEARCH_INTERVAL="3600"           # Intervalo entre ciclos (segundos)
export MAX_APPLICATIONS="20"            # Máx aplicações por ciclo
export MAX_CONCURRENT="5"               # Máx aplicações simultâneas
export APPLICATION_DELAY="30"           # Delay entre aplicações (segundos)
export MIN_MATCH_SCORE="70.0"           # Score mínimo para aplicar (0-100)

# Configurações de retry
export MAX_RETRIES="3"                  # Máx tentativas em caso de erro
export RETRY_DELAY="300"                # Delay entre tentativas (segundos)
```

### Configuração de Logging
```yaml
# config/continuous_config.yaml
logging:
  level: "INFO"        # DEBUG, INFO, WARNING, ERROR
  rotation: "10 MB"    # Rotação de logs
  retention: "7 days"  # Retenção de logs
```

## 🤖 Integração Groq AI

### Funcionalidades
- **Matching Inteligente**: Analisa vagas e perfil para determinar compatibilidade
- **Geração de Cartas**: Cria cartas de apresentação personalizadas
- **Score de Compatibilidade**: Calcula score de 0-100 para cada vaga
- **Recomendações**: Sugere aplicar ou não baseado na análise

### Configuração
```yaml
# config/continuous_config.yaml
enable_groq_ai: true
groq_model: "llama3-8b-8192"  # ou "llama3-70b-8192" para melhor qualidade
```

### Exemplo de Uso
O sistema automaticamente:
1. Busca vagas nas plataformas configuradas
2. Envia descrição da vaga para Groq AI
3. Recebe análise com score e recomendação
4. Aplica apenas para vagas com score >= 70
5. Gera carta personalizada usando AI

## 📈 Estatísticas e Relatórios

### Métricas Coletadas
- **Ciclos Executados**: Número de ciclos de busca/aplicação
- **Total de Aplicações**: Aplicações realizadas
- **Taxa de Sucesso**: Percentual de aplicações bem-sucedidas
- **Vagas Únicas**: Vagas únicas aplicadas (sem duplicatas)
- **Uso de Recursos**: Memória, CPU, tempo de execução

### Relatórios Gerados
- **Relatório Final**: Estatísticas completas ao finalizar
- **Logs Detalhados**: Log de todas as operações
- **Dashboard**: Monitoramento em tempo real

## 🛡️ Sistema de Recuperação

### Tratamento de Erros
- **Retry Automático**: Tenta novamente em caso de falha
- **Timeout Protection**: Evita loops infinitos
- **Graceful Shutdown**: Finalização limpa com Ctrl+C
- **Log de Erros**: Registra todos os erros para análise

### Configurações de Retry
```yaml
max_retries: 3        # Máximo de tentativas
retry_delay: 300      # Delay entre tentativas (5 minutos)
```

## 🔧 Solução de Problemas

### Problemas Comuns

#### 1. Sistema não inicia
```bash
# Verificar dependências
python start_continuous_system.py

# Verificar logs
tail -f data/logs/continuous_autoapply.log
```

#### 2. Groq AI não funciona
```bash
# Verificar API key
echo $GROQ_API_KEY

# Testar conexão
python -c "import groq; print('Groq OK')"
```

#### 3. Alto uso de memória
```bash
# Monitorar recursos
python monitor_system.py

# Ajustar configurações
# Reduzir max_concurrent_applications
# Aumentar application_delay
```

#### 4. Aplicações não funcionam
```bash
# Verificar configuração
cat config/config.yaml

# Verificar perfil
cat config/profile.yaml

# Verificar logs de aplicação
grep "APPLICANDO" data/logs/continuous_autoapply.log
```

### Logs Importantes
- **Erros**: `grep "ERROR" data/logs/continuous_autoapply.log`
- **Aplicações**: `grep "APLICANDO" data/logs/continuous_autoapply.log`
- **Ciclos**: `grep "CICLO" data/logs/continuous_autoapply.log`

## 📞 Suporte

### Comandos Úteis
```bash
# Verificar status
python monitor_system.py

# Parar sistema
pkill -f continuous_autoapply.py

# Reiniciar sistema
python start_continuous_system.py

# Ver logs em tempo real
tail -f data/logs/continuous_autoapply.log
```

### Estrutura de Arquivos
```
autoapply_ai/
├── continuous_autoapply.py          # Sistema principal
├── start_continuous_system.py       # Script de inicialização
├── monitor_system.py                # Monitor do sistema
├── config/
│   ├── config.yaml                  # Configuração principal
│   ├── profile.yaml                 # Perfil do usuário
│   └── continuous_config.yaml       # Config do sistema contínuo
├── data/
│   ├── logs/                        # Logs do sistema
│   ├── applications/                # Relatórios de aplicações
│   └── matches/                     # Vagas com match
└── requirements.txt                 # Dependências
```

## 🎯 Próximos Passos

1. **Configurar API Keys**: Definir GROQ_API_KEY para melhor matching
2. **Ajustar Configurações**: Personalizar intervalos e limites
3. **Monitorar Performance**: Usar dashboard para acompanhar
4. **Analisar Relatórios**: Revisar logs e estatísticas
5. **Otimizar Configurações**: Ajustar baseado nos resultados

---

**⚠️ Importante**: Este sistema é para uso pessoal e educacional. Respeite os termos de uso das plataformas de emprego e use com responsabilidade.
