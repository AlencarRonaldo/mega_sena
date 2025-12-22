"""
Gerador Inteligente de Jogos da Mega-Sena - Interface Web
Execute com: streamlit run app_web.py

Funcionalidades:
- Geracao de jogos com multiplos algoritmos
- Numeros fixos e removidos
- Fechamento/Desdobramento
- Conferencia automatica
- Simulador de jogos
- Salvar/carregar jogos
- Exportar PDF/Excel
- Atualizacao automatica de resultados
"""

import datetime as dt
import io
import itertools
import json
import random
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import requests

import pandas as pd
import streamlit as st

# Constantes
DEZENA_MIN = 1
DEZENA_MAX = 60
TAMANHO_JOGO = 6
FAIXAS = [(1, 20), (21, 40), (41, 60)]
ARQUIVO_JOGOS_SALVOS = "jogos_salvos.json"


@dataclass(frozen=True)
class Concurso:
    numero: int
    data: dt.date
    dezenas: Tuple[int, ...]

    @property
    def dezenas_set(self) -> Set[int]:
        return set(self.dezenas)

    def to_dict(self) -> dict:
        return {
            'numero': self.numero,
            'data': self.data.isoformat(),
            'dezenas': list(self.dezenas)
        }


@dataclass
class JogoSalvo:
    id: int
    dezenas: List[int]
    data_criacao: str
    algoritmos: List[str]
    conferido: bool = False
    acertos: Dict[int, int] = None  # {concurso: acertos}

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'dezenas': self.dezenas,
            'data_criacao': self.data_criacao,
            'algoritmos': self.algoritmos,
            'conferido': self.conferido,
            'acertos': self.acertos or {}
        }

    @staticmethod
    def from_dict(d: dict) -> 'JogoSalvo':
        return JogoSalvo(
            id=d['id'],
            dezenas=d['dezenas'],
            data_criacao=d['data_criacao'],
            algoritmos=d['algoritmos'],
            conferido=d.get('conferido', False),
            acertos=d.get('acertos', {})
        )


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

    def conferir_jogo(self, dezenas: List[int], concurso: Concurso) -> int:
        """Retorna quantidade de acertos do jogo no concurso."""
        return len(set(dezenas) & concurso.dezenas_set)

    def simular_jogo(self, dezenas: List[int], ultimos_n: int = 100) -> Dict[str, any]:
        """Simula um jogo nos ultimos N concursos."""
        concursos_sim = self.concursos[-ultimos_n:] if len(self.concursos) > ultimos_n else self.concursos
        resultados = {
            'total_concursos': len(concursos_sim),
            'acertos': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0},
            'detalhes': []
        }

        for c in concursos_sim:
            acertos = self.conferir_jogo(dezenas, c)
            resultados['acertos'][acertos] += 1
            if acertos >= 4:
                resultados['detalhes'].append({
                    'concurso': c.numero,
                    'data': c.data.isoformat(),
                    'acertos': acertos,
                    'dezenas_sorteadas': list(c.dezenas)
                })

        return resultados


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

    def gerar_uniforme(self, numeros_fixos: Set[int] = None, numeros_removidos: Set[int] = None) -> List[int]:
        numeros_fixos = numeros_fixos or set()
        numeros_removidos = numeros_removidos or set()

        disponiveis = [d for d in range(DEZENA_MIN, DEZENA_MAX + 1)
                       if d not in numeros_removidos and d not in numeros_fixos]

        faltam = TAMANHO_JOGO - len(numeros_fixos)
        if faltam > len(disponiveis):
            faltam = len(disponiveis)

        escolhidos = list(numeros_fixos) + self.rng.sample(disponiveis, faltam)
        return sorted(escolhidos)[:TAMANHO_JOGO]

    def gerar_por_scores(self, pesos: Dict[str, float], forcar_balanceamento: bool = False,
                         numeros_fixos: Set[int] = None, numeros_removidos: Set[int] = None,
                         max_tentativas: int = 500) -> List[int]:
        numeros_fixos = numeros_fixos or set()
        numeros_removidos = numeros_removidos or set()

        scores_freq = self.analisador.scores_frequencia() if pesos.get('frequencia', 0) > 0 else {}
        scores_markov = self.analisador.scores_markov() if pesos.get('markov', 0) > 0 else {}
        scores_cooc = self.analisador.scores_coocorrencia() if pesos.get('coocorrencia', 0) > 0 else {}
        scores_atraso = self.analisador.scores_atraso() if pesos.get('atraso', 0) > 0 else {}

        scores_combinados = {}
        for d in range(DEZENA_MIN, DEZENA_MAX + 1):
            if d in numeros_removidos:
                scores_combinados[d] = 0
            else:
                score = ScoreDezena(
                    dezena=d,
                    frequencia=scores_freq.get(d, 0),
                    markov=scores_markov.get(d, 0),
                    coocorrencia=scores_cooc.get(d, 0),
                    atraso=scores_atraso.get(d, 0)
                )
                scores_combinados[d] = score.score_total(pesos)

        dezenas = [d for d in range(DEZENA_MIN, DEZENA_MAX + 1) if d not in numeros_removidos and d not in numeros_fixos]
        pesos_escolha = [scores_combinados.get(d, 0) + 0.1 for d in dezenas]

        faltam = TAMANHO_JOGO - len(numeros_fixos)

        for _ in range(max_tentativas):
            escolhidas: Set[int] = set(numeros_fixos)
            tentativas_internas = 0
            while len(escolhidas) < TAMANHO_JOGO and tentativas_internas < 100:
                if dezenas and pesos_escolha:
                    escolha = self.rng.choices(dezenas, weights=pesos_escolha, k=1)[0]
                    escolhidas.add(escolha)
                tentativas_internas += 1

            if len(escolhidas) < TAMANHO_JOGO:
                continue

            jogo = sorted(escolhidas)
            if not forcar_balanceamento or self._verificar_balanceamento(jogo):
                return jogo

        return self.gerar_uniforme(numeros_fixos, numeros_removidos)

    def gerar_jogos(self, quantidade: int, algoritmos: List[str], forcar_balanceamento: bool = False,
                    numeros_fixos: Set[int] = None, numeros_removidos: Set[int] = None) -> List[List[int]]:
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
                jogo = self.gerar_uniforme(numeros_fixos, numeros_removidos)
            else:
                jogo = self.gerar_por_scores(pesos, forcar_balanceamento, numeros_fixos, numeros_removidos)

            jogo_tuple = tuple(jogo)
            if jogo_tuple not in jogos_gerados:
                jogos_gerados.add(jogo_tuple)
                jogos.append(jogo)

        return jogos


