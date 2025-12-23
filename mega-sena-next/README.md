# 🍀 Mega-Sena Next.js - Vercel Ready

Gerador Inteligente de Jogos da Mega-Sena - Versão otimizada para Vercel com Next.js 16 e TypeScript.

## 🚀 Deploy na Vercel

### Pré-requisitos
- Conta na [Vercel](https://vercel.com)
- Projeto no [Supabase](https://supabase.com)

### Configuração do Supabase
1. Crie um projeto gratuito no Supabase
2. Execute o SQL em `supabase_schema.sql` no SQL Editor
3. Copie a URL e chave anon pública das configurações
4. Configure as variáveis de ambiente na Vercel

### Deploy Automático
1. Fork este repositório no GitHub
2. Conecte o repositório à Vercel
3. Configure as variáveis de ambiente:
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
   ```

## 🛠️ Desenvolvimento Local

### Instalação
```bash
# Instalar dependências
npm install

# Copiar arquivo de configuração
cp env-example.txt .env.local

# Editar .env.local com suas credenciais
```

### Executar
```bash
# Desenvolvimento
npm run dev

# Build para produção
npm run build

# Deploy local
npm run start
```

## ✨ Funcionalidades

### 🎰 Geração de Jogos
- **6 Algoritmos Inteligentes**: Frequência, Markov, Coocorrência, Atrasados, Balanceado, Uniforme
- **Números Fixos/Removidos**: Controle personalizado
- **Equilíbrio Automático**: 3 pares + 3 ímpares
- **Distribuição por Faixas**: 1-20, 21-40, 41-60

### 📊 Análises Estatísticas
- **Frequência Histórica**: Números mais/menos sorteados
- **Análise de Markov**: Padrões de sequência
- **Coocorrência**: Pares que saem juntos
- **Números Atrasados**: Estatísticas de ausência

### 💾 Armazenamento na Nuvem
- **Supabase Integration**: Dados persistentes
- **Jogos Salvos**: Histórico completo
- **Sincronização**: Multi-dispositivo

### 🎨 Interface Moderna
- **Dark/Light Mode**: Design responsivo
- **Componentes Premium**: shadcn/ui + Tailwind CSS
- **Gráficos Interativos**: Recharts
- **Mobile-First**: Otimizado para dispositivos

## 📁 Estrutura do Projeto

```
mega-sena-next/
├── src/
│   ├── app/
│   │   ├── globals.css      # Estilos globais
│   │   ├── layout.tsx       # Layout principal
│   │   └── page.tsx         # Página principal
│   └── components/
│       └── ui/              # Componentes shadcn/ui
├── lib/
│   ├── supabase.ts          # Cliente Supabase
│   └── algoritmos.ts        # Lógica de geração
├── .env.local               # Configurações locais
├── components.json          # Config shadcn/ui
├── next.config.mjs          # Config Next.js
├── tailwind.config.ts       # Config Tailwind
└── package.json
```

## 🔧 Tecnologias

- **Next.js 16** - Framework React
- **TypeScript** - Tipagem estática
- **Tailwind CSS** - Estilização
- **shadcn/ui** - Componentes UI
- **Supabase** - Backend-as-a-Service
- **Recharts** - Gráficos
- **Lucide Icons** - Ícones

## 📊 Algoritmos Disponíveis

| Algoritmo | Descrição | Complexidade |
|-----------|-----------|--------------|
| **Frequência** | Baseado em números mais sorteados | ⭐⭐⭐ |
| **Markov** | Análise de transições entre concursos | ⭐⭐⭐⭐ |
| **Coocorrência** | Pares que costumam sair juntos | ⭐⭐⭐⭐ |
| **Atrasados** | Números com maior período sem sair | ⭐⭐ |
| **Balanceado** | Equilíbrio matemático perfeito | ⭐⭐⭐⭐⭐ |
| **Uniforme** | Distribuição puramente aleatória | ⭐ |

## 🚀 Performance

- **Build Time**: ~30s
- **Bundle Size**: ~200KB (gzipped)
- **Lighthouse Score**: 95+ (Performance, Accessibility, SEO)
- **Vercel Deploy**: Automático via Git

## 🔐 Segurança

- **Variáveis de Ambiente**: Credenciais protegidas
- **Row Level Security**: Controle de acesso no Supabase
- **API Routes**: Endpoints seguros (futuramente)

## 📈 Roadmap

- [ ] **API Routes**: Endpoints personalizados
- [ ] **Autenticação**: Sistema de usuários
- [ ] **Simulador Avançado**: Testes históricos
- [ ] **Notificações**: Alertas de resultados
- [ ] **PWA**: App instalável
- [ ] **Offline Mode**: Funcionamento sem internet

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

**Desenvolvido com ❤️ para amantes de estatística e jogos** 🍀🎰