"""
Gerador de jogos da Mega-Sena com diferentes lógicas:
- Uniforme: 6 dezenas aleatórias puras.
- Ponderado: 6 dezenas com pesos baseados na frequência dos últimos N anos.
- Balanceado: ponderado + regras de equilíbrio (pares/ímpares e faixas).

Entrada esperada de resultados:
- Excel (.xlsx/.xls): colunas Data, Dezena 1..Dezena 6 (ou Bola 1..Bola 6)
- CSV: colunas data, bola1..bola6
Formato de data flexível (YYYY-MM-DD ou DD/MM/YYYY).
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import random
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Set

try:
    import pandas as pd
    PANDAS_DISPONIVEL = True
except ImportError:
    PANDAS_DISPONIVEL = False


DEZENA_MIN = 1
DEZENA_MAX = 60
TAMANHO_JOGO = 6
FAIXAS = [(1, 20), (21, 40), (41, 60)]


@dataclass(frozen=True)
class Concurso:
    data: dt.date
    dezenas: Set[int]


def parse_data(valor: str) -> dt.date:
    valor = valor.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return dt.datetime.strptime(valor, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Formato de data não reconhecido: {valor}")


def baixar_resultados(url: str, destino: Path) -> bool:
    """Baixa CSV de resultados para o caminho indicado. Retorna True em caso de sucesso."""
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            if resp.status != 200:
                print(f"Falha ao baixar (HTTP {resp.status})")
                return False
            destino.write_bytes(resp.read())
        return True
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        print(f"Erro ao baixar resultados: {exc}")
    except Exception as exc:  # noqa: BLE001
        print(f"Erro inesperado ao baixar resultados: {exc}")
    return False


def carregar_resultados_csv(caminho: Path) -> List[Concurso]:
    """Carrega resultados de um arquivo CSV."""
    concursos: List[Concurso] = []
    with caminho.open("r", newline="", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        colunas = ["bola1", "bola2", "bola3", "bola4", "bola5", "bola6"]
        for linha in leitor:
            try:
                data = parse_data(linha["data"])
                dezenas = {int(linha[c]) for c in colunas}
            except Exception:
                continue
            if len(dezenas) != TAMANHO_JOGO:
                continue
            if not all(DEZENA_MIN <= d <= DEZENA_MAX for d in dezenas):
                continue
            concursos.append(Concurso(data=data, dezenas=dezenas))
    return concursos


def carregar_resultados_excel(caminho: Path) -> List[Concurso]:
    """Carrega resultados de um arquivo Excel (.xlsx)."""
    if not PANDAS_DISPONIVEL:
        print("Erro: pandas não instalado. Execute: pip install pandas openpyxl")
        sys.exit(1)

    concursos: List[Concurso] = []
    df = pd.read_excel(caminho)

    # Mapeamento flexível de colunas
    col_data = None
    colunas_dezenas = []

    for col in df.columns:
        col_lower = col.lower().strip()
        if col_lower in ("data", "data do sorteio"):
            col_data = col
        elif "dezena" in col_lower or "bola" in col_lower:
            colunas_dezenas.append(col)

    # Ordena colunas de dezenas por número (Dezena 1, Dezena 2, etc.)
    colunas_dezenas = sorted(colunas_dezenas, key=lambda x: int(''.join(filter(str.isdigit, x)) or 0))

    if col_data is None or len(colunas_dezenas) < TAMANHO_JOGO:
        print(f"Erro: colunas esperadas não encontradas. Encontradas: {df.columns.tolist()}")
        sys.exit(1)

    for _, linha in df.iterrows():
        try:
            valor_data = linha[col_data]
            if isinstance(valor_data, dt.datetime):
                data = valor_data.date()
            elif isinstance(valor_data, dt.date):
                data = valor_data
            else:
                data = parse_data(str(valor_data))

            dezenas = {int(linha[c]) for c in colunas_dezenas[:TAMANHO_JOGO]}
        except Exception:
            continue

        if len(dezenas) != TAMANHO_JOGO:
            continue
        if not all(DEZENA_MIN <= d <= DEZENA_MAX for d in dezenas):
            continue
        concursos.append(Concurso(data=data, dezenas=dezenas))

    return concursos


def carregar_resultados(caminho: Path) -> List[Concurso]:
    """Carrega resultados de CSV ou Excel, detectando automaticamente."""
    sufixo = caminho.suffix.lower()
    if sufixo in (".xlsx", ".xls"):
        return carregar_resultados_excel(caminho)
    else:
        return carregar_resultados_csv(caminho)


def filtrar_por_anos(concursos: Sequence[Concurso], anos: int) -> List[Concurso]:
    if not concursos:
        return []
    limite = dt.date.today() - dt.timedelta(days=anos * 365)
    return [c for c in concursos if c.data >= limite]


def frequencias(concursos: Iterable[Concurso]) -> List[int]:
    freq = [0] * (DEZENA_MAX + 1)
    for c in concursos:
        for d in c.dezenas:
            freq[d] += 1
    return freq


def gerar_uniforme(rng: random.Random) -> List[int]:
    return sorted(rng.sample(range(DEZENA_MIN, DEZENA_MAX + 1), TAMANHO_JOGO))


def _escolher_com_peso(freq: List[int], rng: random.Random) -> int:
    pesos = [freq[i] + 1 for i in range(DEZENA_MIN, DEZENA_MAX + 1)]
    # random.choices usa população + pesos alinhados
    return rng.choices(population=range(DEZENA_MIN, DEZENA_MAX + 1), weights=pesos, k=1)[0]


def gerar_ponderado(freq: List[int], rng: random.Random) -> List[int]:
    dezenas: Set[int] = set()
    while len(dezenas) < TAMANHO_JOGO:
        dezenas.add(_escolher_com_peso(freq, rng))
    return sorted(dezenas)


def _faixa(dezena: int) -> int:
    for idx, (inicio, fim) in enumerate(FAIXAS):
        if inicio <= dezena <= fim:
            return idx
    return -1


def gerar_balanceado(freq: List[int], rng: random.Random, max_tentativas: int = 500) -> List[int]:
    alvo_pares = TAMANHO_JOGO // 2
    for _ in range(max_tentativas):
        dezenas = gerar_ponderado(freq, rng)
        pares = sum(1 for d in dezenas if d % 2 == 0)
        faixas = [_faixa(d) for d in dezenas]
        cond_pares = pares == alvo_pares
        cond_faixas = all(faixas.count(i) >= 1 for i in range(len(FAIXAS))) and all(
            faixas.count(i) <= 3 for i in range(len(FAIXAS))
        )
        if cond_pares and cond_faixas:
            return dezenas
    # fallback para o melhor disponível
    return gerar_ponderado(freq, rng)


def gerar_jogos(modo: str, qtd: int, freq: List[int], rng: random.Random) -> List[List[int]]:
    jogos: List[List[int]] = []
    geradores = {
        "uniforme": lambda: gerar_uniforme(rng),
        "ponderado": lambda: gerar_ponderado(freq, rng),
        "balanceado": lambda: gerar_balanceado(freq, rng),
    }
    if modo == "mix":
        sequencia = ["balanceado", "ponderado", "uniforme"]
        for i in range(qtd):
            jogos.append(geradores[sequencia[i % len(sequencia)]]())
        return jogos
    if modo not in geradores:
        raise ValueError(f"Modo inválido: {modo}")
    for _ in range(qtd):
        jogos.append(geradores[modo]())
    return jogos


def formatar_jogo(jogo: Sequence[int]) -> str:
    return " ".join(f"{d:02d}" for d in jogo)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera jogos da Mega-Sena usando histórico dos últimos anos."
    )
    parser.add_argument("--resultados", type=Path, default=Path("resultados.xlsx"), help="Arquivo CSV ou Excel com resultados")
    parser.add_argument(
        "--url",
        type=str,
        default="https://raw.githubusercontent.com/renanxcortes/megasena-dataset/master/megasena-dataset.csv",
        help="URL CSV público dos concursos (padrão: dataset aberto no GitHub)",
    )
    parser.add_argument(
        "--baixar",
        action="store_true",
        help="Força baixar o CSV da URL antes de gerar (sobrescreve o arquivo local).",
    )
    parser.add_argument("--anos", type=int, default=3, help="Quantos anos recentes considerar (padrão: 3)")
    parser.add_argument("--jogos", type=int, default=6, help="Quantidade de jogos a gerar")
    parser.add_argument(
        "--modo",
        choices=["uniforme", "ponderado", "balanceado", "mix"],
        default="mix",
        help="Estratégia de geração (mix alterna balanceado/ponderado/uniforme)",
    )
    parser.add_argument("--seed", type=int, default=None, help="Semente opcional para reprodutibilidade")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    if args.baixar or not args.resultados.exists():
        print(f"Baixando resultados de {args.url} ...")
        ok = baixar_resultados(args.url, args.resultados)
        if not ok:
            print("Não foi possível baixar o arquivo. Interrompendo.")
            sys.exit(1)

    concursos = carregar_resultados(args.resultados)
    recentes = filtrar_por_anos(concursos, anos=args.anos)
    if not recentes:
        print("Nenhum concurso encontrado no período especificado.")
        return

    freq = frequencias(recentes)
    jogos = gerar_jogos(args.modo, args.jogos, freq, rng)

    print(f"Gerando {args.jogos} jogos (modo: {args.modo}) usando últimos {args.anos} anos:")
    for idx, jogo in enumerate(jogos, start=1):
        print(f"Jogo {idx:02d}: {formatar_jogo(jogo)}")


if __name__ == "__main__":
    main()


