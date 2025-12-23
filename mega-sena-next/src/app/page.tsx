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

  useEffect(() => {
    carregarDados()
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
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Hero */}
        <div className={`mb-8 rounded-2xl ${cardClass} shadow-xl backdrop-blur-lg p-6`}>
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-emerald-300 text-sm font-semibold">
                <Sparkles className="w-4 h-4" /> {isDark ? "Premium Dark" : "Tema Claro"}
              </div>
              <div className="flex items-center gap-2 mt-2 whitespace-nowrap">
                <span
                  className={`text-3xl md:text-4xl font-bold ${
                    isDark ? "text-emerald-300" : "text-emerald-600"
                  }`}
                  role="img"
                  aria-label="trevo"
                >
                  🍀
                </span>
                <h1
                  className={`text-3xl md:text-4xl font-bold ${
                    isDark ? "text-emerald-300" : "text-emerald-600"
                  }`}
                >
                  Gerador Inteligente - Mega-Sena
          </h1>
              </div>
              <p className={isDark ? "text-emerald-100/80 mt-1" : "text-slate-600 mt-1"}>
                Algoritmos combinados, balanceamento e Supabase integrado
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                aria-label="Alternar tema"
                onClick={() => setTema(isDark ? 'light' : 'dark')}
                className={`p-2 rounded-full border transition ${
                  isDark ? "border-white/20 text-white hover:bg-white/10" : "border-slate-300 text-slate-800 hover:bg-slate-100"
                }`}
              >
                {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
            </div>

            {ultimoConcurso && (
              <div className={`rounded-xl border border-emerald-500/40 ${isDark ? "bg-emerald-500/10" : "bg-emerald-50"} px-4 py-3`}>
                <div className={`text-sm ${isDark ? "text-emerald-200" : "text-emerald-700"}`}>Último concurso</div>
                <div className={`text-2xl font-bold ${isDark ? "text-white" : "text-emerald-800"}`}>#{ultimoConcurso.numero}</div>
                <div className={`text-xs ${isDark ? "text-emerald-100/80" : "text-emerald-700/80"}`}>
                  {new Date(ultimoConcurso.data).toLocaleDateString('pt-BR')}
                </div>
                <div className="flex gap-2 mt-2 flex-wrap">
                  {[ultimoConcurso.dezena1, ultimoConcurso.dezena2, ultimoConcurso.dezena3,
                    ultimoConcurso.dezena4, ultimoConcurso.dezena5, ultimoConcurso.dezena6].map((n) => (
                    <div
                      key={n}
                      className="w-9 h-9 rounded-full bg-gradient-to-br from-emerald-500 to-green-400 text-black font-semibold flex items-center justify-center shadow-lg"
                    >
                      {n.toString().padStart(2, '0')}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className={`mt-4 flex flex-wrap gap-3 text-sm ${isDark ? "text-emerald-100/80" : "text-slate-700"}`}>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              Supabase conectado ({concursos.length} concursos)
            </div>
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              Algoritmos: {algoritmosAtivos.join(', ')}
            </div>
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-emerald-400" />
              Período: {concursos.length > 0 && `${new Date(concursos[0].data).getFullYear()} - ${new Date(concursos[concursos.length - 1].data).getFullYear()}`}
            </div>
          </div>
        </div>

        <Tabs defaultValue="gerar" className="w-full">
          <TabsList className={`grid w-full grid-cols-4 ${isDark ? "bg-white/5 text-emerald-100 border border-white/10" : "bg-white text-emerald-700 border border-slate-200"}`}>
            <TabsTrigger value="gerar">🎰 Gerar Jogos</TabsTrigger>
            <TabsTrigger value="estatisticas">📊 Estatísticas</TabsTrigger>
            <TabsTrigger value="jogos">💾 Meus Jogos</TabsTrigger>
            <TabsTrigger value="config">⚙️ Config</TabsTrigger>
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

          {/* Config */}
          <TabsContent value="config" className="mt-6">
            <Card className={cardClass}>
              <CardHeader>
                <CardTitle className={isDark ? "text-white" : "text-slate-900"}>⚙️ Configurações do Sistema</CardTitle>
              </CardHeader>
              <CardContent className={`space-y-4 ${isDark ? "text-emerald-50" : "text-slate-800"}`}>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className={`p-3 rounded-lg ${isDark ? "bg-white/5 border border-white/10" : "bg-slate-50 border border-slate-200"}`}>
                    <div className="text-sm text-emerald-500/90">Total de Concursos</div>
                    <div className={`text-2xl font-bold ${isDark ? "text-white" : "text-slate-900"}`}>{concursos.length}</div>
                  </div>
                  <div className={`p-3 rounded-lg ${isDark ? "bg-white/5 border border-white/10" : "bg-slate-50 border border-slate-200"}`}>
                    <div className="text-sm text-emerald-500/90">Status Supabase</div>
                    <div className="flex items-center gap-2 text-emerald-500 font-semibold">
                      <CheckCircle className="w-4 h-4" /> Conectado
                    </div>
                  </div>
                  <div className={`p-3 rounded-lg ${isDark ? "bg-white/5 border border-white/10" : "bg-slate-50 border border-slate-200"}`}>
                    <div className="text-sm text-emerald-500/90">Período de Dados</div>
                    <div className="text-sm">
                      {concursos.length > 0 &&
                        `${new Date(concursos[0].data).toLocaleDateString('pt-BR')} - ${new Date(concursos[concursos.length - 1].data).toLocaleDateString('pt-BR')}`}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
        </div>
    </div>
  )
}
