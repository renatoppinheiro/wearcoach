# wearcoach

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Local only](https://img.shields.io/badge/hosting-100%25%20local-brightgreen)

🌐 **Languages / Idiomas:** [English](#english) | [Português (Brasil)](#português-brasil)

---

<a name="english"></a>
# English

**WearCoach** is a local AI running coach running 100% on your machine. It connects your **Strava** activities with your recovery and wellness metrics from an **Oura Ring** or **Garmin**, turning raw training data into personalized daily briefings.

> ⚠️ **Health & Safety Disclaimer:** WearCoach is **not** a medical professional or certified athletic trainer. Stop training immediately if you experience pain. You are solely responsible for your own training decisions.

---

## 💡 How It Works (Choose Your Mode)

WearCoach offers two ways to run:

1. **🤖 Recommended: Using Your Own Coding Agent (Claude Code, Cursor, Windsurf, Copilot, etc.)**
   - The Python scripts only fetch raw data into `data/`; your coding agent reads `CLAUDE.md` and acts directly as your coach.
   - **Benefit:** No dedicated LLM API key required (uses whichever AI model/subscription you already have in your editor/CLI).
   - **Persistent Memory:** The agent maintains a local knowledge base in `.wiki/` (powered by [llm-wiki](https://github.com/nvk/llm-wiki) implementing [Karpathy's LLM-wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)), preserving your race goals, injury history, HRV baselines, and training patterns across sessions.

2. **⚡ Standalone Mode (CLI without a coding agent)**
   - Run `python main.py brief` to directly query Claude (Anthropic) or GPT (OpenAI) via your own API key.
   - Best if you prefer a single terminal command without interacting via an AI chat interface.

---

## 🛠️ Quick Setup (~5 min)

### 1. Prerequisites & Installation
Requires **Python 3.10+**.

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment variables template
cp .env.example .env
```

### 2. Configure Integrations

1. **Strava (Required, free, ~2 min):**
   - Visit [Strava API Settings](https://www.strava.com/settings/api).
   - Set *Authorization Callback Domain* to: `localhost`.
   - Copy your **Client ID** and **Client Secret**.

2. **Oura Ring (Optional — if you own an Oura ring):**
   - Visit [Oura Cloud Applications](https://cloud.ouraring.com/oauth/applications).
   - Set *Redirect URI* to: `http://localhost:8734/callback`.
   - Copy your **Client ID** and **Client Secret**.

3. **Garmin (Optional — if you have Garmin instead of Oura):**
   - Have your **Garmin Connect email & password** ready (no API app registration required).

### 3. Run Setup Wizard
Run the interactive wizard:
```bash
python main.py setup
```
The wizard will ask if you are using a coding agent (skipping the LLM API key setup if so) and walk you through connecting Strava, Oura, or Garmin.

---

## 📖 How to Use

### Mode 1: With Your Coding Agent (Recommended)

1. **Fetch recent data:**
   ```bash
   python main.py fetch
   ```
2. Open this folder in your AI coding agent (**Claude Code**, **Cursor**, **Windsurf**, etc.).
3. Ask in chat:
   > *"Give me today's briefing"*
   
   The agent will read `CLAUDE.md`, inspect the latest snapshot in `data/`, and provide tailored coaching advice.
4. Talk naturally with your coach:
   - *"I felt a tweak in my knee during yesterday's run."*
   - *"Plan my next 3 weeks targeting my upcoming marathon."*
   - *"How is my HRV trend looking?"*

#### 🧠 Persistent Training Memory (`.wiki/`)
As you chat, durable context is saved into `.wiki/`:
- **Claude Code users:** Install the plugin once per machine:
  ```bash
  claude plugin install wiki@llm-wiki
  ```
- **Other Agents (Cursor, Windsurf, Copilot, etc.):** Fetch the portable protocol once:
  ```bash
  curl -sL https://raw.githubusercontent.com/nvk/llm-wiki/master/AGENTS.md -o AGENTS.md
  ```

---

### Mode 2: Standalone Mode (No Coding Agent)

Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `.env`.

```bash
# Pull recent activities & wellness to data/
python main.py fetch

# Fetch data & generate today's briefing directly in terminal (saved to data/briefing-YYYY-MM-DD.md)
python main.py brief

# Pull custom history window (default: 7 days, max: 60)
python main.py fetch --days 14
```

---

## 💻 Command Reference

| Command | Description |
|---|---|
| `python main.py setup` | Interactive wizard to choose coach mode and connect accounts |
| `python main.py fetch [--days N]` | Pull recent activities and wellness data into `data/` |
| `python main.py brief [--days N]` | `fetch`, then ask built-in LLM for a daily briefing |
| `python main.py --help` | Display CLI help and command options |

---

## 🧪 Development & Testing

```bash
pip install -r requirements-dev.txt
python -m pytest
```

> **Note:** Tests mock all network calls (Strava, Oura, Garmin, Anthropic, OpenAI) — no credentials or real accounts needed.

---

## 🔒 Privacy & Security

- **100% Local:** No data is uploaded to any server controlled by this project (no backend, no remote hosting, no telemetry).
- **Gitignored Secrets:** `.env` and `data/` are gitignored — your keys and token data never leave your computer.
- **Garmin Credentials:** Passwords go directly to Garmin's official login via `garminconnect`.

---

## ❓ Why Oura instead of Garmin for Wellness?

Garmin lacks a self-serve developer API for personal wellness data; integration relies on a community library. If you own an Oura Ring, its official OAuth2 API is safer and recommended.

---

<a name="português-brasil"></a>
# Português (Brasil)

**WearCoach** é um treinador de corrida pessoal baseado em IA que executa 100% localmente na sua máquina. Ele integra seus dados de atividades do **Strava** com suas métricas de recuperação e bem-estar do **Oura Ring** ou **Garmin**, gerando *briefings* diários de treino personalizados.

> ⚠️ **Aviso de Saúde & Isenção de Responsabilidade:** O WearCoach **não** é um profissional médico ou de educação física. Pare o treino imediatamente em caso de dor. Você é o único responsável pelas suas decisões de treinamento.

---

## 💡 Como Funciona (Escolha seu Modo de Uso)

O WearCoach oferece duas maneiras de ser utilizado:

1. **🤖 Recomendado: Usando seu próprio Agente de Código (Claude Code, Cursor, Windsurf, Copilot, etc.)**
   - Os scripts em Python servem apenas para coletar os dados; o seu assistente de código lê o arquivo `CLAUDE.md` e atua diretamente como seu treinador.
   - **Vantagem:** Não precisa de chave de API de LLM dedicada (usará o modelo/assinatura que você já possui no seu editor/CLI).
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
