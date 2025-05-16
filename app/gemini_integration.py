import os
import tempfile
import json
from typing import Dict, List, Tuple, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from config.settings import GEMINI_API_KEY

# Inicializar cliente Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

class BoletoSchema(BaseModel):
    """Schema para estruturar os dados extraídos do boleto"""
    # Beneficiário (Cedente)
    nome_beneficiario: str = Field(description="Nome completo ou Razão Social do beneficiário (cedente) do boleto.")
    documento_beneficiario: str = Field(description="Número do CNPJ ou CPF do beneficiário (cedente).")
    agencia_codigo_cedente: Optional[str] = Field(default=None, description="Número da agência e código do cedente/beneficiário.")
    endereco_beneficiario: Optional[str] = Field(default=None, description="Endereço completo do beneficiário (cedente).")

    # Pagador (Sacado)  
    nome_pagador: Optional[str] = Field(default=None, description="Nome completo ou Razão Social do pagador (sacado) do boleto.")
    documento_pagador: Optional[str] = Field(default=None, description="Número do CNPJ ou CPF do pagador (sacado).")
    endereco_pagador: Optional[str] = Field(default=None, description="Endereço completo do pagador (sacado).")

    # Dados do Boleto
    codigo_banco_emissor: str = Field(description="Código do banco emissor do boleto (3 dígitos).")
    nome_banco_emissor: Optional[str] = Field(default=None, description="Nome do banco emissor do boleto.")
    linha_digitavel: str = Field(description="Linha digitável completa do boleto.")
    codigo_barras_numerico: Optional[str] = Field(default=None, description="Código de barras numérico (44 dígitos).")
    nosso_numero: Optional[str] = Field(default=None, description="Nosso Número do boleto.")
    numero_documento_boleto: Optional[str] = Field(default=None, description="Número do documento/boleto.")
    data_vencimento: str = Field(description="Data de vencimento no formato DD/MM/AAAA.")
    data_documento: Optional[str] = Field(default=None, description="Data de emissão no formato DD/MM/AAAA.")
    valor_documento: float = Field(description="Valor do documento/boleto.")
    valor_cobrado: Optional[float] = Field(default=None, description="Valor final a ser cobrado.")
    
    # Campos adicionais
    especie_doc: Optional[str] = Field(default=None, description="Espécie do documento.")
    local_pagamento: Optional[str] = Field(default=None, description="Local de pagamento.")
    demonstrativo: List[str] = Field(default_factory=list, description="Linhas do demonstrativo/detalhamento.")
    instrucoes_caixa: List[str] = Field(default_factory=list, description="Instruções para o caixa.")


# Prompt para extração de dados do PDF
PROMPT_EXTRACAO = """
Analise este boleto bancário brasileiro e extraia TODAS as informações visíveis.

INSTRUÇÕES IMPORTANTES:
1. Extraia exatamente o que está escrito no boleto
2. Para datas, use o formato DD/MM/AAAA
3. Para valores, use números decimais (ex: 1234.56)
4. Para documentos (CPF/CNPJ), mantenha a formatação original
5. Se algum campo não estiver visível, coloque "N/A"
6. Seja precisos com nomes, códigos e números

Retorne os dados no formato JSON estruturado conforme o schema.
"""


class AnaliseComparacaoSchema(BaseModel):
    """Schema para análise de comparação entre boletos"""
    eh_fraudulento: bool = Field(description="True se o boleto é potencialmente fraudulento, False se parece legítimo")
    nivel_confianca: float = Field(description="Nível de confiança da análise (0.0 a 1.0)")
    resumo_analise: str = Field(description="Resumo da análise explicando o resultado")
    diferencas_encontradas: List[str] = Field(description="Lista das principais diferenças encontradas")
    pontos_suspeitos: List[str] = Field(description="Lista de pontos suspeitos identificados")
    recomendacao: str = Field(description="Recomendação final (PAGAR, NAO_PAGAR, VERIFICAR_MANUALMENTE)")


def criar_prompt_comparacao(boletos_referencia: List[Dict], boleto_analise: Dict) -> str:
    """Cria prompt para comparação de boletos"""
    return f"""
Você é um especialista em detecção de fraudes em boletos bancários.

TAREFA: Analisar se o boleto em questão é potencialmente FRAUDULENTO comparando com boletos de referência ORIGINAIS da mesma conta.

BOLETOS DE REFERÊNCIA (ORIGINAIS - MESMA CONTA):
```json
{json.dumps(boletos_referencia, indent=2, ensure_ascii=False)}
```

BOLETO PARA ANÁLISE:
```json
{json.dumps(boleto_analise, indent=2, ensure_ascii=False)}
```

CRITÉRIOS DE ANÁLISE:
1. **Beneficiário**: Nome, documento, agência devem ser IDÊNTICOS
2. **Banco**: Código e nome do banco devem ser os mesmos
3. **Estrutura**: Formato da linha digitável, código de barras
4. **Padrões**: Verificar se segue o mesmo padrão dos boletos originais
5. **Inconsistências**: Detectar qualquer informação que não faça sentido

SINAIS DE FRAUDE COMUNS:
- Beneficiário diferente ou com pequenas alterações
- Banco emissor diferente
- Linha digitável com padrão inconsistente
- Dados mal formatados ou inconsistentes
- Endereços ou informações que não coincidem

ANÁLISE SOLICITADA:
- Compare meticulosamente todos os campos relevantes
- Identifique qualquer divergência significativa
- Avalie o nível de suspeita
- Forneça uma recomendação clara

Seja rigoroso na análise. É melhor ser cauteloso demais do que permitir uma fraude.
"""


