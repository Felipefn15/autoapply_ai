# 🚀 Quick Start - Sistema Contínuo AutoApply.AI

## ⚡ Início Rápido (5 minutos)

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar Groq AI (Opcional mas Recomendado)
```bash
python setup_groq.py
```
- Siga as instruções para obter API key gratuita
- Ou pule se não quiser usar AI

### 3. Testar Sistema
```bash
python test_continuous_system.py
```

### 4. Iniciar Sistema Contínuo
```bash
python start_continuous_system.py
```

### 5. Monitorar Sistema (em outro terminal)
```bash
python monitor_system.py
```

## 🎯 O que o Sistema Faz

✅ **Busca vagas automaticamente** em múltiplas plataformas  
✅ **Usa Groq AI** para melhorar matching de vagas  
✅ **Aplica automaticamente** para vagas compatíveis  
✅ **Evita duplicatas** - não aplica para a mesma vaga duas vezes  
✅ **Roda em loop contínuo** - funciona 24/7  
✅ **Gera logs detalhados** - acompanhe tudo que acontece  
✅ **Sistema robusto** - recupera de erros automaticamente  

## ⚙️ Configurações Básicas

### Intervalo de Busca
- **Padrão**: 1 hora (3600 segundos)
- **Alterar**: Edite `config/continuous_config.yaml`
- **Variável**: `export SEARCH_INTERVAL="1800"` (30 minutos)

### Máximo de Aplicações
- **Padrão**: 20 aplicações por ciclo
- **Alterar**: `export MAX_APPLICATIONS="50"`
- **Arquivo**: `config/continuous_config.yaml`

### Plataformas
- **Padrão**: Todas habilitadas
- **Personalizar**: Edite `platforms` em `continuous_config.yaml`
- **Opções**: remotive, weworkremotely, email, direct, linkedin

## 📊 Monitoramento

### Dashboard em Tempo Real
```bash
python monitor_system.py
```
Mostra:
- Status do sistema
- Uso de memória/CPU
- Estatísticas de aplicações
- Logs recentes

### Logs Detalhados
```bash
# Ver logs em tempo real
tail -f data/logs/continuous_autoapply.log

# Ver apenas aplicações
grep "APLICANDO" data/logs/continuous_autoapply.log

# Ver apenas erros
grep "ERROR" data/logs/continuous_autoapply.log
```

## 🛑 Parar o Sistema

### Método 1: Ctrl+C
- Pressione `Ctrl+C` no terminal onde o sistema está rodando
- Sistema fará shutdown graceful

### Método 2: Kill Process
```bash
# Linux/Mac
pkill -f continuous_autoapply.py

# Windows
taskkill /f /im python.exe
```

## 🔧 Solução de Problemas

### Sistema não inicia
```bash
# Verificar dependências
python test_continuous_system.py

# Verificar configuração
python start_continuous_system.py
```

### Groq AI não funciona
```bash
# Verificar API key
echo $GROQ_API_KEY

# Reconfigurar
python setup_groq.py
```

### Alto uso de memória
```bash
# Monitorar recursos
python monitor_system.py

# Reduzir aplicações simultâneas
# Editar config/continuous_config.yaml
max_concurrent_applications: 2
```

## 📈 Exemplos de Uso

### Configuração Básica (sem AI)
```yaml
# config/continuous_config.yaml
search_interval: 3600
max_applications_per_cycle: 20
enable_groq_ai: false
```

### Configuração com AI
```yaml
# config/continuous_config.yaml
search_interval: 1800
max_applications_per_cycle: 15
enable_groq_ai: true
min_match_score: 80.0
```

### Configuração Agressiva
```yaml
# config/continuous_config.yaml
search_interval: 600
max_applications_per_cycle: 50
max_concurrent_applications: 10
```

## 🎯 Próximos Passos

1. **Execute o teste**: `python test_continuous_system.py`
2. **Configure Groq AI**: `python setup_groq.py`
3. **Inicie o sistema**: `python start_continuous_system.py`
4. **Monitore**: `python monitor_system.py`
5. **Ajuste configurações** baseado nos resultados

## 📞 Comandos Úteis

```bash
# Verificar status
python monitor_system.py

# Ver logs
tail -f data/logs/continuous_autoapply.log

# Testar sistema
python test_continuous_system.py

# Exemplos de uso
python example_usage.py

# Configurar Groq AI
python setup_groq.py

# Iniciar sistema
python start_continuous_system.py
```

## ⚠️ Importante

- **Use com responsabilidade** - respeite os termos das plataformas
- **Monitore regularmente** - use o dashboard para acompanhar
- **Ajuste configurações** - baseado no seu perfil e necessidades
- **Mantenha logs** - para análise e otimização

---

**🎉 Pronto! Seu sistema de aplicação automática está funcionando!**
