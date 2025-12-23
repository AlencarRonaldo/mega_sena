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
import time
import os
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import requests

import pandas as pd
import streamlit as st

# Importar cliente Supabase
from supabase_client import (
    buscar_todos_concursos,
    buscar_concursos_ultimo_ano,
    buscar_ultimo_concurso as buscar_ultimo_concurso_db,
    buscar_jogos_salvos as buscar_jogos_salvos_db,
    salvar_jogo as salvar_jogo_db,
    salvar_jogos_em_lote,
    deletar_jogo as deletar_jogo_db,
    deletar_todos_jogos,
    conferir_jogo_no_banco,
    sincronizar_com_caixa,
    verificar_atualizacao,
    contar_concursos,
)

# Importar estilos premium
from styles import (
    get_premium_styles,
    criar_bola_html,
    criar_bolas_jogo,
    criar_header_premium,
    criar_kpi_card,
    criar_volante_premium,
    criar_game_card,
)

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

    # ============== ANÁLISES ESTATÍSTICAS AVANÇADAS ==============

    def probabilidades_reais(self) -> Dict[str, Dict]:
        """Calcula probabilidades reais da Mega-Sena."""
        from math import comb

        total_combinacoes = comb(60, 6)  # 50.063.860

        return {
            'sena': {
                'chance': 1,
                'total': total_combinacoes,
                'probabilidade': 1 / total_combinacoes,
                'percentual': (1 / total_combinacoes) * 100,
                'texto': f"1 em {total_combinacoes:,}".replace(',', '.')
            },
            'quina': {
                'chance': comb(6, 5) * comb(54, 1),
                'total': total_combinacoes,
                'probabilidade': (comb(6, 5) * comb(54, 1)) / total_combinacoes,
                'percentual': ((comb(6, 5) * comb(54, 1)) / total_combinacoes) * 100,
                'texto': f"1 em {total_combinacoes // (comb(6, 5) * comb(54, 1)):,}".replace(',', '.')
            },
            'quadra': {
                'chance': comb(6, 4) * comb(54, 2),
                'total': total_combinacoes,
                'probabilidade': (comb(6, 4) * comb(54, 2)) / total_combinacoes,
                'percentual': ((comb(6, 4) * comb(54, 2)) / total_combinacoes) * 100,
                'texto': f"1 em {total_combinacoes // (comb(6, 4) * comb(54, 2)):,}".replace(',', '.')
            }
        }

    def analise_soma(self) -> Dict[str, any]:
        """Analisa a soma dos números sorteados."""
        somas = [sum(c.dezenas) for c in self.concursos]

        if not somas:
            return {'media': 0, 'min': 0, 'max': 0, 'faixa_ideal': (0, 0)}

        media = sum(somas) / len(somas)
        desvio = (sum((s - media) ** 2 for s in somas) / len(somas)) ** 0.5

        # Faixa ideal = média ± 1 desvio padrão
        faixa_min = int(media - desvio)
        faixa_max = int(media + desvio)

        # Distribuição por faixas
        faixas = {'< 150': 0, '150-175': 0, '176-200': 0, '201-225': 0, '> 225': 0}
        for s in somas:
            if s < 150:
                faixas['< 150'] += 1
            elif s <= 175:
                faixas['150-175'] += 1
            elif s <= 200:
                faixas['176-200'] += 1
            elif s <= 225:
                faixas['201-225'] += 1
            else:
                faixas['> 225'] += 1

        return {
            'media': round(media, 1),
            'min': min(somas),
            'max': max(somas),
            'desvio': round(desvio, 1),
            'faixa_ideal': (faixa_min, faixa_max),
            'distribuicao': faixas,
            'historico': somas[-50:]  # Últimas 50
        }

    def analise_padroes(self) -> Dict[str, any]:
        """Analisa padrões nos sorteios."""
        consecutivos = 0
        mesmo_final = 0
        repetidos_anterior = 0

        for i, c in enumerate(self.concursos):
            dezenas = sorted(c.dezenas)

            # Consecutivos
            for j in range(len(dezenas) - 1):
                if dezenas[j + 1] - dezenas[j] == 1:
                    consecutivos += 1

            # Mesmo final
            finais = [d % 10 for d in dezenas]
            if len(finais) != len(set(finais)):
                mesmo_final += 1

            # Repetidos do anterior
            if i > 0:
                anterior = set(self.concursos[i - 1].dezenas)
                atual = set(dezenas)
                if anterior & atual:
                    repetidos_anterior += 1

        total = len(self.concursos)
        return {
            'consecutivos': {
                'total': consecutivos,
                'media_por_sorteio': round(consecutivos / total, 2) if total > 0 else 0,
                'percentual': round((consecutivos / (total * 5)) * 100, 1) if total > 0 else 0
            },
            'mesmo_final': {
                'total': mesmo_final,
                'percentual': round((mesmo_final / total) * 100, 1) if total > 0 else 0
            },
            'repetidos': {
                'total': repetidos_anterior,
                'percentual': round((repetidos_anterior / total) * 100, 1) if total > 0 else 0
            }
        }

    def ciclos_atraso(self) -> Dict[int, Dict]:
        """Calcula ciclos médios de atraso para cada número."""
        aparicoes = {d: [] for d in range(1, 61)}

        for i, c in enumerate(self.concursos):
            for d in c.dezenas:
                aparicoes[d].append(i)

        ciclos = {}
        for d in range(1, 61):
            pos = aparicoes[d]
            if len(pos) >= 2:
                intervalos = [pos[i + 1] - pos[i] for i in range(len(pos) - 1)]
                media = sum(intervalos) / len(intervalos)
                ciclos[d] = {
                    'media': round(media, 1),
                    'min': min(intervalos),
                    'max': max(intervalos),
                    'ultimo_atraso': len(self.concursos) - 1 - pos[-1] if pos else 0,
                    'aparicoes': len(pos)
                }
            else:
                ciclos[d] = {
                    'media': 0,
                    'min': 0,
                    'max': 0,
                    'ultimo_atraso': len(self.concursos) if not pos else len(self.concursos) - 1 - pos[-1],
                    'aparicoes': len(pos)
                }

        return ciclos

    def analise_quadrantes(self) -> Dict[str, any]:
        """Analisa distribuição por quadrantes (faixas de 15)."""
        quadrantes = {
            '01-15': 0,
            '16-30': 0,
            '31-45': 0,
            '46-60': 0
        }

        distribuicoes = []

        for c in self.concursos:
            dist = [0, 0, 0, 0]
            for d in c.dezenas:
                if d <= 15:
                    quadrantes['01-15'] += 1
                    dist[0] += 1
                elif d <= 30:
                    quadrantes['16-30'] += 1
                    dist[1] += 1
                elif d <= 45:
                    quadrantes['31-45'] += 1
                    dist[2] += 1
                else:
                    quadrantes['46-60'] += 1
                    dist[3] += 1
            distribuicoes.append(tuple(dist))

        # Padrão mais comum
        from collections import Counter
        padroes = Counter(distribuicoes)
        mais_comum = padroes.most_common(5)

        total = sum(quadrantes.values())
        percentuais = {k: round((v / total) * 100, 1) if total > 0 else 0 for k, v in quadrantes.items()}

        return {
            'contagem': quadrantes,
            'percentuais': percentuais,
            'padroes_comuns': mais_comum,
            'ideal': [1, 2, 2, 1]  # Distribuição ideal sugerida
        }

    def simulacao_monte_carlo(self, num_simulacoes: int = 10000) -> Dict[str, any]:
        """Simula milhares de jogos para calcular ROI esperado."""
        import random

        # Probabilidades reais
        prob = self.probabilidades_reais()

        # Valores dos prêmios (médios)
        premios = {
            6: 50_000_000,  # Sena média
            5: 50_000,       # Quina média
            4: 1_000         # Quadra média
        }

        custo_jogo = 5.00
        ganhos_total = 0
        acertos = {4: 0, 5: 0, 6: 0}

        # Simular
        rng = random.Random()
        for _ in range(num_simulacoes):
            # Gerar jogo aleatório
            jogo = set(rng.sample(range(1, 61), 6))

            # Gerar resultado aleatório
            resultado = set(rng.sample(range(1, 61), 6))

            # Conferir
            hits = len(jogo & resultado)
            if hits >= 4:
                acertos[hits] += 1
                ganhos_total += premios.get(hits, 0)

        custo_total = num_simulacoes * custo_jogo
        roi = ((ganhos_total - custo_total) / custo_total) * 100 if custo_total > 0 else 0

        return {
            'simulacoes': num_simulacoes,
            'custo_total': custo_total,
            'ganhos_total': ganhos_total,
            'lucro': ganhos_total - custo_total,
            'roi': round(roi, 2),
            'acertos': acertos,
            'quadras_esperadas': round(num_simulacoes * prob['quadra']['probabilidade'], 2),
            'quinas_esperadas': round(num_simulacoes * prob['quina']['probabilidade'], 4),
            'senas_esperadas': round(num_simulacoes * prob['sena']['probabilidade'], 8)
        }

    def indice_confianca(self, dezenas: List[int]) -> Dict[str, any]:
        """Calcula índice de confiança para um jogo."""
        score = 0
        fatores = {}

        # 1. Frequência (0-20 pontos)
        freq = self.calcular_frequencias()
        media_freq = sum(freq.values()) / 60 if freq else 0
        freq_jogo = sum(freq.get(d, 0) for d in dezenas) / 6
        fator_freq = min(20, (freq_jogo / media_freq) * 10) if media_freq > 0 else 10
        score += fator_freq
        fatores['frequencia'] = round(fator_freq, 1)

        # 2. Soma ideal (0-20 pontos)
        soma_analise = self.analise_soma()
        soma_jogo = sum(dezenas)
        faixa_min, faixa_max = soma_analise['faixa_ideal']
        if faixa_min <= soma_jogo <= faixa_max:
            fator_soma = 20
        else:
            distancia = min(abs(soma_jogo - faixa_min), abs(soma_jogo - faixa_max))
            fator_soma = max(0, 20 - distancia)
        score += fator_soma
        fatores['soma'] = round(fator_soma, 1)

        # 3. Balanceamento par/ímpar (0-15 pontos)
        pares = sum(1 for d in dezenas if d % 2 == 0)
        if pares == 3:
            fator_bal = 15
        elif pares in [2, 4]:
            fator_bal = 10
        else:
            fator_bal = 5
        score += fator_bal
        fatores['balanceamento'] = fator_bal

        # 4. Distribuição por quadrante (0-15 pontos)
        quads = [0, 0, 0, 0]
        for d in dezenas:
            if d <= 15: quads[0] += 1
            elif d <= 30: quads[1] += 1
            elif d <= 45: quads[2] += 1
            else: quads[3] += 1

        zeros = quads.count(0)
        if zeros == 0:
            fator_dist = 15
        elif zeros == 1:
            fator_dist = 10
        else:
            fator_dist = 5
        score += fator_dist
        fatores['distribuicao'] = fator_dist

        # 5. Consecutivos moderados (0-15 pontos)
        dezenas_ord = sorted(dezenas)
        consecutivos = sum(1 for i in range(5) if dezenas_ord[i + 1] - dezenas_ord[i] == 1)
        if consecutivos in [1, 2]:
            fator_cons = 15
        elif consecutivos == 0:
            fator_cons = 10
        else:
            fator_cons = 5
        score += fator_cons
        fatores['consecutivos'] = fator_cons

        # 6. Atraso dos números (0-15 pontos)
        atrasos = self.calcular_atrasos()
        media_atraso = sum(atrasos.get(d, 0) for d in dezenas) / 6
        if 3 <= media_atraso <= 8:
            fator_atraso = 15
        elif media_atraso < 3:
            fator_atraso = 10
        else:
            fator_atraso = 5
        score += fator_atraso
        fatores['atraso'] = fator_atraso

        # Classificação
        if score >= 85:
            classificacao = "Excelente"
            cor = "#22c55e"
        elif score >= 70:
            classificacao = "Bom"
            cor = "#84cc16"
        elif score >= 55:
            classificacao = "Regular"
            cor = "#eab308"
        else:
            classificacao = "Fraco"
            cor = "#ef4444"

        return {
            'score': round(score, 1),
            'maximo': 100,
            'percentual': round(score, 1),
            'classificacao': classificacao,
            'cor': cor,
            'fatores': fatores
        }


