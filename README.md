# Gerador Inteligente de Jogos - Mega-Sena

Sistema completo para geracao de jogos da Mega-Sena usando algoritmos estatisticos avancados.

## Funcionalidades

### Geracao de Jogos
- **Multiplos algoritmos** combinaveis (Frequencia, Markov, Co-ocorrencia, Atrasados)
- **Numeros fixos**: Force numeros especificos em todos os jogos
- **Numeros removidos**: Exclua numeros indesejados
- **Balanceamento automatico**: Equilibrio par/impar e distribuicao por faixas
- **Geracao em lote**: Ate 50 jogos por vez

### Fechamento / Desdobramento
- Jogue mais numeros com garantia de premiacao minima
- Suporte para 7 a 15 dezenas
- Garantias: Quadra, Quina ou Sena
- Tabela de referencia com quantidade de jogos necessarios

### Simulador de Jogos
- Teste seus jogos em sorteios anteriores
- Visualize quantas vezes teria acertado quadra, quina ou sena
- Simule em ate 500 concursos passados
- Detalhamento de cada premiacao

### Conferencia Automatica
- Confira jogos contra resultados oficiais
- Selecione qualquer concurso dos ultimos 20
- Conferencia individual ou em lote
- Destaque visual dos numeros acertados

### Salvar e Gerenciar Jogos
- Salve jogos para conferir depois
- Historico de algoritmos usados
- Registro de acertos por concurso
- Exporte todos os jogos salvos

### Exportacao
- **Excel**: Planilha completa com todos os jogos e informacoes
- **CSV**: Formato simples para importacao

### Estatisticas Avancadas
- Top numeros mais/menos frequentes
- Pares mais comuns (co-ocorrencia)
- Numeros atrasados
- Graficos de frequencia e atraso
- Historico completo de concursos

### Atualizacao de Resultados
- Busca automatica na API da Caixa
- Visualizacao do ultimo concurso disponivel

## Como Usar

### Aplicacao Web (Recomendado)
```bash
# Instalar dependencias
pip install streamlit pandas openpyxl requests

# Executar aplicacao
streamlit run app_web.py
```

Acesse: http://localhost:8501

### Script Python (Linha de Comando)
```bash
python gerador_megasena.py --resultados resultados_exemplo.csv --anos 3 --jogos 5 --modo mix
```

## Abas do Sistema

| Aba | Funcao |
|-----|--------|
| **Gerar Jogos** | Geracao com algoritmos, numeros fixos/removidos, exportacao |
| **Estatisticas** | Analises, graficos, pares frequentes |
| **Fechamento** | Desdobramento com garantia de premiacao |
| **Simulador** | Teste jogos em sorteios passados |
| **Meus Jogos** | Gerenciamento de jogos salvos |
| **Conferir** | Conferencia contra resultados oficiais |
| **Config** | Atualizacao de dados, informacoes do sistema |

## Algoritmos Disponiveis

| Algoritmo | Descricao |
|-----------|-----------|
| **Frequencia** | Prioriza numeros que mais sairam no periodo |
| **Markov** | Analisa quais numeros tendem a seguir os do ultimo sorteio |
| **Co-ocorrencia** | Prioriza numeros que costumam sair juntos |
| **Atrasados** | Prioriza numeros que nao saem ha muito tempo |
| **Balanceado** | Forca 3 pares/3 impares e distribuicao por faixas |
| **Uniforme** | Geracao totalmente aleatoria |

## Estrutura do Projeto

```
mega_sena/
├── app_web.py              # Aplicacao web Streamlit (principal)
├── gerador_megasena.py     # Script de linha de comando
├── mega_sena_app.py        # Versao alternativa da app
├── resultados.xlsx         # Dados historicos
├── resultados_exemplo.csv  # Exemplo de dados CSV
├── jogos_salvos.json       # Jogos salvos pelo usuario
└── README.md               # Esta documentacao
```

## Dados

O sistema utiliza dados historicos da Mega-Sena em formato Excel/CSV com as colunas:
- `concurso`: Numero do concurso
- `data`: Data do sorteio
- `dezena1` a `dezena6`: Numeros sorteados

## Comparativo com Concorrentes

| Funcionalidade | Nosso Sistema | Concorrentes |
|----------------|---------------|--------------|
| Algoritmo Markov | Sim | Nao |
| Numeros fixos/removidos | Sim | Sim |
| Fechamento | Sim | Sim |
| Simulador | Sim | Alguns |
| Conferencia automatica | Sim | Sim |
| Salvar jogos | Sim | Sim |
| Exportar Excel/CSV | Sim | Alguns |
| Interface web moderna | Sim | Variavel |
| Codigo aberto | Sim | Nao |

## Importante

**Loteria e um jogo de azar!** Nenhum algoritmo pode prever com certeza os numeros sorteados. Este sistema apenas organiza as apostas baseado em estatisticas historicas para otimizar suas chances dentro das possibilidades matematicas.

## Requisitos

- Python 3.8+
- streamlit
- pandas
- openpyxl
- requests

## Licenca

Este projeto e open source e esta disponivel sob a licenca MIT.

---

**Desenvolvido com Python e Streamlit**
