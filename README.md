# wearcoach

[![License: MIT](https://img.shields.io/badge/licença-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Local only](https://img.shields.io/badge/hospedagem-100%25%20local-brightgreen)

**WearCoach** é um treinador de corrida pessoal baseado em IA que executa 100% localmente na sua máquina. Ele integra seus dados de atividades do **Strava** com suas métricas de recuperação e bem-estar do **Oura Ring** ou **Garmin**, gerando *briefings* diários de treino altamente personalizados.

> ⚠️ **Aviso de Saúde & Isenção de Responsabilidade:** O WearCoach **não** é um profissional médico ou de educação física. Pare o treino imediatamente em caso de dor. Você é o único responsável pelas suas decisões de treinamento.

---

## 💡 Como Funciona (Escolha seu Modo de Uso)

O WearCoach oferece duas maneiras de ser utilizado:

1. **🤖 Recomendado: Usando seu próprio Agente de Código (Claude Code, Cursor, Windsurf, Copilot, etc.)**
   - Os scripts em Python servem apenas para coletar os dados; o seu assistente de código lê o arquivo `CLAUDE.md` e atua diretamente como seu treinador.
   - **Vantagem:** Não precisa de chave de API de LLM (usará o modelo/assinatura que você já possui no seu agente).
   - **Memória Persistente:** O agente mantém um histórico de contexto contínuo (metas de provas, histórico de lesões, ritmos de referência e padrões) em uma base de conhecimento local em `.wiki/` (baseada no padrão [LLM-Wiki de Andrej Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) via [llm-wiki](https://github.com/nvk/llm-wiki)).

2. **⚡ Modo Standalone (CLI direto sem agente de código)**
   - O comando `python main.py brief` consulta diretamente a API da Anthropic (Claude) ou OpenAI (GPT) utilizando sua própria chave de API.
   - Ideal para quem prefere rodar um comando no terminal sem interagir com uma interface de chat de IA.

---

## 🛠️ Configuração Rápida (~5 min)

### 1. Pré-requisitos e Instalação
Requer **Python 3.10+**.

```bash
# Instale as dependências do projeto
pip install -r requirements.txt

# Crie seu arquivo de variáveis de ambiente a partir do exemplo
cp .env.example .env
```

### 2. Criando/Obtendo as Credenciais de API

1. **Strava (Obrigatório, gratuito, ~2 min):**
   - Acesse [Strava API Settings](https://www.strava.com/settings/api).
   - Em *Authorization Callback Domain*, defina como: `localhost`.
   - Copie o **Client ID** e o **Client Secret**.

2. **Oura Ring (Opcional — se possuir o anel Oura):**
   - Acesse [Oura Cloud Applications](https://cloud.ouraring.com/oauth/applications).
   - Defina o *Redirect URI* como: `http://localhost:8734/callback`.
   - Copie o **Client ID** e o **Client Secret**.

3. **Garmin (Opcional — caso utilize Garmin em vez do Oura):**
   - Tenha à mão seu **e-mail** e **senha** do Garmin Connect (não é necessário registro de app de API).

### 3. Executando o Assistente de Configuração (Wizard)
Execute o comando interativo:
```bash
python main.py setup
```
O assistente irá perguntar qual modo você deseja usar (pulando a configuração da API key de LLM se optar pelo agente de código) e guiará a conexão autenticada com Strava, Oura ou Garmin.

---

## 📖 Como Usar

### Modo 1: Com seu Agente de Código (Recomendado)

1. **Atualize os dados de treino:**
   ```bash
   python main.py fetch
   ```
2. Abra a pasta deste projeto no seu editor/agente de IA favorito (**Claude Code**, **Cursor**, **Windsurf**, etc.).
3. Peça ao agente no chat:
   > *"Dê-me o briefing de treino para hoje"*
   
   O agente lerá as diretrizes em `CLAUDE.md`, analisará os dados mais recentes em `data/` e fornecerá o direcionamento do dia (ex: treino forte, rodagem leve ou descanso).
4. Converse naturalmente com seu treinador:
   - *"Senti uma leve fisgada no joelho na corrida de ontem."*
   - *"Planeje as minhas próximas 3 semanas focando na maratona."*
   - *"Como está minha tendência de HRV e recuperação?"*

#### 🧠 Memória Persistente de Treino (`.wiki/`)
À medida que você conversa, o agente armazena informações relevantes (metas de provas, lesões prévias, linhas de base de HRV) na pasta local `.wiki/`:
- **Usuários do Claude Code:** Instale o plugin do wiki uma vez na máquina:
  ```bash
  claude plugin install wiki@llm-wiki
  ```
- **Outros Agentes (Cursor, Windsurf, Copilot, etc.):** Baixe o protocolo portátil uma única vez:
  ```bash
  curl -sL https://raw.githubusercontent.com/nvk/llm-wiki/master/AGENTS.md -o AGENTS.md
  ```

> *Nota: O diretório `.wiki/` é estritamente pessoal e fica salvo apenas na sua máquina (está no `.gitignore`).*

---

### Modo 2: Modo Standalone (CLI sem agente)

Certifique-se de preencher `ANTHROPIC_API_KEY` ou `OPENAI_API_KEY` no seu `.env`.

```bash
# Apenas busca os dados mais recentes do Strava/Oura/Garmin e salva em data/
python main.py fetch

# Busca os dados recentes e gera o briefing de hoje via terminal (salva em data/briefing-YYYY-MM-DD.md)
python main.py brief

# Busca um período personalizado de histórico (padrão: 7 dias, máximo: 60 dias)
python main.py fetch --days 14
```

---

## 💻 Referência de Comandos (CLI)

| Comando | Descrição |
|---|---|
| `python main.py setup` | Assistente interativo para definir o modo do treinador e conectar contas. |
| `python main.py fetch [--days N]` | Coleta atividades e dados de bem-estar recentes para a pasta `data/`. |
| `python main.py brief [--days N]` | Executa `fetch` e gera o briefing do dia utilizando o LLM configurado. |
| `python main.py --help` | Exibe a ajuda da CLI e todas as opções disponíveis. |

---

## 🧪 Desenvolvimento e Testes

Para rodar a suíte de testes unitários:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

> **Garantia de Isolamento:** Os testes utilizam mocks para todas as chamadas externas de rede (Strava, Oura, Garmin, Anthropic, OpenAI). Nenhuma conta real ou credencial é necessária para executar os testes.

---

## 🔒 Privacidade & Segurança

- **100% Local:** Nenhum dado é enviado para servidores do WearCoach (não há backend, nem hospedagem remota, nem telemetria).
- **Proteção de Segredos:** O arquivo `.env` e a pasta `data/` (onde são armazenados os tokens de acesso e dados de treino) são ignorados pelo Git (`.gitignore`).
- **Autenticação Garmin:** As credenciais do Garmin são enviadas exclusivamente para o login oficial da Garmin através da biblioteca `garminconnect`.

---

## ❓ Por que Oura em vez de Garmin para Bem-Estar/Recuperação?

A Garmin não disponibiliza uma API pública e self-service de dados de bem-estar para desenvolvedores individuais; a integração utiliza uma biblioteca da comunidade baseada no login do usuário. Embora funcione no WearCoach, caso você possua um anel Oura, a API oficial via OAuth2 do Oura é a opção mais segura e recomendada.
