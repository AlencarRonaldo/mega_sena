import { Concurso } from './supabase'

export const DEZENA_MIN = 1
export const DEZENA_MAX = 60
export const TAMANHO_JOGO = 6

export interface ScoreDezena {
  dezena: number
  frequencia: number
  markov: number
  coocorrencia: number
  atraso: number
}

export class AnalisadorMegaSena {
  constructor(private concursos: Concurso[]) {}

  filtrarPorAnos(anos: number): AnalisadorMegaSena {
    const limite = new Date()
    limite.setFullYear(limite.getFullYear() - anos)
    const filtrados = this.concursos.filter(c => new Date(c.data) >= limite)
    return new AnalisadorMegaSena(filtrados)
  }

  calcularFrequencias(): Map<number, number> {
    const freq = new Map<number, number>()
    for (const concurso of this.concursos) {
      const dezenas = [concurso.dezena1, concurso.dezena2, concurso.dezena3,
                      concurso.dezena4, concurso.dezena5, concurso.dezena6]
      for (const dezena of dezenas) {
        freq.set(dezena, (freq.get(dezena) || 0) + 1)
      }
    }
    return freq
  }

  scoresFrequencia(): Map<number, number> {
    const freq = this.calcularFrequencias()
    if (freq.size === 0) {
      const empty = new Map<number, number>()
      for (let i = DEZENA_MIN; i <= DEZENA_MAX; i++) empty.set(i, 0)
      return empty
    }

    const maxFreq = Math.max(...freq.values())
    const scores = new Map<number, number>()
    for (let i = DEZENA_MIN; i <= DEZENA_MAX; i++) {
      scores.set(i, (freq.get(i) || 0) / maxFreq)
    }
    return scores
  }

  calcularMatrizMarkov(): Map<number, Map<number, number>> {
    const matriz = new Map<number, Map<number, number>>()

    for (let i = 0; i < this.concursos.length - 1; i++) {
      const atual = this.concursos[i]
      const proximo = this.concursos[i + 1]

      const dezenasAtual = [atual.dezena1, atual.dezena2, atual.dezena3,
                           atual.dezena4, atual.dezena5, atual.dezena6]
      const dezenasProximo = [proximo.dezena1, proximo.dezena2, proximo.dezena3,
                             proximo.dezena4, proximo.dezena5, proximo.dezena6]

      for (const dAtual of dezenasAtual) {
        for (const dProximo of dezenasProximo) {
          if (!matriz.has(dAtual)) matriz.set(dAtual, new Map())
          const seguidores = matriz.get(dAtual)!
          seguidores.set(dProximo, (seguidores.get(dProximo) || 0) + 1)
        }
      }
    }

    return matriz
  }

  scoresMarkov(): Map<number, number> {
    const ultimoConcurso = this.concursos[this.concursos.length - 1]
    if (!ultimoConcurso) {
      const empty = new Map<number, number>()
      for (let i = DEZENA_MIN; i <= DEZENA_MAX; i++) empty.set(i, 0)
      return empty
    }

    const dezenasReferencia = [ultimoConcurso.dezena1, ultimoConcurso.dezena2,
                               ultimoConcurso.dezena3, ultimoConcurso.dezena4,
                               ultimoConcurso.dezena5, ultimoConcurso.dezena6]

    const matriz = this.calcularMatrizMarkov()
    const scores = new Map<number, number>()

    for (const dRef of dezenasReferencia) {
      const seguidores = matriz.get(dRef)
      if (seguidores) {
        for (const [dSeguidor, contagem] of seguidores) {
          scores.set(dSeguidor, (scores.get(dSeguidor) || 0) + contagem)
        }
      }
    }

    const maxScore = Math.max(...scores.values()) || 1
    const normalized = new Map<number, number>()
    for (let i = DEZENA_MIN; i <= DEZENA_MAX; i++) {
      normalized.set(i, (scores.get(i) || 0) / maxScore)
    }
    return normalized
  }

  calcularCoocorrencias(): Map<string, number> {
    const cooc = new Map<string, number>()

    for (const concurso of this.concursos) {
      const dezenas = [concurso.dezena1, concurso.dezena2, concurso.dezena3,
                      concurso.dezena4, concurso.dezena5, concurso.dezena6].sort((a, b) => a - b)

      for (let i = 0; i < dezenas.length; i++) {
        for (let j = i + 1; j < dezenas.length; j++) {
          const par = `${dezenas[i]}-${dezenas[j]}`
          cooc.set(par, (cooc.get(par) || 0) + 1)
        }
      }
    }

    return cooc
  }

