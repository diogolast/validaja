import streamlit as st
from typing import Dict
import traceback

# Imports internos
from app.gemini_integration import (
    extrair_dados_boleto,
    analisar_fraude_boleto,
    processar_multiplos_boletos_referencia
)
from app.storage import storage


def mostrar_dados_boleto(dados: Dict, titulo: str = "Dados do Boleto", mostrar_expander: bool = True):
    """Exibe dados de um boleto de forma organizada"""
    st.subheader(titulo)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Beneficiário:**")
        st.write(f"Nome: {dados.get('nome_beneficiario', 'N/A')}")
        st.write(f"Documento: {dados.get('documento_beneficiario', 'N/A')}")
        st.write(f"Endereço: {dados.get('endereco_beneficiario', 'N/A')}")
        
        st.write("**Banco:**")
        st.write(f"Código: {dados.get('codigo_banco_emissor', 'N/A')}")
        st.write(f"Nome: {dados.get('nome_banco_emissor', 'N/A')}")
    
    with col2:
        st.write("**Valor e Datas:**")
        st.write(f"Valor Documento: R$ {dados.get('valor_documento', 'N/A')}")
        st.write(f"Valor Cobrado: R$ {dados.get('valor_cobrado', 'N/A')}")
        st.write(f"Vencimento: {dados.get('data_vencimento', 'N/A')}")
        st.write(f"Data Documento: {dados.get('data_documento', 'N/A')}")
        
        st.write("**Linha Digitável:**")
        st.code(dados.get('linha_digitavel', 'N/A'))
    
    # Detalhes em expansor apenas se permitido
    if mostrar_expander:
        with st.expander("Ver todos os dados extraídos"):
            st.json(dados)
    else:
        st.write("**Todos os dados extraídos:**")
        st.json(dados)


def mostrar_contas_referencia_cadastradas():
    """Mostra as contas de referência cadastradas"""
    st.subheader("Contas de Referência Cadastradas")
    
    contas = storage.listar_contas_referencia()
    
    if contas:
        for conta in contas:
            with st.expander(
                f"**{conta['apelido_conta']}** - "
                f"{conta.get('nome_beneficiario', 'N/A')} "
                f"({conta.get('numero_boletos_base', 0)} boletos)"
            ):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Beneficiário:** {conta.get('nome_beneficiario', 'N/A')}")
                    st.write(f"**Documento:** {conta.get('documento_beneficiario', 'N/A')}")
                    st.write(f"**Banco:** {conta.get('codigo_banco_emissor', 'N/A')}")
                    st.write(f"**Criado em:** {conta.get('data_criacao', 'N/A')[:10]}")
                
                with col2:
                    if st.button("🗑️ Remover", key=f"remove_{conta['apelido_conta']}"):
                        if storage.remover_conta_referencia(conta['apelido_conta']):
                            st.success(f"Conta '{conta['apelido_conta']}' removida!")
                            st.rerun()
                        else:
                            st.error("Erro ao remover conta")
    else:
        st.info("Nenhuma conta de referência cadastrada ainda.")


