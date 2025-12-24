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

function getGrupoFromDezena(dezena: number): number {
  if (dezena === 0) return 25
  return Math.ceil(dezena / 4)
}

function getAnimalFromGrupo(grupo: number): string {
  return ANIMAIS[grupo] || 'Desconhecido'
}

export async function GET() {
  try {
    // Tentar buscar de múltiplas fontes
    const sources = [
      'https://www.ojogodobicho.com/deu_no_poste.htm',
      'https://www.eojogodobicho.com/deu-no-poste.html'
    ]

    let html = ''
    let sourceUsed = ''

    for (const source of sources) {
      try {
        const response = await fetch(source, {
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
          },
          next: { revalidate: 300 } // Cache por 5 minutos
        })

        if (response.ok) {
          html = await response.text()
          sourceUsed = source
          break
        }
      } catch {
        continue
      }
    }

    if (!html) {
      return NextResponse.json({
        success: false,
        error: 'Não foi possível buscar resultados',
        message: 'Tente novamente mais tarde',
        resultados: []
      }, { status: 503 })
    }

    const $ = cheerio.load(html)
    const resultados: ResultadoBicho[] = []

    // Parsing para ojogodobicho.com
    if (sourceUsed.includes('ojogodobicho')) {
      // Buscar tabelas de resultados
      $('table').each((_, table) => {
        const $table = $(table)
        const headerText = $table.find('th, td').first().text().trim()

        // Identificar extrações (PTM, PT, PTV, PTN, COR, etc.)
        const extracaoMatch = headerText.match(/(PTM|PT|PTV|PTN|PPT|COR|FED)/i)
        if (!extracaoMatch) return

        const extracao = extracaoMatch[1].toUpperCase()
        const premios: ResultadoBicho['premios'] = []

        // Buscar milhares na tabela
        $table.find('tr').each((rowIndex, row) => {
          const cells = $(row).find('td')
          if (cells.length >= 2) {
            const posicaoText = $(cells[0]).text().trim()
            const milharText = $(cells[1]).text().trim()

            const posicao = parseInt(posicaoText.replace(/[^\d]/g, ''))
            const milhar = milharText.replace(/[^\d]/g, '').padStart(4, '0')

            if (posicao >= 1 && posicao <= 7 && milhar.length === 4) {
              const dezena = parseInt(milhar.slice(-2))
              const grupo = getGrupoFromDezena(dezena)
              premios.push({
                posicao,
                milhar,
                grupo,
                animal: getAnimalFromGrupo(grupo)
              })
            }
          }
        })

        if (premios.length > 0) {
          resultados.push({
            extracao,
            horario: getHorarioExtracao(extracao),
            data: new Date().toLocaleDateString('pt-BR'),
            premios: premios.sort((a, b) => a.posicao - b.posicao)
          })
        }
      })

      // Fallback: buscar padrão de números diretamente
      if (resultados.length === 0) {
        const textContent = $('body').text()

        // Regex para encontrar padrões de resultados
        const extracoes = ['PPT', 'PTM', 'PT', 'PTV', 'PTN', 'COR']

        for (const ext of extracoes) {
          const regex = new RegExp(`${ext}[^\\d]*(\\d{4})[^\\d]*(\\d{4})[^\\d]*(\\d{4})[^\\d]*(\\d{4})[^\\d]*(\\d{4})`, 'i')
          const match = textContent.match(regex)

          if (match) {
            const premios: ResultadoBicho['premios'] = []
            for (let i = 1; i <= 5; i++) {
              const milhar = match[i].padStart(4, '0')
              const dezena = parseInt(milhar.slice(-2))
              const grupo = getGrupoFromDezena(dezena)
              premios.push({
                posicao: i,
                milhar,
                grupo,
                animal: getAnimalFromGrupo(grupo)
              })
            }
            resultados.push({
              extracao: ext,
              horario: getHorarioExtracao(ext),
              data: new Date().toLocaleDateString('pt-BR'),
              premios
            })
          }
        }
      }
    }

    // Se ainda não conseguiu, tentar parsing genérico
    if (resultados.length === 0) {
      // Buscar qualquer sequência de 5 números de 4 dígitos
      const allText = $('body').text()
      const milharPattern = /\b(\d{4})\b/g
      const milhares = [...allText.matchAll(milharPattern)].map(m => m[1])

      if (milhares.length >= 5) {
        const premios: ResultadoBicho['premios'] = []
        for (let i = 0; i < Math.min(5, milhares.length); i++) {
          const milhar = milhares[i]
          const dezena = parseInt(milhar.slice(-2))
          const grupo = getGrupoFromDezena(dezena)
          premios.push({
            posicao: i + 1,
            milhar,
            grupo,
            animal: getAnimalFromGrupo(grupo)
          })
        }
        resultados.push({
          extracao: 'Último',
          horario: '--:--',
          data: new Date().toLocaleDateString('pt-BR'),
          premios
        })
      }
    }

    return NextResponse.json({
      success: true,
      fonte: sourceUsed,
      atualizadoEm: new Date().toISOString(),
      resultados
    })

  } catch (error) {
    console.error('Erro ao buscar resultados:', error)
    return NextResponse.json({
      success: false,
      error: 'Erro interno',
      message: error instanceof Error ? error.message : 'Erro desconhecido',
      resultados: []
    }, { status: 500 })
  }
}

function getHorarioExtracao(extracao: string): string {
  const horarios: Record<string, string> = {
    'PPT': '09:30',
    'PTM': '11:30',
    'PT': '14:30',
    'PTV': '16:30',
    'PTN': '18:30',
    'COR': '21:30',
    'FED': '19:00'
  }
  return horarios[extracao.toUpperCase()] || '--:--'
}