class GeradorJogos:
    def __init__(self, analisador: AnalisadorMegaSena, rng: Optional[random.Random] = None):
        self.analisador = analisador
        # Usar seed combinando tempo + bytes aleatorios do sistema
        seed = int.from_bytes(os.urandom(8), 'big') ^ time.time_ns()
        self.rng = rng or random.Random(seed)

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
                    numeros_fixos: Set[int] = None, numeros_removidos: Set[int] = None) -> Tuple[List[List[int]], List[str]]:
        """
        Gera jogos com lógica inteligente:
        - Se quantidade <= algoritmos selecionados: 1 jogo PURO por algoritmo
        - Se quantidade > algoritmos: primeiro 1 puro de cada, depois mistura

        Retorna: (lista_jogos, lista_algoritmos_usados)
        """
        jogos = []
        algoritmos_usados = []
        jogos_gerados: Set[tuple] = set()

        # Separar algoritmos de score dos outros
        algoritmos_score = [a for a in algoritmos if a in ['frequencia', 'markov', 'coocorrencia', 'atraso']]
        tem_balanceado = 'balanceado' in algoritmos
        tem_uniforme = 'uniforme' in algoritmos

        # FASE 1: Gerar 1 jogo PURO para cada algoritmo selecionado
        for alg in algoritmos_score:
            if len(jogos) >= quantidade:
                break

            pesos_puro = {
                'frequencia': 1.0 if alg == 'frequencia' else 0,
                'markov': 1.0 if alg == 'markov' else 0,
                'coocorrencia': 1.0 if alg == 'coocorrencia' else 0,
                'atraso': 1.0 if alg == 'atraso' else 0,
            }

            tentativas = 0
            while tentativas < 50:
                tentativas += 1
                usar_bal = tem_balanceado or forcar_balanceamento
                jogo = self.gerar_por_scores(pesos_puro, usar_bal, numeros_fixos, numeros_removidos)
                jogo_tuple = tuple(jogo)
                if jogo_tuple not in jogos_gerados:
                    jogos_gerados.add(jogo_tuple)
                    jogos.append(jogo)
                    algoritmos_usados.append(alg.capitalize())
                    break

        # Jogo balanceado puro (se selecionado e ainda tem espaço)
        if tem_balanceado and len(jogos) < quantidade and not algoritmos_score:
            tentativas = 0
            while tentativas < 50:
                tentativas += 1
                jogo = self.gerar_uniforme(numeros_fixos, numeros_removidos)
                if self._verificar_balanceamento(jogo):
                    jogo_tuple = tuple(jogo)
                    if jogo_tuple not in jogos_gerados:
                        jogos_gerados.add(jogo_tuple)
                        jogos.append(jogo)
                        algoritmos_usados.append("Balanceado")
                        break

        # Jogo uniforme puro (se selecionado e ainda tem espaço)
        if tem_uniforme and len(jogos) < quantidade:
            tentativas = 0
            while tentativas < 50:
                tentativas += 1
                jogo = self.gerar_uniforme(numeros_fixos, numeros_removidos)
                jogo_tuple = tuple(jogo)
                if jogo_tuple not in jogos_gerados:
                    jogos_gerados.add(jogo_tuple)
                    jogos.append(jogo)
                    algoritmos_usados.append("Aleatório")
                    break

        # FASE 2: Gerar jogos MISTURADOS (se ainda precisa de mais)
        if len(jogos) < quantidade and algoritmos_score:
            peso_base = 1.0 / len(algoritmos_score)
            pesos_mix = {
                'frequencia': peso_base if 'frequencia' in algoritmos_score else 0,
                'markov': peso_base if 'markov' in algoritmos_score else 0,
                'coocorrencia': peso_base if 'coocorrencia' in algoritmos_score else 0,
                'atraso': peso_base if 'atraso' in algoritmos_score else 0,
            }

            tentativas = 0
            while len(jogos) < quantidade and tentativas < quantidade * 10:
                tentativas += 1
                usar_bal = tem_balanceado or forcar_balanceamento
                jogo = self.gerar_por_scores(pesos_mix, usar_bal, numeros_fixos, numeros_removidos)
                jogo_tuple = tuple(jogo)
                if jogo_tuple not in jogos_gerados:
                    jogos_gerados.add(jogo_tuple)
                    jogos.append(jogo)
                    algoritmos_usados.append("Misto")

        # Fallback: completar com uniforme se ainda faltam jogos
        tentativas = 0
        while len(jogos) < quantidade and tentativas < quantidade * 5:
            tentativas += 1
            jogo = self.gerar_uniforme(numeros_fixos, numeros_removidos)
            jogo_tuple = tuple(jogo)
            if jogo_tuple not in jogos_gerados:
                jogos_gerados.add(jogo_tuple)
                jogos.append(jogo)
                algoritmos_usados.append("Aleatório")

        return jogos, algoritmos_usados


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
    """Carrega jogos salvos do Supabase."""
    try:
        dados = buscar_jogos_salvos_db()
        jogos = []
        for j in dados:
            jogos.append(JogoSalvo(
                id=j.get('id', 0),
                dezenas=j.get('dezenas', []),
                data_criacao=j.get('data_criacao', ''),
                algoritmos=j.get('algoritmos', []),
                conferido=j.get('conferido', False),
                acertos=j.get('acertos', {})
            ))
        return jogos
    except Exception:
        return []


