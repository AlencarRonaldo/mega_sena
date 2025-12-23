import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Tipos para o banco de dados
export interface Concurso {
  id: number
  numero: number
  data: string
  dezena1: number
  dezena2: number
  dezena3: number
  dezena4: number
  dezena5: number
  dezena6: number
}

export interface JogoSalvo {
  id: number
  dezenas: number[]
  data_criacao: string
  algoritmos: string[]
  conferido: boolean
  acertos: Record<string, any>
}

// Funções para buscar dados
export async function buscarTodosConcursos(): Promise<Concurso[]> {
  const { data, error } = await supabase
    .from('concursos')
    .select('*')
    .order('numero', { ascending: true })

  if (error) throw error
  return data || []
}

export async function buscarConcursosUltimoAno(): Promise<Concurso[]> {
  const umAnoAtras = new Date()
  umAnoAtras.setFullYear(umAnoAtras.getFullYear() - 1)

  const { data, error } = await supabase
    .from('concursos')
    .select('*')
    .gte('data', umAnoAtras.toISOString().split('T')[0])
    .order('numero', { ascending: true })

  if (error) throw error
  return data || []
}

export async function buscarUltimoConcurso(): Promise<Concurso | null> {
  const { data, error } = await supabase
    .from('concursos')
    .select('*')
    .order('numero', { ascending: false })
    .limit(1)

  if (error) throw error
  return data?.[0] || null
}

export async function salvarJogo(dezenas: number[], algoritmos: string[]): Promise<JogoSalvo> {
  const { data, error } = await supabase
    .from('jogos_salvos')
    .insert([{ dezenas, algoritmos }])
    .select()
    .single()

  if (error) throw error
  return data
}

export async function buscarJogosSalvos(): Promise<JogoSalvo[]> {
  const { data, error } = await supabase
    .from('jogos_salvos')
    .select('*')
    .order('data_criacao', { ascending: false })

  if (error) throw error
  return data || []
}