class GeradorFechamento:
    """Gera fechamentos/desdobramentos para garantir premiacoes."""

    @staticmethod
    def gerar_fechamento(dezenas_base: List[int], garantia: int = 4) -> List[List[int]]:
        """
        Gera um fechamento a partir de dezenas base.
        garantia: 4 = garantir quadra, 5 = garantir quina, 6 = garantir sena
        """
        if len(dezenas_base) < 6:
            return [sorted(dezenas_base)]

        if len(dezenas_base) == 6:
            return [sorted(dezenas_base)]

        # Gerar todas as combinacoes de 6 numeros
        todas_combinacoes = list(itertools.combinations(sorted(dezenas_base), 6))

        if garantia == 6:
            # Para garantir sena, precisa de todas as combinacoes
            return [list(c) for c in todas_combinacoes]

        # Fechamento otimizado para garantir quadra ou quina
        jogos_selecionados = []
        combinacoes_cobertas = set()

        # Gerar subconjuntos que precisam ser cobertos
        tamanho_cobertura = garantia
        subconjuntos_necessarios = set(itertools.combinations(sorted(dezenas_base), tamanho_cobertura))

        for combo in todas_combinacoes:
            # Verificar quais subconjuntos esta combinacao cobre
            subs_cobertos = set(itertools.combinations(combo, tamanho_cobertura))
            novos_cobertos = subs_cobertos - combinacoes_cobertas

            if novos_cobertos:
                jogos_selecionados.append(list(combo))
                combinacoes_cobertas.update(subs_cobertos)

                if combinacoes_cobertas >= subconjuntos_necessarios:
                    break

        return jogos_selecionados

    @staticmethod
    def info_fechamento(num_dezenas: int) -> Dict[str, int]:
        """Retorna informacoes sobre o fechamento."""
        from math import comb
        total_jogos = comb(num_dezenas, 6)

        # Estimativas de jogos necessarios para cada garantia
        # (valores aproximados baseados em tabelas de fechamento)
        fechamentos = {
            7: {'total': 7, 'quadra': 4, 'quina': 6, 'sena': 7},
            8: {'total': 28, 'quadra': 6, 'quina': 12, 'sena': 28},
            9: {'total': 84, 'quadra': 9, 'quina': 30, 'sena': 84},
            10: {'total': 210, 'quadra': 14, 'quina': 50, 'sena': 210},
            11: {'total': 462, 'quadra': 20, 'quina': 77, 'sena': 462},
            12: {'total': 924, 'quadra': 27, 'quina': 132, 'sena': 924},
            13: {'total': 1716, 'quadra': 35, 'quina': 210, 'sena': 1716},
            14: {'total': 3003, 'quadra': 45, 'quina': 315, 'sena': 3003},
            15: {'total': 5005, 'quadra': 56, 'quina': 455, 'sena': 5005},
            16: {'total': 8008, 'quadra': 70, 'quina': 640, 'sena': 8008},
        }

        return fechamentos.get(num_dezenas, {'total': total_jogos, 'quadra': '?', 'quina': '?', 'sena': total_jogos})


