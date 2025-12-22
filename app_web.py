"""
Gerador Inteligente de Jogos da Mega-Sena - Interface Web
Execute com: streamlit run app_web.py
"""

import datetime as dt
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
import streamlit as st

# Constantes
DEZENA_MIN = 1
DEZENA_MAX = 60
TAMANHO_JOGO = 6
FAIXAS = [(1, 20), (21, 40), (41, 60)]


@dataclass(frozen=True)
class Concurso:
    numero: int
    data: dt.date
    dezenas: Tuple[int, ...]

    @property
    def dezenas_set(self) -> Set[int]:
        return set(self.dezenas)


@dataclass
class ScoreDezena:
    dezena: int
    frequencia: float = 0.0
    markov: float = 0.0
    coocorrencia: float = 0.0
    atraso: float = 0.0

    def score_total(self, pesos: Dict[str, float]) -> float:
        return (
            self.frequencia * pesos.get('frequencia', 0) +
            self.markov * pesos.get('markov', 0) +
            self.coocorrencia * pesos.get('coocorrencia', 0) +
            self.atraso * pesos.get('atraso', 0)
        )


class AnalisadorMegaSena:
    def __init__(self, concursos: List[Concurso]):
        self.concursos = sorted(concursos, key=lambda c: c.data)
        self.ultimo_concurso = self.concursos[-1] if self.concursos else None
        self._frequencias: Optional[Dict[int, int]] = None
        self._matriz_markov: Optional[Dict[int, Dict[int, int]]] = None
        self._coocorrencias: Optional[Dict[Tuple[int, int], int]] = None
        self._atrasos: Optional[Dict[int, int]] = None

    def filtrar_por_anos(self, anos: int) -> 'AnalisadorMegaSena':
        limite = dt.date.today() - dt.timedelta(days=anos * 365)
        filtrados = [c for c in self.concursos if c.data >= limite]
        return AnalisadorMegaSena(filtrados)

    def calcular_frequencias(self) -> Dict[int, int]:
        if self._frequencias is None:
            self._frequencias = defaultdict(int)
            for c in self.concursos:
                for d in c.dezenas:
                    self._frequencias[d] += 1
        return self._frequencias

    def scores_frequencia(self) -> Dict[int, float]:
        freq = self.calcular_frequencias()
        if not freq:
            return {d: 0.0 for d in range(DEZENA_MIN, DEZENA_MAX + 1)}
        max_freq = max(freq.values()) if freq else 1
        return {d: freq.get(d, 0) / max_freq for d in range(DEZENA_MIN, DEZENA_MAX + 1)}

    def calcular_matriz_markov(self) -> Dict[int, Dict[int, int]]:
        if self._matriz_markov is None:
            self._matriz_markov = defaultdict(lambda: defaultdict(int))
            for i in range(len(self.concursos) - 1):
                atual = self.concursos[i]
                proximo = self.concursos[i + 1]
                for d_atual in atual.dezenas:
                    for d_proximo in proximo.dezenas:
                        self._matriz_markov[d_atual][d_proximo] += 1
        return self._matriz_markov

    def scores_markov(self, dezenas_referencia: Optional[Set[int]] = None) -> Dict[int, float]:
        if dezenas_referencia is None:
            if self.ultimo_concurso is None:
                return {d: 0.0 for d in range(DEZENA_MIN, DEZENA_MAX + 1)}
            dezenas_referencia = self.ultimo_concurso.dezenas_set

        matriz = self.calcular_matriz_markov()
        scores = defaultdict(float)

        for d_ref in dezenas_referencia:
            seguidores = matriz.get(d_ref, {})
            for d_seguidor, contagem in seguidores.items():
                scores[d_seguidor] += contagem

        max_score = max(scores.values()) if scores else 1
        return {d: scores.get(d, 0) / max_score for d in range(DEZENA_MIN, DEZENA_MAX + 1)}

    def calcular_coocorrencias(self) -> Dict[Tuple[int, int], int]:
        if self._coocorrencias is None:
            self._coocorrencias = defaultdict(int)
            for c in self.concursos:
                dezenas = sorted(c.dezenas)
                for i in range(len(dezenas)):
                    for j in range(i + 1, len(dezenas)):
                        par = (dezenas[i], dezenas[j])
                        self._coocorrencias[par] += 1
        return self._coocorrencias

    def scores_coocorrencia(self) -> Dict[int, float]:
        cooc = self.calcular_coocorrencias()
        top_pares = sorted(cooc.items(), key=lambda x: x[1], reverse=True)[:100]
        scores = defaultdict(float)
        for (d1, d2), contagem in top_pares:
            scores[d1] += contagem
            scores[d2] += contagem
        max_score = max(scores.values()) if scores else 1
        return {d: scores.get(d, 0) / max_score for d in range(DEZENA_MIN, DEZENA_MAX + 1)}

    def pares_mais_frequentes(self, top_n: int = 20) -> List[Tuple[Tuple[int, int], int]]:
        cooc = self.calcular_coocorrencias()
        return sorted(cooc.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def calcular_atrasos(self) -> Dict[int, int]:
        if self._atrasos is None:
            self._atrasos = {}
            for d in range(DEZENA_MIN, DEZENA_MAX + 1):
                atraso = 0
                for c in reversed(self.concursos):
                    if d in c.dezenas_set:
                        break
                    atraso += 1
                self._atrasos[d] = atraso
        return self._atrasos

    def scores_atraso(self) -> Dict[int, float]:
        atrasos = self.calcular_atrasos()
        max_atraso = max(atrasos.values()) if atrasos else 1
        return {d: atrasos.get(d, 0) / max_atraso for d in range(DEZENA_MIN, DEZENA_MAX + 1)}

    def dezenas_mais_atrasadas(self, top_n: int = 10) -> List[Tuple[int, int]]:
        atrasos = self.calcular_atrasos()
        return sorted(atrasos.items(), key=lambda x: x[1], reverse=True)[:top_n]


class GeradorJogos:
    def __init__(self, analisador: AnalisadorMegaSena, rng: Optional[random.Random] = None):
        self.analisador = analisador
        self.rng = rng or random.Random()

    def _faixa(self, dezena: int) -> int:
        for idx, (inicio, fim) in enumerate(FAIXAS):
            if inicio <= dezena <= fim:
                return idx
        return -1

    def _verificar_balanceamento(self, dezenas: List[int]) -> bool:
        pares = sum(1 for d in dezenas if d % 2 == 0)
        if pares != 3:
            return False
        faixas = [self._faixa(d) for d in dezenas]
        for i in range(len(FAIXAS)):
            count = faixas.count(i)
            if count < 1 or count > 3:
                return False
        return True

    def gerar_uniforme(self) -> List[int]:
        return sorted(self.rng.sample(range(DEZENA_MIN, DEZENA_MAX + 1), TAMANHO_JOGO))

    def gerar_por_scores(self, pesos: Dict[str, float], forcar_balanceamento: bool = False, max_tentativas: int = 500) -> List[int]:
        scores_freq = self.analisador.scores_frequencia() if pesos.get('frequencia', 0) > 0 else {}
        scores_markov = self.analisador.scores_markov() if pesos.get('markov', 0) > 0 else {}
        scores_cooc = self.analisador.scores_coocorrencia() if pesos.get('coocorrencia', 0) > 0 else {}
        scores_atraso = self.analisador.scores_atraso() if pesos.get('atraso', 0) > 0 else {}

        scores_combinados = {}
        for d in range(DEZENA_MIN, DEZENA_MAX + 1):
            score = ScoreDezena(
                dezena=d,
                frequencia=scores_freq.get(d, 0),
                markov=scores_markov.get(d, 0),
                coocorrencia=scores_cooc.get(d, 0),
                atraso=scores_atraso.get(d, 0)
            )
            scores_combinados[d] = score.score_total(pesos)

        dezenas = list(range(DEZENA_MIN, DEZENA_MAX + 1))
        pesos_escolha = [scores_combinados[d] + 0.1 for d in dezenas]

        for _ in range(max_tentativas):
            escolhidas: Set[int] = set()
            tentativas_internas = 0
            while len(escolhidas) < TAMANHO_JOGO and tentativas_internas < 100:
                escolha = self.rng.choices(dezenas, weights=pesos_escolha, k=1)[0]
                escolhidas.add(escolha)
                tentativas_internas += 1

            if len(escolhidas) < TAMANHO_JOGO:
                continue

            jogo = sorted(escolhidas)
            if not forcar_balanceamento or self._verificar_balanceamento(jogo):
                return jogo

        return self.gerar_uniforme()

    def gerar_jogos(self, quantidade: int, algoritmos: List[str], forcar_balanceamento: bool = False) -> List[List[int]]:
        peso_base = 1.0 / len(algoritmos) if algoritmos else 0
        pesos = {
            'frequencia': peso_base if 'frequencia' in algoritmos else 0,
            'markov': peso_base if 'markov' in algoritmos else 0,
            'coocorrencia': peso_base if 'coocorrencia' in algoritmos else 0,
            'atraso': peso_base if 'atraso' in algoritmos else 0,
        }

        jogos = []
        jogos_gerados: Set[tuple] = set()

        tentativas = 0
        while len(jogos) < quantidade and tentativas < quantidade * 10:
            tentativas += 1
            if 'uniforme' in algoritmos and not any(pesos.values()):
                jogo = self.gerar_uniforme()
            else:
                jogo = self.gerar_por_scores(pesos, forcar_balanceamento)

            jogo_tuple = tuple(jogo)
            if jogo_tuple not in jogos_gerados:
                jogos_gerados.add(jogo_tuple)
                jogos.append(jogo)

        return jogos


@st.cache_data
def carregar_resultados_excel(caminho: str) -> List[Concurso]:
    df = pd.read_excel(caminho)
    concursos = []

    col_concurso = None
    col_data = None
    colunas_dezenas = []

    for col in df.columns:
        col_lower = str(col).lower().strip()
        if col_lower == 'concurso':
            col_concurso = col
        elif col_lower in ('data', 'data do sorteio'):
            col_data = col
        elif 'dezena' in col_lower or 'bola' in col_lower:
            colunas_dezenas.append(col)

    colunas_dezenas = sorted(colunas_dezenas, key=lambda x: int(''.join(filter(str.isdigit, str(x))) or 0))

    for _, linha in df.iterrows():
        try:
            numero = int(linha[col_concurso]) if col_concurso else 0
            valor_data = linha[col_data]
            if isinstance(valor_data, dt.datetime):
                data = valor_data.date()
            elif isinstance(valor_data, dt.date):
                data = valor_data
            else:
                data = dt.datetime.strptime(str(valor_data), "%d/%m/%Y").date()

            dezenas = tuple(sorted(int(linha[c]) for c in colunas_dezenas[:6]))

            if len(dezenas) == 6 and all(DEZENA_MIN <= d <= DEZENA_MAX for d in dezenas):
                concursos.append(Concurso(numero=numero, data=data, dezenas=dezenas))
        except Exception:
            continue

    return concursos


def criar_volante_html(dezenas: List[int]) -> str:
    """Cria um volante visual da Mega-Sena."""
    html = """
    <style>
        .volante {
            display: grid;
            grid-template-columns: repeat(10, 1fr);
            gap: 5px;
            max-width: 400px;
            margin: 10px 0;
        }
        .numero {
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 14px;
            border: 2px solid #ccc;
            background: white;
        }
        .numero.marcado {
            background: linear-gradient(135deg, #2e7d32, #4caf50);
            color: white;
            border-color: #1b5e20;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
    </style>
    <div class="volante">
    """

    for i in range(1, 61):
        classe = "numero marcado" if i in dezenas else "numero"
        html += f'<div class="{classe}">{i:02d}</div>'

    html += "</div>"
    return html


def main():
    st.set_page_config(
        page_title="Mega-Sena - Gerador Inteligente",
        page_icon="🍀",
        layout="wide"
    )

    # CSS personalizado
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(135deg, #1a5f2a, #2e7d32);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 20px;
        }
        .jogo-card {
            background: linear-gradient(135deg, #f5f5f5, #e0e0e0);
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            border-left: 5px solid #2e7d32;
        }
        .numero-grande {
            display: inline-block;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            background: linear-gradient(135deg, #2e7d32, #4caf50);
            color: white;
            text-align: center;
            line-height: 45px;
            font-weight: bold;
            font-size: 18px;
            margin: 3px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-numero {
            font-size: 32px;
            font-weight: bold;
            color: #2e7d32;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🍀 Gerador Inteligente - Mega-Sena</h1>
        <p>Combine algoritmos estatisticos para gerar seus jogos</p>
    </div>
    """, unsafe_allow_html=True)

    # Carregar dados
    caminho = Path("resultados.xlsx")
    if not caminho.exists():
        st.error("Arquivo 'resultados.xlsx' nao encontrado!")
        return

    concursos = carregar_resultados_excel(str(caminho))
    analisador_completo = AnalisadorMegaSena(concursos)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuracoes")

        st.subheader("📅 Periodo de Analise")
        anos = st.slider("Anos de historico:", 1, 10, 3)

        analisador = analisador_completo.filtrar_por_anos(anos)
        st.info(f"📊 {len(analisador.concursos)} concursos analisados")

        st.subheader("🧮 Algoritmos")

        usar_frequencia = st.checkbox("📈 Frequencia", value=True, help="Numeros mais sorteados")
        usar_markov = st.checkbox("🔗 Markov", value=True, help="Seguidores do ultimo sorteio")
        usar_coocorrencia = st.checkbox("👥 Co-ocorrencia", value=False, help="Pares frequentes")
        usar_atraso = st.checkbox("⏰ Atrasados", value=False, help="Numeros que nao saem ha tempo")
        usar_balanceado = st.checkbox("⚖️ Balanceado", value=True, help="Equilibrio par/impar")
        usar_uniforme = st.checkbox("🎲 Uniforme", value=False, help="Aleatorio puro")

        st.subheader("🎯 Quantidade")
        qtd_jogos = st.number_input("Jogos a gerar:", 1, 20, 6)

    # Tabs principais
    tab1, tab2, tab3 = st.tabs(["🎰 Gerar Jogos", "📊 Estatisticas", "ℹ️ Sobre"])

    with tab1:
        col1, col2 = st.columns([2, 1])

        with col1:
            if st.button("🍀 GERAR JOGOS", type="primary", use_container_width=True):
                algoritmos = []
                if usar_frequencia:
                    algoritmos.append('frequencia')
                if usar_markov:
                    algoritmos.append('markov')
                if usar_coocorrencia:
                    algoritmos.append('coocorrencia')
                if usar_atraso:
                    algoritmos.append('atraso')
                if usar_uniforme:
                    algoritmos.append('uniforme')

                if not algoritmos and not usar_balanceado:
                    st.warning("Selecione pelo menos um algoritmo!")
                else:
                    gerador = GeradorJogos(analisador)
                    jogos = gerador.gerar_jogos(qtd_jogos, algoritmos, usar_balanceado)

                    st.success(f"✅ {len(jogos)} jogos gerados!")

                    # Exibir algoritmos usados
                    algos_nomes = []
                    if usar_frequencia: algos_nomes.append("Frequencia")
                    if usar_markov: algos_nomes.append("Markov")
                    if usar_coocorrencia: algos_nomes.append("Co-ocorrencia")
                    if usar_atraso: algos_nomes.append("Atrasados")
                    if usar_balanceado: algos_nomes.append("Balanceado")
                    if usar_uniforme: algos_nomes.append("Uniforme")

                    st.caption(f"Algoritmos: {', '.join(algos_nomes)}")

                    for i, jogo in enumerate(jogos, 1):
                        pares = sum(1 for d in jogo if d % 2 == 0)
                        impares = 6 - pares

                        with st.container():
                            st.markdown(f"### Jogo {i:02d}")

                            # Numeros grandes
                            numeros_html = "".join([f'<span class="numero-grande">{d:02d}</span>' for d in jogo])
                            st.markdown(f'<div>{numeros_html}</div>', unsafe_allow_html=True)

                            # Info do jogo
                            col_a, col_b, col_c = st.columns(3)
                            col_a.metric("Pares", pares)
                            col_b.metric("Impares", impares)

                            faixas = [0, 0, 0]
                            for d in jogo:
                                if d <= 20: faixas[0] += 1
                                elif d <= 40: faixas[1] += 1
                                else: faixas[2] += 1
                            col_c.metric("Faixas", f"{faixas[0]}-{faixas[1]}-{faixas[2]}")

                            # Volante visual
                            with st.expander("Ver Volante"):
                                st.markdown(criar_volante_html(jogo), unsafe_allow_html=True)

                            st.divider()

        with col2:
            st.subheader("📋 Ultimo Sorteio")
            if analisador.ultimo_concurso:
                st.write(f"**Concurso:** {analisador.ultimo_concurso.numero}")
                st.write(f"**Data:** {analisador.ultimo_concurso.data}")
                numeros = " - ".join([f"{d:02d}" for d in analisador.ultimo_concurso.dezenas])
                st.code(numeros)

    with tab2:
        st.subheader("📊 Analise Estatistica")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 🔥 Numeros Quentes")
            freq = analisador.calcular_frequencias()
            top_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]

            df_freq = pd.DataFrame(top_freq, columns=['Dezena', 'Frequencia'])
            df_freq['Dezena'] = df_freq['Dezena'].apply(lambda x: f"{x:02d}")
            st.dataframe(df_freq, use_container_width=True, hide_index=True)

        with col2:
            st.markdown("### ❄️ Numeros Atrasados")
            atrasados = analisador.dezenas_mais_atrasadas(10)

            df_atraso = pd.DataFrame(atrasados, columns=['Dezena', 'Sorteios sem sair'])
            df_atraso['Dezena'] = df_atraso['Dezena'].apply(lambda x: f"{x:02d}")
            st.dataframe(df_atraso, use_container_width=True, hide_index=True)

        with col3:
            st.markdown("### 👥 Pares Frequentes")
            pares = analisador.pares_mais_frequentes(10)

            df_pares = pd.DataFrame([(f"{p[0]:02d}-{p[1]:02d}", c) for p, c in pares],
                                   columns=['Par', 'Vezes juntos'])
            st.dataframe(df_pares, use_container_width=True, hide_index=True)

        # Graficos
        st.subheader("📈 Graficos")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Frequencia por Dezena")
            todas_freq = [(d, freq.get(d, 0)) for d in range(1, 61)]
            df_todas = pd.DataFrame(todas_freq, columns=['Dezena', 'Frequencia'])
            st.bar_chart(df_todas.set_index('Dezena'))

        with col2:
            st.markdown("#### Atraso por Dezena")
            atrasos = analisador.calcular_atrasos()
            todos_atrasos = [(d, atrasos.get(d, 0)) for d in range(1, 61)]
            df_atrasos = pd.DataFrame(todos_atrasos, columns=['Dezena', 'Atraso'])
            st.bar_chart(df_atrasos.set_index('Dezena'))

    with tab3:
        st.subheader("ℹ️ Como Funciona")

        st.markdown("""
        ### Algoritmos Disponiveis

        | Algoritmo | Descricao |
        |-----------|-----------|
        | **Frequencia** | Prioriza numeros que mais sairam no periodo |
        | **Markov** | Analisa quais numeros tendem a seguir os do ultimo sorteio |
        | **Co-ocorrencia** | Prioriza numeros que costumam sair juntos |
        | **Atrasados** | Prioriza numeros que nao saem ha muito tempo |
        | **Balanceado** | Forca 3 pares/3 impares e distribuicao por faixas |
        | **Uniforme** | Geracao totalmente aleatoria |

        ### Formula de Pontuacao

        Cada dezena recebe um score combinado:
        ```
        Score = (freq × peso) + (markov × peso) + (cooc × peso) + (atraso × peso)
        ```

        Os jogos sao gerados priorizando dezenas com maiores scores.

        ### Importante

        ⚠️ **Loteria e um jogo de azar.** Nenhum algoritmo pode prever os numeros sorteados.
        Estes metodos apenas organizam as apostas baseado em estatisticas historicas.
        """)

        st.markdown("---")
        st.caption(f"Base de dados: {len(concursos)} concursos | Periodo: {concursos[0].data} a {concursos[-1].data}")


if __name__ == "__main__":
    main()