def extrair_dados_boleto(arquivo_pdf_bytes: bytes) -> Tuple[Dict, bool]:
    """
    Extrai dados do boleto usando Gemini
    
    Args:
        arquivo_pdf_bytes: Bytes do arquivo PDF
    
    Returns:
        Tuple[Dict, bool]: (dados_extraidos, sucesso)
    """
    try:
        # Cria arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(arquivo_pdf_bytes)
            temp_file.flush()
            
            try:
                # Upload para Gemini
                file_upload = client.files.upload(file=temp_file.name)
                
                # Extrai dados
                response = client.models.generate_content(
                    model='gemini-2.0-flash-001',
                    contents=[PROMPT_EXTRACAO, file_upload],
                    config=types.GenerateContentConfig(
                        response_mime_type='application/json',
                        response_schema=BoletoSchema,
                    ),
                )
                
                dados_boleto = json.loads(response.text)
                return dados_boleto, True
                
            finally:
                # Remove arquivo temporário
                os.unlink(temp_file.name)
                
    except Exception as e:
        print(f"Erro ao extrair dados do boleto: {e}")
        return {}, False


def normalizar_dados_comparacao(boleto: Dict) -> Dict:
    """
    Normaliza dados do boleto focando nos campos essenciais para comparação
    """
    return {
        # Campos essenciais que devem ser idênticos
        'nome_beneficiario': boleto.get('nome_beneficiario', '').strip().upper(),
        'documento_beneficiario': boleto.get('documento_beneficiario', '').replace('.', '').replace('/', '').replace('-', '').strip(),
        'codigo_banco_emissor': boleto.get('codigo_banco_emissor', '').replace('-', '').strip(),
        'agencia_codigo_cedente': boleto.get('agencia_codigo_cedente', '').strip(),
        'endereco_beneficiario': boleto.get('endereco_beneficiario', '').strip().upper(),
        
        # Campos que podem variar (para contexto)
        'valor_documento': boleto.get('valor_documento'),
        'nosso_numero': boleto.get('nosso_numero'),
        'linha_digitavel': boleto.get('linha_digitavel'),
        'data_vencimento': boleto.get('data_vencimento'),
    }


