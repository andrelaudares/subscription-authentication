import os
import requests
from ..core.config import ASAAS_API_KEY

ASAAS_API_URL = "https://api-sandbox.asaas.com/v3"

def get_asaas_api_key() -> str:
    key = os.environ.get("ASAAS_API_KEY")
    if not key:
        raise ValueError("Variável de ambiente ASAAS_API_KEY deve estar configurada.")
    return key

def asaas_request(method: str, endpoint: str, data: dict = None) -> requests.Response:
    """
    Função genérica para fazer requisições à API do Asaas.
    """
    api_key = get_asaas_api_key()
    headers = {
        "access_token": api_key,
        "Content-Type": "application/json"
    }
    url = f"{ASAAS_API_URL}/{endpoint}"

    if method.upper() == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method.upper() == "GET":
        response = requests.get(url, headers=headers, params=data)
    elif method.upper() == "PUT":
        response = requests.put(url, headers=headers, json=data)
    elif method.upper() == "DELETE":
        response = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Método HTTP não suportado: {method}")

    response.raise_for_status() # Lança exceção para códigos de status HTTP de erro
    return response

def create_asaas_customer(customer_data: dict) -> dict:
    """
    Cria um novo cliente no Asaas.
    """
    response = asaas_request("POST", "customers", data=customer_data)
    return response.json() 