def aba_cadastrar_referencia_conta():
    """Aba para cadastrar conta de referência"""
    st.header("📁 Cadastre uma Conta de Referência")
    st.markdown("""
        Faça upload de **pelo menos 2 boletos ORIGINAIS** da mesma conta, preferencialmente de meses diferentes.
        Estes boletos serão usados como referência para detectar fraudes.
        
        ⚠️ **IMPORTANTE**: Use apenas boletos que você tem certeza absoluta que são legítimos!
    """)

    with st.form(key="form_cadastro_conta"):
        apelido_conta = st.text_input(
            "Nome/Apelido para esta conta:",
            placeholder="Ex: Aluguel Casa Centro, Mensalidade Escola, Conta de Luz",
            key="apelido_conta_cad"
        )
        
        uploaded_files_referencia = st.file_uploader(
            "Selecione os PDFs dos boletos ORIGINAIS (pelo menos 2)",
            type=["pdf"],
            accept_multiple_files=True,
            key="files_referencia_cad",
            help="Faça upload de boletos que você tem certeza que são legítimos. Quanto mais boletos, melhor a detecção."
        )
        
        submit_button_conta = st.form_submit_button(label="🔄 Processar e Salvar Conta de Referência")

    if submit_button_conta:
        if not apelido_conta:
            st.warning("⚠️ Por favor, forneça um nome para a conta de referência.")
            return
        
        if not uploaded_files_referencia or len(uploaded_files_referencia) < 2:
            st.warning("⚠️ Por favor, selecione pelo menos 2 arquivos PDF.")
            return
        
        if storage.conta_existe(apelido_conta):
            st.error(f"❌ Já existe uma conta com o nome '{apelido_conta}'. Escolha outro nome.")
            return
        
        # Processa os boletos
        with st.spinner(f"🔄 Processando {len(uploaded_files_referencia)} boletos..."):
            try:
                # Prepara arquivos para processamento
                arquivos_para_processar = []
                for uploaded_file in uploaded_files_referencia:
                    arquivo_bytes = uploaded_file.read()
                    arquivos_para_processar.append((arquivo_bytes, uploaded_file.name))
                
                # Processa boletos com Gemini
                boletos_dados, sucesso = processar_multiplos_boletos_referencia(arquivos_para_processar)
                
                if not sucesso or not boletos_dados:
                    st.error("❌ Erro ao processar os boletos. Verifique se os arquivos são PDFs válidos.")
                    return
                
                # Salva a conta de referência
                if storage.salvar_conta_referencia(apelido_conta, boletos_dados):
                    st.success(f"✅ Conta '{apelido_conta}' salva com sucesso!")
                    
                    # Mostra resumo
                    boleto_base = boletos_dados[0]
                    st.info(
                        f"📋 **Conta salva:**\n\n"
                        f"**Beneficiário:** {boleto_base.get('nome_beneficiario', 'N/A')}\n\n"
                        f"**Documento:** {boleto_base.get('documento_beneficiario', 'N/A')}\n\n"
                        f"**Banco:** {boleto_base.get('codigo_banco_emissor', 'N/A')}\n\n"
                        f"**Total de boletos:** {len(boletos_dados)}"
                    )
                    
                    st.balloons()
                    
                    # Mostra detalhes dos boletos processados
                    with st.expander("👁️ Ver detalhes dos boletos processados"):
                        for i, boleto in enumerate(boletos_dados):
                            st.write(f"**Boleto {i+1}:** {boleto.get('nome_arquivo', 'N/A')}")
                            mostrar_dados_boleto(boleto, f"Boleto {i+1}", mostrar_expander=False)
                    
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar a conta de referência.")
                    
            except Exception as e:
                st.error(f"❌ Erro inesperado: {str(e)}")
                with st.expander("Ver detalhes do erro"):
                    st.code(traceback.format_exc())

    st.divider()
    mostrar_contas_referencia_cadastradas()


def mostrar_resultado_analise(resultado: Dict):
    """Mostra o resultado da análise de fraude"""
    st.subheader("🔍 Resultado da Análise de Fraude")
    
    # Status principal
    if resultado.get('eh_fraudulento'):
        st.error("🚨 **BOLETO POTENCIALMENTE FRAUDULENTO**")
    else:
        st.success("✅ **BOLETO PARECE LEGÍTIMO**")
    
    # Nível de confiança
    confianca = resultado.get('nivel_confianca', 0)
    st.metric("Nível de Confiança", f"{confianca:.1%}")
    
    # Recomendação
    recomendacao = resultado.get('recomendacao', 'VERIFICAR_MANUALMENTE')
    if recomendacao == 'NAO_PAGAR':
        st.error(f"🚫 **RECOMENDAÇÃO: {recomendacao}**")
    elif recomendacao == 'PAGAR':
        st.success(f"💰 **RECOMENDAÇÃO: {recomendacao}**")
    else:
        st.warning(f"⚠️ **RECOMENDAÇÃO: {recomendacao}**")
    
    # Resumo da análise
    st.subheader("📝 Resumo da Análise")
    st.write(resultado.get('resumo_analise', 'Análise não disponível'))
    
    # Diferenças encontradas
    diferencas = resultado.get('diferencas_encontradas', [])
    if diferencas:
        st.subheader("⚡ Diferenças Encontradas")
        for diferenca in diferencas:
            st.write(f"• {diferenca}")
    
    # Pontos suspeitos
    pontos_suspeitos = resultado.get('pontos_suspeitos', [])
    if pontos_suspeitos:
        st.subheader("🔴 Pontos Suspeitos")
        for ponto in pontos_suspeitos:
            st.write(f"• {ponto}")


