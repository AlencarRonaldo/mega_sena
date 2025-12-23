"""
Estilos Premium Dark Mode para Mega-Sena App
Design moderno com glassmorphism, gradientes e animacoes
"""

PREMIUM_CSS = """
<style>
/* ============================================
   IMPORTAR FONTE INTER
   ============================================ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ============================================
   VARIAVEIS CSS - PALETA DARK PREMIUM
   ============================================ */
:root {
    /* Backgrounds */
    --bg-primary: #0f1419;
    --bg-secondary: #1a1f2e;
    --bg-tertiary: #242b3d;
    --bg-card: rgba(30, 41, 59, 0.7);
    --bg-card-hover: rgba(40, 51, 69, 0.8);

    /* Accent Colors */
    --accent-emerald: #10b981;
    --accent-emerald-light: #34d399;
    --accent-gold: #f59e0b;
    --accent-gold-light: #fbbf24;
    --accent-purple: #8b5cf6;
    --accent-cyan: #06b6d4;

    /* Gradients */
    --gradient-primary: linear-gradient(135deg, #10b981 0%, #059669 100%);
    --gradient-gold: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    --gradient-premium: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --gradient-success: linear-gradient(135deg, #10b981 0%, #14b8a6 100%);
    --gradient-header: linear-gradient(135deg, #1e3a5f 0%, #0f172a 50%, #1e293b 100%);
    --gradient-glass: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);

    /* Text */
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;

    /* Borders */
    --border-subtle: rgba(148, 163, 184, 0.1);
    --border-accent: rgba(16, 185, 129, 0.3);

    /* Shadows */
    --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
    --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.4);
    --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.5);
    --shadow-glow: 0 0 20px rgba(16, 185, 129, 0.3);

    /* Spacing */
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 24px;
}

/* ============================================
   RESET E BASE
   ============================================ */
.stApp {
    background: var(--bg-primary) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.stApp > header {
    background: transparent !important;
}

/* Main container */
.main .block-container {
    padding: 2rem 3rem !important;
    max-width: 1400px !important;
}

/* ============================================
   SIDEBAR - DESIGN PREMIUM
   ============================================ */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1f2e 0%, #0f1419 100%) !important;
    border-right: 1px solid var(--border-subtle) !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 1.5rem !important;
}

/* Sidebar headers */
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
    margin-bottom: 1rem !important;
}

[data-testid="stSidebar"] .stMarkdown h3 {
    font-size: 0.85rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--text-secondary) !important;
    margin-top: 1.5rem !important;
    padding-bottom: 0.5rem !important;
    border-bottom: 1px solid var(--border-subtle) !important;
}

/* ============================================
   CHECKBOXES -> TOGGLE STYLE
   ============================================ */
[data-testid="stSidebar"] .stCheckbox {
    background: var(--bg-tertiary) !important;
    border-radius: var(--radius-md) !important;
    padding: 0.75rem 1rem !important;
    margin-bottom: 0.5rem !important;
    border: 1px solid var(--border-subtle) !important;
    transition: all 0.3s ease !important;
}

[data-testid="stSidebar"] .stCheckbox:hover {
    background: var(--bg-card-hover) !important;
    border-color: var(--accent-emerald) !important;
    transform: translateX(4px);
}

[data-testid="stSidebar"] .stCheckbox label {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
}

[data-testid="stSidebar"] .stCheckbox [data-testid="stCheckbox"] > label > span:first-child {
    background: var(--bg-primary) !important;
    border: 2px solid var(--text-muted) !important;
    border-radius: 6px !important;
    width: 22px !important;
    height: 22px !important;
}

[data-testid="stSidebar"] .stCheckbox input:checked + div {
    background: var(--gradient-primary) !important;
    border-color: var(--accent-emerald) !important;
}

/* ============================================
   SLIDERS
   ============================================ */
.stSlider > div > div > div {
    background: var(--accent-emerald) !important;
}

.stSlider [data-testid="stTickBarMin"],
.stSlider [data-testid="stTickBarMax"] {
    color: var(--text-secondary) !important;
}

/* ============================================
   NUMBER INPUT
   ============================================ */
.stNumberInput > div > div > input {
    background: var(--bg-tertiary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}

.stNumberInput > div > div > input:focus {
    border-color: var(--accent-emerald) !important;
    box-shadow: var(--shadow-glow) !important;
}

/* ============================================
   MULTISELECT
   ============================================ */
.stMultiSelect > div > div {
    background: var(--bg-tertiary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
}

.stMultiSelect > div > div:hover {
    border-color: var(--accent-emerald) !important;
}

.stMultiSelect [data-baseweb="tag"] {
    background: var(--gradient-primary) !important;
    border-radius: var(--radius-sm) !important;
}

/* ============================================
   BUTTONS - PREMIUM STYLE
   ============================================ */
.stButton > button {
    background: var(--gradient-gold) !important;
    color: #1a1a1a !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    letter-spacing: 0.02em !important;
    border: none !important;
    border-radius: var(--radius-lg) !important;
    padding: 0.875rem 2rem !important;
    box-shadow: var(--shadow-md), 0 0 20px rgba(245, 158, 11, 0.3) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    text-transform: uppercase !important;
}

.stButton > button:hover {
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: var(--shadow-lg), 0 0 30px rgba(245, 158, 11, 0.5) !important;
    filter: brightness(1.1) !important;
}

.stButton > button:active {
    transform: translateY(0) scale(0.98) !important;
}

/* Primary button variant */
.stButton > button[kind="primary"] {
    background: var(--gradient-gold) !important;
}

/* Secondary buttons */
.stDownloadButton > button,
button[data-testid="baseButton-secondary"] {
    background: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-subtle) !important;
    box-shadow: var(--shadow-sm) !important;
}

.stDownloadButton > button:hover,
button[data-testid="baseButton-secondary"]:hover {
    background: var(--bg-card-hover) !important;
    border-color: var(--accent-emerald) !important;
    box-shadow: var(--shadow-glow) !important;
}

/* ============================================
   TABS - MODERN STYLE
   ============================================ */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-secondary) !important;
    border-radius: var(--radius-lg) !important;
    padding: 0.5rem !important;
    gap: 0.5rem !important;
    border: 1px solid var(--border-subtle) !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-secondary) !important;
    border-radius: var(--radius-md) !important;
    font-weight: 500 !important;
    padding: 0.75rem 1.5rem !important;
    transition: all 0.3s ease !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-primary) !important;
    background: var(--bg-tertiary) !important;
}

.stTabs [aria-selected="true"] {
    background: var(--gradient-primary) !important;
    color: white !important;
    font-weight: 600 !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}

.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}

/* ============================================
   METRICS / KPI WIDGETS
   ============================================ */
[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 700 !important;
    background: var(--gradient-primary) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
}

[data-testid="stMetricLabel"] {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.1em !important;
}

[data-testid="stMetricDelta"] {
    color: var(--accent-emerald) !important;
}

/* Metric container */
[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.25rem !important;
    transition: all 0.3s ease !important;
}

[data-testid="metric-container"]:hover {
    border-color: var(--accent-emerald) !important;
    box-shadow: var(--shadow-glow) !important;
}

/* ============================================
   ALERTS / INFO BOXES
   ============================================ */
.stAlert {
    background: var(--bg-card) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-lg) !important;
    color: var(--text-primary) !important;
}

.stAlert[data-baseweb="notification"] {
    background: var(--bg-card) !important;
}

/* Success alert */
div[data-testid="stAlert"]:has(.st-emotion-cache-1gulkj5) {
    border-left: 4px solid var(--accent-emerald) !important;
}

/* Info alert */
div[data-testid="stAlert"]:has(.st-emotion-cache-1n76uvr) {
    border-left: 4px solid var(--accent-cyan) !important;
}

/* Warning alert */
div[data-testid="stAlert"]:has(.st-emotion-cache-k7vsyb) {
    border-left: 4px solid var(--accent-gold) !important;
}

/* ============================================
   EXPANDERS
   ============================================ */
.streamlit-expanderHeader {
    background: var(--bg-tertiary) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
    border: 1px solid var(--border-subtle) !important;
}

.streamlit-expanderHeader:hover {
    border-color: var(--accent-emerald) !important;
}

.streamlit-expanderContent {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-top: none !important;
    border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
}

/* ============================================
   DATAFRAMES / TABLES
   ============================================ */
.stDataFrame {
    border-radius: var(--radius-lg) !important;
    overflow: hidden !important;
}

.stDataFrame [data-testid="stDataFrameResizable"] {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-lg) !important;
}

/* ============================================
   SELECTBOX
   ============================================ */
.stSelectbox > div > div {
    background: var(--bg-tertiary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-primary) !important;
}

.stSelectbox > div > div:hover {
    border-color: var(--accent-emerald) !important;
}

/* ============================================
   DIVIDERS
   ============================================ */
hr {
    border-color: var(--border-subtle) !important;
    margin: 2rem 0 !important;
}

/* ============================================
   CUSTOM CLASSES
   ============================================ */

/* Header Premium com Glassmorphism */
.premium-header {
    background: var(--gradient-header) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: var(--radius-xl) !important;
    padding: 2.5rem !important;
    margin-bottom: 2rem !important;
    position: relative !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-lg) !important;
}

.premium-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(16, 185, 129, 0.1) 0%, transparent 50%);
    animation: pulse-glow 4s ease-in-out infinite;
}

@keyframes pulse-glow {
    0%, 100% { opacity: 0.5; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.1); }
}

.premium-header h1 {
    font-size: 2.5rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #fff 0%, #94a3b8 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    margin-bottom: 0.5rem !important;
    position: relative !important;
    z-index: 1 !important;
}

.premium-header p {
    color: var(--text-secondary) !important;
    font-size: 1.1rem !important;
    position: relative !important;
    z-index: 1 !important;
}

/* Bolas de Loteria 3D */
.lottery-ball {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 56px !important;
    height: 56px !important;
    border-radius: 50% !important;
    background: linear-gradient(145deg, #10b981 0%, #059669 50%, #047857 100%) !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 1.25rem !important;
    margin: 6px !important;
    box-shadow:
        inset 0 -8px 20px rgba(0, 0, 0, 0.3),
        inset 0 8px 20px rgba(255, 255, 255, 0.2),
        0 8px 16px rgba(0, 0, 0, 0.4),
        0 0 20px rgba(16, 185, 129, 0.3) !important;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    position: relative !important;
    transform-style: preserve-3d !important;
    transition: all 0.3s ease !important;
}

.lottery-ball::before {
    content: '';
    position: absolute;
    top: 8px;
    left: 12px;
    width: 16px;
    height: 10px;
    background: rgba(255, 255, 255, 0.4);
    border-radius: 50%;
    filter: blur(2px);
}

.lottery-ball:hover {
    transform: translateY(-4px) rotateX(10deg) !important;
    box-shadow:
        inset 0 -8px 20px rgba(0, 0, 0, 0.3),
        inset 0 8px 20px rgba(255, 255, 255, 0.2),
        0 12px 24px rgba(0, 0, 0, 0.5),
        0 0 30px rgba(16, 185, 129, 0.5) !important;
}

/* Bola Fixa (azul) */
.lottery-ball-fixed {
    background: linear-gradient(145deg, #3b82f6 0%, #2563eb 50%, #1d4ed8 100%) !important;
    box-shadow:
        inset 0 -8px 20px rgba(0, 0, 0, 0.3),
        inset 0 8px 20px rgba(255, 255, 255, 0.2),
        0 8px 16px rgba(0, 0, 0, 0.4),
        0 0 20px rgba(59, 130, 246, 0.3) !important;
}

/* Bola Acerto (dourada) */
.lottery-ball-hit {
    background: linear-gradient(145deg, #fbbf24 0%, #f59e0b 50%, #d97706 100%) !important;
    color: #1a1a1a !important;
    box-shadow:
        inset 0 -8px 20px rgba(0, 0, 0, 0.2),
        inset 0 8px 20px rgba(255, 255, 255, 0.3),
        0 8px 16px rgba(0, 0, 0, 0.4),
        0 0 25px rgba(245, 158, 11, 0.5) !important;
    animation: gold-pulse 2s ease-in-out infinite !important;
}

@keyframes gold-pulse {
    0%, 100% { box-shadow:
        inset 0 -8px 20px rgba(0, 0, 0, 0.2),
        inset 0 8px 20px rgba(255, 255, 255, 0.3),
        0 8px 16px rgba(0, 0, 0, 0.4),
        0 0 25px rgba(245, 158, 11, 0.5); }
    50% { box-shadow:
        inset 0 -8px 20px rgba(0, 0, 0, 0.2),
        inset 0 8px 20px rgba(255, 255, 255, 0.3),
        0 8px 16px rgba(0, 0, 0, 0.4),
        0 0 40px rgba(245, 158, 11, 0.8); }
}

/* Cards de Jogo */
.game-card {
    background: var(--bg-card) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-xl) !important;
    padding: 1.5rem !important;
    margin: 1rem 0 !important;
    transition: all 0.3s ease !important;
}

.game-card:hover {
    border-color: var(--accent-emerald) !important;
    box-shadow: var(--shadow-glow) !important;
    transform: translateY(-2px) !important;
}

/* KPI Card */
.kpi-card {
    background: var(--bg-card) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.25rem !important;
    text-align: center !important;
    transition: all 0.3s ease !important;
}

.kpi-card:hover {
    border-color: var(--accent-emerald) !important;
    box-shadow: var(--shadow-glow) !important;
}

.kpi-value {
    font-size: 2rem !important;
    font-weight: 700 !important;
    background: var(--gradient-primary) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
}

.kpi-label {
    color: var(--text-secondary) !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    margin-top: 0.25rem !important;
}

/* Volante Premium */
.volante-premium {
    display: grid !important;
    grid-template-columns: repeat(10, 1fr) !important;
    gap: 8px !important;
    max-width: 500px !important;
    margin: 1rem auto !important;
    padding: 1.5rem !important;
    background: var(--bg-secondary) !important;
    border-radius: var(--radius-xl) !important;
    border: 1px solid var(--border-subtle) !important;
}

.volante-numero {
    width: 40px !important;
    height: 40px !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    background: var(--bg-tertiary) !important;
    color: var(--text-secondary) !important;
    border: 2px solid transparent !important;
    transition: all 0.2s ease !important;
    cursor: default !important;
}

.volante-numero.marcado {
    background: var(--gradient-primary) !important;
    color: white !important;
    border-color: var(--accent-emerald-light) !important;
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.4) !important;
    transform: scale(1.1) !important;
}

/* Stats Section */
.stats-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)) !important;
    gap: 1rem !important;
    margin: 1rem 0 !important;
}

/* Ultimo Sorteio Card */
.ultimo-sorteio {
    background: var(--bg-card) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-xl) !important;
    padding: 1.5rem !important;
}

.ultimo-sorteio h3 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    margin-bottom: 1rem !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
}

/* Animacoes */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in {
    animation: fadeIn 0.5s ease-out forwards !important;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}

.animate-slide-in {
    animation: slideIn 0.4s ease-out forwards !important;
}

/* Scrollbar Custom */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-primary);
}

::-webkit-scrollbar-thumb {
    background: var(--bg-tertiary);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--text-muted);
}

/* Info Panel Premium */
.info-panel {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%) !important;
    border: 1px solid rgba(16, 185, 129, 0.2) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1rem 1.5rem !important;
    display: flex !important;
    align-items: center !important;
    gap: 1rem !important;
}

.info-panel-icon {
    font-size: 1.5rem !important;
}

.info-panel-text {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}

/* Premio Tags */
.premio-sena {
    background: var(--gradient-gold) !important;
    color: #1a1a1a !important;
    padding: 0.25rem 0.75rem !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 700 !important;
    font-size: 0.875rem !important;
}

.premio-quina {
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
    color: white !important;
    padding: 0.25rem 0.75rem !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
}

.premio-quadra {
    background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%) !important;
    color: white !important;
    padding: 0.25rem 0.75rem !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
}

/* Responsivo */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem !important;
    }

    .premium-header h1 {
        font-size: 1.75rem !important;
    }

    .lottery-ball {
        width: 44px !important;
        height: 44px !important;
        font-size: 1rem !important;
    }

    .volante-premium {
        grid-template-columns: repeat(6, 1fr) !important;
    }
}
</style>
"""


