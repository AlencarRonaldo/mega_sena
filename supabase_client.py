"""
Cliente Supabase para o Gerador Mega-Sena
Gerencia conexao e operacoes com o banco de dados
"""

import os
import requests
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# URL da API da Caixa
API_CAIXA_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"

# Carregar configurações
try:
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    # Fallback para variáveis de ambiente
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def get_supabase_client() -> Client:
    """Retorna cliente Supabase configurado."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Credenciais do Supabase nao configuradas. Verifique o arquivo .env")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ============== OPERACOES COM CONCURSOS ==============

def inserir_concurso(numero: int, data: date, dezenas: List[int]) -> bool:
    """Insere um novo concurso no banco."""
    try:
        supabase = get_supabase_client()
        dezenas_sorted = sorted(dezenas)[:6]

        data_str = data.isoformat() if isinstance(data, date) else str(data)

        supabase.table("concursos").upsert({
            "numero": numero,
            "data": data_str,
            "dezena1": dezenas_sorted[0],
            "dezena2": dezenas_sorted[1],
            "dezena3": dezenas_sorted[2],
            "dezena4": dezenas_sorted[3],
            "dezena5": dezenas_sorted[4],
            "dezena6": dezenas_sorted[5],
        }).execute()
        return True
    except Exception as e:
        print(f"Erro ao inserir concurso: {e}")
        return False


def inserir_concursos_em_lote(concursos: List[Dict]) -> Tuple[int, int]:
    """
    Insere multiplos concursos de uma vez.
    Retorna: (sucesso, falhas)
    """
    sucesso = 0
    falhas = 0

    try:
        supabase = get_supabase_client()

        registros = []
        for c in concursos:
            dezenas = c.get("dezenas", [])
            if len(dezenas) < 6:
                dezenas = [
                    c.get("dezena1", 0),
                    c.get("dezena2", 0),
                    c.get("dezena3", 0),
                    c.get("dezena4", 0),
                    c.get("dezena5", 0),
                    c.get("dezena6", 0),
                ]

            dezenas_sorted = sorted([d for d in dezenas if d > 0])[:6]
            if len(dezenas_sorted) < 6:
                falhas += 1
                continue

            data_val = c.get("data")
            if isinstance(data_val, date):
                data_str = data_val.isoformat()
            elif isinstance(data_val, datetime):
                data_str = data_val.date().isoformat()
            else:
                data_str = str(data_val)

            registros.append({
                "numero": c.get("numero") or c.get("concurso"),
                "data": data_str,
                "dezena1": dezenas_sorted[0],
                "dezena2": dezenas_sorted[1],
                "dezena3": dezenas_sorted[2],
                "dezena4": dezenas_sorted[3],
                "dezena5": dezenas_sorted[4],
                "dezena6": dezenas_sorted[5],
            })

        if registros:
            supabase.table("concursos").upsert(registros).execute()
            sucesso = len(registros)

    except Exception as e:
        print(f"Erro ao inserir concursos em lote: {e}")
        falhas = len(concursos)

    return sucesso, falhas


def buscar_todos_concursos() -> List[Dict]:
    """Busca todos os concursos ordenados por numero."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("concursos")\
            .select("*")\
            .order("numero", desc=False)\
            .execute()
        return response.data
    except Exception as e:
        print(f"Erro ao buscar concursos: {e}")
        return []


def buscar_ultimo_concurso() -> Optional[Dict]:
    """Busca o concurso mais recente."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("concursos")\
            .select("*")\
            .order("numero", desc=True)\
            .limit(1)\
            .execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Erro ao buscar ultimo concurso: {e}")
        return None


def buscar_concursos_recentes(limite: int = 100) -> List[Dict]:
    """Busca os N concursos mais recentes."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("concursos")\
            .select("*")\
            .order("numero", desc=True)\
            .limit(limite)\
            .execute()
        return response.data
    except Exception as e:
        print(f"Erro ao buscar concursos recentes: {e}")
        return []


def contar_concursos() -> int:
    """Retorna o total de concursos no banco."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("concursos")\
            .select("id", count="exact")\
            .execute()
        return response.count or 0
    except Exception as e:
        print(f"Erro ao contar concursos: {e}")
        return 0


# ============== OPERACOES COM JOGOS SALVOS ==============

def salvar_jogo(dezenas: List[int], algoritmos: List[str] = None) -> Optional[int]:
    """Salva um novo jogo e retorna o ID."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("jogos_salvos").insert({
            "dezenas": sorted(dezenas),
            "algoritmos": algoritmos or [],
            "conferido": False,
            "acertos": {}
        }).execute()
        return response.data[0]["id"] if response.data else None
    except Exception as e:
        print(f"Erro ao salvar jogo: {e}")
        return None