def salvar_jogos(jogos: List[JogoSalvo]):
    """Salva jogos no Supabase (usado apenas para compatibilidade)."""
    # Esta funcao agora é usada apenas para operacoes de lote
    # Jogos individuais sao salvos com salvar_jogo_db()
    pass


def proximo_id_jogo(jogos: List[JogoSalvo]) -> int:
    """Retorna o proximo ID disponivel (nao mais necessario com Supabase)."""
    return 0  # Supabase gera IDs automaticamente


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


@st.cache_data(ttl=300)  # Cache por 5 minutos
def carregar_resultados_supabase(usar_ultimo_ano: bool = True) -> List[Concurso]:
    """Carrega concursos do Supabase."""
    try:
        if usar_ultimo_ano:
            dados = buscar_concursos_ultimo_ano()
        else:
            dados = buscar_todos_concursos()

        concursos = []
        for c in dados:
            try:
                numero = c.get('numero', 0)
                data_str = c.get('data', '')

                if isinstance(data_str, str):
                    data = dt.datetime.strptime(data_str, "%Y-%m-%d").date()
                else:
                    data = data_str

                dezenas = tuple(sorted([
                    c.get('dezena1', 0),
                    c.get('dezena2', 0),
                    c.get('dezena3', 0),
                    c.get('dezena4', 0),
                    c.get('dezena5', 0),
                    c.get('dezena6', 0),
                ]))

                if len(dezenas) == 6 and all(DEZENA_MIN <= d <= DEZENA_MAX for d in dezenas):
                    concursos.append(Concurso(numero=numero, data=data, dezenas=dezenas))
            except Exception:
                continue

        return concursos
    except Exception as e:
        st.error(f"Erro ao carregar do Supabase: {e}")
        return []


