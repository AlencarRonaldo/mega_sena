'use client'

import { useState, useEffect, useMemo } from 'react'
import {
  Tabs, TabsContent, TabsList, TabsTrigger
} from '@/components/ui/tabs'
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import {
  Shuffle, TrendingUp, Clock, Users, Target, CheckCircle,
  Sparkles, Settings, Database, Activity, Save, Copy, Sun, Moon
} from 'lucide-react'
import {
  buscarTodosConcursos, buscarUltimoConcurso, salvarJogo, Concurso
} from '@/lib/supabase'
import { AnalisadorMegaSena, GeradorJogos } from '@/lib/algoritmos'

export default function MegaSenaApp() {
  const [concursos, setConcursos] = useState<Concurso[]>([])
  const [ultimoConcurso, setUltimoConcurso] = useState<Concurso | null>(null)
  const [loading, setLoading] = useState(true)
  const [analisador, setAnalisador] = useState<AnalisadorMegaSena | null>(null)
  const [gerador, setGerador] = useState<GeradorJogos | null>(null)

  // Configurações
  const [anosAnalise, setAnosAnalise] = useState([3])
  const [quantidadeJogos, setQuantidadeJogos] = useState(6)
  const [algoritmos, setAlgoritmos] = useState({
    frequencia: true,
    markov: true,
    coocorrencia: false,
    atraso: false,
    balanceado: true,
    uniforme: false
  })
  const [numerosFixos, setNumerosFixos] = useState<number[]>([])
  const [numerosRemovidos, setNumerosRemovidos] = useState<number[]>([])

  // Resultados
  const [jogosGerados, setJogosGerados] = useState<number[][]>([])
  const [algoritmosUsados, setAlgoritmosUsados] = useState<string[]>([])
  const [estatisticas, setEstatisticas] = useState<any>(null)
  const [jogoConferir, setJogoConferir] = useState<string>("")
  const [resultadoConferencia, setResultadoConferencia] = useState<{
    jaSaiu: boolean
    melhorAcerto: number
    ocorrencias: { concurso: number; data: string; acertos: number }[]
  } | null>(null)

  // Modal de boas-vindas
  const [showWelcomeModal, setShowWelcomeModal] = useState(false)
  const [tabInicial, setTabInicial] = useState<string>('gerar')

  // Modal de resultado do bicho ampliado
  const [resultadoSelecionado, setResultadoSelecionado] = useState<{
    extracao: string
    horario: string
    data: string
    premios: { posicao: number; milhar: string; grupo: number; animal: string }[]
  } | null>(null)

  // Jogo do Bicho
  const [palpiteBicho, setPalpiteBicho] = useState<{
    grupo: number
    animal: string
    emoji: string
    dezena: string
    centena: string
    milhar: string
  } | null>(null)

  // Palpite do Dia - calculado uma vez baseado na data (não muda)
  const [palpiteDoDia, setPalpiteDoDia] = useState<{
    grupo: number
    animal: string
    emoji: string
    milhar: string
    justificativa: string
  }[] | null>(null)

  const ANIMAIS_BICHO = [
    { nome: "Avestruz", emoji: "🦢" },
    { nome: "Águia", emoji: "🦅" },
    { nome: "Burro", emoji: "🫏" },
    { nome: "Borboleta", emoji: "🦋" },
    { nome: "Cachorro", emoji: "🐕" },
    { nome: "Cabra", emoji: "🐐" },
    { nome: "Carneiro", emoji: "🐏" },
    { nome: "Camelo", emoji: "🐫" },
    { nome: "Cobra", emoji: "🐍" },
    { nome: "Coelho", emoji: "🐇" },
    { nome: "Cavalo", emoji: "🐴" },
    { nome: "Elefante", emoji: "🐘" },
    { nome: "Galo", emoji: "🐓" },
    { nome: "Gato", emoji: "🐱" },
    { nome: "Jacaré", emoji: "🐊" },
    { nome: "Leão", emoji: "🦁" },
    { nome: "Macaco", emoji: "🐒" },
    { nome: "Porco", emoji: "🐷" },
    { nome: "Pavão", emoji: "🦚" },
    { nome: "Peru", emoji: "🦃" },
    { nome: "Touro", emoji: "🐂" },
    { nome: "Tigre", emoji: "🐅" },
    { nome: "Urso", emoji: "🐻" },
    { nome: "Veado", emoji: "🦌" },
    { nome: "Vaca", emoji: "🐄" },
  ]

  // Dados completos dos grupos com milhares e centenas (da planilha Excel)
  const GRUPOS_BICHO_COMPLETO: Record<number, { milhares: string[], centenas: string[] }> = {
    1: { milhares: ["3101","5301","7202","5302","2203","6304","9601","4501","2701","4102","7902","5403","5104","3204","2601"], centenas: ["201","503","101","603","701","903","401","704","402","104","502","904","602","804","702","504"] },
    2: { milhares: ["9106","7206","3905","4105","7805","3808","5208","2908","5807","3705","2406","5607","5506","1207","9407","7108"], centenas: ["606","207","708","205","706","907","708","705","505","806","707","308","305","906","507","508"] },
    3: { milhares: ["1510","6509","3201","7712","8511","6311","0011","3410","9610","3209","5109","4109","2711","6110","5412","3912"], centenas: ["209","211","309","109","710","610","310","111","011","812","712","212","506","409","810","811"] },
    4: { milhares: ["9116","5814","7216","3515","4115","7915","3816","5315","2715","3714","2714","5414","5413","1213","9113","7213"], centenas: ["716","714","016","416","215","515","715","815","614","814","913","013","113","213","316","214"] },
    5: { milhares: ["3519","8617","3819","5720","7320","9020","1520","4319","3719","2817","3518","2018","1318","0918","2417","6517"], centenas: ["720","518","320","020","520","619","719","519","919","018","318","918","417","517","617","817"] },
    6: { milhares: ["6724","9822","1824","3124","5324","3223","7523","0123","2723","3722","5622","0021","0121","2023","2022"], centenas: ["724","821","824","124","324","323","223","123","423","921","121","023","022","622","522","822"] },
    7: { milhares: ["3228","3128","7426","8426","5828","9028","4127","8527","3027","1927","1626","3026","5025","1525","0625"], centenas: ["128","426","728","828","028","127","327","527","027","526","026","326","025","625","725","525"] },
    8: { milhares: ["3229","2031","3129","7429","8529","2430","6530","1230","2030","4531","2331","6731","4032","7532","8932","6432"], centenas: ["129","131","429","031","529","531","929","631","430","332","530","032","630","932","930","532"] },
    9: { milhares: ["2634","3136","4234","3836","5534","4636","7134","6336","2133","8135","6833","9235","2733","7535","2135","6433"], centenas: ["734","735","634","835","334","935","034","435","533","036","633","636","433","736","033","436"] },
    10: { milhares: ["6237","3436","0337","1637","2937","7638","8438","9138","0538","4539","5739","6839","1440","2640","3040","4840"], centenas: ["137","339","237","039","437","139","537","239","738","540","238","740","338","940","938","340"] },
    11: { milhares: ["9141","8643","7641","6443","5741","4843","3241","2943","1642","9244","8142","7344","6542","5744","4342","3544"], centenas: ["041","743","541","441","341","442","842","242","742","343","043","543","144","044","944","844"] },
    12: { milhares: ["8645","7047","6945","6145","2345","0646","2146","4346","6649","5347","3647","1847","1348","3248","5748","7948"], centenas: ["745","347","845","045","445","746","046","846","546","147","247","547","548","048","648","148"] },
    13: { milhares: ["1849","9251","3449","2149","4749","5350","6450","8650","0950","1651","2751","3951","4852","5452","7952","6852"], centenas: ["949","151","549","551","049","349","150","250","550","850","451","351","752","252","552","352"] },
    14: { milhares: ["9653","6155","0953","1453","2853","3754","4154","5854","7954","8355","7855","9455","3256","5356","6956","8756"], centenas: ["753","055","853","353","653","654","054","654","754","155","755","255","056","656","856","156"] },
    15: { milhares: ["1857","9259","9657","2057","8057","3358","6158","4558","9258","9459","8559","7759","1560","2860","4960","8360"], centenas: ["057","259","957","857","257","258","558","158","258","759","159","359","760","960","660","560"] },
    16: { milhares: ["7246","8963","8461","7661","9261","1862","3762","6462","7362","1463","2763","4863","9164","1864","3464","6364"], centenas: ["261","463","361","061","161","562","262","962","062","763","363","663","564","764","064"] },
    17: { milhares: ["2265","7467","3465","7665","3065","9366","2566","9766","8966","7367","7567","3867","2468","3268","5768","7368"], centenas: ["868","866","768","068","168","567","267","367","467","166","566","366","065","265","465","365"] },
    18: { milhares: ["3169","1271","7469","8769","2869","9570","1570","3870","9070","1571","2771","5971","1072","3872","4772","5372"], centenas: ["669","971","569","369","069","570","470","370","670","871","471","171","072","672","972","872"] },
    19: { milhares: ["5473","9875","5773","8273","4573","2474","3574","8274","9675","6275","7675","1376","1576","2876","5776"], centenas: ["973","175","676","273","373","274","174","674","074","775","575","875","376","476","676","576"] },
    20: { milhares: ["4177","5379","5377","6977","2477","3678","4278","7478","1578","5179","8679","8279","9580","1780","6380","2480"], centenas: ["877","780","277","077","177","678","178","878","978","880","680","080","779","079","479","579"] },
    21: { milhares: ["3781","4683","3281","9681","7881","3482","3582","9782","3782","4583","5783","5383","1684","1584","3284","9584"], centenas: ["384","282","484","284","784","581","181","681","381","682","382","482","683","983","583","283"] },
    22: { milhares: ["3785","4187","3285","3485","9385","1386","1586","9786","0686","5587","5687","3487","1088","7388","7588","9788"], centenas: ["385","487","685","085","185","186","286","486","586","287","787","387","088","188","688","288"] },
    23: { milhares: ["1389","7491","3489","3789","5989","7690","7890","4290","4190","7291","5691","6991","3292","3792","5392","4092"], centenas: ["389","291","289","189","089","190","490","590","690","591","191","391","292","192","892","992"] },
    24: { milhares: ["4093","3195","4193","4293","6593","6694","9894","3594","2394","7495","7695","7895","7596","2696","1596","7896"], centenas: ["193","295","393","093","993","894","794","494","094","395","595","195","696","296","396","496"] },
    25: { milhares: ["9397","7199","9597","8097","3197","9898","3498","2398","7698","7499","3899","4399","7497","6800","9900","5000"], centenas: ["597","799","497","397","297","398","698","998","298","699","599","099","500","800","900","700"] },
  }

  // Estado para milhar anterior (estratégia da planilha)
  const [milharAnterior, setMilharAnterior] = useState('')
  const [grupoSelecionado, setGrupoSelecionado] = useState(1)
  const [palpitesMilhar, setPalpitesMilhar] = useState<string[] | null>(null)

  // Função para gerar palpites baseado na milhar anterior (lógica da planilha +3)
  const gerarPalpitesPorMilhar = (milhar: string): string[] => {
    if (milhar.length !== 4 || !/^\d+$/.test(milhar)) return []

    const ultimoDigito = parseInt(milhar[3])
    const k34 = ultimoDigito + 3
    const k35 = k34 + 3
    const k36 = k35 + 3
    const k37 = k36 + 3

    const i23 = k34 % 10
    const i24 = k35 % 10
    const i25 = k36 % 10
    const i26 = k37 % 10

    return [
      `${i23}${i24}`,           // Dezena 1
      `${i25}${i26}`,           // Dezena 2
      `${i26}${i25}`,           // Dezena 3 (invertida)
      `${i24}${i25}`,           // Dezena 4
      String(i23 + i24 + i25 + i26).padStart(2, '0'), // Dezena 5 (soma)
    ]
  }

  // Tabela de puxadas - qual animal "puxa" quais outros (baseado em tradição)
  const PUXADAS: Record<number, number[]> = {
    1: [25, 2, 13, 19, 20],    // Avestruz puxa Vaca, Águia, Galo, Pavão, Peru
    2: [10, 1, 13, 19, 20],    // Águia puxa Coelho, Avestruz, Galo, Pavão, Peru
    3: [11, 12, 21, 24, 10],   // Burro puxa Cavalo, Elefante, Touro, Veado, Coelho
    4: [6, 12, 14, 16, 5],     // Borboleta puxa Cabra, Elefante, Gato, Leão, Cachorro
    5: [13, 14, 8, 17, 18],    // Cachorro puxa Galo, Gato, Camelo, Macaco, Porco
    6: [7, 17, 12, 21, 22],    // Cabra puxa Carneiro, Macaco, Elefante, Touro, Tigre
    7: [6, 10, 25],            // Carneiro puxa Cabra, Coelho, Vaca
    8: [5, 12, 23],            // Camelo puxa Cachorro, Elefante, Urso
    9: [15, 18, 3, 14],        // Cobra puxa Jacaré, Porco, Burro, Gato
    10: [7, 2, 3],             // Coelho puxa Carneiro, Águia, Burro
    11: [3, 12, 21],           // Cavalo puxa Burro, Elefante, Touro
    12: [3, 6, 8, 11],         // Elefante puxa Burro, Cabra, Camelo, Cavalo
    13: [1, 2, 4, 5],          // Galo puxa Avestruz, Águia, Borboleta, Cachorro
    14: [4, 5, 9, 7],          // Gato puxa Borboleta, Cachorro, Cobra, Carneiro
    15: [9, 6],                // Jacaré puxa Cobra, Cabra
    16: [4, 22],               // Leão puxa Borboleta, Tigre
    17: [6, 5],                // Macaco puxa Cabra, Cachorro
    18: [5, 9],                // Porco puxa Cachorro, Cobra
    19: [1, 2, 5],             // Pavão puxa Avestruz, Águia, Cachorro
    20: [1, 2],                // Peru puxa Avestruz, Águia
    21: [3, 6, 11],            // Touro puxa Burro, Cabra, Cavalo
    22: [6, 16],               // Tigre puxa Cabra, Leão
    23: [6, 8],                // Urso puxa Cabra, Camelo
    24: [3],                   // Veado puxa Burro
    25: [1, 7],                // Vaca puxa Avestruz, Carneiro
  }

  // Estado para estratégia - 4 estratégias baseadas em análise estatística real
  const [estrategiaBicho, setEstrategiaBicho] = useState<
    'quente' | 'frio' | 'puxada' | 'ciclo'
  >('quente')

  // ================== DADOS ESTATÍSTICOS REAIS (Set-Dez/2025) ==================

  // GRUPOS QUENTES - Baseado em frequência real dos últimos 3 meses
  // Peru (20): 8 ocorrências, Avestruz (01): 8, Burro (03): 6, Águia/Cabra/Carneiro/Camelo: 5 cada
  const NUMEROS_QUENTES = [20, 1, 3, 2, 6, 7, 8] // Ordenado por frequência real

  // GRUPOS FRIOS - Baseado em dias de atraso (maior potencial de sair)
  // Porco (18): 90 dias, Gato (14): 76 dias, Cavalo (11): 70 dias
  const NUMEROS_FRIOS = [18, 14, 11, 15, 12, 13] // Ordenado por dias de atraso

  // Dados de frequência por grupo (análise Set-Dez/2025)
  const FREQUENCIA_GRUPOS: Record<number, { freq: number; atraso: number; prob: number }> = {
    1: { freq: 8, atraso: 0, prob: 8.9 },   // Avestruz - quente
    2: { freq: 5, atraso: 5, prob: 5.6 },   // Águia
    3: { freq: 6, atraso: 0, prob: 6.7 },   // Burro - quente
    4: { freq: 3, atraso: 26, prob: 3.3 },  // Borboleta
    5: { freq: 4, atraso: 4, prob: 4.4 },   // Cachorro
    6: { freq: 5, atraso: 23, prob: 5.6 },  // Cabra
    7: { freq: 5, atraso: 0, prob: 5.6 },   // Carneiro
    8: { freq: 5, atraso: 1, prob: 5.6 },   // Camelo
    9: { freq: 4, atraso: 4, prob: 4.4 },   // Cobra
    10: { freq: 3, atraso: 9, prob: 3.3 },  // Coelho
    11: { freq: 1, atraso: 70, prob: 1.1 }, // Cavalo - FRIO (alto potencial)
    12: { freq: 2, atraso: 5, prob: 2.2 },  // Elefante
    13: { freq: 2, atraso: 1, prob: 2.2 },  // Galo
    14: { freq: 1, atraso: 76, prob: 1.1 }, // Gato - FRIO (alto potencial)
    15: { freq: 1, atraso: 28, prob: 1.1 }, // Jacaré
    16: { freq: 3, atraso: 39, prob: 3.3 }, // Leão
    17: { freq: 4, atraso: 23, prob: 4.4 }, // Macaco
    18: { freq: 1, atraso: 90, prob: 1.1 }, // Porco - MUITO FRIO (altíssimo potencial!)
    19: { freq: 3, atraso: 5, prob: 3.3 },  // Pavão
    20: { freq: 8, atraso: 0, prob: 8.9 },  // Peru - quente
    21: { freq: 4, atraso: 1, prob: 4.4 },  // Touro
    22: { freq: 4, atraso: 1, prob: 4.4 },  // Tigre
    23: { freq: 4, atraso: 1, prob: 4.4 },  // Urso
    24: { freq: 4, atraso: 28, prob: 4.4 }, // Veado
    25: { freq: 4, atraso: 9, prob: 4.4 },  // Vaca
  }

  // Puxadas REAIS observadas na análise estatística
  const PUXADAS_REAIS: Record<number, { grupos: number[]; confianca: number }> = {
    1: { grupos: [7, 8, 9, 5], confianca: 0.4 },      // Avestruz → grupos 7-9 (40%)
    2: { grupos: [20, 1, 19], confianca: 0.35 },      // Águia → aves
    3: { grupos: [21, 11, 6], confianca: 0.38 },      // Burro → trabalho
    5: { grupos: [17, 18, 8], confianca: 0.33 },      // Cachorro → domésticos
    6: { grupos: [7, 21, 22], confianca: 0.35 },      // Cabra → força
    7: { grupos: [6, 5, 25], confianca: 0.32 },       // Carneiro
    8: { grupos: [23, 12, 5], confianca: 0.36 },      // Camelo → grandes
    9: { grupos: [3, 15, 14], confianca: 0.42 },      // Cobra → rastejantes
    13: { grupos: [1, 2, 20], confianca: 0.40 },      // Galo → aves
    16: { grupos: [22, 4, 12], confianca: 0.38 },     // Leão → força
    20: { grupos: [1, 2, 13], confianca: 0.45 },      // Peru → aves (forte!)
    21: { grupos: [6, 3, 11], confianca: 0.40 },      // Touro → trabalho
    22: { grupos: [16, 6, 23], confianca: 0.38 },     // Tigre → força
    23: { grupos: [8, 12, 6], confianca: 0.35 },      // Urso → grandes
    24: { grupos: [3, 21, 11], confianca: 0.38 },     // Veado → trabalho
  }

  // Padrões ocultos detectados na análise
  const PADROES_OCULTOS = {
    // Grupos que tendem a sair no fim do mês (dias 23-31)
    fimDeMes: [21, 23, 9, 16],
    // Grupos que tendem a sair no início do mês (dias 1-10)
    inicioDeMes: [1, 7, 22, 5],
    // Puxada +3: quando grupo X sai, X+3 tem 28% de chance no dia seguinte
    puxadaMais3: 0.28,
    // Milhares palindrômicas têm 2x mais chance
    palindromicaMultiplier: 2,
    // Ciclo de 15 dias para grupos 16 (Leão) e alguns outros
    ciclo15Dias: [16, 12, 15],
  }

  // Milhares históricas mais sorteadas por grupo (baseado na análise)
  const MILHARES_FREQUENTES: Record<number, string[]> = {
    1: ['1001', '7303', '6102', '8004', '3101'],
    2: ['7305', '5506', '4008', '2806', '0806'],
    3: ['9009', '3610', '6011', '0212', '6710'],
    6: ['3221', '2823', '9824', '5724', '1421'],
    7: ['9226', '4727', '4328', '6926', '6627'],
    8: ['2029', '0332', '6332', '7893', '3230'],
    9: ['3536', '0533', '3233', '8334', '9235'],
    18: ['8869', '6918', '0018', '5918', '1918'], // Porco - frio
    20: ['7677', '2778', '0380', '4178', '0078'],
    21: ['1081', '6983', '8083', '7782', '3482'],
    22: ['2186', '6986', '1385', '9963', '4788'],
    23: ['4492', '0091', '7290', '2690', '4190'],
  }

  // Animais por dia da semana (tradição popular)
  const ANIMAIS_DIA_SEMANA: Record<number, number[]> = {
    0: [1, 13, 19],    // Domingo: Avestruz, Galo, Pavão (aves)
    1: [16, 22, 12],   // Segunda: Leão, Tigre, Elefante (força)
    2: [9, 15, 14],    // Terça: Cobra, Jacaré, Gato (astúcia)
    3: [17, 10, 7],    // Quarta: Macaco, Coelho, Carneiro (agilidade)
    4: [21, 11, 3],    // Quinta: Touro, Cavalo, Burro (trabalho)
    5: [18, 5, 6],     // Sexta: Porco, Cachorro, Cabra (fartura)
    6: [4, 2, 20],     // Sábado: Borboleta, Águia, Peru (liberdade)
  }

  // Gera milhar para um grupo específico
  const gerarMilharParaGrupo = (grupo: number): string => {
    if (MILHARES_FREQUENTES[grupo]) {
      const milhares = MILHARES_FREQUENTES[grupo]
      return milhares[Math.floor(Math.random() * milhares.length)]
    }
    // Fallback: gera milhar aleatória do grupo
    const dezenaBase = ((grupo - 1) * 4) + 1
    const dezena = dezenaBase + Math.floor(Math.random() * 4)
    const prefixo = Math.floor(Math.random() * 10)
    const milhar = prefixo * 1000 + Math.floor(Math.random() * 10) * 100 + dezena
    return milhar.toString().padStart(4, '0')
  }

  // Gera o Palpite do Dia (fixo baseado na data - não muda ao clicar)
  const gerarPalpiteDoDia = () => {
    const hoje = new Date()
    const dia = hoje.getDate()

    // Seed baseada na data para resultados consistentes
    const seed = hoje.getFullYear() * 10000 + (hoje.getMonth() + 1) * 100 + dia
    const seededRandom = (offset: number) => {
      const x = Math.sin(seed + offset) * 10000
      return x - Math.floor(x)
    }

    const palpites: typeof palpiteDoDia = []

    // 1. FRIO - Grupo mais atrasado (Porco 90d, Gato 76d, Cavalo 70d)
    const grupoFrio = NUMEROS_FRIOS[Math.floor(seededRandom(1) * 3)] // Top 3 frios
    const animalFrio = ANIMAIS_BICHO[grupoFrio - 1]
    palpites.push({
      grupo: grupoFrio,
      animal: animalFrio.nome,
      emoji: animalFrio.emoji,
      milhar: MILHARES_FREQUENTES[grupoFrio]?.[0] || gerarMilharParaGrupo(grupoFrio),
      justificativa: `${FREQUENCIA_GRUPOS[grupoFrio]?.atraso || 0} dias atrasado`
    })

    // 2. QUENTE - Grupo mais frequente (Peru 8.9%, Avestruz 8.9%, Burro 6.7%)
    const grupoQuente = NUMEROS_QUENTES[Math.floor(seededRandom(2) * 3)] // Top 3 quentes
    const animalQuente = ANIMAIS_BICHO[grupoQuente - 1]
    palpites.push({
      grupo: grupoQuente,
      animal: animalQuente.nome,
      emoji: animalQuente.emoji,
      milhar: MILHARES_FREQUENTES[grupoQuente]?.[0] || gerarMilharParaGrupo(grupoQuente),
      justificativa: `${FREQUENCIA_GRUPOS[grupoQuente]?.prob || 0}% frequência`
    })

    // 3. CICLO - Baseado no dia do mês
    let grupoCiclo: number
    if (dia >= 23) {
      grupoCiclo = PADROES_OCULTOS.fimDeMes[Math.floor(seededRandom(3) * PADROES_OCULTOS.fimDeMes.length)]
    } else if (dia <= 10) {
      grupoCiclo = PADROES_OCULTOS.inicioDeMes[Math.floor(seededRandom(3) * PADROES_OCULTOS.inicioDeMes.length)]
    } else {
      grupoCiclo = PADROES_OCULTOS.ciclo15Dias[Math.floor(seededRandom(3) * PADROES_OCULTOS.ciclo15Dias.length)]
    }
    const animalCiclo = ANIMAIS_BICHO[grupoCiclo - 1]
    palpites.push({
      grupo: grupoCiclo,
      animal: animalCiclo.nome,
      emoji: animalCiclo.emoji,
      milhar: MILHARES_FREQUENTES[grupoCiclo]?.[0] || gerarMilharParaGrupo(grupoCiclo),
      justificativa: dia >= 23 ? 'Padrão fim de mês' : dia <= 10 ? 'Padrão início de mês' : 'Ciclo 15 dias'
    })

    setPalpiteDoDia(palpites)
  }

  const gerarPalpiteBicho = () => {
    let grupo: number
    const hoje = new Date()
    const dia = hoje.getDate()

    switch (estrategiaBicho) {
      case 'quente':
        // Escolhe entre os números "quentes" com peso pela frequência real
        const pesosQuentes = NUMEROS_QUENTES.map(g => FREQUENCIA_GRUPOS[g]?.freq || 1)
        const totalPesoQuente = pesosQuentes.reduce((a, b) => a + b, 0)
        let randQuente = Math.random() * totalPesoQuente
        for (let i = 0; i < NUMEROS_QUENTES.length; i++) {
          randQuente -= pesosQuentes[i]
          if (randQuente <= 0) {
            grupo = NUMEROS_QUENTES[i]
            break
          }
        }
        grupo = grupo! || NUMEROS_QUENTES[0]
        break

      case 'frio':
        // Escolhe entre os números "frios" com peso pelo atraso
        const pesosFrios = NUMEROS_FRIOS.map(g => FREQUENCIA_GRUPOS[g]?.atraso || 1)
        const totalPesoFrio = pesosFrios.reduce((a, b) => a + b, 0)
        let randFrio = Math.random() * totalPesoFrio
        for (let i = 0; i < NUMEROS_FRIOS.length; i++) {
          randFrio -= pesosFrios[i]
          if (randFrio <= 0) {
            grupo = NUMEROS_FRIOS[i]
            break
          }
        }
        grupo = grupo! || NUMEROS_FRIOS[0]
        break

      case 'puxada':
        // Usa puxadas REAIS baseadas na análise estatística
        if (palpiteBicho) {
          const puxadaReal = PUXADAS_REAIS[palpiteBicho.grupo]
          if (puxadaReal) {
            grupo = puxadaReal.grupos[Math.floor(Math.random() * puxadaReal.grupos.length)]
          } else {
            const puxaveis = PUXADAS[palpiteBicho.grupo] || []
            grupo = puxaveis.length > 0
              ? puxaveis[Math.floor(Math.random() * puxaveis.length)]
              : Math.floor(Math.random() * 25) + 1
          }
        } else {
          // Sem palpite anterior, usa grupo quente como base
          grupo = NUMEROS_QUENTES[Math.floor(Math.random() * 3)]
        }
        break

      case 'ciclo':
        // Baseado no padrão do dia do mês
        if (dia >= 23) {
          grupo = PADROES_OCULTOS.fimDeMes[Math.floor(Math.random() * PADROES_OCULTOS.fimDeMes.length)]
        } else if (dia <= 10) {
          grupo = PADROES_OCULTOS.inicioDeMes[Math.floor(Math.random() * PADROES_OCULTOS.inicioDeMes.length)]
        } else {
          grupo = PADROES_OCULTOS.ciclo15Dias[Math.floor(Math.random() * PADROES_OCULTOS.ciclo15Dias.length)]
        }
        break

      default:
        grupo = NUMEROS_QUENTES[0]
    }

    const animal = ANIMAIS_BICHO[grupo - 1]
    const milharStr = MILHARES_FREQUENTES[grupo]
      ? MILHARES_FREQUENTES[grupo][Math.floor(Math.random() * MILHARES_FREQUENTES[grupo].length)]
      : gerarMilharParaGrupo(grupo)

    const milhar = parseInt(milharStr)
    const centena = milhar % 1000
    const dezena = milhar % 100

    setPalpiteBicho({
      grupo,
      animal: animal.nome,
      emoji: animal.emoji,
      dezena: dezena.toString().padStart(2, '0'),
      centena: centena.toString().padStart(3, '0'),
      milhar: milhar.toString().padStart(4, '0'),
    })
  }

  const [resultadosBicho, setResultadosBicho] = useState<{
    success: boolean
    fonte?: string
    atualizadoEm?: string
    resultados: {
      extracao: string
      horario: string
      data: string
      premios: { posicao: number; milhar: string; grupo: number; animal: string }[]
    }[]
  } | null>(null)
  const [loadingBicho, setLoadingBicho] = useState(true)

  const buscarResultadosBicho = async () => {
    setLoadingBicho(true)
    try {
      const response = await fetch('/api/bicho')
      const data = await response.json()
      setResultadosBicho(data)
    } catch (error) {
      console.error('Erro ao buscar resultados do bicho:', error)
      setResultadosBicho({ success: false, resultados: [] })
    } finally {
      setLoadingBicho(false)
    }
  }

  // Tema claro/escuro
  const [tema, setTema] = useState<'dark' | 'light'>('dark')
  useEffect(() => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem('mega_tema') : null
    if (stored === 'light' || stored === 'dark') setTema(stored)
  }, [])
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('mega_tema', tema)
    }
  }, [tema])
  const isDark = tema === 'dark'

  // Verificar se deve mostrar modal de boas-vindas
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const visited = localStorage.getItem('mega_visited')
      if (!visited) {
        setShowWelcomeModal(true)
      }
    }
  }, [])

  const handleWelcomeChoice = (choice: 'megasena' | 'bicho') => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('mega_visited', 'true')
    }
    setShowWelcomeModal(false)
    if (choice === 'bicho') {
      setTabInicial('bicho')
    } else {
      setTabInicial('gerar')
    }
  }

  useEffect(() => {
    carregarDados()
    buscarResultadosBicho() // Buscar resultados do bicho ao carregar
    gerarPalpiteDoDia() // Gerar palpite do dia (fixo baseado na data)
  }, [])

  // Auto-atualização do jogo do bicho a cada 5 minutos
  useEffect(() => {
    const interval = setInterval(() => {
      buscarResultadosBicho()
    }, 5 * 60 * 1000) // 5 minutos

    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (concursos.length > 0) {
      const analisadorTemp = new AnalisadorMegaSena(concursos).filtrarPorAnos(anosAnalise[0])
      setAnalisador(analisadorTemp)
      setGerador(new GeradorJogos(analisadorTemp))
      calcularEstatisticas(analisadorTemp)
    }
  }, [concursos, anosAnalise])

  const carregarDados = async () => {
    try {
      const [todosConcursos, ultimo] = await Promise.all([
        buscarTodosConcursos(),
        buscarUltimoConcurso()
      ])
      setConcursos(todosConcursos)
      setUltimoConcurso(ultimo)
    } catch (error) {
      console.error('Erro ao carregar dados:', error)
    } finally {
      setLoading(false)
    }
  }

  const calcularEstatisticas = (analisador: AnalisadorMegaSena) => {
    const freq = analisador.calcularFrequencias()
    const atrasos = analisador.calcularAtrasos()

    const topFrequentes = Array.from(freq.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([dezena, frequencia]) => ({ dezena, frequencia }))

    const topAtrasados = Array.from(atrasos.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([dezena, atraso]) => ({ dezena, atraso }))

    setEstatisticas({
      totalConcursos: analisador['concursos'].length,
      topFrequentes,
      topAtrasados,
      frequenciasChart: Array.from(freq.entries()).map(([dezena, frequencia]) => ({
        dezena: dezena.toString(),
        frequencia
      }))
    })
  }

  const algoritmosAtivos = useMemo(
    () => Object.entries(algoritmos).filter(([, ativo]) => ativo).map(([k]) => k),
    [algoritmos]
  )

  const gerarJogos = () => {
    if (!gerador) return
    if (algoritmosAtivos.length === 0) {
      alert('Selecione pelo menos um algoritmo!')
      return
    }
    const resultado = gerador.gerarJogos(
      quantidadeJogos,
      algoritmosAtivos,
      algoritmos.balanceado,
      numerosFixos,
      numerosRemovidos
    )
    setJogosGerados(resultado.jogos)
    setAlgoritmosUsados(resultado.algoritmosUsados)
  }

  const salvarJogos = async () => {
    if (jogosGerados.length === 0) return
    try {
      for (let i = 0; i < jogosGerados.length; i++) {
        await salvarJogo(jogosGerados[i], [algoritmosUsados[i] || 'Misto'])
      }
      alert(`${jogosGerados.length} jogos salvos com sucesso!`)
    } catch (error) {
      console.error('Erro ao salvar jogos:', error)
      alert('Erro ao salvar jogos!')
    }
  }

  const conferirJogo = (jogo: number[]) => {
    if (!concursos.length) return {
      jaSaiu: false,
      melhorAcerto: 0,
      ocorrencias: []
    }
    const ocorrencias = concursos.map(c => {
      const dezenas = [c.dezena1, c.dezena2, c.dezena3, c.dezena4, c.dezena5, c.dezena6]
      const acertos = jogo.filter(n => dezenas.includes(n)).length
      return { concurso: c.numero, data: c.data, acertos }
    }).filter(o => o.acertos > 0)

    const melhorAcerto = ocorrencias.reduce((m, o) => Math.max(m, o.acertos), 0)
    const jaSaiu = ocorrencias.some(o => o.acertos === 6)
    const relevantes = ocorrencias.filter(o => o.acertos >= 4).slice(0, 5)

    return { jaSaiu, melhorAcerto, ocorrencias: relevantes }
  }

  const handleInput = (
    value: string,
    addFn: (n: number) => void
  ) => {
    const nums = value.split(',')
      .map(n => parseInt(n.trim()))
      .filter(n => n >= 1 && n <= 60)
    nums.forEach(addFn)
  }

  const removerNumeroFixo = (n: number) => setNumerosFixos(numerosFixos.filter(i => i !== n))
  const removerNumeroRemovido = (n: number) => setNumerosRemovidos(numerosRemovidos.filter(i => i !== n))

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0f1419] via-[#0f1a26] to-[#111827] text-white">
        <div className="text-center space-y-3">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-emerald-400 border-t-transparent mx-auto" />
          <p className="text-emerald-200">Carregando dados...</p>
        </div>
      </div>
    )
  }

  const bgMain = isDark
    ? "bg-gradient-to-br from-[#0f1419] via-[#0f1a26] to-[#111827] text-white"
    : "bg-gradient-to-br from-slate-50 via-white to-slate-100 text-slate-900"
  const cardClass = isDark ? "bg-white/5 border-white/10 shadow-lg" : "bg-white border border-slate-200 shadow-lg"
  const inputClass = isDark ? "bg-white/5 border-white/10 text-white placeholder:text-white/50" : "bg-white border-slate-300 text-slate-900 placeholder:text-slate-400"
  const badgeHighlight = isDark ? "bg-emerald-500/20 text-emerald-100" : "bg-emerald-100 text-emerald-800"
  const sliderClass = "w-full accent-emerald-400 h-2 rounded-lg " + (isDark ? "bg-white/10" : "bg-emerald-100")

  return (
    <div className={`min-h-screen ${bgMain}`}>
      {/* Modal de Resultado Ampliado */}
      {resultadoSelecionado && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={() => setResultadoSelecionado(null)}>
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" />

          {/* Modal */}
          <div
            className={`relative w-full max-w-2xl rounded-3xl overflow-hidden shadow-2xl ${isDark ? "bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border border-amber-500/30" : "bg-white border border-amber-200"}`}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className={`px-6 py-5 ${isDark ? "bg-gradient-to-r from-amber-500/20 to-orange-500/20 border-b border-amber-500/20" : "bg-gradient-to-r from-amber-100 to-orange-100 border-b border-amber-200"}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`w-14 h-14 rounded-2xl ${isDark ? "bg-amber-500/30" : "bg-amber-200"} flex items-center justify-center text-3xl`}>
                    🦁
                  </div>
                  <div>
                    <div className={`text-2xl font-black ${isDark ? "text-white" : "text-slate-900"}`}>
                      {resultadoSelecionado.extracao}
                    </div>
                    <div className={`text-sm ${isDark ? "text-amber-200" : "text-amber-700"}`}>
                      {resultadoSelecionado.horario} • {resultadoSelecionado.data}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setResultadoSelecionado(null)}
                  className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${isDark ? "bg-white/10 hover:bg-white/20 text-white" : "bg-slate-100 hover:bg-slate-200 text-slate-600"}`}
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Prêmios */}
            <div className="p-6">
              <div className="grid grid-cols-5 gap-3">
                {resultadoSelecionado.premios.slice(0, 5).map((premio) => {
                  const animalInfo = ANIMAIS_BICHO[premio.grupo - 1]
                  return (
                    <div
                      key={premio.posicao}
                      className={`rounded-2xl p-4 text-center ${isDark ? "bg-gradient-to-br from-amber-500/20 to-orange-500/10 border border-amber-500/30" : "bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200"}`}
                    >
                      <div className={`text-xs font-bold mb-2 ${isDark ? "text-amber-400" : "text-amber-600"}`}>
                        {premio.posicao}º PRÊMIO
                      </div>
                      <div className="text-4xl mb-2">
                        {animalInfo?.emoji || '🐾'}
                      </div>
                      <div className={`text-3xl font-black mb-1 ${isDark ? "text-white" : "text-slate-900"}`}>
                        {premio.milhar}
                      </div>
                      <div className={`text-sm font-bold ${isDark ? "text-amber-300" : "text-amber-700"}`}>
                        G{premio.grupo.toString().padStart(2, '0')}
                      </div>
                      <div className={`text-xs font-medium ${isDark ? "text-amber-100" : "text-amber-800"}`}>
                        {premio.animal}
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Prêmios extras se houver */}
              {resultadoSelecionado.premios.length > 5 && (
                <div className="mt-4 pt-4 border-t border-amber-500/20">
                  <div className={`text-xs font-bold mb-3 ${isDark ? "text-amber-400" : "text-amber-600"}`}>
                    PRÊMIOS EXTRAS
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {resultadoSelecionado.premios.slice(5).map((premio) => (
                      <div
                        key={premio.posicao}
                        className={`rounded-xl p-3 flex items-center gap-3 ${isDark ? "bg-white/5" : "bg-slate-50"}`}
                      >
                        <span className={`text-xs font-bold ${isDark ? "text-amber-400" : "text-amber-600"}`}>
                          {premio.posicao}º
                        </span>
                        <span className={`font-mono font-bold ${isDark ? "text-white" : "text-slate-900"}`}>
                          {premio.milhar}
                        </span>
                        <span className={`text-sm ${isDark ? "text-amber-200" : "text-amber-700"}`}>
                          {premio.animal}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className={`px-6 py-4 text-center border-t ${isDark ? "border-white/5" : "border-slate-100"}`}>
              <p className={`text-xs ${isDark ? "text-slate-500" : "text-slate-400"}`}>
                Clique fora do modal ou no X para fechar
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Boas-vindas */}
      {showWelcomeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" />

          {/* Modal */}
          <div className={`relative w-full max-w-lg rounded-3xl overflow-hidden shadow-2xl ${isDark ? "bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border border-white/10" : "bg-white"}`}>
            {/* Header com gradiente */}
            <div className={`px-6 py-8 text-center ${isDark ? "bg-gradient-to-r from-emerald-500/20 via-transparent to-amber-500/20" : "bg-gradient-to-r from-emerald-50 via-white to-amber-50"}`}>
              <div className="flex justify-center gap-4 mb-4">
                <span className="text-5xl animate-bounce" style={{ animationDelay: '0ms' }}>🍀</span>
                <span className="text-5xl animate-bounce" style={{ animationDelay: '150ms' }}>🦁</span>
              </div>
              <h2 className={`text-2xl md:text-3xl font-black mb-2 ${isDark ? "text-white" : "text-slate-900"}`}>
                Bem-vindo!
              </h2>
              <p className={`text-sm ${isDark ? "text-slate-400" : "text-slate-600"}`}>
                O que você gostaria de acessar hoje?
              </p>
            </div>

            {/* Opções */}
            <div className="p-6 space-y-4">
              {/* Opção Mega-Sena */}
              <button
                onClick={() => handleWelcomeChoice('megasena')}
                className={`w-full p-5 rounded-2xl text-left transition-all transform hover:scale-[1.02] ${
                  isDark
                    ? "bg-gradient-to-br from-emerald-500/20 to-green-500/10 border-2 border-emerald-500/30 hover:border-emerald-400"
                    : "bg-gradient-to-br from-emerald-50 to-green-50 border-2 border-emerald-200 hover:border-emerald-400"
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-14 h-14 rounded-2xl ${isDark ? "bg-emerald-500/30" : "bg-emerald-100"} flex items-center justify-center text-3xl`}>
                    🍀
                  </div>
                  <div className="flex-1">
                    <div className={`text-lg font-bold ${isDark ? "text-white" : "text-slate-900"}`}>
                      Mega-Sena
                    </div>
                    <div className={`text-sm ${isDark ? "text-emerald-200" : "text-emerald-700"}`}>
                      Gerar jogos inteligentes com IA
                    </div>
                  </div>
                  <div className={`text-2xl ${isDark ? "text-emerald-400" : "text-emerald-600"}`}>
                    →
                  </div>
                </div>
              </button>

              {/* Opção Jogo do Bicho */}
              <button
                onClick={() => handleWelcomeChoice('bicho')}
                className={`w-full p-5 rounded-2xl text-left transition-all transform hover:scale-[1.02] ${
                  isDark
                    ? "bg-gradient-to-br from-amber-500/20 to-orange-500/10 border-2 border-amber-500/30 hover:border-amber-400"
                    : "bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 hover:border-amber-400"
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-14 h-14 rounded-2xl ${isDark ? "bg-amber-500/30" : "bg-amber-100"} flex items-center justify-center text-3xl`}>
                    🦁
                  </div>
                  <div className="flex-1">
                    <div className={`text-lg font-bold ${isDark ? "text-white" : "text-slate-900"}`}>
                      Jogo do Bicho
                    </div>
                    <div className={`text-sm ${isDark ? "text-amber-200" : "text-amber-700"}`}>
                      Resultados, tabelas e palpites
                    </div>
                  </div>
                  <div className={`text-2xl ${isDark ? "text-amber-400" : "text-amber-600"}`}>
                    →
                  </div>
                </div>
              </button>
            </div>

            {/* Footer */}
            <div className={`px-6 py-4 text-center border-t ${isDark ? "border-white/5" : "border-slate-100"}`}>
              <p className={`text-xs ${isDark ? "text-slate-500" : "text-slate-400"}`}>
                Você pode alternar entre as opções a qualquer momento usando as abas
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Hero - Redesign Premium */}
        <div className={`mb-8 rounded-3xl ${isDark ? "bg-gradient-to-br from-slate-900/90 via-slate-800/50 to-slate-900/90 border border-white/10" : "bg-white border border-slate-200"} shadow-2xl backdrop-blur-xl overflow-hidden`}>
          {/* Header com gradiente */}
          <div className={`px-6 py-4 ${isDark ? "bg-gradient-to-r from-emerald-500/10 via-transparent to-amber-500/10 border-b border-white/5" : "bg-gradient-to-r from-emerald-50 via-white to-amber-50 border-b border-slate-100"}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-2xl ${isDark ? "bg-gradient-to-br from-emerald-500 to-green-400" : "bg-gradient-to-br from-emerald-500 to-green-400"} flex items-center justify-center shadow-lg shadow-emerald-500/30`}>
                  <span className="text-2xl">🍀</span>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className={`text-2xl md:text-3xl font-bold tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>
                      Mega-Sena
                    </h1>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${isDark ? "bg-emerald-500/20 text-emerald-300" : "bg-emerald-100 text-emerald-700"}`}>
                      PRO
                    </span>
                  </div>
                  <p className={`text-sm ${isDark ? "text-slate-400" : "text-slate-500"}`}>
                    Gerador Inteligente com IA
                  </p>
                </div>
              </div>
              <button
                aria-label="Alternar tema"
                onClick={() => setTema(isDark ? 'light' : 'dark')}
                className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                  isDark ? "bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white" : "bg-slate-100 hover:bg-slate-200 text-slate-600"
                }`}
              >
                {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Cards de Resultados */}
          <div className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Card Mega-Sena */}
              {ultimoConcurso && (
                <div className={`rounded-2xl ${isDark ? "bg-gradient-to-br from-emerald-500/10 to-green-500/5 border border-emerald-500/20" : "bg-gradient-to-br from-emerald-50 to-green-50 border border-emerald-200"} p-5`}>
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <span className={`text-xs font-medium uppercase tracking-wider ${isDark ? "text-emerald-400" : "text-emerald-600"}`}>
                        Último Resultado
                      </span>
                      <div className="flex items-baseline gap-2 mt-1">
                        <span className={`text-3xl font-black ${isDark ? "text-white" : "text-slate-900"}`}>
                          #{ultimoConcurso.numero}
                        </span>
                        <span className={`text-sm ${isDark ? "text-slate-400" : "text-slate-500"}`}>
                          {new Date(ultimoConcurso.data).toLocaleDateString('pt-BR')}
                        </span>
                      </div>
                    </div>
                    <div className={`w-10 h-10 rounded-xl ${isDark ? "bg-emerald-500/20" : "bg-emerald-100"} flex items-center justify-center`}>
                      <Sparkles className={`w-5 h-5 ${isDark ? "text-emerald-400" : "text-emerald-600"}`} />
                    </div>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    {[ultimoConcurso.dezena1, ultimoConcurso.dezena2, ultimoConcurso.dezena3,
                      ultimoConcurso.dezena4, ultimoConcurso.dezena5, ultimoConcurso.dezena6].map((n, i) => (
                      <div
                        key={n}
                        className={`w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-green-400 text-white font-bold text-lg flex items-center justify-center shadow-lg shadow-emerald-500/30 transform hover:scale-105 transition-transform`}
                        style={{ animationDelay: `${i * 100}ms` }}
                      >
                        {n.toString().padStart(2, '0')}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Card Jogo do Bicho */}
              {(() => {
                const ultimoResultado = resultadosBicho?.success && resultadosBicho.resultados.length > 0
                  ? resultadosBicho.resultados[0]
                  : null
                return (
                  <div
                    onClick={() => ultimoResultado && setResultadoSelecionado(ultimoResultado)}
                    className={`rounded-2xl ${isDark ? "bg-gradient-to-br from-amber-500/10 to-orange-500/5 border border-amber-500/20 hover:border-amber-500/50" : "bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 hover:border-amber-400"} p-5 ${ultimoResultado ? "cursor-pointer transition-all hover:scale-[1.01]" : ""}`}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs font-medium uppercase tracking-wider ${isDark ? "text-amber-400" : "text-amber-600"}`}>
                            Jogo do Bicho
                          </span>
                          {loadingBicho ? (
                            <div className="animate-spin rounded-full h-3 w-3 border-2 border-amber-400 border-t-transparent" />
                          ) : (
                            <span className={`text-[10px] px-1.5 py-0.5 rounded ${isDark ? "bg-amber-500/20 text-amber-300" : "bg-amber-100 text-amber-700"}`}>
                              🔄 5min
                            </span>
                          )}
                        </div>
                        {ultimoResultado && (
                          <div className="flex items-baseline gap-2 mt-1">
                            <span className={`text-2xl font-black ${isDark ? "text-white" : "text-slate-900"}`}>
                              {ultimoResultado.extracao}
                            </span>
                            <span className={`text-sm ${isDark ? "text-slate-400" : "text-slate-500"}`}>
                              {ultimoResultado.horario} • {ultimoResultado.data}
                            </span>
                          </div>
                        )}
                      </div>
                      <div className={`w-10 h-10 rounded-xl ${isDark ? "bg-amber-500/20" : "bg-amber-100"} flex items-center justify-center`}>
                        <span className="text-xl">{ultimoResultado ? "🔍" : "🦁"}</span>
                      </div>
                    </div>
                    {ultimoResultado ? (
                      <div className="flex gap-2 flex-wrap">
                        {ultimoResultado.premios.slice(0, 5).map((premio, i) => (
                          <div
                            key={premio.posicao}
                            className={`flex flex-col items-center p-2 rounded-xl ${isDark ? "bg-black/20" : "bg-white/80"} min-w-[52px]`}
                          >
                            <span className={`text-[10px] font-medium ${isDark ? "text-amber-400/80" : "text-amber-600"}`}>
                              {premio.posicao}º
                            </span>
                            <span className={`w-11 h-9 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 text-white font-bold flex items-center justify-center text-sm shadow-md shadow-amber-500/30`}>
                              {premio.milhar}
                            </span>
                            <span className={`text-[10px] font-medium mt-1 ${isDark ? "text-amber-200" : "text-amber-800"}`}>
                              {premio.animal.slice(0, 6)}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className={`text-sm py-4 text-center ${isDark ? "text-amber-100/60" : "text-amber-600"}`}>
                        {loadingBicho ? "Carregando..." : "Aguardando dados..."}
                      </div>
                    )}
                  </div>
                )
              })()}
            </div>

            {/* Status Bar */}
            <div className={`mt-5 pt-4 border-t ${isDark ? "border-white/5" : "border-slate-100"}`}>
              <div className="flex flex-wrap gap-4">
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${isDark ? "bg-emerald-500/10" : "bg-emerald-50"}`}>
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className={`text-xs font-medium ${isDark ? "text-emerald-300" : "text-emerald-700"}`}>
                    Supabase • {concursos.length} concursos
                  </span>
                </div>
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${isDark ? "bg-white/5" : "bg-slate-50"}`}>
                  <Activity className={`w-3.5 h-3.5 ${isDark ? "text-slate-400" : "text-slate-500"}`} />
                  <span className={`text-xs ${isDark ? "text-slate-300" : "text-slate-600"}`}>
                    {algoritmosAtivos.join(', ')}
                  </span>
                </div>
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${isDark ? "bg-white/5" : "bg-slate-50"}`}>
                  <Database className={`w-3.5 h-3.5 ${isDark ? "text-slate-400" : "text-slate-500"}`} />
                  <span className={`text-xs ${isDark ? "text-slate-300" : "text-slate-600"}`}>
                    {concursos.length > 0 && `${new Date(concursos[0].data).getFullYear()} - ${new Date(concursos[concursos.length - 1].data).getFullYear()}`}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <Tabs defaultValue={tabInicial} key={tabInicial} className="w-full">
          <TabsList className={`grid w-full grid-cols-4 ${isDark ? "bg-white/5 text-emerald-100 border border-white/10" : "bg-white text-emerald-700 border border-slate-200"}`}>
            <TabsTrigger value="gerar">🎰 Gerar Jogos</TabsTrigger>
            <TabsTrigger value="estatisticas">📊 Estatísticas</TabsTrigger>
            <TabsTrigger value="jogos">💾 Meus Jogos</TabsTrigger>
            <TabsTrigger value="bicho">🦁 Jogo do Bicho</TabsTrigger>
          </TabsList>

          {/* Gerar */}
          <TabsContent value="gerar" className="mt-6 space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Config */}
              <div className="space-y-4">
                <Card className={cardClass}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="w-5 h-5 text-emerald-400" />
                      Configurações
                    </CardTitle>
                    <CardDescription className={isDark ? "" : "text-slate-600"}>Controle fino dos algoritmos</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <Label className={isDark ? "text-emerald-50" : "text-slate-700"}>Anos de análise</Label>
                        <div className="flex items-center gap-2">
                          <Input
                            type="number"
                            min={1}
                            max={10}
                            value={anosAnalise[0]}
                            onChange={(e) => {
                              const v = Math.min(10, Math.max(1, Number(e.target.value) || 1))
                              setAnosAnalise([v])
                            }}
                            className={`w-16 h-9 text-sm ${inputClass}`}
                          />
                          <span className={`px-2 py-1 rounded-md font-semibold ${badgeHighlight}`}>
                            {anosAnalise[0]}
                          </span>
                        </div>
                      </div>
                      <input
                        type="range"
                        min={1}
                        max={10}
                        step={1}
                        value={anosAnalise[0]}
                        onChange={(e) => setAnosAnalise([Number(e.target.value)])}
                        className={sliderClass}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <Label className={isDark ? "text-emerald-50" : "text-slate-700"}>Quantidade de jogos</Label>
                        <div className="flex items-center gap-2">
                          <Input
                            type="number"
                            min={1}
                            max={20}
                            value={quantidadeJogos}
                            onChange={(e) => {
                              const v = Math.min(20, Math.max(1, Number(e.target.value) || 1))
                              setQuantidadeJogos(v)
                            }}
                            className={`w-16 h-9 text-sm ${inputClass}`}
                          />
                          <span className={`px-2 py-1 rounded-md font-semibold ${badgeHighlight}`}>
                            {quantidadeJogos}
                          </span>
                        </div>
                      </div>
                      <input
                        type="range"
                        min={1}
                        max={20}
                        step={1}
                        value={quantidadeJogos}
                        onChange={(e) => setQuantidadeJogos(Number(e.target.value))}
                        className={sliderClass}
                      />
                    </div>
                    <Separator className="bg-white/10" />
                    <div className="space-y-3">
                      <Label className={isDark ? "text-emerald-100 text-sm" : "text-slate-700 text-sm"}>Algoritmos</Label>
                      {[
                        { id: 'freq', label: 'Frequência', icon: <TrendingUp className="w-4 h-4" />, key: 'frequencia' },
                        { id: 'markov', label: 'Markov', icon: <Shuffle className="w-4 h-4" />, key: 'markov' },
                        { id: 'cooc', label: 'Coocorrência', icon: <Users className="w-4 h-4" />, key: 'coocorrencia' },
                        { id: 'atraso', label: 'Atrasados', icon: <Clock className="w-4 h-4" />, key: 'atraso' },
                        { id: 'balanceado', label: 'Balanceado', icon: <Settings className="w-4 h-4" />, key: 'balanceado' },
                        { id: 'uniforme', label: 'Uniforme', icon: <Shuffle className="w-4 h-4" />, key: 'uniforme' },
                      ].map(item => (
                        <div key={item.id} className="flex items-center space-x-2">
                          <Checkbox
                            id={item.id}
                            checked={(algoritmos as any)[item.key]}
                            onCheckedChange={(checked) => setAlgoritmos({
                              ...algoritmos,
                              [item.key]: checked as boolean
                            })}
                          />
                          <Label htmlFor={item.id} className={`flex items-center gap-2 text-sm ${isDark ? "text-emerald-50" : "text-slate-800"}`}>
                            {item.icon} {item.label}
                          </Label>
                        </div>
                      ))}
                    </div>
                    <Separator className="bg-white/10" />
                    <div className="space-y-3">
                      <Label className="text-emerald-100">Números Fixos</Label>
                      <div className="flex flex-wrap gap-1">
                        {numerosFixos.map(num => (
                          <Badge
                            key={num}
                            variant="outline"
                            className="bg-emerald-500/20 border-emerald-400/50 text-emerald-100 cursor-pointer"
                            onClick={() => removerNumeroFixo(num)}
                          >
                            {num.toString().padStart(2, '0')}
                          </Badge>
                        ))}
                      </div>
                      <Input
                        className="bg-white/5 border-white/10 text-white placeholder:text-white/50"
                        placeholder="Ex: 5,12,23"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleInput(e.currentTarget.value, (n) => {
                              if (!numerosFixos.includes(n) && !numerosRemovidos.includes(n)) {
                                setNumerosFixos([...numerosFixos, n])
                              }
                            })
                            e.currentTarget.value = ''
                          }
                        }}
                      />
                    </div>
                    <div className="space-y-3">
                      <Label className="text-emerald-100">Números Removidos</Label>
                      <div className="flex flex-wrap gap-1">
                        {numerosRemovidos.map(num => (
                          <Badge
                            key={num}
                            variant="destructive"
                            className="bg-red-500/20 border-red-400/50 text-red-100 cursor-pointer"
                            onClick={() => removerNumeroRemovido(num)}
                          >
                            {num.toString().padStart(2, '0')}
                          </Badge>
                        ))}
                      </div>
                      <Input
                        className="bg-white/5 border-white/10 text-white placeholder:text-white/50"
                        placeholder="Ex: 1,2,3"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleInput(e.currentTarget.value, (n) => {
                              if (!numerosFixos.includes(n) && !numerosRemovidos.includes(n)) {
                                setNumerosRemovidos([...numerosRemovidos, n])
                              }
                            })
                            e.currentTarget.value = ''
                          }
                        }}
                      />
                    </div>
                    <Button onClick={gerarJogos} className="w-full bg-emerald-500 hover:bg-emerald-600 text-black font-semibold">
                      🍀 GERAR JOGOS
                    </Button>
                  </CardContent>
                </Card>
              </div>

              {/* Resultados */}
              <div className="lg:col-span-2 space-y-4">
                <Card className={cardClass}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className={isDark ? "text-white" : "text-slate-900"}>Jogos Gerados</CardTitle>
                        <CardDescription className={isDark ? "text-emerald-100/80" : "text-slate-600"}>
                          {jogosGerados.length} jogos • Algoritmos: {algoritmosAtivos.join(', ')}
                        </CardDescription>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" className={isDark ? "border-emerald-400/60 text-emerald-100" : "border-emerald-300 text-emerald-700"} onClick={salvarJogos}>
                          <Save className="w-4 h-4 mr-1" /> Salvar
                        </Button>
                        <Button
                          variant="outline"
                          className={isDark ? "border-emerald-400/60 text-emerald-100" : "border-emerald-300 text-emerald-700"}
                          onClick={() => {
                            if (jogosGerados.length === 0) return
                            const text = jogosGerados.map((jogo, idx) => `Jogo ${idx + 1}: ${jogo.join(' ')}`).join('\n')
                            navigator.clipboard.writeText(text)
                          }}
                        >
                          <Copy className="w-4 h-4 mr-1" /> Copiar
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {jogosGerados.length > 0 ? (
                      jogosGerados.map((jogo, idx) => (
                        <div
                          key={idx}
                          className={`p-4 rounded-xl flex items-center justify-between flex-wrap gap-3 ${isDark ? "bg-white/5 border border-white/10" : "bg-slate-50 border border-slate-200"}`}
                        >
                          <div className="flex items-center gap-3">
                            <Badge className={isDark ? "bg-emerald-500/20 border-emerald-400/50 text-emerald-100" : "bg-emerald-100 border-emerald-300 text-emerald-800"}>
                              {algoritmosUsados[idx] || 'Misto'}
                            </Badge>
                            <div className="flex gap-2 flex-wrap">
                              {jogo.map((num) => (
                                <div
                                  key={num}
                                  className={`w-9 h-9 bg-gradient-to-br from-emerald-500 to-green-400 ${isDark ? "text-black" : "text-emerald-950"} font-semibold rounded-full flex items-center justify-center shadow-md`}
                                >
                                  {num.toString().padStart(2, '0')}
                                </div>
                              ))}
                            </div>
                          </div>
                          <div className={`text-xs space-y-1 ${isDark ? "text-emerald-100/80" : "text-slate-600"}`}>
                            <div>Pares {jogo.filter(n => n % 2 === 0).length} • Ímpares {jogo.filter(n => n % 2 !== 0).length}</div>
                            {(() => {
                              const res = conferirJogo(jogo)
                              return (
                                <div className="flex items-center gap-2">
                                  <span className={res.jaSaiu ? (isDark ? "text-emerald-400" : "text-emerald-700") : (isDark ? "text-amber-200/90" : "text-amber-600")}>
                                    {res.jaSaiu ? "Já saiu (Sena!)" : `Melhor acerto: ${res.melhorAcerto}`}
                                  </span>
                                  {res.melhorAcerto >= 4 && res.ocorrencias.length > 0 && (
                                    <span className={`text-[11px] ${isDark ? "text-emerald-100/80" : "text-slate-600"}`}>
                                      #{res.ocorrencias[0].concurso} ({new Date(res.ocorrencias[0].data).toLocaleDateString('pt-BR')})
                                    </span>
                                  )}
                                </div>
                              )
                            })()}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className={`text-center py-10 ${isDark ? "text-emerald-100/70" : "text-slate-600"}`}>
                        <Shuffle className="w-10 h-10 mx-auto mb-3 opacity-70 text-emerald-400" />
                        Clique em “Gerar Jogos” para começar
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* Estatísticas */}
          <TabsContent value="estatisticas" className="mt-6 space-y-6">
            {estatisticas && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <Card className={`${cardClass} lg:col-span-1`}>
                  <CardHeader>
                    <CardTitle className={isDark ? "text-white" : "text-slate-900"}>🔥 Top Frequentes</CardTitle>
                    <CardDescription className={isDark ? "text-emerald-100/80" : "text-slate-600"}>6 números mais sorteados</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    {estatisticas.topFrequentes.map((item: any) => (
                      <div key={item.dezena} className={`flex justify-between ${isDark ? "text-emerald-50" : "text-slate-700"}`}>
                        <span className="font-mono text-sm">{item.dezena.toString().padStart(2, '0')}</span>
                        <span className="font-semibold">{item.frequencia}x</span>
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card className={`${cardClass} lg:col-span-1`}>
                  <CardHeader>
                    <CardTitle className={isDark ? "text-white" : "text-slate-900"}>❄️ Top Atrasados</CardTitle>
                    <CardDescription className={isDark ? "text-emerald-100/80" : "text-slate-600"}>6 números mais atrasados</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    {estatisticas.topAtrasados.map((item: any) => (
                      <div key={item.dezena} className={`flex justify-between ${isDark ? "text-emerald-50" : "text-slate-700"}`}>
                        <span className="font-mono text-sm">{item.dezena.toString().padStart(2, '0')}</span>
                        <span className="font-semibold">{item.atraso} sorteios</span>
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card className={`${cardClass} lg:col-span-3`}>
                  <CardHeader>
                    <CardTitle className={isDark ? "text-white" : "text-slate-900"}>📊 Frequência por Número</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={estatisticas.frequenciasChart}>
                        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#1f2937" : "#e5e7eb"} />
                        <XAxis dataKey="dezena" stroke={isDark ? "#9ca3af" : "#4b5563"} />
                        <YAxis stroke={isDark ? "#9ca3af" : "#4b5563"} />
                        <Tooltip contentStyle={isDark ? { background: '#0f172a', border: '1px solid #10b981', color: 'white' } : { background: '#ffffff', border: '1px solid #10b981', color: '#0f172a' }} />
                        <Bar dataKey="frequencia" fill="#10b981" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {/* Meus Jogos */}
          <TabsContent value="jogos" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className={cardClass}>
                <CardHeader>
                  <CardTitle className={isDark ? "text-white" : "text-slate-900"}>💾 Jogos Salvos</CardTitle>
                  <CardDescription className={isDark ? "text-emerald-100/80" : "text-slate-600"}>
                    Seus jogos armazenados na nuvem
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className={isDark ? "text-emerald-100/70 text-sm" : "text-slate-600 text-sm"}>Funcionalidade em desenvolvimento...</p>
                </CardContent>
              </Card>

              <Card className={cardClass}>
                <CardHeader>
                  <CardTitle className={isDark ? "text-white" : "text-slate-900"}>✅ Conferir Jogo</CardTitle>
                  <CardDescription className={isDark ? "text-emerald-100/80" : "text-slate-600"}>
                    Veja se um jogo já saiu ou qual foi o melhor acerto
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Input
                    className={inputClass}
                    placeholder="Digite 6 números (ex: 01 05 12 23 34 45)"
                    value={jogoConferir}
                    onChange={(e) => setJogoConferir(e.target.value)}
                  />
                  <Button
                    className={`font-semibold ${isDark ? "bg-emerald-500 hover:bg-emerald-600 text-black" : "bg-emerald-500 hover:bg-emerald-600 text-white"}`}
                    onClick={() => {
                      const nums = jogoConferir
                        .split(/[\s,]+/)
                        .map(n => parseInt(n, 10))
                        .filter(n => n >= 1 && n <= 60)
                      if (nums.length !== 6) {
                        alert('Digite 6 números válidos.')
                        return
                      }
                      setResultadoConferencia(conferirJogo(nums.sort((a, b) => a - b)))
                    }}
                  >
                    Conferir
                  </Button>

                  {resultadoConferencia && (
                    <div className={`p-3 rounded-lg text-sm space-y-2 ${isDark ? "bg-white/5 border border-white/10 text-emerald-50" : "bg-slate-50 border border-slate-200 text-slate-800"}`}>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">Já saiu?</span>
                        <span className={resultadoConferencia.jaSaiu ? (isDark ? "text-emerald-300" : "text-emerald-700") : (isDark ? "text-amber-200/90" : "text-amber-600")}>
                          {resultadoConferencia.jaSaiu ? "Sim (Sena!)" : "Não"}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">Melhor acerto:</span>
                        <span className={isDark ? "text-emerald-200" : "text-emerald-700"}>{resultadoConferencia.melhorAcerto} números</span>
                      </div>
                      {resultadoConferencia.ocorrencias.length > 0 && (
                        <div className="space-y-1">
                          <div className={isDark ? "font-semibold text-emerald-200/90" : "font-semibold text-emerald-700"}>Ocorrências (4+ acertos)</div>
                          {resultadoConferencia.ocorrencias.map((o, i) => (
                            <div key={i} className={`flex justify-between ${isDark ? "text-emerald-100/80" : "text-slate-700"}`}>
                              <span>#{o.concurso}</span>
                              <span>{o.acertos} acertos • {new Date(o.data).toLocaleDateString('pt-BR')}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Jogo do Bicho */}
          <TabsContent value="bicho" className="mt-6 space-y-6">
            {/* Header do Bicho */}
            <Card className={cardClass}>
              <CardHeader>
                <CardTitle className={`flex items-center gap-2 ${isDark ? "text-white" : "text-slate-900"}`}>
                  🦁 Jogo do Bicho - Tabelas e Palpites
                </CardTitle>
                <CardDescription className={isDark ? "text-amber-100/80" : "text-slate-600"}>
                  Tabela dos 25 animais, puxadas, horários e gerador de palpites
                </CardDescription>
              </CardHeader>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Tabela dos 25 Animais */}
              <Card className={cardClass}>
                <CardHeader>
                  <CardTitle className={isDark ? "text-white" : "text-slate-900"}>🐾 Tabela dos 25 Grupos</CardTitle>
                  <CardDescription className={isDark ? "text-amber-100/80" : "text-slate-600"}>
                    Animais e suas dezenas correspondentes
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 gap-1 text-sm max-h-[400px] overflow-y-auto">
                    {[
                      { grupo: 1, animal: "Avestruz", emoji: "🦢", dezenas: "01-02-03-04" },
                      { grupo: 2, animal: "Águia", emoji: "🦅", dezenas: "05-06-07-08" },
                      { grupo: 3, animal: "Burro", emoji: "🫏", dezenas: "09-10-11-12" },
                      { grupo: 4, animal: "Borboleta", emoji: "🦋", dezenas: "13-14-15-16" },
                      { grupo: 5, animal: "Cachorro", emoji: "🐕", dezenas: "17-18-19-20" },
                      { grupo: 6, animal: "Cabra", emoji: "🐐", dezenas: "21-22-23-24" },
                      { grupo: 7, animal: "Carneiro", emoji: "🐏", dezenas: "25-26-27-28" },
                      { grupo: 8, animal: "Camelo", emoji: "🐫", dezenas: "29-30-31-32" },
                      { grupo: 9, animal: "Cobra", emoji: "🐍", dezenas: "33-34-35-36" },
                      { grupo: 10, animal: "Coelho", emoji: "🐇", dezenas: "37-38-39-40" },
                      { grupo: 11, animal: "Cavalo", emoji: "🐴", dezenas: "41-42-43-44" },
                      { grupo: 12, animal: "Elefante", emoji: "🐘", dezenas: "45-46-47-48" },
                      { grupo: 13, animal: "Galo", emoji: "🐓", dezenas: "49-50-51-52" },
                      { grupo: 14, animal: "Gato", emoji: "🐱", dezenas: "53-54-55-56" },
                      { grupo: 15, animal: "Jacaré", emoji: "🐊", dezenas: "57-58-59-60" },
                      { grupo: 16, animal: "Leão", emoji: "🦁", dezenas: "61-62-63-64" },
                      { grupo: 17, animal: "Macaco", emoji: "🐒", dezenas: "65-66-67-68" },
                      { grupo: 18, animal: "Porco", emoji: "🐷", dezenas: "69-70-71-72" },
                      { grupo: 19, animal: "Pavão", emoji: "🦚", dezenas: "73-74-75-76" },
                      { grupo: 20, animal: "Peru", emoji: "🦃", dezenas: "77-78-79-80" },
                      { grupo: 21, animal: "Touro", emoji: "🐂", dezenas: "81-82-83-84" },
                      { grupo: 22, animal: "Tigre", emoji: "🐅", dezenas: "85-86-87-88" },
                      { grupo: 23, animal: "Urso", emoji: "🐻", dezenas: "89-90-91-92" },
                      { grupo: 24, animal: "Veado", emoji: "🦌", dezenas: "93-94-95-96" },
                      { grupo: 25, animal: "Vaca", emoji: "🐄", dezenas: "97-98-99-00" },
                    ].map((item) => (
                      <div
                        key={item.grupo}
                        className={`flex items-center justify-between p-2 rounded-lg ${isDark ? "bg-white/5 hover:bg-white/10" : "bg-slate-50 hover:bg-slate-100"} transition`}
                      >
                        <div className="flex items-center gap-2">
                          <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${isDark ? "bg-amber-500/20 text-amber-200" : "bg-amber-100 text-amber-800"}`}>
                            {item.grupo.toString().padStart(2, '0')}
                          </span>
                          <span className="text-lg">{item.emoji}</span>
                          <span className={isDark ? "text-white" : "text-slate-900"}>{item.animal}</span>
                        </div>
                        <span className={`font-mono text-xs ${isDark ? "text-amber-200" : "text-amber-700"}`}>
                          {item.dezenas}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Tabela de Puxadas */}
              <Card className={cardClass}>
                <CardHeader>
                  <CardTitle className={isDark ? "text-white" : "text-slate-900"}>🔗 Tabela de Puxadas</CardTitle>
                  <CardDescription className={isDark ? "text-amber-100/80" : "text-slate-600"}>
                    Qual animal "puxa" quais outros
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 gap-1 text-sm max-h-[400px] overflow-y-auto">
                    {[
                      { animal: "Avestruz", emoji: "🦢", puxa: "Vaca, Águia, Galo, Pavão, Peru" },
                      { animal: "Águia", emoji: "🦅", puxa: "Coelho, Avestruz, Galo, Pavão, Peru" },
                      { animal: "Burro", emoji: "🫏", puxa: "Cavalo, Elefante, Touro, Veado, Coelho" },
                      { animal: "Borboleta", emoji: "🦋", puxa: "Cabra, Elefante, Gato, Leão, Cachorro" },
                      { animal: "Cachorro", emoji: "🐕", puxa: "Galo, Gato, Camelo, Macaco, Porco" },
                      { animal: "Cabra", emoji: "🐐", puxa: "Carneiro, Macaco, Elefante, Touro, Tigre" },
                      { animal: "Carneiro", emoji: "🐏", puxa: "Cabra, Coelho, Vaca" },
                      { animal: "Camelo", emoji: "🐫", puxa: "Cachorro, Elefante, Urso" },
                      { animal: "Cobra", emoji: "🐍", puxa: "Jacaré, Porco, Burro, Gato" },
                      { animal: "Coelho", emoji: "🐇", puxa: "Carneiro, Águia, Burro" },
                      { animal: "Cavalo", emoji: "🐴", puxa: "Burro, Elefante, Touro" },
                      { animal: "Elefante", emoji: "🐘", puxa: "Burro, Cabra, Camelo, Cavalo" },
                      { animal: "Galo", emoji: "🐓", puxa: "Avestruz, Águia, Borboleta, Cachorro" },
                      { animal: "Gato", emoji: "🐱", puxa: "Borboleta, Cachorro, Cobra, Carneiro" },
                      { animal: "Jacaré", emoji: "🐊", puxa: "Cobra, Cabra" },
                      { animal: "Leão", emoji: "🦁", puxa: "Borboleta, Tigre" },
                      { animal: "Macaco", emoji: "🐒", puxa: "Cabra, Cachorro" },
                      { animal: "Porco", emoji: "🐷", puxa: "Cachorro, Cobra" },
                      { animal: "Pavão", emoji: "🦚", puxa: "Avestruz, Águia, Cachorro" },
                      { animal: "Peru", emoji: "🦃", puxa: "Avestruz, Águia" },
                      { animal: "Touro", emoji: "🐂", puxa: "Burro, Cabra, Cavalo" },
                      { animal: "Tigre", emoji: "🐅", puxa: "Cabra, Leão" },
                      { animal: "Urso", emoji: "🐻", puxa: "Cabra, Camelo" },
                      { animal: "Veado", emoji: "🦌", puxa: "Burro" },
                      { animal: "Vaca", emoji: "🐄", puxa: "Avestruz, Carneiro" },
                    ].map((item, idx) => (
                      <div
                        key={idx}
                        className={`flex items-center justify-between p-2 rounded-lg ${isDark ? "bg-white/5 hover:bg-white/10" : "bg-slate-50 hover:bg-slate-100"} transition`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{item.emoji}</span>
                          <span className={`font-medium ${isDark ? "text-white" : "text-slate-900"}`}>{item.animal}</span>
                        </div>
                        <span className={`text-xs ${isDark ? "text-amber-200/80" : "text-amber-700"}`}>
                          {item.puxa}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Resultados Atualizados */}
              <Card className={cardClass}>
                <CardHeader>
                  <CardTitle className={`flex items-center justify-between ${isDark ? "text-white" : "text-slate-900"}`}>
                    <span>📺 Resultados Ao Vivo</span>
                    <Button
                      size="sm"
                      onClick={buscarResultadosBicho}
                      disabled={loadingBicho}
                      className="bg-amber-500 hover:bg-amber-600 text-black"
                    >
                      {loadingBicho ? "⏳" : "🔄"} Atualizar
                    </Button>
                  </CardTitle>
                  <CardDescription className={isDark ? "text-amber-100/80" : "text-slate-600"}>
                    Deu no Poste - PT Rio (RJ)
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {/* Links externos */}
                  <div className="grid grid-cols-2 gap-2">
                    <a
                      href="https://www.ojogodobicho.com/deu_no_poste.htm"
                      target="_blank"
                      rel="noopener noreferrer"
                      className={`p-2 rounded-lg text-center text-xs font-medium transition ${isDark ? "bg-amber-500/20 hover:bg-amber-500/30 text-amber-100" : "bg-amber-100 hover:bg-amber-200 text-amber-800"}`}
                    >
                      🎯 Deu no Poste
                    </a>
                    <a
                      href="https://ptrio.inf.br/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className={`p-2 rounded-lg text-center text-xs font-medium transition ${isDark ? "bg-amber-500/20 hover:bg-amber-500/30 text-amber-100" : "bg-amber-100 hover:bg-amber-200 text-amber-800"}`}
                    >
                      🏆 PT Rio
                    </a>
                  </div>

                  <Separator className={isDark ? "bg-white/10" : "bg-slate-200"} />

                  {/* Resultados da API */}
                  <div className={`rounded-lg overflow-hidden max-h-[320px] overflow-y-auto ${isDark ? "bg-white/5" : "bg-slate-50"}`}>
                    {!resultadosBicho && !loadingBicho && (
                      <div className="p-6 text-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-2 border-amber-400 border-t-transparent mx-auto mb-2" />
                        <p className={`text-sm ${isDark ? "text-amber-200" : "text-amber-700"}`}>Carregando resultados...</p>
                      </div>
                    )}

                    {loadingBicho && (
                      <div className="p-6 text-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-2 border-amber-400 border-t-transparent mx-auto mb-2" />
                        <p className={`text-sm ${isDark ? "text-amber-200" : "text-amber-700"}`}>Atualizando...</p>
                      </div>
                    )}

                    {resultadosBicho && !loadingBicho && (
                      <div className="p-2 space-y-2">
                        {resultadosBicho.success && resultadosBicho.resultados.length > 0 ? (
                          resultadosBicho.resultados.map((resultado, idx) => (
                            <div
                              key={idx}
                              onClick={() => setResultadoSelecionado(resultado)}
                              className={`p-2 rounded-lg cursor-pointer transition-all hover:scale-[1.02] ${isDark ? "bg-white/5 hover:bg-amber-500/20 hover:border-amber-500/50" : "bg-white hover:bg-amber-50"} border border-transparent`}
                            >
                              <div className="flex items-center justify-between mb-2">
                                <span className={`px-2 py-0.5 rounded text-xs font-bold ${isDark ? "bg-amber-500/30 text-amber-200" : "bg-amber-200 text-amber-900"}`}>
                                  {resultado.extracao} - {resultado.horario}
                                </span>
                                <span className={`text-xs flex items-center gap-1 ${isDark ? "text-amber-100/60" : "text-slate-500"}`}>
                                  {resultado.data}
                                  <span className="text-amber-400">🔍</span>
                                </span>
                              </div>
                              <div className="grid grid-cols-5 gap-1">
                                {resultado.premios.slice(0, 5).map((premio) => (
                                  <div
                                    key={premio.posicao}
                                    className={`text-center p-1 rounded ${isDark ? "bg-amber-500/10" : "bg-amber-50"}`}
                                  >
                                    <div className={`text-[10px] ${isDark ? "text-amber-100/60" : "text-slate-500"}`}>
                                      {premio.posicao}º
                                    </div>
                                    <div className={`font-mono font-bold text-sm ${isDark ? "text-white" : "text-slate-900"}`}>
                                      {premio.milhar}
                                    </div>
                                    <div className={`text-[10px] ${isDark ? "text-amber-200" : "text-amber-700"}`}>
                                      G{premio.grupo.toString().padStart(2, '0')}
                                    </div>
                                    <div className={`text-[9px] truncate ${isDark ? "text-amber-100/80" : "text-slate-600"}`}>
                                      {premio.animal}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className={`p-4 text-center ${isDark ? "text-amber-100/60" : "text-slate-500"}`}>
                            <p className="text-sm">Não foi possível carregar resultados</p>
                            <p className="text-xs mt-1">Tente novamente ou acesse os links acima</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {resultadosBicho?.atualizadoEm && (
                    <p className={`text-[10px] text-center ${isDark ? "text-amber-100/50" : "text-slate-400"}`}>
                      Atualizado: {new Date(resultadosBicho.atualizadoEm).toLocaleString('pt-BR')}
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Gerador de Palpites - Agora em destaque abaixo dos resultados */}
            <Card className={`${cardClass} overflow-hidden`}>
              <CardHeader className={`${isDark ? "bg-gradient-to-r from-orange-600/20 to-amber-600/20 border-b border-orange-500/20" : "bg-gradient-to-r from-orange-100 to-amber-100 border-b border-orange-200"}`}>
                <CardTitle className={isDark ? "text-orange-100" : "text-orange-900"}>🎲 Gerador de Palpites</CardTitle>
                <CardDescription className={isDark ? "text-orange-200/80" : "text-orange-700"}>
                  Gera números baseados na estrutura do jogo
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 pt-4">
                {/* Resultado do Palpite */}
                {palpiteBicho && (
                  <div className={`rounded-2xl p-5 ${isDark ? "bg-gradient-to-br from-orange-900/40 to-amber-900/30 border-2 border-orange-500/50" : "bg-gradient-to-br from-orange-100 to-amber-50 border-2 border-orange-300"}`}>
                    {/* Animal */}
                    <div className="flex items-center gap-4 mb-5">
                      <div className={`w-16 h-16 rounded-2xl ${isDark ? "bg-gradient-to-br from-orange-500 to-amber-500" : "bg-gradient-to-br from-orange-400 to-amber-400"} flex items-center justify-center text-4xl shadow-xl`}>
                        {palpiteBicho.emoji}
                      </div>
                      <div>
                        <div className={`text-sm font-bold uppercase tracking-wider ${isDark ? "text-orange-300" : "text-orange-600"}`}>
                          Grupo {palpiteBicho.grupo.toString().padStart(2, '0')}
                        </div>
                        <div className={`text-2xl font-black ${isDark ? "text-white" : "text-slate-900"}`}>
                          {palpiteBicho.animal}
                        </div>
                      </div>
                    </div>

                    {/* Números */}
                    <div className="grid grid-cols-3 gap-3">
                      <div className={`rounded-xl p-3 text-center ${isDark ? "bg-slate-900/60 border border-orange-500/30" : "bg-white border border-orange-200"}`}>
                        <div className={`text-xs font-bold mb-1 ${isDark ? "text-orange-400" : "text-orange-600"}`}>DEZENA</div>
                        <div className={`text-2xl font-black ${isDark ? "text-orange-100" : "text-orange-900"}`}>{palpiteBicho.dezena}</div>
                        <div className={`text-xs font-semibold ${isDark ? "text-emerald-400" : "text-emerald-600"}`}>60x</div>
                      </div>
                      <div className={`rounded-xl p-3 text-center ${isDark ? "bg-slate-900/60 border border-orange-500/30" : "bg-white border border-orange-200"}`}>
                        <div className={`text-xs font-bold mb-1 ${isDark ? "text-orange-400" : "text-orange-600"}`}>CENTENA</div>
                        <div className={`text-2xl font-black ${isDark ? "text-orange-100" : "text-orange-900"}`}>{palpiteBicho.centena}</div>
                        <div className={`text-xs font-semibold ${isDark ? "text-emerald-400" : "text-emerald-600"}`}>600x</div>
                      </div>
                      <div className={`rounded-xl p-3 text-center ${isDark ? "bg-slate-900/60 border border-orange-500/30" : "bg-white border border-orange-200"}`}>
                        <div className={`text-xs font-bold mb-1 ${isDark ? "text-orange-400" : "text-orange-600"}`}>MILHAR</div>
                        <div className={`text-2xl font-black ${isDark ? "text-orange-100" : "text-orange-900"}`}>{palpiteBicho.milhar}</div>
                        <div className={`text-xs font-semibold ${isDark ? "text-emerald-400" : "text-emerald-600"}`}>4000x</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Seletor de Estratégia - 4 opções baseadas em análise estatística */}
                <div className={`rounded-xl p-3 ${isDark ? "bg-slate-800/50 border border-slate-700" : "bg-slate-100 border border-slate-200"}`}>
                  <div className={`text-xs font-bold mb-2 ${isDark ? "text-orange-300" : "text-orange-700"}`}>🎯 Gerar Novo Palpite (Análise Set-Dez/2025):</div>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
                    {[
                      { id: 'quente', label: '🔥 Quente', desc: 'Peru 8.9%, Avestruz, Burro' },
                      { id: 'frio', label: '❄️ Frio', desc: 'Porco 90d, Gato 76d, Cavalo' },
                      { id: 'puxada', label: '🔗 Puxada', desc: 'Correlações reais (45%)' },
                      { id: 'ciclo', label: '📅 Ciclo', desc: 'Padrão do dia do mês' },
                    ].map((e) => (
                      <button
                        key={e.id}
                        onClick={() => setEstrategiaBicho(e.id as any)}
                        className={`p-2 rounded-lg text-left transition-all ${
                          estrategiaBicho === e.id
                            ? isDark
                              ? "bg-orange-500/30 border-2 border-orange-500"
                              : "bg-orange-200 border-2 border-orange-500"
                            : isDark
                              ? "bg-slate-700/50 border border-slate-600 hover:border-orange-500/50"
                              : "bg-white border border-slate-300 hover:border-orange-400"
                        }`}
                      >
                        <div className={`text-sm font-semibold ${isDark ? "text-white" : "text-slate-900"}`}>{e.label}</div>
                        <div className={`text-[10px] ${isDark ? "text-slate-400" : "text-slate-500"}`}>{e.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* PALPITE DO DIA - Fixo baseado na data */}
                {palpiteDoDia && palpiteDoDia.length > 0 && (
                  <div className={`rounded-xl p-4 ${isDark ? "bg-gradient-to-br from-amber-900/40 to-orange-900/40 border-2 border-amber-500/50" : "bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-400"}`}>
                    <div className={`text-sm font-bold mb-3 text-center ${isDark ? "text-amber-300" : "text-amber-700"}`}>
                      ⭐ PALPITE DO DIA - {new Date().toLocaleDateString('pt-BR')}
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                      {palpiteDoDia.map((p, idx) => (
                        <div
                          key={idx}
                          className={`rounded-lg p-3 text-center ${
                            idx === 0
                              ? isDark ? "bg-blue-900/50 border border-blue-500/50" : "bg-blue-100 border border-blue-300"
                              : idx === 1
                              ? isDark ? "bg-red-900/50 border border-red-500/50" : "bg-red-100 border border-red-300"
                              : isDark ? "bg-purple-900/50 border border-purple-500/50" : "bg-purple-100 border border-purple-300"
                          }`}
                        >
                          <div className="text-2xl mb-1">{p.emoji}</div>
                          <div className={`font-bold text-sm ${isDark ? "text-white" : "text-slate-900"}`}>
                            {p.grupo.toString().padStart(2, '0')} - {p.animal}
                          </div>
                          <div className={`font-mono font-bold text-lg ${isDark ? "text-amber-300" : "text-amber-700"}`}>
                            {p.milhar}
                          </div>
                          <div className={`text-[10px] ${isDark ? "text-slate-400" : "text-slate-500"}`}>
                            {idx === 0 ? "❄️ Frio" : idx === 1 ? "🔥 Quente" : "📅 Ciclo"}: {p.justificativa}
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className={`text-[10px] text-center mt-2 ${isDark ? "text-amber-400/70" : "text-amber-600/70"}`}>
                      Baseado em análise estatística Set-Dez/2025 • Não muda ao recarregar
                    </div>
                  </div>
                )}

                <Button
                  className="w-full h-12 bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-bold text-base shadow-xl shadow-orange-500/40"
                  onClick={gerarPalpiteBicho}
                >
                  🎲 {palpiteBicho ? "NOVO PALPITE" : "GERAR PALPITE"}
                </Button>

                <p className={`text-xs text-center ${isDark ? "text-slate-400" : "text-slate-500"}`}>
                  ⚠️ Palpites são apenas sugestões aleatórias para entretenimento.
                </p>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Horários dos Sorteios */}
              <Card className={cardClass}>
                <CardHeader>
                  <CardTitle className={isDark ? "text-white" : "text-slate-900"}>🕐 Horários (RJ)</CardTitle>
                  <CardDescription className={isDark ? "text-amber-100/80" : "text-slate-600"}>
                    Extrações diárias do Rio de Janeiro
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {[
                      { sigla: "PPT", hora: "09:20", nome: "Primeiro Para Todos" },
                      { sigla: "PTM", hora: "11:20", nome: "Para Todos Manhã" },
                      { sigla: "PT", hora: "14:20", nome: "Para Todos" },
                      { sigla: "PTV", hora: "16:20", nome: "Para Todos Vespertino" },
                      { sigla: "PTN", hora: "18:20", nome: "Para Todos Noite" },
                      { sigla: "COR", hora: "21:20", nome: "Coruja" },
                    ].map((item) => (
                      <div
                        key={item.sigla}
                        className={`flex items-center justify-between p-2 rounded-lg ${isDark ? "bg-white/5" : "bg-slate-50"}`}
                      >
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 rounded text-xs font-bold ${isDark ? "bg-amber-500/20 text-amber-200" : "bg-amber-100 text-amber-800"}`}>
                            {item.sigla}
                          </span>
                          <span className={`text-sm ${isDark ? "text-white" : "text-slate-900"}`}>{item.nome}</span>
                        </div>
                        <span className={`font-mono font-bold ${isDark ? "text-amber-300" : "text-amber-700"}`}>
                          {item.hora}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Cotações */}
              <Card className={cardClass}>
                <CardHeader>
                  <CardTitle className={isDark ? "text-white" : "text-slate-900"}>💰 Cotações</CardTitle>
                  <CardDescription className={isDark ? "text-amber-100/80" : "text-slate-600"}>
                    Multiplicadores por modalidade
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {[
                      { tipo: "Grupo", prob: "1/25 (4%)", mult: "18x" },
                      { tipo: "Dezena", prob: "1/100 (1%)", mult: "60x" },
                      { tipo: "Centena", prob: "1/1000", mult: "600x" },
                      { tipo: "Milhar", prob: "1/10000", mult: "4000x" },
                      { tipo: "Duque Grupo", prob: "-", mult: "18.5x" },
                      { tipo: "Terno Grupo", prob: "-", mult: "130x" },
                    ].map((item) => (
                      <div
                        key={item.tipo}
                        className={`flex items-center justify-between p-2 rounded-lg ${isDark ? "bg-white/5" : "bg-slate-50"}`}
                      >
                        <span className={`text-sm font-medium ${isDark ? "text-white" : "text-slate-900"}`}>{item.tipo}</span>
                        <div className="flex items-center gap-3">
                          <span className={`text-xs ${isDark ? "text-amber-100/60" : "text-slate-500"}`}>{item.prob}</span>
                          <span className={`font-bold ${isDark ? "text-emerald-400" : "text-emerald-600"}`}>{item.mult}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

        </Tabs>
        </div>
    </div>
  )
}
