#!/usr/bin/env python3
"""
Script para testar a conexão com o Supabase
Execute: python teste_supabase.py
"""

import sys
from supabase_client import get_supabase_client, verificar_atualizacao, contar_concursos

def testar_conexao():
    """Testa a conexão básica com o Supabase."""
    print("Testando conexao com Supabase...")

    try:
        # Tentar obter cliente
        client = get_supabase_client()
        print("Cliente Supabase criado com sucesso!")

        # Testar conexão fazendo uma query simples
        response = client.table('concursos').select('count').limit(1).execute()
        print("Conexao com banco de dados estabelecida!")

        # Verificar se há dados
        total = contar_concursos()
        print(f"Total de concursos no banco: {total}")

        # Verificar atualização
        precisa_atualizar, ultimo_concurso = verificar_atualizacao()
        if precisa_atualizar:
            print(f"Banco precisa ser atualizado. Ultimo concurso: {ultimo_concurso}")
        else:
            print(f"Banco esta atualizado. Ultimo concurso: {ultimo_concurso}")

        return True

    except Exception as e:
        print(f"Erro na conexao: {str(e)}")
        return False

def main():
    print("Teste de Conexao - Mega-Sena Supabase\n")

    # Verificar se as credenciais estão configuradas
    from config import SUPABASE_URL, SUPABASE_KEY

    if not SUPABASE_URL or not SUPABASE_KEY or SUPABASE_URL == "https://seu-projeto.supabase.co":
        print("Credenciais do Supabase nao configuradas!")
        print("\nPara configurar:")
        print("1. Acesse https://supabase.com")
        print("2. Crie um projeto gratuito")
        print("3. Va em Settings > API")
        print("4. Copie a 'Project URL' e 'anon public' key")
        print("5. Edite o arquivo .env com suas credenciais:")
        print("   SUPABASE_URL=https://xxx.supabase.co")
        print("   SUPABASE_KEY=eyJ...")
        print("6. Execute o SQL em supabase_schema.sql no SQL Editor do Supabase")
        print("\nDepois execute este script novamente.")
        return

    print(f"URL: {SUPABASE_URL}")
    print(f"Key: {SUPABASE_KEY[:20]}...\n")

    # Testar conexão
    sucesso = testar_conexao()

    if sucesso:
        print("\nConexao estabelecida com sucesso!")
        print("Voce pode executar: streamlit run app_web.py")
    else:
        print("\nFalha na conexao. Verifique suas credenciais.")
        sys.exit(1)

if __name__ == "__main__":
    main()
