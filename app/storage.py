import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class ContaReferenciaStorage:
    """Classe para gerenciar o armazenamento de contas de referência"""

    def __init__(self, arquivo_storage: str = None):
        """
        Inicializa o storage

        Args:
            arquivo_storage: Caminho para o arquivo de storage. Se None, usa STORAGE_BOLETOS
        """
        self.arquivo_storage = arquivo_storage or "data/contas_referencia.json"

        # Cria diretório se não existir
        os.makedirs(os.path.dirname(self.arquivo_storage), exist_ok=True)

        # Inicializa arquivo se não existir
        if not os.path.exists(self.arquivo_storage):
            self._salvar_dados({})

    def _carregar_dados(self) -> Dict:
        """Carrega dados do arquivo"""
        try:
            with open(self.arquivo_storage, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _salvar_dados(self, dados: Dict):
        """Salva dados no arquivo"""
        with open(self.arquivo_storage, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    def salvar_conta_referencia(
        self, apelido_conta: str, boletos_dados: List[Dict]
    ) -> bool:
        """
        Salva uma conta de referência com múltiplos boletos

        Args:
            apelido_conta: Nome/apelido da conta
            boletos_dados: Lista com dados dos boletos processados

        Returns:
            bool: True se salvou com sucesso
        """
        if not boletos_dados or len(boletos_dados) < 2:
            return False

        # Extrai informações básicas do primeiro boleto para identificação rápida
        boleto_base = boletos_dados[0]

        conta_referencia = {
            "apelido_conta": apelido_conta,
            "nome_beneficiario": boleto_base.get("nome_beneficiario", "N/A"),
            "documento_beneficiario": boleto_base.get("documento_beneficiario", "N/A"),
            "codigo_banco_emissor": boleto_base.get("codigo_banco_emissor", "N/A"),
            "numero_boletos_base": len(boletos_dados),
            "data_criacao": datetime.now().isoformat(),
            "boletos_referencia": boletos_dados,  # Todos os boletos para comparação
        }

        # Carrega dados existentes
        dados = self._carregar_dados()

        # Salva nova conta
        dados[apelido_conta] = conta_referencia

        # Persiste no arquivo
        self._salvar_dados(dados)
        return True

    def obter_conta_referencia(self, apelido_conta: str) -> Optional[Dict]:
        """
        Obtém dados de uma conta de referência

        Args:
            apelido_conta: Nome/apelido da conta

        Returns:
            Dict ou None: Dados da conta ou None se não encontrada
        """
        dados = self._carregar_dados()
        return dados.get(apelido_conta)

    def obter_boletos_referencia(self, apelido_conta: str) -> List[Dict]:
        """
        Obtém os boletos de referência de uma conta

        Args:
            apelido_conta: Nome/apelido da conta

        Returns:
            List[Dict]: Lista de boletos de referência
        """
        conta = self.obter_conta_referencia(apelido_conta)
        if conta:
            return conta.get("boletos_referencia", [])
        return []

    def listar_contas_referencia(self) -> List[Dict]:
        """
        Lista todas as contas de referência cadastradas (sem os boletos completos)

        Returns:
            List[Dict]: Lista de contas de referência (dados resumidos)
        """
        dados = self._carregar_dados()
        contas_resumidas = []

        for conta in dados.values():
            conta_resumida = {
                "apelido_conta": conta.get("apelido_conta"),
                "nome_beneficiario": conta.get("nome_beneficiario"),
                "documento_beneficiario": conta.get("documento_beneficiario"),
                "codigo_banco_emissor": conta.get("codigo_banco_emissor"),
                "numero_boletos_base": conta.get("numero_boletos_base"),
                "data_criacao": conta.get("data_criacao"),
            }
            contas_resumidas.append(conta_resumida)

        return contas_resumidas

    def remover_conta_referencia(self, apelido_conta: str) -> bool:
        """
        Remove uma conta de referência

        Args:
            apelido_conta: Nome/apelido da conta

        Returns:
            bool: True se removeu com sucesso
        """
        dados = self._carregar_dados()
        if apelido_conta in dados:
            del dados[apelido_conta]
            self._salvar_dados(dados)
            return True
        return False

    def conta_existe(self, apelido_conta: str) -> bool:
        """
        Verifica se uma conta existe

        Args:
            apelido_conta: Nome/apelido da conta

        Returns:
            bool: True se a conta existe
        """
        dados = self._carregar_dados()
        return apelido_conta in dados


# Instância global para uso no projeto
storage = ContaReferenciaStorage()
