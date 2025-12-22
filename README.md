# 🍀 Gerador Inteligente de Jogos - Mega-Sena

Sistema completo para geração de jogos da Mega-Sena usando algoritmos estatísticos avançados.

## ✨ Funcionalidades

### 📊 **Análises Estatísticas**
- **Frequência**: Números mais sorteados no período
- **Markov**: Seguidores do último concurso
- **Co-ocorrência**: Pares que costumam sair juntos
- **Atrasados**: Números que não saem há muito tempo
- **Balanceamento**: Equilíbrio par/ímpar e distribuição por faixas

### 🎰 **Geração de Jogos**
- Múltiplas estratégias combináveis
- Jogos balanceados automaticamente
- Interface web interativa
- Script Python para linha de comando

### 📈 **Dashboard Estatístico**
- Top números mais/menos frequentes
- Pares mais comuns
- Gráficos de frequência e atraso
- Histórico completo de concursos

## 🚀 Como Usar

### Aplicação Web (Recomendado)
```bash
# Instalar dependências
pip install streamlit pandas

# Executar aplicação
streamlit run app_web.py
```

Acesse: http://localhost:8501

### Script Python
```bash
# Gerar jogos via linha de comando
python gerador_megasena.py --resultados resultados_exemplo.csv --anos 3 --jogos 5 --modo mix
```

### Algoritmos Disponíveis
- `uniforme`: Geração aleatória pura
- `ponderado`: Baseado em frequência histórica
- `balanceado`: Ponderado + regras de equilíbrio
- `mix`: Combinação alternada de estratégias

## 📁 Estrutura do Projeto

```
mega_sena/
├── app_web.py              # Aplicação web Streamlit
├── gerador_megasena.py     # Script de linha de comando
├── mega_sena_app.py        # Versão alternativa da app
├── resultados.xlsx         # Dados históricos
├── resultados_exemplo.csv  # Exemplo de dados CSV
└── README.md              # Esta documentação
```

## 📊 Dados

O sistema utiliza dados históricos da Mega-Sena em formato Excel/CSV com as colunas:
- `concurso`: Número do concurso
- `data`: Data do sorteio
- `dezena1` a `dezena6`: Números sorteados

## ⚠️ Importante

**Loteria é um jogo de azar!** Nenhum algoritmo pode prever com certeza os números sorteados. Este sistema apenas organiza as apostas baseado em estatísticas históricas para otimizar suas chances dentro das possibilidades matemáticas.

## 🤝 Contribuição

Sinta-se à vontade para contribuir com melhorias, novos algoritmos ou correções!

## 📝 Licença

Este projeto é open source e está disponível sob a licença MIT.

---

**Desenvolvido com ❤️ para amantes de estatística e jogos**