def get_premium_styles():
    """Retorna os estilos CSS premium."""
    return PREMIUM_CSS


def criar_bola_html(numero: int, tipo: str = "normal") -> str:
    """
    Cria HTML para uma bola de loteria 3D.
    tipo: 'normal', 'fixed', 'hit'
    """
    classe = "lottery-ball"
    if tipo == "fixed":
        classe += " lottery-ball-fixed"
    elif tipo == "hit":
        classe += " lottery-ball-hit"

    return f'<span class="{classe}">{numero:02d}</span>'


def criar_bolas_jogo(dezenas: list, fixos: set = None, acertos: set = None) -> str:
    """Cria HTML para todas as bolas de um jogo."""
    fixos = fixos or set()
    acertos = acertos or set()

    html = '<div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 4px;">'
    for d in dezenas:
        if d in acertos:
            html += criar_bola_html(d, "hit")
        elif d in fixos:
            html += criar_bola_html(d, "fixed")
        else:
            html += criar_bola_html(d, "normal")
    html += '</div>'
    return html


def criar_header_premium(titulo: str, subtitulo: str) -> str:
    """Cria o header premium com glassmorphism."""
    return f'''
    <div class="premium-header">
        <h1>{titulo}</h1>
        <p>{subtitulo}</p>
    </div>
    '''


def criar_kpi_card(valor: str, label: str, icone: str = "") -> str:
    """Cria um card KPI estilizado."""
    return f'''
    <div class="kpi-card">
        <div class="kpi-value">{icone} {valor}</div>
        <div class="kpi-label">{label}</div>
    </div>
    '''


def criar_volante_premium(dezenas_marcadas: list) -> str:
    """Cria um volante visual premium."""
    html = '<div class="volante-premium">'
    for i in range(1, 61):
        classe = "volante-numero marcado" if i in dezenas_marcadas else "volante-numero"
        html += f'<div class="{classe}">{i:02d}</div>'
    html += '</div>'
    return html


def criar_game_card(numero_jogo: int, dezenas: list, fixos: set = None, info_extra: str = "") -> str:
    """Cria um card de jogo completo."""
    bolas = criar_bolas_jogo(dezenas, fixos)

    return f'''
    <div class="game-card animate-fade-in">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3 style="color: #f1f5f9; margin: 0; font-weight: 600;">Jogo {numero_jogo:02d}</h3>
            {info_extra}
        </div>
        {bolas}
    </div>
    '''