def aba_verificar_novo_boleto():
    """Aba para verificar um novo boleto"""
    st.header("🔍 Verifique um Novo Boleto")
    st.markdown("Faça o upload de um boleto para verificar se é fraudulento.")

    # Selecionar conta de referência
    contas_referencia = storage.listar_contas_referencia()
    
    if not contas_referencia:
        st.warning("⚠️ Você precisa cadastrar pelo menos uma conta de referência antes de verificar boletos.")
        st.info("👆 Vá para a aba 'Cadastrar Conta de Referência' primeiro.")
        return
    
    conta_nomes = [conta["apelido_conta"] for conta in contas_referencia]
    
    conta_selecionada = st.selectbox(
        "Selecione a conta de referência para comparação:",
        options=conta_nomes,
        key="select_conta_referencia"
    )

    uploaded_file_verificar = st.file_uploader(
        "Selecione o PDF do boleto para verificar",
        type=["pdf"],
        key="file_verificar",
        help="Faça upload do boleto que você suspeita que pode ser fraudulento"
    )

    if st.button("🚀 Analisar Boleto", key="btn_analisar"):
        if not uploaded_file_verificar:
            st.warning("⚠️ Por favor, selecione um arquivo PDF para verificar.")
            return
        
        with st.spinner("🔄 Analisando boleto com IA..."):
            try:
                # Extrai dados do novo boleto
                arquivo_bytes = uploaded_file_verificar.read()
                dados_boleto_novo, sucesso_extracao = extrair_dados_boleto(arquivo_bytes)
                
                if not sucesso_extracao:
                    st.error("❌ Erro ao processar o boleto. Verifique se o arquivo é um PDF válido.")
                    return
                
                # Mostra dados extraídos
                st.subheader("📄 Dados Extraídos do Boleto")
                mostrar_dados_boleto(dados_boleto_novo)
                
                # Obtém boletos de referência
                boletos_referencia = storage.obter_boletos_referencia(conta_selecionada)
                
                if not boletos_referencia:
                    st.error(f"❌ Erro: boletos de referência não encontrados para '{conta_selecionada}'")
                    return
                
                # Analisa fraude usando Gemini
                st.divider()
                with st.spinner("🤖 Análise de fraude em progresso..."):
                    resultado_analise, sucesso_analise = analisar_fraude_boleto(
                        boletos_referencia, 
                        dados_boleto_novo
                    )
                
                if not sucesso_analise:
                    st.error("❌ Erro ao analisar o boleto para detecção de fraude.")
                    return
                
                # Mostra resultado da análise
                mostrar_resultado_analise(resultado_analise)
                
                # Aviso final
                st.divider()
                st.warning(
                    "⚠️ **IMPORTANTE**: Esta é uma análise automatizada assistida por IA. "
                    "Sempre verifique manualmente as informações antes de efetuar qualquer pagamento."
                )
                
            except Exception as e:
                st.error(f"❌ Erro inesperado ao analisar boleto: {str(e)}")
                with st.expander("Ver detalhes do erro"):
                    st.code(traceback.format_exc())


def rodar_ui():
    """Função principal para executar a interface"""
    st.set_page_config(
        page_title="ValidaJá! - Detector de Boletos Fraudulentos", 
        page_icon="🔍",
        layout="wide", 
        initial_sidebar_state="auto"
    )
    
    # Header
    st.title("🔍 ValidaJá! - Detector de Boletos Fraudulentos")
    st.caption("Detecte boletos falsos usando Inteligência Artificial")
    
    # Aviso importante
    with st.container():
        st.info(
            "ℹ️ **Como funciona**: Cadastre boletos originais de uma conta como referência, "
            "depois compare novos boletos para detectar possíveis fraudes."
        )
    
    st.markdown("---")

    # Verificações iniciais
    if not st.session_state.get('gemini_api_key_checked'):
        from config.settings import GEMINI_API_KEY
        if not GEMINI_API_KEY:
            st.error(
                "❌ **GEMINI_API_KEY não configurada!** "
                "Configure a variável de ambiente GEMINI_API_KEY no arquivo .env"
            )
            st.stop()
        st.session_state.gemini_api_key_checked = True

    # Tabs principais
    tab_cadastrar, tab_verificar = st.tabs([
        "📁 Cadastrar Conta de Referência", 
        "🔍 Verificar Novo Boleto"
    ])

    with tab_cadastrar:
        aba_cadastrar_referencia_conta()

    with tab_verificar:
        aba_verificar_novo_boleto()
    
    # Footer
    st.markdown("---")
    st.caption("🤖 Powered by Google Gemini AI | ⚠️ Sempre verifique manualmente antes de pagar")