@st.cache_data
def carregar_resultados_excel(caminho: str) -> List[Concurso]:
    """Fallback: Carrega concursos do Excel."""
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
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Inicializar session state
    if 'jogos_gerados' not in st.session_state:
        st.session_state.jogos_gerados = []
    if 'algoritmos_usados' not in st.session_state:
        st.session_state.algoritmos_usados = []
    if 'algoritmos_por_jogo' not in st.session_state:
        st.session_state.algoritmos_por_jogo = []

    # Aplicar CSS Premium
    st.markdown(get_premium_styles(), unsafe_allow_html=True)

    # Header com texto verde
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem 0; margin-bottom: 1rem;">
        <h1 style="color: #22c55e; font-size: 2.2rem; font-weight: 700; margin: 0;">
            🍀 Gerador Inteligente - Mega-Sena
        </h1>
        <p style="color: #22c55e; font-size: 1rem; margin-top: 0.5rem; opacity: 0.8;">
            Algoritmos estatísticos avançados para maximizar suas chances
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Carregar dados do Supabase
    try:
        concursos = carregar_resultados_supabase(usar_ultimo_ano=True)
        if not concursos:
            st.warning("Nenhum concurso encontrado no banco. Sincronizando...")
            with st.spinner("🔄 Sincronizando com a Caixa..."):
                novos, _, msg = sincronizar_com_caixa(dias_atras=365)
            if novos > 0:
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Não foi possível carregar os dados.")
                return

        analisador_completo = AnalisadorMegaSena(concursos)

        # Verificar atualizações automaticamente
        if 'atualizacao_verificada' not in st.session_state:
            st.session_state.atualizacao_verificada = False

        if not st.session_state.atualizacao_verificada:
            ha_novos, ultimo_local, ultimo_caixa = verificar_atualizacao()
            if ha_novos:
                with st.spinner("🔄 Atualizando resultados..."):
                    novos, _, msg = sincronizar_com_caixa(dias_atras=30)
                if novos > 0:
                    st.cache_data.clear()
                    st.session_state.atualizacao_verificada = True
                    st.rerun()
            st.session_state.atualizacao_verificada = True

    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {e}")
        st.info("Verifique as configurações no arquivo .env")
        return

    # ===== CONTROLES INLINE (sem sidebar) =====
    # Filtrar dados por período padrão
    analisador = analisador_completo.filtrar_por_anos(3)

    # Variáveis de configuração com valores padrão
    anos = 3
    qtd_jogos = 6
    usar_frequencia = True
    usar_markov = True
    usar_balanceado = True
    usar_atraso = False
    usar_coocorrencia = False
    usar_uniforme = False
    numeros_fixos_sel = []
    numeros_removidos_sel = []
    todos_numeros = list(range(1, 61))

    # Painel de configurações expansível
    with st.expander("⚙️ Escolha as configurações", expanded=False):
        col_cfg1, col_cfg2, col_cfg3 = st.columns(3)

        with col_cfg1:
            st.markdown("**📅 Período**")
            anos = st.slider("Anos", 1, 10, 3, key="anos_slider")
            analisador = analisador_completo.filtrar_por_anos(anos)
            st.caption(f"📊 {len(analisador.concursos)} concursos")

        with col_cfg2:
            st.markdown("**🎯 Quantidade**")
            qtd_jogos = st.number_input("Jogos", 1, 50, 6, key="qtd_input")
            custo = qtd_jogos * 5.00
            st.caption(f"💰 R$ {custo:.2f}")

        with col_cfg3:
            st.markdown("**🧠 Algoritmos**")
            usar_frequencia = st.checkbox("Frequência", True, key="chk_freq")
            usar_markov = st.checkbox("Markov", True, key="chk_markov")
            usar_balanceado = st.checkbox("Balanceado", True, key="chk_bal")

        col_cfg4, col_cfg5, col_cfg6 = st.columns(3)

        with col_cfg4:
            st.markdown("**🧠 Mais Algoritmos**")
            usar_atraso = st.checkbox("Atrasados", False, key="chk_atraso")
            usar_coocorrencia = st.checkbox("Coocorrência", False, key="chk_cooc")
            usar_uniforme = st.checkbox("Aleatório", False, key="chk_unif")

        with col_cfg5:
            st.markdown("**🔒 Números Fixos**")
            numeros_fixos_sel = st.multiselect(
                "Fixos",
                todos_numeros,
                default=[],
                max_selections=5,
                format_func=lambda x: f"{x:02d}",
                key="fixos_sel",
                label_visibility="collapsed"
            )

        with col_cfg6:
            st.markdown("**🚫 Excluídos**")
            numeros_disponiveis = [n for n in todos_numeros if n not in numeros_fixos_sel]
            numeros_removidos_sel = st.multiselect(
                "Excluídos",
                numeros_disponiveis,
                default=[],
                format_func=lambda x: f"{x:02d}",
                key="removidos_sel",
                label_visibility="collapsed"
            )

    # Converter selecoes para sets de inteiros
    numeros_fixos = set(numeros_fixos_sel)
    numeros_removidos = set(numeros_removidos_sel)

    # Tabs principais
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🎰 Gerar Jogos",
        "📊 Estatísticas",
        "🎲 Probabilidades",
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
                if usar_balanceado:
                    algoritmos.append('balanceado')
                if usar_uniforme:
                    algoritmos.append('uniforme')

                if not algoritmos:
                    st.warning("Selecione pelo menos um algoritmo!")
                else:
                    gerador = GeradorJogos(analisador)
                    jogos, algoritmos_por_jogo = gerador.gerar_jogos(
                        qtd_jogos, algoritmos, usar_balanceado, numeros_fixos, numeros_removidos
                    )

                    st.session_state.jogos_gerados = jogos
                    st.session_state.algoritmos_por_jogo = algoritmos_por_jogo
                    st.session_state.algoritmos_usados = algoritmos

                    st.success(f"✅ {len(jogos)} jogos gerados!")

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
                        # Salvar no Supabase
                        jogos_para_salvar = [
                            {"dezenas": jogo, "algoritmos": st.session_state.algoritmos_usados}
                            for jogo in st.session_state.jogos_gerados
                        ]
                        sucesso, falhas = salvar_jogos_em_lote(jogos_para_salvar)
                        if sucesso > 0:
                            st.success(f"✅ {sucesso} jogos salvos no banco!")
                        else:
                            st.error("Erro ao salvar jogos.")

                st.markdown("---")

                # Obter lista de algoritmos por jogo
                algoritmos_por_jogo = st.session_state.get('algoritmos_por_jogo', [])

                # CSS para bolinhas verdes
                st.markdown("""
                <style>
                .bola-verde {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 42px;
                    height: 42px;
                    background: linear-gradient(145deg, #22c55e, #16a34a);
                    color: white;
                    border-radius: 50%;
                    font-weight: 700;
                    font-size: 1rem;
                    margin: 3px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3), inset 0 2px 4px rgba(255,255,255,0.3);
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                }
                .jogo-container {
                    background: rgba(30, 41, 59, 0.6);
                    border-radius: 12px;
                    padding: 1rem;
                    margin-bottom: 0.75rem;
                    border: 1px solid rgba(34, 197, 94, 0.2);
                }
                .jogo-header {
                    color: #94a3b8;
                    font-size: 0.85rem;
                    margin-bottom: 0.5rem;
                }
                .jogo-header strong {
                    color: #22c55e;
                }
                .bolas-row {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 6px;
                }
                </style>
                """, unsafe_allow_html=True)

                # Exibição com bolinhas verdes
                for i, jogo in enumerate(st.session_state.jogos_gerados, 1):
                    alg_usado = algoritmos_por_jogo[i-1] if i <= len(algoritmos_por_jogo) else "Misto"

                    bolas_html = "".join(f'<span class="bola-verde">{n:02d}</span>' for n in jogo)

                    st.markdown(f"""
                    <div class="jogo-container">
                        <div class="jogo-header">
                            <strong>Jogo {i:02d}</strong> • {alg_usado}
                        </div>
                        <div class="bolas-row">
                            {bolas_html}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="ultimo-sorteio">
                <h3>🎱 Último Sorteio</h3>
            </div>
            """, unsafe_allow_html=True)

            if analisador.ultimo_concurso:
                st.markdown(f"""
                <div style="margin-bottom: 1rem;">
                    <div style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 0.5rem;">
                        Concurso <span style="color: #10b981; font-weight: 600;">{analisador.ultimo_concurso.numero}</span>
                        • {analisador.ultimo_concurso.data.strftime('%d/%m/%Y')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Mostrar bolas 3D do último sorteio
                st.markdown(
                    criar_bolas_jogo(list(analisador.ultimo_concurso.dezenas)),
                    unsafe_allow_html=True
                )

                # KPI Cards
                st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
                kpi_col1, kpi_col2 = st.columns(2)
                with kpi_col1:
                    st.markdown(criar_kpi_card(str(len(concursos)), "Concursos Analisados", "📊"), unsafe_allow_html=True)
                with kpi_col2:
                    pares_ult = sum(1 for d in analisador.ultimo_concurso.dezenas if d % 2 == 0)
                    st.markdown(criar_kpi_card(f"{pares_ult}/6", "Pares no Último", "⚖️"), unsafe_allow_html=True)

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
        st.subheader("🎲 Probabilidades e Analise Avancada")

        st.markdown("""
        Analise estatistica avancada baseada em **probabilidades reais** e **simulacoes**.
        """)

        # Probabilidades Reais
        st.markdown("### 📊 Probabilidades Reais da Mega-Sena")
        probs = analisador_completo.probabilidades_reais()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "🎯 Sena (6 acertos)",
                probs['sena']['texto'],
                help=f"Probabilidade: {probs['sena']['percentual']:.10f}%"
            )
        with col2:
            st.metric(
                "🎯 Quina (5 acertos)",
                probs['quina']['texto'],
                help=f"Probabilidade: {probs['quina']['percentual']:.6f}%"
            )
        with col3:
            st.metric(
                "🎯 Quadra (4 acertos)",
                probs['quadra']['texto'],
                help=f"Probabilidade: {probs['quadra']['percentual']:.4f}%"
            )

        st.divider()

        # Analise de Soma
        st.markdown("### 📈 Analise de Soma dos Numeros")
        soma_analise = analisador_completo.analise_soma()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Media", f"{soma_analise['media']:.1f}")
        with col2:
            st.metric("Minima", str(soma_analise['min']))
        with col3:
            st.metric("Maxima", str(soma_analise['max']))
        with col4:
            st.metric("Desvio Padrao", f"{soma_analise['desvio']:.1f}")

        faixa_min, faixa_max = soma_analise['faixa_ideal']
        st.info(f"💡 **Faixa ideal de soma**: {faixa_min} a {faixa_max} (media ± 1 desvio padrao)")

        # Grafico de distribuicao de soma
        if soma_analise['distribuicao']:
            df_soma = pd.DataFrame(list(soma_analise['distribuicao'].items()), columns=['Faixa', 'Frequencia'])
            st.bar_chart(df_soma.set_index('Faixa'))

        st.divider()

        # Analise de Padroes
        st.markdown("### 🔍 Padroes nos Sorteios")
        padroes = analisador_completo.analise_padroes()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Numeros Consecutivos**")
            st.write(f"Total de pares: {padroes['consecutivos']['total']}")
            st.write(f"Media por sorteio: {padroes['consecutivos']['media_por_sorteio']:.2f}")
            st.write(f"Percentual: {padroes['consecutivos']['percentual']:.1f}%")

        with col2:
            st.markdown("**Mesmo Final**")
            st.write(f"Sorteios com mesmo final: {padroes['mesmo_final']['total']}")
            st.write(f"Percentual: {padroes['mesmo_final']['percentual']:.1f}%")

        with col3:
            st.markdown("**Numeros Repetidos**")
            st.write(f"Sorteios com repetidos: {padroes['repetidos']['total']}")
            st.write(f"Percentual: {padroes['repetidos']['percentual']:.1f}%")

        st.divider()

        # Analise de Quadrantes
        st.markdown("### 🎯 Distribuicao por Quadrantes")
        quadrantes = analisador_completo.analise_quadrantes()

        st.markdown("""
        Os numeros sao divididos em 4 faixas (quadrantes):
        - **Q1**: 01-15 | **Q2**: 16-30 | **Q3**: 31-45 | **Q4**: 46-60
        """)

        col1, col2, col3, col4 = st.columns(4)
        cols = [col1, col2, col3, col4]
        for i, (q_nome, q_total) in enumerate(quadrantes['contagem'].items()):
            with cols[i]:
                percentual = quadrantes['percentuais'].get(q_nome, 0)
                st.metric(
                    q_nome,
                    f"{q_total} nums",
                    help=f"Percentual: {percentual:.1f}%"
                )

        ideal = quadrantes['ideal']
        st.info(f"💡 **Distribuicao ideal sugerida**: {ideal[0]}-{ideal[1]}-{ideal[2]}-{ideal[3]} (Q1-Q2-Q3-Q4)")

        st.divider()

        # Ciclos de Atraso
        st.markdown("### ⏱️ Ciclos de Atraso")
        ciclos = analisador_completo.ciclos_atraso()

        # Top 10 numeros mais atrasados
        top_atrasados = sorted(ciclos.items(), key=lambda x: x[1]['ultimo_atraso'], reverse=True)[:10]

        st.markdown("**Top 10 Numeros Mais Atrasados:**")
        for num, dados in top_atrasados:
            ciclo_medio = dados['media'] if dados['media'] > 0 else 1
            progresso = min(dados['ultimo_atraso'] / ciclo_medio, 2.0)
            cor = "🔴" if progresso > 1.5 else "🟡" if progresso > 1.0 else "🟢"
            st.write(f"{cor} **{num:02d}**: {dados['ultimo_atraso']} sorteios (ciclo medio: {dados['media']:.1f})")

        st.divider()

        # Simulacao Monte Carlo
        st.markdown("### 🎰 Simulacao Monte Carlo")
        st.markdown("Simulacao de milhares de jogos para calcular o retorno esperado.")

        num_simulacoes = st.slider("Numero de simulacoes:", 1000, 50000, 10000, step=1000)

        if st.button("🎲 Executar Simulacao", key="btn_monte_carlo"):
            with st.spinner("Executando simulacao..."):
                resultado_mc = analisador_completo.simulacao_monte_carlo(num_simulacoes)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total de Jogos", f"{resultado_mc['simulacoes']:,}")
                st.metric("Investimento", f"R$ {resultado_mc['custo_total']:,.2f}")
                st.metric("Premios Ganhos", f"R$ {resultado_mc['ganhos_total']:,.2f}")

            with col2:
                st.metric("ROI", f"{resultado_mc['roi']:.2f}%")
                st.metric("Quadras", str(resultado_mc['acertos'].get(4, 0)))
                st.metric("Quinas", str(resultado_mc['acertos'].get(5, 0)))
                st.metric("Senas", str(resultado_mc['acertos'].get(6, 0)))

            if resultado_mc['roi'] < 0:
                st.warning(f"⚠️ **Conclusao**: Prejuizo de {abs(resultado_mc['roi']):.2f}%. Loteria e um jogo de azar!")
            else:
                st.success(f"✅ **Conclusao**: Lucro de {resultado_mc['roi']:.2f}% (sorte na simulacao)")

        st.divider()

        # Indice de Confianca para um jogo
        st.markdown("### 📋 Indice de Confianca de um Jogo")
        st.markdown("Avalie a qualidade estatistica de um jogo especifico.")

        todos_nums_ic = [f"{i:02d}" for i in range(1, 61)]
        jogo_ic = st.multiselect(
            "Selecione 6 numeros para avaliar:",
            options=todos_nums_ic,
            default=[],
            max_selections=6,
            key="indice_confianca_input"
        )

        if len(jogo_ic) == 6:
            dezenas_ic = sorted([int(n) for n in jogo_ic])
            ic = analisador_completo.indice_confianca(dezenas_ic)

            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: {ic['cor']}22; border-radius: 10px; border: 2px solid {ic['cor']};">
                <h2 style="color: {ic['cor']}; margin: 0;">{ic['score']}/100</h2>
                <p style="color: {ic['cor']}; margin: 0.5rem 0 0 0;">{ic['classificacao']}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**Fatores analisados:**")
            for fator, valor in ic['fatores'].items():
                st.write(f"- **{fator.replace('_', ' ').title()}**: {valor:.1f}/100")

    with tab4:
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

    with tab5:
        st.subheader("🎯 Simulador de Jogos")

        st.markdown("""
        Teste seus jogos nos **sorteios anteriores** para ver quantas vezes
        teria acertado quadra, quina ou sena!
        """)

        # Seleção de números
        col_sim1, col_sim2 = st.columns([2, 1])

        with col_sim1:
            todos_nums_sim = list(range(1, 61))
            dezenas_simular_sel = st.multiselect(
                "Selecione 6 números para simular:",
                options=todos_nums_sim,
                default=[],
                format_func=lambda x: f"{x:02d}",
                help="Selecione exatamente 6 números",
                max_selections=6
            )

        with col_sim2:
            qtd_concursos = st.slider("Concursos:", 50, 500, 100)

        # Validação e botão
        if len(dezenas_simular_sel) == 6:
            dezenas_sim = sorted(dezenas_simular_sel)
            st.info(f"🎲 Jogo: {' - '.join(f'{d:02d}' for d in dezenas_sim)}")

            if st.button("🎯 Simular nos últimos concursos", type="primary"):
                with st.spinner("Simulando..."):
                    resultados = analisador_completo.simular_jogo(dezenas_sim, qtd_concursos)

                st.markdown("---")
                st.markdown("### 📊 Resultados da Simulação")
                st.caption(f"Analisados {resultados['total_concursos']} concursos")

                # Métricas principais
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("🏆 Senas", resultados['acertos'][6])
                col_m2.metric("⭐ Quinas", resultados['acertos'][5])
                col_m3.metric("🎯 Quadras", resultados['acertos'][4])

                # Distribuição completa
                st.markdown("#### Distribuição de Acertos")
                df_acertos = pd.DataFrame([
                    {'Acertos': f'{i}', 'Quantidade': resultados['acertos'][i]}
                    for i in range(7)
                ])
                st.bar_chart(df_acertos.set_index('Acertos'))

                # Detalhes de prêmios
                if resultados['detalhes']:
                    st.markdown("#### 🏅 Premiações (4+ acertos)")
                    for det in resultados['detalhes']:
                        emoji = "🏆" if det['acertos'] == 6 else "⭐" if det['acertos'] == 5 else "🎯"
                        dezenas_str = " - ".join(f"{d:02d}" for d in det['dezenas_sorteadas'])
                        st.success(f"{emoji} Concurso {det['concurso']} ({det['data']}): **{det['acertos']} acertos** | Sorteio: {dezenas_str}")
                else:
                    st.info("Nenhuma premiação (4+) nos concursos simulados.")

        elif len(dezenas_simular_sel) > 0:
            st.warning(f"Selecione exatamente 6 números! (Selecionados: {len(dezenas_simular_sel)})")

    with tab6:
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
                    deletar_todos_jogos()
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
                            deletar_jogo_db(jogo.id)
                            st.rerun()

                    st.divider()

    with tab7:
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
                        conferir_jogo_no_banco(jogo.id, concurso_conf.numero, acertos)
                        jogo.acertos = jogo.acertos or {}
                        jogo.acertos[concurso_conf.numero] = acertos

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