def carregar_jogos_salvos() -> List[JogoSalvo]:
    """Carrega jogos salvos do arquivo JSON."""
    caminho = Path(ARQUIVO_JOGOS_SALVOS)
    if not caminho.exists():
        return []
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            return [JogoSalvo.from_dict(j) for j in dados]
    except Exception:
        return []


def salvar_jogos(jogos: List[JogoSalvo]):
    """Salva jogos no arquivo JSON."""
    with open(ARQUIVO_JOGOS_SALVOS, 'w', encoding='utf-8') as f:
        json.dump([j.to_dict() for j in jogos], f, ensure_ascii=False, indent=2)


def proximo_id_jogo(jogos: List[JogoSalvo]) -> int:
    """Retorna o proximo ID disponivel."""
    if not jogos:
        return 1
    return max(j.id for j in jogos) + 1


def buscar_concurso_caixa(numero: int = None) -> Dict:
    """Busca um concurso especifico ou o ultimo da API da Caixa."""
    try:
        if numero:
            url = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena/{numero}"
        else:
            url = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


def buscar_todos_concursos_novos(ultimo_local: int, limite: int = 10) -> List[Dict]:
    """Busca concursos novos desde o ultimo local (maximo de 'limite' por vez)."""
    novos = []

    # Primeiro busca o ultimo concurso para saber ate onde ir
    ultimo = buscar_concurso_caixa()
    if not ultimo:
        return novos

    ultimo_numero = ultimo.get('numero', 0)

    # Se ja esta atualizado
    if ultimo_local >= ultimo_numero:
        return []

    # Limitar quantidade para nao demorar muito
    inicio = ultimo_local + 1
    fim = min(ultimo_numero + 1, inicio + limite)

    # Busca concursos faltantes (limitado)
    for num in range(inicio, fim):
        concurso = buscar_concurso_caixa(num)
        if concurso:
            novos.append(concurso)

    return novos


def converter_concurso_caixa(dados: Dict) -> Dict:
    """Converte dados da API da Caixa para formato do Excel."""
    try:
        dezenas = dados.get('listaDezenas', [])
        if not dezenas:
            dezenas = dados.get('dezenas', [])

        # Converter para inteiros
        dezenas_int = [int(d) for d in dezenas[:6]]

        return {
            'concurso': dados.get('numero'),
            'data': dados.get('dataApuracao', ''),
            'dezena1': dezenas_int[0] if len(dezenas_int) > 0 else 0,
            'dezena2': dezenas_int[1] if len(dezenas_int) > 1 else 0,
            'dezena3': dezenas_int[2] if len(dezenas_int) > 2 else 0,
            'dezena4': dezenas_int[3] if len(dezenas_int) > 3 else 0,
            'dezena5': dezenas_int[4] if len(dezenas_int) > 4 else 0,
            'dezena6': dezenas_int[5] if len(dezenas_int) > 5 else 0,
        }
    except Exception:
        return None


