# ValidaJá! - Detector de Boletos Fraudulentos

## 🎯 Objetivo

O ValidaJá! utiliza Inteligência Artificial (Google Gemini) para detectar boletos bancários fraudulentos. O sistema compara novos boletos com boletos originais previamente cadastrados da mesma conta para identificar possíveis fraudes.

**📚 Projeto desenvolvido durante a Imersão IA da Alura em parceria com o Google Gemini**

## 📖 Como Usar o ValidaJá!

Para entender o funcionamento do sistema e como verificar seus boletos, veja nossa **[página Wiki de Funcionamento](https://github.com/diogolast/validaja/wiki/Entendendo-o-Funcionamento)**.

## 🤖 Como Funciona

### 1. **Cadastro de Referências**
- Usuário faz upload de 2+ boletos **ORIGINAIS** da mesma conta (preferencialmente de meses diferentes)
- Gemini extrai e estrutura os dados em JSON
- Sistema salva os boletos como referência para aquela conta

### 2. **Detecção de Fraude**
- Usuário faz upload de um boleto suspeito
- Gemini extrai os dados do novo boleto
- Gemini compara com os boletos de referência e determina:
  - Se é fraudulento ou legítimo
  - Nível de confiança da análise
  - Pontos suspeitos encontrados
  - Recomendação final (PAGAR/NÃO PAGAR/VERIFICAR)

## 🚀 Instalação e Uso

### 1. Configuração

#### Opção 1: Com pip (tradicional)
```bash
# Clone o projeto
git clone https://github.com/diogolast/validaja.git
cd validaja

# Instale dependências
pip install -r requirements.txt
```

#### Opção 2: Com uv (mais rápido)
```bash
# Clone o projeto
git clone https://github.com/diogolast/validaja.git
cd validaja
# Crie um ambiente virtual
uv venv
# Instale dependências com uv
uv pip install -r requirements.txt
```

#### Configure a API Key do Gemini
```bash
# Configure a API Key do Gemini
cp .env.example .env
# Edite .env e adicione sua GEMINI_API_KEY
```

### 2. Execução

#### Com pip:
```bash
streamlit run main.py
```

#### Com uv:
```bash
uv run streamlit run main.py
```

### 3. Como Usar

#### **Passo 1: Cadastrar Conta de Referência**
1. Vá para aba "Cadastrar Conta de Referência"
2. Dê um nome para a conta (ex: "Aluguel Casa Centro")
3. Faça upload de 2+ boletos ORIGINAIS da mesma conta
4. Sistema processará e salvará como referência

#### **Passo 2: Verificar Boleto Suspeito**
1. Vá para aba "Verificar Novo Boleto"  
2. Selecione a conta de referência
3. Faça upload do boleto a ser verificado
4. Analise o resultado:
   - 🟢 **LEGÍTIMO**: Boleto parece original
   - 🔴 **FRAUDULENTO**: Boleto potencialmente falso
   - ⚠️ **VERIFICAR**: Requer análise manual adicional

## 📁 Estrutura do Projeto

```
ValidaJá!/
├── main.py                    # Ponto de entrada
├── requirements.txt           # Dependências pip
├── pyproject.toml            # Configuração uv
├── .env.example              # Configuração da API
├── config/
│   └── settings.py           # Configurações
├── app/
│   ├── ui.py                 # Interface Streamlit
│   ├── gemini_integration.py # IA e processamento
│   └── storage.py            # Persistência de dados
└── data/
    └── contas_referencia.json # Boletos salvos
```

## 🔍 Detecção de Fraudes

O Gemini analisa automaticamente:

### ✅ **Pontos Verificados**
- **Beneficiário**: Nome, documento, endereço
- **Banco**: Código e nome do emissor  
- **Dados**: Linha digitável, código de barras
- **Consistência**: Padrões e formatação
- **Estrutura**: Layout e campos do boleto

### 🚨 **Sinais de Fraude**
- Beneficiário diferente ou alterado
- Banco emissor inconsistente  
- Linha digitável com formato suspeito
- Dados mal formatados
- Informações que não coincidem

## ⚠️ Avisos Importantes

### 🔴 **NUNCA PAGUE** boletos que apresentem:
- Status "FRAUDULENTO" na análise
- Beneficiário diferente da referência
- Dados inconsistentes ou suspeitos

### ✅ **Sempre Verifique**
- Esta é uma ferramenta auxiliar, não substitui análise manual
- Confira todos os dados antes de efetuar pagamentos
- Em caso de dúvida, contate o beneficiário diretamente

## 🛠️ Configuração

### Obter API Key do Gemini
1. Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crie uma nova API Key
3. Adicione no arquivo `.env`:

```env
GEMINI_API_KEY=sua_chave_aqui
```

### Variáveis de Ambiente (.env)
```env
# Obrigatória
GEMINI_API_KEY=sua_chave_da_api_gemini

# Opcional (caminho para salvar dados)
STORAGE_BOLETOS=data/contas_referencia.json
```

## 💡 Dicas de Uso

### 📋 **Para Melhores Resultados**
- Use boletos originais de alta qualidade como referência
- Cadastre boletos de meses diferentes da mesma conta
- Quanto mais boletos de referência, melhor a detecção
- Sempre verifique manualmente antes de pagar

### 🚫 **Limitações**
- Funciona apenas com boletos em PDF
- Requer conexão com internet para API do Gemini
- IA pode não detectar fraudes muito sofisticadas
- Sempre confirme manualmente dados importantes

## 🔒 Segurança e Privacidade

- Boletos são processados temporariamente pelo Gemini
- Dados ficam armazenados localmente no seu computador
- Não compartilhamos informações com terceiros
- Use apenas em ambiente seguro e confiável

## 🐛 Problemas Comuns

### ❌ Erro de API Key
- Verifique se a `GEMINI_API_KEY` está configurada corretamente
- Confirme se a chave é válida no Google AI Studio

### ❌ Erro ao Processar PDF
- Verifique se o arquivo não está corrompido
- Tente com um PDF de melhor qualidade
- Confirme se é realmente um boleto bancário

### ❌ Erro de Conexão
- Verifique sua conexão com internet
- Tente novamente após alguns minutos

## 🏫 Créditos

Projeto desenvolvido durante a **Imersão IA da Alura** em parceria com **Google Gemini**.

## 📄 Licença

Este projeto é para fins educacionais e de estudo.

---

**⚠️ AVISO LEGAL**: Esta ferramenta é auxiliar para detecção de fraudes. Os desenvolvedores não se responsabilizam por pagamentos realizados. Sempre verifique informações manualmente antes de efetuar qualquer pagamento.

**🤖 Powered by Google Gemini AI**
