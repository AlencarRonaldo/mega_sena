#!/usr/bin/env python3
"""
Script para verificar o estado do banco Supabase
Execute: python verificar_banco.py
"""

from supabase_client import get_supabase_client

def verificar_tabelas():
    """Verifica se as tabelas existem e têm dados."""
    print("Verificando tabelas do Supabase...")

    try:
        client = get_supabase_client()

        # Verificar tabela concursos
        print("\n1. Tabela 'concursos':")
        response = client.table('concursos').select('*').limit(1).execute()
        if response.data:
            print("   Tabela existe e tem dados")
            print(f"   Primeiro registro: {response.data[0]}")
        else:
            print("   Tabela existe mas esta vazia")

        # Contar registros
        count_response = client.table('concursos').select('count', count='exact').execute()
        total_concursos = count_response.count if hasattr(count_response, 'count') else len(count_response.data)
        print(f"   Total de registros: {total_concursos}")

        # Verificar tabela jogos_salvos
        print("\n2. Tabela 'jogos_salvos':")
        jogos_response = client.table('jogos_salvos').select('*').limit(1).execute()
        if jogos_response.data:
            print("   Tabela existe e tem dados")
            print(f"   Primeiro jogo: {jogos_response.data[0]}")
        else:
            print("   Tabela existe mas esta vazia")

        # Verificar último concurso
        print("\n3. Ultimo concurso:")
        ultimo_response = client.table('concursos').select('*').order('numero', desc=True).limit(1).execute()
        if ultimo_response.data:
            ultimo = ultimo_response.data[0]
            print(f"   Concurso {ultimo['numero']} - {ultimo['data']}")
            print(f"   Dezenas: {ultimo['dezena1']}-{ultimo['dezena2']}-{ultimo['dezena3']}-{ultimo['dezena4']}-{ultimo['dezena5']}-{ultimo['dezena6']}")
        else:
            print("   Nenhum concurso encontrado")

        return True

    except Exception as e:
        print(f"Erro ao verificar tabelas: {str(e)}")
        return False

def main():
    print("Verificacao do Banco Supabase - Mega-Sena\n")

    sucesso = verificar_tabelas()

    if sucesso:
        print("\nVerificacao concluida!")
        print("Banco Supabase esta funcionando corretamente!")
    else:
        print("\nProblemas encontrados no banco.")
        print("Verifique se o schema SQL foi executado corretamente.")

if __name__ == "__main__":
    main()
