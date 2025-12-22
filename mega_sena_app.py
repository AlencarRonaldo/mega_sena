"""
Gerador Inteligente de Jogos da Mega-Sena
Permite combinar múltiplos algoritmos para gerar jogos otimizados.

Algoritmos disponíveis:
1. Frequência - Números mais sorteados no período
2. Markov - Números que tendem a seguir os últimos sorteados
3. Co-ocorrência - Pares de números que saem juntos frequentemente
4. Atrasados - Números que não saem há muito tempo
5. Balanceado - Equilíbrio par/ímpar e distribuição por faixas
6. Uniforme - Totalmente aleatório (controle)
"""

from __future__ import annotations

import datetime as dt
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    import pandas as pd
    PANDAS_DISPONIVEL = True
except ImportError:
    PANDAS_DISPONIVEL = False

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
    """Armazena os scores de cada algoritmo para uma dezena."""
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
    """Classe principal que implementa todos os algoritmos de análise."""

    def __init__(self, concursos: List[Concurso]):
        self.concursos = sorted(concursos, key=lambda c: c.data)
        self.ultimo_concurso = self.concursos[-1] if self.concursos else None

        # Cache de análises
        self._frequencias: Optional[Dict[int, int]] = None
        self._matriz_markov: Optional[Dict[int, Dict[int, int]]] = None
        self._coocorrencias: Optional[Dict[Tuple[int, int], int]] = None
        self._atrasos: Optional[Dict[int, int]] = None

    def filtrar_por_anos(self, anos: int) -> 'AnalisadorMegaSena':
        """Retorna novo analisador com concursos dos últimos N anos."""
        limite = dt.date.today() - dt.timedelta(days=anos * 365)
        filtrados = [c for c in self.concursos if c.data >= limite]
        return AnalisadorMegaSena(filtrados)

    # ==================== ALGORITMO 1: FREQUÊNCIA ====================

    def calcular_frequencias(self) -> Dict[int, int]:
        """Conta quantas vezes cada dezena foi sorteada."""
        if self._frequencias is None:
            self._frequencias = defaultdict(int)
            for c in self.concursos:
                for d in c.dezenas:
                    self._frequencias[d] += 1
        return self._frequencias

    def scores_frequencia(self) -> Dict[int, float]:
        """Retorna score normalizado (0-1) baseado em frequência."""
        freq = self.calcular_frequencias()
        if not freq:
            return {d: 0.0 for d in range(DEZENA_MIN, DEZENA_MAX + 1)}

        max_freq = max(freq.values()) if freq else 1
        return {d: freq.get(d, 0) / max_freq for d in range(DEZENA_MIN, DEZENA_MAX + 1)}

    # ==================== ALGORITMO 2: MARKOV ====================

    def calcular_matriz_markov(self) -> Dict[int, Dict[int, int]]:
        """
        Calcula matriz de transição de Markov.
        Para cada dezena, conta quais dezenas aparecem no sorteio SEGUINTE.
        """
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
        """
        Retorna score baseado em Markov.
        Usa as dezenas do último sorteio como referência (ou as fornecidas).
        """
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

        # Normaliza
        max_score = max(scores.values()) if scores else 1
        return {d: scores.get(d, 0) / max_score for d in range(DEZENA_MIN, DEZENA_MAX + 1)}

    # ==================== ALGORITMO 3: CO-OCORRÊNCIA ====================

    def calcular_coocorrencias(self) -> Dict[Tuple[int, int], int]:
        """Conta quantas vezes cada par de dezenas apareceu junto."""
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
        """
        Score baseado em quantos pares frequentes cada dezena participa.
        """
        cooc = self.calcular_coocorrencias()

        # Pega os top 100 pares mais frequentes
        top_pares = sorted(cooc.items(), key=lambda x: x[1], reverse=True)[:100]

        scores = defaultdict(float)
        for (d1, d2), contagem in top_pares:
            scores[d1] += contagem
            scores[d2] += contagem

        max_score = max(scores.values()) if scores else 1
        return {d: scores.get(d, 0) / max_score for d in range(DEZENA_MIN, DEZENA_MAX + 1)}

    def pares_mais_frequentes(self, top_n: int = 20) -> List[Tuple[Tuple[int, int], int]]:
        """Retorna os N pares mais frequentes."""
        cooc = self.calcular_coocorrencias()
        return sorted(cooc.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # ==================== ALGORITMO 4: ATRASOS ====================

    def calcular_atrasos(self) -> Dict[int, int]:
        """Calcula há quantos sorteios cada dezena não aparece."""
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
        """Score normalizado baseado em atraso (mais atrasado = maior score)."""
        atrasos = self.calcular_atrasos()
        max_atraso = max(atrasos.values()) if atrasos else 1
        return {d: atrasos.get(d, 0) / max_atraso for d in range(DEZENA_MIN, DEZENA_MAX + 1)}

    def dezenas_mais_atrasadas(self, top_n: int = 10) -> List[Tuple[int, int]]:
        """Retorna as N dezenas mais atrasadas."""
        atrasos = self.calcular_atrasos()
        return sorted(atrasos.items(), key=lambda x: x[1], reverse=True)[:top_n]


class GeradorJogos:
    """Gera jogos combinando múltiplos algoritmos."""

    def __init__(self, analisador: AnalisadorMegaSena, rng: Optional[random.Random] = None):
        self.analisador = analisador
        self.rng = rng or random.Random()

    def _faixa(self, dezena: int) -> int:
        for idx, (inicio, fim) in enumerate(FAIXAS):
            if inicio <= dezena <= fim:
                return idx
        return -1

    def _verificar_balanceamento(self, dezenas: List[int]) -> bool:
        """Verifica se o jogo está balanceado (3 pares, distribuição por faixas)."""
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
        """Gera jogo totalmente aleatório."""
        return sorted(self.rng.sample(range(DEZENA_MIN, DEZENA_MAX + 1), TAMANHO_JOGO))

    def gerar_por_scores(
        self,
        pesos: Dict[str, float],
        forcar_balanceamento: bool = False,
        max_tentativas: int = 500
    ) -> List[int]:
        """
        Gera jogo baseado nos scores combinados dos algoritmos selecionados.
        """
        # Calcula scores de cada algoritmo
        scores_freq = self.analisador.scores_frequencia() if pesos.get('frequencia', 0) > 0 else {}
        scores_markov = self.analisador.scores_markov() if pesos.get('markov', 0) > 0 else {}
        scores_cooc = self.analisador.scores_coocorrencia() if pesos.get('coocorrencia', 0) > 0 else {}
        scores_atraso = self.analisador.scores_atraso() if pesos.get('atraso', 0) > 0 else {}

        # Combina scores
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

        # Gera pesos para escolha ponderada
        dezenas = list(range(DEZENA_MIN, DEZENA_MAX + 1))
        pesos_escolha = [scores_combinados[d] + 0.1 for d in dezenas]  # +0.1 evita peso zero

        for _ in range(max_tentativas):
            # Escolhe 6 dezenas com peso
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

        # Fallback
        return self.gerar_uniforme()

    def gerar_jogos(
        self,
        quantidade: int,
        algoritmos: List[str],
        forcar_balanceamento: bool = False
    ) -> List[Tuple[List[int], Dict[str, float]]]:
        """
        Gera múltiplos jogos usando os algoritmos especificados.
        Retorna lista de (jogo, pesos_usados).
        """
        # Define pesos baseado nos algoritmos selecionados
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
                jogos.append((jogo, pesos.copy()))

        return jogos


def carregar_resultados_excel(caminho: Path) -> List[Concurso]:
    """Carrega resultados de um arquivo Excel."""
    if not PANDAS_DISPONIVEL:
        print("Erro: pandas não instalado. Execute: pip install pandas openpyxl")
        sys.exit(1)

    df = pd.read_excel(caminho)
    concursos = []

    # Detecta colunas
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


def exibir_menu_principal():
    """Exibe o menu principal."""
    print("\n" + "=" * 60)
    print("      GERADOR INTELIGENTE - MEGA-SENA")
    print("=" * 60)
    print("\nALGORITMOS DISPONIVEIS:")
    print("-" * 40)
    print("  1. Frequencia   - Numeros mais sorteados")
    print("  2. Markov       - Seguidores do ultimo sorteio")
    print("  3. Co-ocorrencia- Pares que saem juntos")
    print("  4. Atrasados    - Numeros que nao saem ha tempo")
    print("  5. Balanceado   - Equilibrio par/impar e faixas")
    print("  6. Uniforme     - Totalmente aleatorio")
    print("-" * 40)
    print("\nOPCOES:")
    print("  [G] Gerar jogos")
    print("  [E] Ver estatisticas")
    print("  [S] Sair")
    print("-" * 40)


def selecionar_algoritmos() -> Tuple[List[str], bool]:
    """Permite ao usuário selecionar os algoritmos."""
    print("\n" + "-" * 40)
    print("SELECAO DE ALGORITMOS")
    print("Digite os numeros separados por virgula")
    print("Exemplo: 1,2,4 para Frequencia + Markov + Atrasados")
    print("-" * 40)

    opcoes = {
        '1': 'frequencia',
        '2': 'markov',
        '3': 'coocorrencia',
        '4': 'atraso',
        '5': 'balanceado',
        '6': 'uniforme'
    }

    while True:
        entrada = input("\nAlgoritmos (1-6): ").strip()
        if not entrada:
            print("Usando padrao: Frequencia + Markov + Balanceado")
            return ['frequencia', 'markov'], True

        try:
            selecionados = [s.strip() for s in entrada.split(',')]
            algoritmos = []
            balanceado = False

            for s in selecionados:
                if s in opcoes:
                    if s == '5':
                        balanceado = True
                    else:
                        algoritmos.append(opcoes[s])

            if not algoritmos and not balanceado:
                algoritmos = ['uniforme']

            return algoritmos, balanceado
        except Exception:
            print("Entrada invalida. Tente novamente.")


def exibir_estatisticas(analisador: AnalisadorMegaSena):
    """Exibe estatísticas da base de dados."""
    print("\n" + "=" * 60)
    print("ESTATISTICAS DA BASE")
    print("=" * 60)

    print(f"\nTotal de concursos: {len(analisador.concursos)}")
    if analisador.concursos:
        print(f"Periodo: {analisador.concursos[0].data} a {analisador.concursos[-1].data}")
        print(f"Ultimo sorteio: {analisador.ultimo_concurso.dezenas}")

    # Números mais frequentes
    freq = analisador.calcular_frequencias()
    top_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\n TOP 10 NUMEROS MAIS FREQUENTES:")
    for i, (dezena, count) in enumerate(top_freq, 1):
        barra = "#" * (count // 20)
        print(f"  {i:2}. Dezena {dezena:02d}: {count:4d} vezes {barra}")

    # Números mais atrasados
    print("\n TOP 10 NUMEROS MAIS ATRASADOS:")
    atrasados = analisador.dezenas_mais_atrasadas(10)
    for i, (dezena, atraso) in enumerate(atrasados, 1):
        print(f"  {i:2}. Dezena {dezena:02d}: {atraso:3d} sorteios sem sair")

    # Pares mais frequentes
    print("\n TOP 10 PARES MAIS FREQUENTES:")
    pares = analisador.pares_mais_frequentes(10)
    for i, ((d1, d2), count) in enumerate(pares, 1):
        print(f"  {i:2}. ({d1:02d}, {d2:02d}): {count:3d} vezes juntos")

    input("\nPressione ENTER para continuar...")


def formatar_jogo(jogo: List[int]) -> str:
    """Formata um jogo para exibição."""
    return " - ".join(f"{d:02d}" for d in jogo)


def main():
    """Funcao principal da aplicacao."""
    print("\n" + "=" * 60)
    print("   CARREGANDO BASE DE DADOS...")
    print("=" * 60)

    caminho = Path("resultados.xlsx")
    if not caminho.exists():
        print(f"Erro: arquivo '{caminho}' nao encontrado!")
        sys.exit(1)

    concursos = carregar_resultados_excel(caminho)
    print(f"Carregados {len(concursos)} concursos.")

    analisador_completo = AnalisadorMegaSena(concursos)

    while True:
        exibir_menu_principal()
        opcao = input("\nEscolha uma opcao: ").strip().upper()

        if opcao == 'S':
            print("\nAte a proxima! Boa sorte!")
            break

        elif opcao == 'E':
            exibir_estatisticas(analisador_completo)

        elif opcao == 'G':
            # Perguntar período de análise
            print("\n" + "-" * 40)
            try:
                anos = input("Anos de historico a considerar [3]: ").strip()
                anos = int(anos) if anos else 3
            except ValueError:
                anos = 3

            analisador = analisador_completo.filtrar_por_anos(anos)
            print(f"Usando {len(analisador.concursos)} concursos dos ultimos {anos} anos.")

            # Selecionar algoritmos
            algoritmos, balanceado = selecionar_algoritmos()

            # Quantidade de jogos
            try:
                qtd = input("\nQuantidade de jogos [6]: ").strip()
                qtd = int(qtd) if qtd else 6
                qtd = max(1, min(qtd, 50))
            except ValueError:
                qtd = 6

            # Gerar jogos
            print("\n" + "=" * 60)
            print(f"GERANDO {qtd} JOGOS")
            print(f"Algoritmos: {', '.join(algoritmos)}")
            print(f"Balanceamento: {'Sim' if balanceado else 'Nao'}")
            print("=" * 60)

            gerador = GeradorJogos(analisador)
            jogos = gerador.gerar_jogos(qtd, algoritmos, balanceado)

            print("\n JOGOS GERADOS:\n")
            for i, (jogo, _) in enumerate(jogos, 1):
                pares = sum(1 for d in jogo if d % 2 == 0)
                impares = 6 - pares
                print(f"  Jogo {i:02d}: {formatar_jogo(jogo)}  (P:{pares}/I:{impares})")

            print("\n" + "-" * 40)
            print("Legenda: P = Pares, I = Impares")

            input("\nPressione ENTER para continuar...")

        else:
            print("Opcao invalida!")


if __name__ == "__main__":
    main()
