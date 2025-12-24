import { NextResponse } from 'next/server'
import * as cheerio from 'cheerio'

interface ResultadoBicho {
  extracao: string
  horario: string
  data: string
  premios: {
    posicao: number
    milhar: string
    grupo: number
    animal: string
  }[]
}

const ANIMAIS = [
  '', 'Avestruz', 'Águia', 'Burro', 'Borboleta', 'Cachorro',
  'Cabra', 'Carneiro', 'Camelo', 'Cobra', 'Coelho',
  'Cavalo', 'Elefante', 'Galo', 'Gato', 'Jacaré',
  'Leão', 'Macaco', 'Porco', 'Pavão', 'Peru',
  'Touro', 'Tigre', 'Urso', 'Veado', 'Vaca'
]

const HORARIOS: Record<string, string> = {
  'PPT': '09:20',
  'PTM': '11:20',
  'PT': '14:20',
  'PTV': '16:20',
  'PTN': '18:20',
  'COR': '21:20',
  'FED': '19:00'
}

function getGrupoFromDezena(dezena: number): number {
  if (dezena === 0) return 25 // 00 = Vaca (grupo 25)
  return Math.ceil(dezena / 4)
}

function getAnimalFromGrupo(grupo: number): string {
  return ANIMAIS[grupo] || 'Desconhecido'
}

// Extrai grupo do formato "milhar-grupo" (ex: "9009-78" ou "778-20")
function parseResultado(texto: string): { milhar: string, grupo: number } | null {
  // Formato: XXXX-GG (milhar-grupo)
  const match = texto.match(/(\d{4})-(\d{1,2})/)
  if (match) {
    return {
      milhar: match[1],
      grupo: parseInt(match[2])
    }
  }

  // Formato: XXX-GG (centena-grupo)
  const matchCentena = texto.match(/(\d{3})-(\d{1,2})/)
  if (matchCentena) {
    return {
      milhar: '0' + matchCentena[1],
      grupo: parseInt(matchCentena[2])
    }
  }

  return null
}

export async function GET() {
  try {
    // Buscar do site
    const response = await fetch('https://www.ojogodobicho.com/deu_no_poste.htm', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
      },
      cache: 'no-store'
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const html = await response.text()
    const $ = cheerio.load(html)
    const resultados: ResultadoBicho[] = []

    // Buscar a tabela principal de resultados
    // O site geralmente tem uma tabela com colunas: Pos, PPT, PTM, PT, PTV, PTN, COR

    const extracoes = ['PPT', 'PTM', 'PT', 'PTV', 'PTN', 'COR']
    const resultadosPorExtracao: Record<string, ResultadoBicho['premios']> = {}

    // Inicializar
    extracoes.forEach(ext => {
      resultadosPorExtracao[ext] = []
    })

    // Buscar tabelas
    $('table').each((_, table) => {
      const $table = $(table)
      const headers: string[] = []

      // Pegar cabeçalhos
      $table.find('tr').first().find('th, td').each((_, cell) => {
        headers.push($(cell).text().trim().toUpperCase())
      })

      // Verificar se é a tabela de resultados (tem as colunas das extrações)
      const hasExtracoes = extracoes.some(ext => headers.includes(ext))
      if (!hasExtracoes) return

      // Encontrar índice de cada extração
      const extracaoIndices: Record<string, number> = {}
      extracoes.forEach(ext => {
        const idx = headers.findIndex(h => h === ext)
        if (idx >= 0) extracaoIndices[ext] = idx
      })

      // Processar linhas de dados (1º ao 7º)
      $table.find('tr').slice(1).each((rowIdx, row) => {
        const cells = $(row).find('td')
        const posicaoText = $(cells[0]).text().trim()
        const posicao = parseInt(posicaoText.replace(/[^\d]/g, ''))

        if (posicao < 1 || posicao > 7) return

        // Para cada extração, pegar o valor da coluna correspondente
        Object.entries(extracaoIndices).forEach(([ext, colIdx]) => {
          const cellText = $(cells[colIdx]).text().trim()

          // Ignorar se for 0000-0 ou vazio
          if (!cellText || cellText.includes('0000-0') || cellText === '0000' || cellText === '0') {
            return
          }

          const resultado = parseResultado(cellText)
          if (resultado && resultado.grupo >= 1 && resultado.grupo <= 25) {
            resultadosPorExtracao[ext].push({
              posicao,
              milhar: resultado.milhar,
              grupo: resultado.grupo,
              animal: getAnimalFromGrupo(resultado.grupo)
            })
          }
        })
      })
    })

    // Montar resultados finais (apenas extrações com dados válidos)
    extracoes.forEach(ext => {
      const premios = resultadosPorExtracao[ext]
      if (premios.length > 0) {
        // Verificar se não são todos 0000
        const temDadosValidos = premios.some(p => p.milhar !== '0000')
        if (temDadosValidos) {
          resultados.push({
            extracao: ext,
            horario: HORARIOS[ext] || '--:--',
            data: new Date().toLocaleDateString('pt-BR'),
            premios: premios.sort((a, b) => a.posicao - b.posicao)
          })
        }
      }
    })

    // Se não encontrou na tabela, tentar parsing alternativo
    if (resultados.length === 0) {
      const bodyText = $('body').text()

      // Tentar encontrar padrões de milhares com grupos
      extracoes.forEach(ext => {
        // Buscar seção da extração
        const regex = new RegExp(`${ext}[\\s\\S]*?(\\d{4}-\\d{1,2})[\\s\\S]*?(\\d{4}-\\d{1,2})[\\s\\S]*?(\\d{4}-\\d{1,2})[\\s\\S]*?(\\d{4}-\\d{1,2})[\\s\\S]*?(\\d{4}-\\d{1,2})`, 'i')
        const match = bodyText.match(regex)

        if (match) {
          const premios: ResultadoBicho['premios'] = []
          for (let i = 1; i <= 5; i++) {
            const resultado = parseResultado(match[i])
            if (resultado && resultado.grupo >= 1 && resultado.grupo <= 25 && resultado.milhar !== '0000') {
              premios.push({
                posicao: i,
                milhar: resultado.milhar,
                grupo: resultado.grupo,
                animal: getAnimalFromGrupo(resultado.grupo)
              })
            }
          }

          if (premios.length > 0) {
            resultados.push({
              extracao: ext,
              horario: HORARIOS[ext] || '--:--',
              data: new Date().toLocaleDateString('pt-BR'),
              premios
            })
          }
        }
      })
    }

    // Ordenar por horário (mais recente primeiro)
    const ordemExtracoes = ['COR', 'PTN', 'PTV', 'PT', 'PTM', 'PPT']
    resultados.sort((a, b) => {
      return ordemExtracoes.indexOf(a.extracao) - ordemExtracoes.indexOf(b.extracao)
    })

    return NextResponse.json({
      success: true,
      fonte: 'ojogodobicho.com',
      atualizadoEm: new Date().toISOString(),
      resultados
    })

  } catch (error) {
    console.error('Erro ao buscar resultados:', error)
    return NextResponse.json({
      success: false,
      error: 'Erro ao buscar resultados',
      message: error instanceof Error ? error.message : 'Erro desconhecido',
      resultados: []
    }, { status: 500 })
  }
}
