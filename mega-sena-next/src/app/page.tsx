'use client'

import { useState, useEffect } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { Shuffle, TrendingUp, Clock, Users, Target, CheckCircle, XCircle } from 'lucide-react'
import { buscarTodosConcursos, buscarUltimoConcurso, salvarJogo, Concurso } from '@/lib/supabase'
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

    // Top 10 mais frequentes
    const topFrequentes = Array.from(freq.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([dezena, frequencia]) => ({ dezena, frequencia }))

    // Top 10 mais atrasados
    const topAtrasados = Array.from(atrasos.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([dezena, atraso]) => ({ dezena, atraso }))

    setEstatisticas({
      totalConcursos: analisador['concursos'].length,
      topFrequentes,
      topAtrasados,
      frequenciasChart: Array.from(freq.entries()).map(([dezena, frequencia]) => ({
        dezena: dezena.toString(),
        frequencia
      })),
      atrasosChart: Array.from(atrasos.entries()).map(([dezena, atraso]) => ({
        dezena: dezena.toString(),
        atraso
      }))
    })
  }

  const gerarJogos = () => {
    if (!gerador) return

    const algoritmosAtivos = Object.entries(algoritmos)
      .filter(([_, ativo]) => ativo)
      .map(([alg]) => alg)

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
      const algoritmosAtivos = Object.entries(algoritmos)
        .filter(([_, ativo]) => ativo)
        .map(([alg]) => alg)

      for (let i = 0; i < jogosGerados.length; i++) {
        await salvarJogo(jogosGerados[i], [algoritmosUsados[i] || 'Misto'])
      }

      alert(`${jogosGerados.length} jogos salvos com sucesso!`)
    } catch (error) {
      console.error('Erro ao salvar jogos:', error)
      alert('Erro ao salvar jogos!')
    }
  }

  const adicionarNumeroFixo = (numero: number) => {
    if (!numerosFixos.includes(numero) && !numerosRemovidos.includes(numero)) {
      setNumerosFixos([...numerosFixos, numero])
    }
  }

  const removerNumeroFixo = (numero: number) => {
    setNumerosFixos(numerosFixos.filter(n => n !== numero))
  }

  const adicionarNumeroRemovido = (numero: number) => {
    if (!numerosFixos.includes(numero) && !numerosRemovidos.includes(numero)) {
      setNumerosRemovidos([...numerosRemovidos, numero])
    }
  }

  const removerNumeroRemovido = (numero: number) => {
    setNumerosRemovidos(numerosRemovidos.filter(n => n !== numero))
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando dados...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-green-600 dark:text-green-400 mb-2">
            🍀 Gerador Mega-Sena
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Algoritmos inteligentes para otimizar suas chances
          </p>
        </div>

        <Tabs defaultValue="gerar" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="gerar">🎰 Gerar Jogos</TabsTrigger>
            <TabsTrigger value="estatisticas">📊 Estatísticas</TabsTrigger>
            <TabsTrigger value="jogos">💾 Meus Jogos</TabsTrigger>
            <TabsTrigger value="config">⚙️ Config</TabsTrigger>
          </TabsList>

          {/* Aba Gerar Jogos */}
          <TabsContent value="gerar" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Configurações */}
              <div className="lg:col-span-1 space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="w-5 h-5" />
                      Configurações
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label>Anos de análise: {anosAnalise[0]}</Label>
                      <Slider
                        value={anosAnalise}
                        onValueChange={setAnosAnalise}
                        max={10}
                        min={1}
                        step={1}
                        className="mt-2"
                      />
                    </div>

                    <div>
                      <Label>Quantidade de jogos: {quantidadeJogos}</Label>
                      <Slider
                        value={[quantidadeJogos]}
                        onValueChange={(value) => setQuantidadeJogos(value[0])}
                        max={20}
                        min={1}
                        step={1}
                        className="mt-2"
                      />
                    </div>

                    <Separator />

                    <div className="space-y-3">
                      <Label className="text-sm font-medium">Algoritmos:</Label>

                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="freq"
                          checked={algoritmos.frequencia}
                          onCheckedChange={(checked) =>
                            setAlgoritmos({...algoritmos, frequencia: checked as boolean})
                          }
                        />
                        <Label htmlFor="freq" className="flex items-center gap-2">
                          <TrendingUp className="w-4 h-4" />
                          Frequência
                        </Label>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="markov"
                          checked={algoritmos.markov}
                          onCheckedChange={(checked) =>
                            setAlgoritmos({...algoritmos, markov: checked as boolean})
                          }
                        />
                        <Label htmlFor="markov" className="flex items-center gap-2">
                          <Shuffle className="w-4 h-4" />
                          Markov
                        </Label>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="cooc"
                          checked={algoritmos.coocorrencia}
                          onCheckedChange={(checked) =>
                            setAlgoritmos({...algoritmos, coocorrencia: checked as boolean})
                          }
                        />
                        <Label htmlFor="cooc" className="flex items-center gap-2">
                          <Users className="w-4 h-4" />
                          Coocorrência
                        </Label>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="atraso"
                          checked={algoritmos.atraso}
                          onCheckedChange={(checked) =>
                            setAlgoritmos({...algoritmos, atraso: checked as boolean})
                          }
                        />
                        <Label htmlFor="atraso" className="flex items-center gap-2">
                          <Clock className="w-4 h-4" />
                          Atrasados
                        </Label>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="balanceado"
                          checked={algoritmos.balanceado}
                          onCheckedChange={(checked) =>
                            setAlgoritmos({...algoritmos, balanceado: checked as boolean})
                          }
                        />
                        <Label htmlFor="balanceado">⚖️ Balanceado</Label>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="uniforme"
                          checked={algoritmos.uniforme}
                          onCheckedChange={(checked) =>
                            setAlgoritmos({...algoritmos, uniforme: checked as boolean})
                          }
                        />
                        <Label htmlFor="uniforme">🎲 Uniforme</Label>
                      </div>
                    </div>

                    <Separator />

                    <div className="space-y-3">
                      <Label>Números Fixos:</Label>
                      <div className="flex flex-wrap gap-1">
                        {numerosFixos.map(num => (
                          <Badge
                            key={num}
                            variant="default"
                            className="cursor-pointer"
                            onClick={() => removerNumeroFixo(num)}
                          >
                            {num.toString().padStart(2, '0')}
                          </Badge>
                        ))}
                      </div>
                      <Input
                        placeholder="Digite números (ex: 5,12,23)"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            const nums = e.currentTarget.value.split(',').map(n => parseInt(n.trim())).filter(n => n >= 1 && n <= 60)
                            nums.forEach(num => adicionarNumeroFixo(num))
                            e.currentTarget.value = ''
                          }
                        }}
                      />
                    </div>

                    <div className="space-y-3">
                      <Label>Números Removidos:</Label>
                      <div className="flex flex-wrap gap-1">
                        {numerosRemovidos.map(num => (
                          <Badge
                            key={num}
                            variant="destructive"
                            className="cursor-pointer"
                            onClick={() => removerNumeroRemovido(num)}
                          >
                            {num.toString().padStart(2, '0')}
                          </Badge>
                        ))}
                      </div>
                      <Input
                        placeholder="Digite números (ex: 1,2,3)"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            const nums = e.currentTarget.value.split(',').map(n => parseInt(n.trim())).filter(n => n >= 1 && n <= 60)
                            nums.forEach(num => adicionarNumeroRemovido(num))
                            e.currentTarget.value = ''
                          }
                        }}
                      />
                    </div>

                    <Button onClick={gerarJogos} className="w-full" size="lg">
                      🍀 GERAR JOGOS
                    </Button>
                  </CardContent>
                </Card>

                {/* Último Concurso */}
                {ultimoConcurso && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">🏆 Último Concurso</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          #{ultimoConcurso.numero}
                        </div>
                        <div className="text-sm text-gray-600 mb-4">
                          {new Date(ultimoConcurso.data).toLocaleDateString('pt-BR')}
                        </div>
                        <div className="flex flex-wrap justify-center gap-2">
                          {[ultimoConcurso.dezena1, ultimoConcurso.dezena2, ultimoConcurso.dezena3,
                            ultimoConcurso.dezena4, ultimoConcurso.dezena5, ultimoConcurso.dezena6].map(num => (
                            <div
                              key={num}
                              className="w-10 h-10 bg-green-500 text-white rounded-full flex items-center justify-center font-bold"
                            >
                              {num.toString().padStart(2, '0')}
                            </div>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>

              {/* Resultados */}
              <div className="lg:col-span-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Jogos Gerados</CardTitle>
                    <CardDescription>
                      {jogosGerados.length} jogos gerados • Algoritmos: {Object.entries(algoritmos).filter(([_, v]) => v).map(([k]) => k).join(', ')}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {jogosGerados.length > 0 ? (
                      <div className="space-y-4">
                        {jogosGerados.map((jogo, idx) => (
                          <div key={idx} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div className="flex items-center gap-4">
                              <Badge variant="outline">
                                {algoritmosUsados[idx] || 'Misto'}
                              </Badge>
                              <div className="flex gap-2">
                                {jogo.map(num => (
                                  <div
                                    key={num}
                                    className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold"
                                  >
                                    {num.toString().padStart(2, '0')}
                                  </div>
                                ))}
                              </div>
                            </div>
                            <div className="text-sm text-gray-600">
                              Pares: {jogo.filter(n => n % 2 === 0).length} •
                              Ímpares: {jogo.filter(n => n % 2 !== 0).length}
                            </div>
                          </div>
                        ))}

                        <div className="flex gap-2 pt-4">
                          <Button onClick={salvarJogos} variant="outline">
                            💾 Salvar Jogos
                          </Button>
                          <Button
                            onClick={() => {
                              const text = jogosGerados.map((jogo, idx) =>
                                `Jogo ${idx + 1}: ${jogo.join(' ')}`
                              ).join('\n')
                              navigator.clipboard.writeText(text)
                            }}
                            variant="outline"
                          >
                            📋 Copiar
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <Shuffle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>Clique em "GERAR JOGOS" para começar</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* Aba Estatísticas */}
          <TabsContent value="estatisticas" className="space-y-6">
            {estatisticas && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>🔥 Números Mais Frequentes</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {estatisticas.topFrequentes.map((item: any) => (
                        <div key={item.dezena} className="flex justify-between">
                          <span className="font-mono">{item.dezena.toString().padStart(2, '0')}</span>
                          <span className="font-bold">{item.frequencia}x</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>❄️ Números Mais Atrasados</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {estatisticas.topAtrasados.map((item: any) => (
                        <div key={item.dezena} className="flex justify-between">
                          <span className="font-mono">{item.dezena.toString().padStart(2, '0')}</span>
                          <span className="font-bold">{item.atraso} sorteios</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle>📊 Frequência por Número</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={estatisticas.frequenciasChart}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="dezena" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="frequencia" fill="#10b981" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {/* Aba Meus Jogos */}
          <TabsContent value="jogos" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>💾 Jogos Salvos</CardTitle>
                <CardDescription>
                  Seus jogos armazenados na nuvem
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">Funcionalidade em desenvolvimento...</p>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Aba Config */}
          <TabsContent value="config" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>⚙️ Configurações do Sistema</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Total de Concursos</Label>
                    <div className="text-2xl font-bold text-green-600">
                      {concursos.length}
                    </div>
                  </div>
                  <div>
                    <Label>Status Supabase</Label>
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-green-500" />
                      <span className="text-green-600">Conectado</span>
                    </div>
                  </div>
                </div>

                <Separator />

                <div>
                  <Label>Período de Dados</Label>
                  <div className="text-gray-600">
                    {concursos.length > 0 &&
                      `${new Date(concursos[0].data).toLocaleDateString('pt-BR')} - ${new Date(concursos[concursos.length - 1].data).toLocaleDateString('pt-BR')}`
                    }
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
