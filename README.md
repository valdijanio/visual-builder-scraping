# Visual Builder Scraping

Sistema de web scraping com designer visual para criar templates de extração de dados.

## Componentes

- **Backend**: FastAPI + asyncio + Playwright + APScheduler
- **Frontend**: Nuxt.js 3 + Tailwind CSS
- **Extensão**: Chrome/Firefox para captura visual de selectors
- **Banco**: PostgreSQL

## Pré-requisitos

- Python 3.12+
- Node.js 18+
- PostgreSQL 14+

## Instalação

### 1. PostgreSQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Criar usuário e banco
sudo -u postgres psql
CREATE USER scraper WITH PASSWORD 'scraper123';
CREATE DATABASE scraper_db OWNER scraper;
GRANT ALL PRIVILEGES ON DATABASE scraper_db TO scraper;
\q

# Testar conexão
psql -h localhost -U scraper -d scraper_db
```

### 2. Backend

```bash
cd backend

# Criar ambiente virtual
python3.12 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Instalar Playwright browsers
playwright install chromium

# Copiar e configurar .env
cp .env.example .env

# Iniciar servidor
uvicorn app.main:app --reload
```

O backend estará disponível em `http://localhost:8000`

### 3. Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Iniciar servidor de desenvolvimento
npm run dev
```

O frontend estará disponível em `http://localhost:3000`

### 4. Extensão do Browser

1. Abra o Chrome e vá para `chrome://extensions/`
2. Ative o "Modo do desenvolvedor"
3. Clique em "Carregar sem compactação"
4. Selecione a pasta `extension/`

## Uso

### Criar Template com a Extensão

1. Navegue até o site que deseja fazer scraping
2. Clique no ícone da extensão
3. Clique em "Iniciar Seleção"
4. Clique nos elementos da página que deseja capturar
5. Nomeie cada campo
6. Clique em "Salvar Template"

### Criar Agendamento

1. Acesse o frontend em `http://localhost:3000`
2. Vá para "Agendamentos"
3. Clique em "Novo Agendamento"
4. Selecione o template, URL e frequência
5. Salve

### Visualizar Resultados

Os resultados das extrações ficam disponíveis em "Resultados" no frontend.

## API Endpoints

```
GET  /api/health                    # Status do sistema

# Templates
GET  /api/templates                 # Listar templates
POST /api/templates                 # Criar template
GET  /api/templates/{id}            # Detalhes template
PUT  /api/templates/{id}            # Atualizar template
DELETE /api/templates/{id}          # Remover template
POST /api/templates/{id}/test       # Testar template

# Agendamentos
GET  /api/schedules                 # Listar agendamentos
POST /api/schedules                 # Criar agendamento
GET  /api/schedules/{id}            # Detalhes agendamento
PUT  /api/schedules/{id}            # Atualizar agendamento
DELETE /api/schedules/{id}          # Remover agendamento
POST /api/schedules/{id}/run        # Executar agora

# Jobs
GET  /api/jobs                      # Listar jobs em execução
POST /api/jobs                      # Criar job manual
GET  /api/jobs/{id}                 # Status do job

# Resultados
GET  /api/results                   # Listar resultados (paginado)
GET  /api/results/{id}              # Detalhes resultado
DELETE /api/results/{id}            # Remover resultado
```

## Estrutura do Projeto

```
visual-builder-scraping/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Configurações
│   │   ├── core/
│   │   │   ├── database.py      # Pool asyncpg
│   │   │   └── manager.py       # Gerenciador de workers
│   │   ├── api/                 # Routes e schemas
│   │   ├── workers/             # Workers de scraping
│   │   ├── scraping/            # Browser pool e executor
│   │   └── scheduler/           # APScheduler
│   └── requirements.txt
├── frontend/
│   ├── pages/                   # Páginas Nuxt
│   ├── components/              # Componentes Vue
│   ├── composables/             # Hooks reutilizáveis
│   └── nuxt.config.ts
└── extension/
    ├── manifest.json
    ├── content.js               # Script de seleção
    ├── popup.html/js/css        # Interface da extensão
    └── background.js
```

## Configuração

### Variáveis de Ambiente (Backend)

```env
DATABASE_URL=postgresql://scraper:scraper123@localhost:5432/scraper_db
BROWSER_HEADLESS=true
BROWSER_POOL_SIZE=3
WORKER_COUNT=2
CORS_ORIGINS=["http://localhost:3000"]
DEBUG=false
```

### Cron Expressions

Exemplos de expressões cron para agendamentos:

- `*/5 * * * *` - A cada 5 minutos
- `0 * * * *` - A cada hora
- `0 */6 * * *` - A cada 6 horas
- `0 9 * * *` - Todo dia às 9h
- `0 9 * * 1-5` - Dias úteis às 9h
- `0 0 1 * *` - Primeiro dia do mês à meia-noite

## Licença

MIT
