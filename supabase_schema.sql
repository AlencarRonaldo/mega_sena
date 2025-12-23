-- Schema para Mega Sena no Supabase
-- Execute este SQL no SQL Editor do Supabase Dashboard

-- Tabela de concursos (resultados dos sorteios)
CREATE TABLE IF NOT EXISTS concursos (
    id BIGSERIAL PRIMARY KEY,
    numero INTEGER UNIQUE NOT NULL,
    data DATE NOT NULL,
    dezena1 INTEGER NOT NULL CHECK (dezena1 BETWEEN 1 AND 60),
    dezena2 INTEGER NOT NULL CHECK (dezena2 BETWEEN 1 AND 60),
    dezena3 INTEGER NOT NULL CHECK (dezena3 BETWEEN 1 AND 60),
    dezena4 INTEGER NOT NULL CHECK (dezena4 BETWEEN 1 AND 60),
    dezena5 INTEGER NOT NULL CHECK (dezena5 BETWEEN 1 AND 60),
    dezena6 INTEGER NOT NULL CHECK (dezena6 BETWEEN 1 AND 60),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de jogos salvos pelo usuario
CREATE TABLE IF NOT EXISTS jogos_salvos (
    id BIGSERIAL PRIMARY KEY,
    dezenas INTEGER[] NOT NULL,
    data_criacao TIMESTAMPTZ DEFAULT NOW(),
    algoritmos TEXT[] DEFAULT '{}',
    conferido BOOLEAN DEFAULT FALSE,
    acertos JSONB DEFAULT '{}',
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Indices para melhor performance
CREATE INDEX IF NOT EXISTS idx_concursos_numero ON concursos(numero DESC);
CREATE INDEX IF NOT EXISTS idx_concursos_data ON concursos(data DESC);
CREATE INDEX IF NOT EXISTS idx_jogos_salvos_user ON jogos_salvos(user_id);
CREATE INDEX IF NOT EXISTS idx_jogos_salvos_data ON jogos_salvos(data_criacao DESC);

-- Habilitar RLS (Row Level Security)
ALTER TABLE concursos ENABLE ROW LEVEL SECURITY;
ALTER TABLE jogos_salvos ENABLE ROW LEVEL SECURITY;

-- Politicas de acesso para concursos (leitura publica)
CREATE POLICY "Concursos sao publicos para leitura" ON concursos
    FOR SELECT USING (true);

CREATE POLICY "Apenas admins podem inserir concursos" ON concursos
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Apenas admins podem atualizar concursos" ON concursos
    FOR UPDATE USING (true);

-- Politicas de acesso para jogos_salvos (por usuario ou anonimo)
CREATE POLICY "Usuarios podem ver seus proprios jogos" ON jogos_salvos
    FOR SELECT USING (user_id = auth.uid() OR user_id IS NULL);

CREATE POLICY "Usuarios podem criar jogos" ON jogos_salvos
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Usuarios podem atualizar seus proprios jogos" ON jogos_salvos
    FOR UPDATE USING (user_id = auth.uid() OR user_id IS NULL);

CREATE POLICY "Usuarios podem deletar seus proprios jogos" ON jogos_salvos
    FOR DELETE USING (user_id = auth.uid() OR user_id IS NULL);