def analisar_fraude_boleto(boletos_referencia: List[Dict], boleto_analise: Dict) -> Tuple[Dict, bool]:
    """
    Analisa se o boleto é fraudulento comparando com boletos de referência
    
    Args:
        boletos_referencia: Lista de boletos originais da mesma conta
        boleto_analise: Boleto a ser analisado
    
    Returns:
        Tuple[Dict, bool]: (resultado_analise, sucesso)
    """
    try:
        # Verificação dos campos essenciais (que DEVEM ser idênticos)
        ref_normalizado = normalizar_dados_comparacao(boletos_referencia[0])
        analise_normalizado = normalizar_dados_comparacao(boleto_analise)
        
        # Lista para armazenar apenas problemas REAIS
        problemas_reais = []
        pontos_suspeitos = []
        
        # Verifica nome do beneficiário (deve ser exato)
        if ref_normalizado['nome_beneficiario'] != analise_normalizado['nome_beneficiario']:
            problemas_reais.append(f"Nome do beneficiário diferente: '{boleto_analise.get('nome_beneficiario')}' vs '{boletos_referencia[0].get('nome_beneficiario')}'")
            pontos_suspeitos.append("Nome do beneficiário não confere")
        
        # Verifica documento do beneficiário (deve ser idêntico)
        if ref_normalizado['documento_beneficiario'] != analise_normalizado['documento_beneficiario']:
            problemas_reais.append(f"Documento do beneficiário diferente: '{boleto_analise.get('documento_beneficiario')}' vs '{boletos_referencia[0].get('documento_beneficiario')}'")
            pontos_suspeitos.append("CNPJ/CPF do beneficiário não confere")
        
        # Verifica banco emissor (deve ser o mesmo)
        if ref_normalizado['codigo_banco_emissor'] != analise_normalizado['codigo_banco_emissor']:
            problemas_reais.append(f"Banco emissor diferente: '{boleto_analise.get('codigo_banco_emissor')}' vs '{boletos_referencia[0].get('codigo_banco_emissor')}'")
            pontos_suspeitos.append("Banco emissor não confere")
        
        # Verifica agência/cedente (deve ser igual)
        if ref_normalizado.get('agencia_codigo_cedente') and analise_normalizado.get('agencia_codigo_cedente'):
            if ref_normalizado['agencia_codigo_cedente'] != analise_normalizado['agencia_codigo_cedente']:
                problemas_reais.append(f"Agência/cedente diferente: '{boleto_analise.get('agencia_codigo_cedente')}' vs '{boletos_referencia[0].get('agencia_codigo_cedente')}'")
                pontos_suspeitos.append("Agência/código cedente não confere")
        
        # Se há problemas REAIS, é fraude
        if problemas_reais:
            return {
                'eh_fraudulento': True,
                'nivel_confianca': 0.95,
                'resumo_analise': f"Boleto fraudulento detectado devido a divergências críticas: {'; '.join(problemas_reais)}",
                'diferencas_encontradas': problemas_reais,
                'pontos_suspeitos': pontos_suspeitos,
                'recomendacao': 'NAO_PAGAR'
            }, True
        
        # Se chegou aqui, os campos essenciais conferem
        # Agora vamos fazer uma análise mais refinada, mas sendo menos rigoroso
        # 
        # Nota: Valores, datas, nosso número e linha digitável DIFERENTES são NORMAIS!
        
        # Vamos verificar se há padrões muito estranhos nos campos variáveis
        anomalias_menores = []
        
        # Verifica se o padrão do nosso número é muito diferente (apenas o formato, não o número)
        nosso_nums_ref = [b.get('nosso_numero', '') for b in boletos_referencia if b.get('nosso_numero')]
        nosso_num_analise = boleto_analise.get('nosso_numero', '')
        
        if nosso_nums_ref and nosso_num_analise:
            # Extrai o padrão (formato) do nosso número
            import re
            padroes_ref = [re.sub(r'\d', '#', n) for n in nosso_nums_ref]
            padrao_analise = re.sub(r'\d', '#', nosso_num_analise)
            
            if padrao_analise not in padroes_ref and len(set(padroes_ref)) == 1:
                anomalias_menores.append(f"Formato do nosso número diferente: {padrao_analise} vs {padroes_ref[0]}")
        
        # Se os campos essenciais estão OK e não há anomalias graves, classifica como legítimo
        if not anomalias_menores:
            return {
                'eh_fraudulento': False,
                'nivel_confianca': 0.90,
                'resumo_analise': 'Boleto validado com sucesso. Todos os dados essenciais (beneficiário, documento, banco) conferem com os boletos de referência. As diferenças encontradas (valor, datas, nosso número) são variações normais entre boletos da mesma conta.',
                'diferencas_encontradas': [
                    'Valor do documento: normal ser diferente entre boletos de meses diferentes',
                    'Datas: normal variar entre períodos diferentes',
                    'Nosso número: sempre único para cada boleto',
                    'Linha digitável: varia conforme valor e nosso número'
                ],
                'pontos_suspeitos': [],
                'recomendacao': 'PAGAR'
            }, True
        
        # Se há apenas anomalias menores, recomenda verificação manual
        return {
            'eh_fraudulento': False,
            'nivel_confianca': 0.70,
            'resumo_analise': f'Boleto parece legítimo, mas apresenta algumas pequenas variações que merecem atenção: {"; ".join(anomalias_menores)}. Os dados essenciais (beneficiário, documento, banco) conferem corretamente.',
            'diferencas_encontradas': anomalias_menores,
            'pontos_suspeitos': ['Pequenas variações no formato detectadas'],
            'recomendacao': 'VERIFICAR_MANUALMENTE'
        }, True
        
    except Exception as e:
        print(f"Erro ao analisar fraude: {e}")
        return {}, False


def processar_multiplos_boletos_referencia(arquivos_pdf: List[Tuple[bytes, str]]) -> Tuple[List[Dict], bool]:
    """
    Processa múltiplos boletos para criar referência
    
    Args:
        arquivos_pdf: Lista de tuplas (bytes_do_arquivo, nome_do_arquivo)
    
    Returns:
        Tuple[List[Dict], bool]: (boletos_processados, sucesso)
    """
    boletos_processados = []
    
    for arquivo_bytes, nome_arquivo in arquivos_pdf:
        dados_boleto, sucesso = extrair_dados_boleto(arquivo_bytes)
        if sucesso:
            dados_boleto['nome_arquivo'] = nome_arquivo
            boletos_processados.append(dados_boleto)
        else:
            return [], False
    
    return boletos_processados, len(boletos_processados) >= 2