def salvar_jogos_em_lote(jogos: List[Dict]) -> Tuple[int, int]:
    """
    Salva multiplos jogos de uma vez.
    Cada jogo deve ter: dezenas, algoritmos (opcional)
    Retorna: (sucesso, falhas)
    """
    try:
        supabase = get_supabase_client()

        registros = []
        for j in jogos:
            registros.append({
                "dezenas": sorted(j.get("dezenas", [])),
                "algoritmos": j.get("algoritmos", []),
                "conferido": False,
                "acertos": {}
            })

        if registros:
            supabase.table("jogos_salvos").insert(registros).execute()
            return len(registros), 0

    except Exception as e:
        print(f"Erro ao salvar jogos em lote: {e}")
        return 0, len(jogos)

    return 0, 0


def buscar_jogos_salvos() -> List[Dict]:
    """Busca todos os jogos salvos."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("jogos_salvos")\
            .select("*")\
            .order("data_criacao", desc=True)\
            .execute()
        return response.data
    except Exception as e:
        print(f"Erro ao buscar jogos salvos: {e}")
        return []


def atualizar_jogo(jogo_id: int, dados: Dict) -> bool:
    """Atualiza um jogo existente."""
    try:
        supabase = get_supabase_client()
        supabase.table("jogos_salvos")\
            .update(dados)\
            .eq("id", jogo_id)\
            .execute()
        return True
    except Exception as e:
        print(f"Erro ao atualizar jogo: {e}")
        return False


def deletar_jogo(jogo_id: int) -> bool:
    """Deleta um jogo pelo ID."""
    try:
        supabase = get_supabase_client()
        supabase.table("jogos_salvos")\
            .delete()\
            .eq("id", jogo_id)\
            .execute()
        return True
    except Exception as e:
        print(f"Erro ao deletar jogo: {e}")
        return False


def deletar_todos_jogos() -> bool:
    """Deleta todos os jogos salvos."""
    try:
        supabase = get_supabase_client()
        supabase.table("jogos_salvos")\
            .delete()\
            .neq("id", 0)\
            .execute()
        return True
    except Exception as e:
        print(f"Erro ao deletar todos os jogos: {e}")
        return False


def conferir_jogo_no_banco(jogo_id: int, concurso_numero: int, acertos: int) -> bool:
    """Atualiza o resultado de conferencia de um jogo."""
    try:
        supabase = get_supabase_client()

        # Buscar jogo atual
        response = supabase.table("jogos_salvos")\
            .select("acertos")\
            .eq("id", jogo_id)\
            .execute()

        if not response.data:
            return False

        acertos_atual = response.data[0].get("acertos") or {}
        acertos_atual[str(concurso_numero)] = acertos

        supabase.table("jogos_salvos")\
            .update({
                "acertos": acertos_atual,
                "conferido": True
            })\
            .eq("id", jogo_id)\
            .execute()

        return True
    except Exception as e:
        print(f"Erro ao conferir jogo: {e}")
        return False


# ============== SINCRONIZACAO COM API CAIXA ==============

def buscar_concurso_caixa(numero: int = None) -> Optional[Dict]:
    """Busca um concurso especifico ou o ultimo da API da Caixa."""
    try:
        url = f"{API_CAIXA_URL}/{numero}" if numero else API_CAIXA_URL
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Erro ao buscar concurso da Caixa: {e}")
    return None


def sincronizar_com_caixa(dias_atras: int = 365) -> Tuple[int, int, str]:
    """
    Sincroniza o banco com os resultados da API da Caixa.

    Args:
        dias_atras: Quantos dias para tras buscar (default: 365 = 1 ano)

    Returns:
        (novos, atualizados, mensagem)
    """
    try:
        supabase = get_supabase_client()

        # Buscar ultimo concurso da Caixa
        ultimo_caixa = buscar_concurso_caixa()
        if not ultimo_caixa:
            return 0, 0, "Erro ao conectar com API da Caixa"

        ultimo_num = ultimo_caixa.get('numero')
        data_limite = datetime.now() - timedelta(days=dias_atras)

        # Buscar ultimo concurso local
        ultimo_local = buscar_ultimo_concurso()
        ultimo_local_num = ultimo_local['numero'] if ultimo_local else 0

        # Se ja esta atualizado
        if ultimo_local_num >= ultimo_num:
            return 0, 0, "Base ja esta atualizada!"

        # Buscar concursos faltantes
        concursos = []
        num = ultimo_num

        while num > ultimo_local_num and num > 0:
            dados = buscar_concurso_caixa(num)
            if dados:
                data_str = dados.get('dataApuracao', '')
                try:
                    data_concurso = datetime.strptime(data_str, '%d/%m/%Y')
                except:
                    num -= 1
                    continue

                # Parar se passou do limite de dias
                if data_concurso < data_limite:
                    break

                dezenas = dados.get('listaDezenas', [])
                dezenas_int = sorted([int(d) for d in dezenas])

                if len(dezenas_int) == 6:
                    concursos.append({
                        'numero': dados.get('numero'),
                        'data': data_concurso.strftime('%Y-%m-%d'),
                        'dezena1': dezenas_int[0],
                        'dezena2': dezenas_int[1],
                        'dezena3': dezenas_int[2],
                        'dezena4': dezenas_int[3],
                        'dezena5': dezenas_int[4],
                        'dezena6': dezenas_int[5],
                    })
            num -= 1

        if not concursos:
            return 0, 0, "Nenhum concurso novo encontrado"

        # Inserir em lotes de 50
        for i in range(0, len(concursos), 50):
            lote = concursos[i:i+50]
            supabase.table('concursos').upsert(lote, on_conflict='numero').execute()

        return len(concursos), 0, f"Sincronizados {len(concursos)} concursos!"

    except Exception as e:
        return 0, 0, f"Erro na sincronizacao: {str(e)}"


def verificar_atualizacao() -> Tuple[bool, int, int]:
    """
    Verifica se ha novos concursos disponiveis.

    Returns:
        (ha_novos, ultimo_local, ultimo_caixa)
    """
    try:
        ultimo_caixa = buscar_concurso_caixa()
        if not ultimo_caixa:
            return False, 0, 0

        ultimo_caixa_num = ultimo_caixa.get('numero', 0)

        ultimo_local = buscar_ultimo_concurso()
        ultimo_local_num = ultimo_local['numero'] if ultimo_local else 0

        return ultimo_caixa_num > ultimo_local_num, ultimo_local_num, ultimo_caixa_num
    except:
        return False, 0, 0


def buscar_concursos_ultimo_ano() -> List[Dict]:
    """Busca todos os concursos do ultimo ano do banco."""
    try:
        supabase = get_supabase_client()
        data_limite = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        response = supabase.table("concursos")\
            .select("*")\
            .gte("data", data_limite)\
            .order("numero", desc=False)\
            .execute()
        return response.data
    except Exception as e:
        print(f"Erro ao buscar concursos do ultimo ano: {e}")
        return []


# ============== UTILITARIOS ==============

def testar_conexao() -> Tuple[bool, str]:
    """Testa a conexao com o Supabase."""
    try:
        supabase = get_supabase_client()
        # Tenta fazer uma query simples
        supabase.table("concursos").select("id").limit(1).execute()
        return True, "Conexao estabelecida com sucesso!"
    except Exception as e:
        return False, f"Erro na conexao: {str(e)}"


def migrar_excel_para_supabase(caminho_excel: str = "resultados.xlsx") -> Tuple[int, int]:
    """
    Migra dados do Excel para o Supabase.
    Retorna: (sucesso, falhas)
    """
    import pandas as pd
    from pathlib import Path

    caminho = Path(caminho_excel)
    if not caminho.exists():
        return 0, 0

    try:
        df = pd.read_excel(caminho)

        concursos = []
        for _, row in df.iterrows():
            concursos.append({
                "numero": int(row.get("concurso", 0)),
                "data": row.get("data"),
                "dezena1": int(row.get("dezena1", 0)),
                "dezena2": int(row.get("dezena2", 0)),
                "dezena3": int(row.get("dezena3", 0)),
                "dezena4": int(row.get("dezena4", 0)),
                "dezena5": int(row.get("dezena5", 0)),
                "dezena6": int(row.get("dezena6", 0)),
            })

        return inserir_concursos_em_lote(concursos)

    except Exception as e:
        print(f"Erro na migracao: {e}")
        return 0, 0


if __name__ == "__main__":
    # Teste de conexao
    sucesso, msg = testar_conexao()
    print(msg)

    if sucesso:
        print(f"Total de concursos: {contar_concursos()}")

        ultimo = buscar_ultimo_concurso()
        if ultimo:
            print(f"Ultimo concurso: {ultimo['numero']}")
