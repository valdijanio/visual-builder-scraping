-- Migrations are created automatically by the application
-- This file is for reference only

-- Templates de scraping
CREATE TABLE IF NOT EXISTS scrape_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    url_pattern TEXT,
    selectors JSONB NOT NULL DEFAULT '[]',
    config JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Agendamentos
CREATE TABLE IF NOT EXISTS scrape_schedules (
    id SERIAL PRIMARY KEY,
    template_id INT REFERENCES scrape_templates(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    url TEXT NOT NULL,
    cron_expression VARCHAR(100),      -- ex: '0 */6 * * *'
    interval_minutes INT,               -- alternativa ao cron
    is_enabled BOOLEAN DEFAULT true,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Resultados de scraping
CREATE TABLE IF NOT EXISTS scrape_results (
    id SERIAL PRIMARY KEY,
    template_id INT REFERENCES scrape_templates(id),
    schedule_id INT REFERENCES scrape_schedules(id),
    url TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,        -- pending, running, success, failed
    data JSONB,
    error TEXT,
    duration_ms INT,
    extracted_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_results_template ON scrape_results(template_id);
CREATE INDEX IF NOT EXISTS idx_results_schedule ON scrape_results(schedule_id);
CREATE INDEX IF NOT EXISTS idx_results_extracted ON scrape_results(extracted_at DESC);
CREATE INDEX IF NOT EXISTS idx_schedules_enabled ON scrape_schedules(is_enabled);
CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON scrape_schedules(next_run_at);
