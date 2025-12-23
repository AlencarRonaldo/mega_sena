"""
Configurações da aplicação Mega-Sena
Configure suas credenciais do Supabase aqui
"""

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Configurações da aplicação
APP_TITLE = "🍀 Gerador Inteligente - Mega-Sena"
APP_ICON = "🍀"

# Configurações de desenvolvimento
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# URLs da API da Caixa
API_CAIXA_BASE = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"
API_CAIXA_LATEST = f"{API_CAIXA_BASE}/latest"  # Último concurso
API_CAIXA_BY_NUMBER = f"{API_CAIXA_BASE}/"  # + numero do concurso