def atualizar_arquivo_resultados(caminho: str = "resultados.xlsx") -> Tuple[bool, str, int]:
    """
    Atualiza o arquivo de resultados com novos concursos da Caixa.
    Retorna: (sucesso, mensagem, quantidade_novos)
    """
    try:
        # Carregar dados existentes
        if Path(caminho).exists():
            df = pd.read_excel(caminho)
            ultimo_local = int(df['concurso'].max()) if 'concurso' in df.columns else 0
        else:
            df = pd.DataFrame(columns=['concurso', 'data', 'dezena1', 'dezena2', 'dezena3', 'dezena4', 'dezena5', 'dezena6'])
            ultimo_local = 0

        # Buscar novos concursos
        novos = buscar_todos_concursos_novos(ultimo_local)

        if not novos:
            return True, "Base de dados ja esta atualizada!", 0

        # Converter e adicionar novos concursos
        novos_convertidos = []
        for c in novos:
            convertido = converter_concurso_caixa(c)
            if convertido:
                novos_convertidos.append(convertido)

        if novos_convertidos:
            df_novos = pd.DataFrame(novos_convertidos)
            df = pd.concat([df, df_novos], ignore_index=True)
            df = df.drop_duplicates(subset=['concurso'], keep='last')
            df = df.sort_values('concurso')

            # Salvar arquivo
            df.to_excel(caminho, index=False)

            return True, f"Adicionados {len(novos_convertidos)} novos concursos!", len(novos_convertidos)

        return True, "Nenhum concurso novo encontrado.", 0

    except Exception as e:
        return False, f"Erro ao atualizar: {str(e)}", 0


def verificar_atualizacao_automatica(caminho: str = "resultados.xlsx") -> Tuple[bool, int]:
    """
    Verifica se ha novos concursos disponiveis.
    Retorna: (ha_novos, ultimo_disponivel)
    """
    try:
        ultimo = buscar_concurso_caixa()
        if not ultimo:
            return False, 0

        ultimo_disponivel = ultimo.get('numero', 0)

        if Path(caminho).exists():
            df = pd.read_excel(caminho)
            ultimo_local = int(df['concurso'].max()) if 'concurso' in df.columns else 0
        else:
            ultimo_local = 0

        return ultimo_disponivel > ultimo_local, ultimo_disponivel
    except Exception:
        return False, 0


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


def gerar_excel_jogos(jogos: List[List[int]], algoritmos: List[str]) -> bytes:
    """Gera arquivo Excel com os jogos."""
    dados = []
    for i, jogo in enumerate(jogos, 1):
        linha = {'Jogo': i}
        for j, d in enumerate(jogo, 1):
            linha[f'Dezena {j}'] = d
        linha['Pares'] = sum(1 for d in jogo if d % 2 == 0)
        linha['Impares'] = 6 - linha['Pares']
        dados.append(linha)

    df = pd.DataFrame(dados)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Jogos')

        # Adicionar aba com info
        info_df = pd.DataFrame({
            'Informacao': ['Data de Geracao', 'Algoritmos Usados', 'Total de Jogos'],
            'Valor': [dt.datetime.now().strftime('%d/%m/%Y %H:%M'), ', '.join(algoritmos), len(jogos)]
        })
        info_df.to_excel(writer, index=False, sheet_name='Info')

    return output.getvalue()


def gerar_csv_jogos(jogos: List[List[int]]) -> str:
    """Gera CSV com os jogos."""
    linhas = ['Jogo,Dezena1,Dezena2,Dezena3,Dezena4,Dezena5,Dezena6']
    for i, jogo in enumerate(jogos, 1):
        linhas.append(f'{i},{",".join(str(d) for d in jogo)}')
    return '\n'.join(linhas)