  scoresCoocorrencia(): Map<number, number> {
    const cooc = this.calcularCoocorrencias()
    const topPares = Array.from(cooc.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 100)

    const scores = new Map<number, number>()
    for (const [par, contagem] of topPares) {
      const [d1, d2] = par.split('-').map(Number)
      scores.set(d1, (scores.get(d1) || 0) + contagem)
      scores.set(d2, (scores.get(d2) || 0) + contagem)
    }

    const maxScore = Math.max(...scores.values()) || 1
    const normalized = new Map<number, number>()
    for (let i = DEZENA_MIN; i <= DEZENA_MAX; i++) {
      normalized.set(i, (scores.get(i) || 0) / maxScore)
    }
    return normalized
  }

  calcularAtrasos(): Map<number, number> {
    const atrasos = new Map<number, number>()

    for (let d = DEZENA_MIN; d <= DEZENA_MAX; d++) {
      let atraso = 0
      for (let i = this.concursos.length - 1; i >= 0; i--) {
        const dezenas = [this.concursos[i].dezena1, this.concursos[i].dezena2,
                        this.concursos[i].dezena3, this.concursos[i].dezena4,
                        this.concursos[i].dezena5, this.concursos[i].dezena6]
        if (dezenas.includes(d)) break
        atraso++
      }
      atrasos.set(d, atraso)
    }

    return atrasos
  }

  scoresAtraso(): Map<number, number> {
    const atrasos = this.calcularAtrasos()
    const maxAtraso = Math.max(...atrasos.values()) || 1
    const scores = new Map<number, number>()
    for (let i = DEZENA_MIN; i <= DEZENA_MAX; i++) {
      scores.set(i, atrasos.get(i)! / maxAtraso)
    }
    return scores
  }
}

export class GeradorJogos {
  private rng: () => number

  constructor(
    private analisador: AnalisadorMegaSena,
    seed?: number
  ) {
    this.rng = seed ? this.seededRandom(seed) : Math.random
  }

  private seededRandom(seed: number) {
    let x = Math.sin(seed) * 10000
    return () => {
      x = Math.sin(x) * 10000
      return x - Math.floor(x)
    }
  }

  private verificarBalanceamento(dezenas: number[]): boolean {
    const pares = dezenas.filter(d => d % 2 === 0).length
    if (pares !== 3) return false

    const faixas = [0, 0, 0] // 1-20, 21-40, 41-60
    for (const d of dezenas) {
      if (d <= 20) faixas[0]++
      else if (d <= 40) faixas[1]++
      else faixas[2]++
    }

    return faixas.every(count => count >= 1 && count <= 3)
  }

  gerarUniforme(numerosFixos: number[] = [], numerosRemovidos: number[] = []): number[] {
    const disponiveis = []
    for (let i = DEZENA_MIN; i <= DEZENA_MAX; i++) {
      if (!numerosFixos.includes(i) && !numerosRemovidos.includes(i)) {
        disponiveis.push(i)
      }
    }

    // Adicionar números fixos
    const jogo = [...numerosFixos]

    // Completar com números aleatórios
    while (jogo.length < TAMANHO_JOGO && disponiveis.length > 0) {
      const idx = Math.floor(this.rng() * disponiveis.length)
      jogo.push(disponiveis.splice(idx, 1)[0])
    }

    return jogo.sort((a, b) => a - b)
  }

