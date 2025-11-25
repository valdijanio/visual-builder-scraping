# Backend - Visual Builder Scraping

API FastAPI para o sistema de web scraping.

## Setup

```bash
# Criar ambiente virtual
python3.12 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Instalar Playwright
playwright install chromium

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env conforme necessário

# Iniciar servidor
uvicorn app.main:app --reload
```

## Estrutura

```
app/
├── main.py          # FastAPI app e lifespan
├── config.py        # Configurações (pydantic-settings)
├── core/
│   ├── database.py  # Pool asyncpg + auto-criação tabelas
│   └── manager.py   # Gerenciador de workers e filas
├── api/
│   ├── router.py    # Router principal
│   ├── schemas.py   # Schemas Pydantic
│   └── routes_*.py  # Endpoints
├── workers/
│   ├── base.py      # Worker base abstrato
│   └── scraper.py   # Worker de scraping
├── scraping/
│   ├── browser.py   # Pool de browsers Playwright
│   └── executor.py  # Executor de templates
└── scheduler/
    └── jobs.py      # APScheduler manager
```

## Documentação da API

Com o servidor rodando, acesse:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