def main():
    st.set_page_config(
        page_title="Mega-Sena - Gerador Inteligente",
        page_icon="🍀",
        layout="wide"
    )

    # Inicializar session state
    if 'jogos_gerados' not in st.session_state:
        st.session_state.jogos_gerados = []
    if 'algoritmos_usados' not in st.session_state:
        st.session_state.algoritmos_usados = []

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
        .numero-fixo {
            background: linear-gradient(135deg, #1565c0, #42a5f5) !important;
        }
        .numero-acerto {
            background: linear-gradient(135deg, #f9a825, #fdd835) !important;
            color: #333 !important;
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
        .premio-sena { color: #2e7d32; font-weight: bold; }
        .premio-quina { color: #1565c0; font-weight: bold; }
        .premio-quadra { color: #f9a825; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🍀 Gerador Inteligente - Mega-Sena</h1>
        <p>Gere jogos com algoritmos estatisticos, fechamentos, simulacoes e muito mais!</p>
    </div>
    """, unsafe_allow_html=True)

    # Carregar dados
    caminho = Path("resultados.xlsx")
    if not caminho.exists():
        st.error("Arquivo 'resultados.xlsx' nao encontrado!")
        st.info("Clique em 'Atualizar Resultados' na aba Configuracoes para baixar os dados.")
        return

    concursos = carregar_resultados_excel(str(caminho))
    analisador_completo = AnalisadorMegaSena(concursos)

    # Atualizar automaticamente se houver novos concursos
    if 'atualizacao_verificada' not in st.session_state:
        st.session_state.atualizacao_verificada = False

    if not st.session_state.atualizacao_verificada:
        ha_atualizacao, ultimo_caixa = verificar_atualizacao_automatica()
        if ha_atualizacao:
            with st.spinner("🔄 Atualizando resultados..."):
                sucesso, msg, qtd = atualizar_arquivo_resultados()
            if sucesso and qtd > 0:
                st.cache_data.clear()
                st.session_state.atualizacao_verificada = True
                st.rerun()
        st.session_state.atualizacao_verificada = True

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
        qtd_jogos = st.number_input("Jogos a gerar:", 1, 50, 6)

        # Lista de todos os numeros disponiveis
        todos_numeros = [f"{i:02d}" for i in range(1, 61)]

        st.subheader("🔢 Numeros Fixos")
        numeros_fixos_sel = st.multiselect(
            "Selecione numeros fixos (max 6):",
            options=todos_numeros,
            default=[],
            help="Numeros que DEVEM aparecer em todos os jogos",
            max_selections=6
        )

        st.subheader("🚫 Numeros Removidos")
        # Filtrar numeros ja selecionados como fixos
        numeros_disponiveis = [n for n in todos_numeros if n not in numeros_fixos_sel]
        numeros_removidos_sel = st.multiselect(
            "Selecione numeros a remover:",
            options=numeros_disponiveis,
            default=[],
            help="Numeros que NAO devem aparecer"
        )

    # Converter selecoes para sets de inteiros
    numeros_fixos = {int(n) for n in numeros_fixos_sel}
    numeros_removidos = {int(n) for n in numeros_removidos_sel}

    # Tabs principais
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🎰 Gerar Jogos",
        "📊 Estatisticas",
        "🔒 Fechamento",
        "🎯 Simulador",
        "💾 Meus Jogos",
        "✅ Conferir"
    ])

    with tab1:
        col1, col2 = st.columns([2, 1])

        with col1:
            # Mostrar numeros fixos/removidos
            if numeros_fixos:
                st.info(f"🔵 Numeros Fixos: {', '.join(f'{n:02d}' for n in sorted(numeros_fixos))}")
            if numeros_removidos:
                st.warning(f"🔴 Numeros Removidos: {', '.join(f'{n:02d}' for n in sorted(numeros_removidos))}")

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
                    jogos = gerador.gerar_jogos(qtd_jogos, algoritmos, usar_balanceado, numeros_fixos, numeros_removidos)

                    st.session_state.jogos_gerados = jogos
                    st.session_state.algoritmos_usados = algoritmos + (['balanceado'] if usar_balanceado else [])

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

            # Exibir jogos gerados
            if st.session_state.jogos_gerados:
                st.markdown("---")

                # Botoes de exportacao
                col_exp1, col_exp2, col_exp3 = st.columns(3)

                with col_exp1:
                    excel_data = gerar_excel_jogos(st.session_state.jogos_gerados, st.session_state.algoritmos_usados)
                    st.download_button(
                        label="📥 Baixar Excel",
                        data=excel_data,
                        file_name=f"jogos_megasena_{dt.datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                with col_exp2:
                    csv_data = gerar_csv_jogos(st.session_state.jogos_gerados)
                    st.download_button(
                        label="📥 Baixar CSV",
                        data=csv_data,
                        file_name=f"jogos_megasena_{dt.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )

                with col_exp3:
                    if st.button("💾 Salvar Jogos"):
                        jogos_salvos = carregar_jogos_salvos()
                        for jogo in st.session_state.jogos_gerados:
                            novo_jogo = JogoSalvo(
                                id=proximo_id_jogo(jogos_salvos),
                                dezenas=jogo,
                                data_criacao=dt.datetime.now().isoformat(),
                                algoritmos=st.session_state.algoritmos_usados
                            )
                            jogos_salvos.append(novo_jogo)
                        salvar_jogos(jogos_salvos)
                        st.success(f"✅ {len(st.session_state.jogos_gerados)} jogos salvos!")

                st.markdown("---")

                for i, jogo in enumerate(st.session_state.jogos_gerados, 1):
                    pares = sum(1 for d in jogo if d % 2 == 0)
                    impares = 6 - pares

                    with st.container():
                        st.markdown(f"### Jogo {i:02d}")

                        # Numeros grandes (destacar fixos)
                        numeros_html = ""
                        for d in jogo:
                            classe = "numero-grande numero-fixo" if d in numeros_fixos else "numero-grande"
                            numeros_html += f'<span class="{classe}">{d:02d}</span>'
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
            if df_todas['Frequencia'].sum() > 0:
                st.bar_chart(df_todas.set_index('Dezena'))
            else:
                st.info("Sem dados de frequencia para exibir.")

        with col2:
            st.markdown("#### Atraso por Dezena")
            atrasos = analisador.calcular_atrasos()
            todos_atrasos = [(d, atrasos.get(d, 0)) for d in range(1, 61)]
            df_atrasos = pd.DataFrame(todos_atrasos, columns=['Dezena', 'Atraso'])
            if df_atrasos['Atraso'].sum() > 0:
                st.bar_chart(df_atrasos.set_index('Dezena'))
            else:
                st.info("Sem dados de atraso para exibir.")

    with tab3:
        st.subheader("🔒 Fechamento / Desdobramento")

        st.markdown("""
        O **fechamento** permite jogar mais numeros distribuidos em varios jogos,
        garantindo uma premiacao minima se acertar uma quantidade de numeros.
        """)

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### Configurar Fechamento")

            todos_nums = [f"{i:02d}" for i in range(1, 61)]
            dezenas_fechamento_sel = st.multiselect(
                "Selecione as dezenas (7 a 15 numeros):",
                options=todos_nums,
                default=[],
                help="Selecione entre 7 e 15 numeros para o fechamento"
            )

            garantia = st.selectbox(
                "Garantia minima:",
                options=[4, 5, 6],
                format_func=lambda x: {4: "Quadra (4 acertos)", 5: "Quina (5 acertos)", 6: "Sena (6 acertos)"}[x]
            )

        with col2:
            st.markdown("### Tabela de Referencia")
            st.markdown("""
            | Dezenas | Jogos (Quadra) | Jogos (Quina) | Jogos (Sena) |
            |---------|----------------|---------------|--------------|
            | 7       | 4              | 6             | 7            |
            | 8       | 6              | 12            | 28           |
            | 9       | 9              | 30            | 84           |
            | 10      | 14             | 50            | 210          |
            | 11      | 20             | 77            | 462          |
            | 12      | 27             | 132           | 924          |
            """)

        if dezenas_fechamento_sel:
            dezenas_list = [int(n) for n in dezenas_fechamento_sel]

            if len(dezenas_list) < 7:
                st.warning("Minimo de 7 numeros para fechamento!")
            elif len(dezenas_list) > 15:
                st.warning("Maximo de 15 numeros para fechamento (para evitar muitos jogos)!")
            else:
                st.info(f"📊 {len(dezenas_list)} numeros selecionados: {', '.join(f'{d:02d}' for d in sorted(dezenas_list))}")

                if st.button("🔒 Gerar Fechamento", type="primary"):
                    with st.spinner("Gerando fechamento..."):
                        jogos_fechamento = GeradorFechamento.gerar_fechamento(dezenas_list, garantia)

                    st.success(f"✅ Fechamento gerado com {len(jogos_fechamento)} jogos!")
                    st.caption(f"Garantia: {'Quadra' if garantia == 4 else 'Quina' if garantia == 5 else 'Sena'}")

                    # Exportar
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        excel_fech = gerar_excel_jogos(jogos_fechamento, [f'Fechamento {garantia}'])
                        st.download_button(
                            "📥 Baixar Fechamento (Excel)",
                            data=excel_fech,
                            file_name=f"fechamento_{len(dezenas_list)}dez_{garantia}garantia.xlsx"
                        )

                    # Exibir jogos
                    for i, jogo in enumerate(jogos_fechamento, 1):
                        numeros_html = "".join([f'<span class="numero-grande">{d:02d}</span>' for d in jogo])
                        st.markdown(f"**Jogo {i:02d}:** {numeros_html}", unsafe_allow_html=True)

    with tab4:
        st.subheader("🎯 Simulador de Jogos")

        st.markdown("""
        Teste seus jogos nos **sorteios anteriores** para ver quantas vezes
        teria acertado quadra, quina ou sena!
        """)

        col1, col2 = st.columns([1, 1])

        with col1:
            todos_nums_sim = [f"{i:02d}" for i in range(1, 61)]
            dezenas_simular_sel = st.multiselect(
                "Selecione 6 numeros para simular:",
                options=todos_nums_sim,
                default=[],
                help="Selecione exatamente 6 numeros",
                max_selections=6
            )

            qtd_concursos = st.slider("Quantidade de concursos para simular:", 50, 500, 100)

        if dezenas_simular_sel:
            dezenas_sim = sorted([int(n) for n in dezenas_simular_sel])

            if len(dezenas_sim) != 6:
                st.warning(f"Selecione exatamente 6 numeros! (Selecionados: {len(dezenas_sim)})")
            else:
                st.info(f"Simulando: {' - '.join(f'{d:02d}' for d in dezenas_sim)}")

                if st.button("🎯 Simular", type="primary"):
                    resultados = analisador_completo.simular_jogo(dezenas_sim, qtd_concursos)

                    with col2:
                        st.markdown("### Resultados da Simulacao")

                        # Metricas
                        col_m1, col_m2, col_m3 = st.columns(3)
                        col_m1.metric("🏆 Senas", resultados['acertos'][6], delta=None)
                        col_m2.metric("⭐ Quinas", resultados['acertos'][5], delta=None)
                        col_m3.metric("🎯 Quadras", resultados['acertos'][4], delta=None)

                        # Distribuicao completa
                        st.markdown("#### Distribuicao de Acertos")
                        df_acertos = pd.DataFrame([
                            {'Acertos': f'{i} acertos', 'Quantidade': resultados['acertos'][i]}
                            for i in range(7)
                        ])
                        if df_acertos['Quantidade'].sum() > 0:
                            st.bar_chart(df_acertos.set_index('Acertos'))
                        else:
                            st.info("Nenhum dado para exibir.")

                        # Detalhes de premios
                        if resultados['detalhes']:
                            st.markdown("#### Premiacoes (4+ acertos)")
                            for det in resultados['detalhes']:
                                classe = 'premio-sena' if det['acertos'] == 6 else 'premio-quina' if det['acertos'] == 5 else 'premio-quadra'
                                st.markdown(
                                    f"<span class='{classe}'>Concurso {det['concurso']}</span> ({det['data']}): "
                                    f"**{det['acertos']} acertos** - Sorteados: {det['dezenas_sorteadas']}",
                                    unsafe_allow_html=True
                                )
                        else:
                            st.info("Nenhuma premiacao (4+) nos concursos simulados.")

    with tab5:
        st.subheader("💾 Meus Jogos Salvos")

        jogos_salvos = carregar_jogos_salvos()

        if not jogos_salvos:
            st.info("Nenhum jogo salvo ainda. Gere jogos na aba 'Gerar Jogos' e clique em 'Salvar'.")
        else:
            st.success(f"📋 {len(jogos_salvos)} jogos salvos")

            # Opcoes
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🗑️ Limpar Todos"):
                    salvar_jogos([])
                    st.rerun()

            with col2:
                excel_salvos = gerar_excel_jogos([j.dezenas for j in jogos_salvos], ['Salvos'])
                st.download_button(
                    "📥 Exportar Todos (Excel)",
                    data=excel_salvos,
                    file_name="meus_jogos_megasena.xlsx"
                )

            st.markdown("---")

            for jogo in jogos_salvos:
                with st.container():
                    col_j1, col_j2, col_j3 = st.columns([3, 1, 1])

                    with col_j1:
                        numeros_html = "".join([f'<span class="numero-grande">{d:02d}</span>' for d in jogo.dezenas])
                        st.markdown(f"**Jogo #{jogo.id}** - {numeros_html}", unsafe_allow_html=True)
                        st.caption(f"Criado em: {jogo.data_criacao[:10]} | Algoritmos: {', '.join(jogo.algoritmos)}")

                    with col_j2:
                        if jogo.acertos:
                            melhor = max(jogo.acertos.values()) if jogo.acertos else 0
                            st.metric("Melhor", f"{melhor} acertos")

                    with col_j3:
                        if st.button("🗑️", key=f"del_{jogo.id}"):
                            jogos_salvos = [j for j in jogos_salvos if j.id != jogo.id]
                            salvar_jogos(jogos_salvos)
                            st.rerun()

                    st.divider()

    with tab6:
        st.subheader("✅ Conferir Jogos")

        st.markdown("Confira seus jogos contra os resultados dos sorteios.")

        # Selecionar concurso
        concursos_recentes = sorted(concursos, key=lambda c: c.numero, reverse=True)[:20]
        opcoes_concurso = {f"Concurso {c.numero} ({c.data}) - {'-'.join(f'{d:02d}' for d in c.dezenas)}": c
                          for c in concursos_recentes}

        concurso_selecionado = st.selectbox("Selecione o concurso:", list(opcoes_concurso.keys()))
        concurso_conf = opcoes_concurso[concurso_selecionado]

        st.info(f"🎱 Numeros sorteados: **{' - '.join(f'{d:02d}' for d in concurso_conf.dezenas)}**")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Conferir Jogo Manual")
            todos_nums_conf = [f"{i:02d}" for i in range(1, 61)]
            jogo_conferir_sel = st.multiselect(
                "Selecione 6 numeros para conferir:",
                options=todos_nums_conf,
                default=[],
                help="Selecione exatamente 6 numeros",
                max_selections=6,
                key="conferir_manual"
            )

            if jogo_conferir_sel:
                dezenas_conf = sorted([int(n) for n in jogo_conferir_sel])

                if len(dezenas_conf) == 6:
                    acertos = analisador_completo.conferir_jogo(dezenas_conf, concurso_conf)
                    acertados = set(dezenas_conf) & concurso_conf.dezenas_set

                    # Exibir com destaque nos acertos
                    numeros_html = ""
                    for d in dezenas_conf:
                        classe = "numero-grande numero-acerto" if d in acertados else "numero-grande"
                        numeros_html += f'<span class="{classe}">{d:02d}</span>'

                    st.markdown(numeros_html, unsafe_allow_html=True)

                    if acertos == 6:
                        st.balloons()
                        st.success(f"🏆 SENA! {acertos} acertos!")
                    elif acertos == 5:
                        st.success(f"⭐ QUINA! {acertos} acertos!")
                    elif acertos == 4:
                        st.success(f"🎯 QUADRA! {acertos} acertos!")
                    else:
                        st.info(f"📊 {acertos} acertos")
                else:
                    st.warning(f"Selecione exatamente 6 numeros! (Selecionados: {len(dezenas_conf)})")

        with col2:
            st.markdown("### Conferir Jogos Salvos")

            jogos_salvos = carregar_jogos_salvos()

            if jogos_salvos:
                if st.button("✅ Conferir Todos", type="primary"):
                    for jogo in jogos_salvos:
                        acertos = analisador_completo.conferir_jogo(jogo.dezenas, concurso_conf)
                        if jogo.acertos is None:
                            jogo.acertos = {}
                        jogo.acertos[concurso_conf.numero] = acertos
                        jogo.conferido = True

                    salvar_jogos(jogos_salvos)
                    st.success("Todos os jogos conferidos!")

                    # Mostrar resultados
                    for jogo in jogos_salvos:
                        acertos = jogo.acertos.get(concurso_conf.numero, 0)
                        acertados = set(jogo.dezenas) & concurso_conf.dezenas_set

                        numeros_html = ""
                        for d in jogo.dezenas:
                            classe = "numero-grande numero-acerto" if d in acertados else "numero-grande"
                            numeros_html += f'<span class="{classe}">{d:02d}</span>'

                        premio = "🏆 SENA!" if acertos == 6 else "⭐ QUINA!" if acertos == 5 else "🎯 QUADRA!" if acertos == 4 else ""
                        st.markdown(f"**Jogo #{jogo.id}:** {numeros_html} - **{acertos} acertos** {premio}", unsafe_allow_html=True)
            else:
                st.info("Nenhum jogo salvo para conferir.")

    # Rodape com informacoes
    st.markdown("---")
    st.caption(f"📊 Base: {len(concursos)} concursos | Ultimo: {concursos[-1].numero} ({concursos[-1].data}) | Atualizacao automatica ativada")


if __name__ == "__main__":
    main()