  gerarPorScores(
    pesos: Record<string, number>,
    forcarBalanceamento: boolean = false,
    numerosFixos: number[] = [],
    numerosRemovidos: number[] = []
  ): number[] {
    const scoresFreq = pesos.frequencia > 0 ? this.analisador.scoresFrequencia() : new Map()
    const scoresMarkov = pesos.markov > 0 ? this.analisador.scoresMarkov() : new Map()
    const scoresCooc = pesos.coocorrencia > 0 ? this.analisador.scoresCoocorrencia() : new Map()
    const scoresAtraso = pesos.atraso > 0 ? this.analisador.scoresAtraso() : new Map()

    const scoresCombinados = new Map<number, number>()
    for (let d = DEZENA_MIN; d <= DEZENA_MAX; d++) {
      if (numerosFixos.includes(d) || numerosRemovidos.includes(d)) continue

      const score =
        (scoresFreq.get(d) || 0) * pesos.frequencia +
        (scoresMarkov.get(d) || 0) * pesos.markov +
        (scoresCooc.get(d) || 0) * pesos.coocorrencia +
        (scoresAtraso.get(d) || 0) * pesos.atraso +
        0.1 // base mínima

      scoresCombinados.set(d, score)
    }

    const dezenasDisponiveis = Array.from(scoresCombinados.keys())
    const pesosArray = Array.from(scoresCombinados.values())

    for (let tentativa = 0; tentativa < 500; tentativa++) {
      const selecionadas = new Set<number>()

      // Adicionar números fixos
      for (const fixo of numerosFixos) {
        selecionadas.add(fixo)
      }

      // Selecionar números restantes
      while (selecionadas.size < TAMANHO_JOGO && dezenasDisponiveis.length > 0) {
        const idx = this.weightedChoice(pesosArray)
        const escolhida = dezenasDisponiveis[idx]
        if (!selecionadas.has(escolhida)) {
          selecionadas.add(escolhida)
          // Remover da lista para não escolher novamente
          dezenasDisponiveis.splice(idx, 1)
          pesosArray.splice(idx, 1)
        }
      }

      if (selecionadas.size >= TAMANHO_JOGO) {
        const jogo = Array.from(selecionadas).sort((a, b) => a - b)
        if (!forcarBalanceamento || this.verificarBalanceamento(jogo)) {
          return jogo
        }
      }
    }

    // Fallback para uniforme
    return this.gerarUniforme(numerosFixos, numerosRemovidos)
  }

  private weightedChoice(weights: number[]): number {
    const total = weights.reduce((sum, w) => sum + w, 0)
    let random = this.rng() * total

    for (let i = 0; i < weights.length; i++) {
      random -= weights[i]
      if (random <= 0) return i
    }

    return weights.length - 1
  }

  gerarJogos(
    quantidade: number,
    algoritmos: string[],
    forcarBalanceamento: boolean = false,
    numerosFixos: number[] = [],
    numerosRemovidos: number[] = []
  ): { jogos: number[][], algoritmosUsados: string[] } {
    const jogos: number[][] = []
    const algoritmosUsados: string[] = []
    const jogosGerados = new Set<string>()

    // Algoritmos de score
    const algoritmosScore = algoritmos.filter(a =>
      ['frequencia', 'markov', 'coocorrencia', 'atraso'].includes(a)
    )

    // Fase 1: Gerar jogos puros para cada algoritmo
    for (const alg of algoritmosScore) {
      if (jogos.length >= quantidade) break

      const pesos: Record<string, number> = {
        frequencia: alg === 'frequencia' ? 1 : 0,
        markov: alg === 'markov' ? 1 : 0,
        coocorrencia: alg === 'coocorrencia' ? 1 : 0,
        atraso: alg === 'atraso' ? 1 : 0,
      }

      const jogo = this.gerarPorScores(pesos, forcarBalanceamento, numerosFixos, numerosRemovidos)
      const jogoStr = jogo.join(',')

      if (!jogosGerados.has(jogoStr)) {
        jogosGerados.add(jogoStr)
        jogos.push(jogo)
        algoritmosUsados.push(alg.charAt(0).toUpperCase() + alg.slice(1))
      }
    }

    // Fase 2: Gerar jogos mistos se ainda precisa
    if (jogos.length < quantidade && algoritmosScore.length > 0) {
      const pesoBase = 1.0 / algoritmosScore.length
      const pesosMix: Record<string, number> = {
        frequencia: algoritmosScore.includes('frequencia') ? pesoBase : 0,
        markov: algoritmosScore.includes('markov') ? pesoBase : 0,
        coocorrencia: algoritmosScore.includes('coocorrencia') ? pesoBase : 0,
        atraso: algoritmosScore.includes('atraso') ? pesoBase : 0,
      }

      for (let i = jogos.length; i < quantidade; i++) {
        const jogo = this.gerarPorScores(pesosMix, forcarBalanceamento, numerosFixos, numerosRemovidos)
        const jogoStr = jogo.join(',')

        if (!jogosGerados.has(jogoStr)) {
          jogosGerados.add(jogoStr)
          jogos.push(jogo)
          algoritmosUsados.push('Misto')
        }
      }
    }

    // Fallback: completar com uniforme
    while (jogos.length < quantidade) {
      const jogo = this.gerarUniforme(numerosFixos, numerosRemovidos)
      const jogoStr = jogo.join(',')

      if (!jogosGerados.has(jogoStr)) {
        jogosGerados.add(jogoStr)
        jogos.push(jogo)
        algoritmosUsados.push('Uniforme')
      }
    }

    return { jogos, algoritmosUsados }
  }
}
