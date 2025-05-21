from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

# Modelos para a tabela subscriptions no banco de dados
class SubscriptionDB(BaseModel):
    id: UUID
    user_id: UUID
    subscription_id: str
    status: str
    plan: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # Compatibilidade com ORM

# Modelos aninhados para dados de cartão de crédito na criação de assinatura
class CreditCardInfo(BaseModel):
    number: str
    holderName: str
    expirationMonth: int
    expirationYear: int
    cvv: str

# Removido AddressInfo pois os campos serão incorporados em CreditCardHolderInfoAsaas
# class AddressInfo(BaseModel):
#     street: str
#     number: str
#     district: str
#     city: str
#     state: str
#     postalCode: str
#     country: str

# Modelo para CreditCardHolderInfo especificamente para o payload do Asaas
class CreditCardHolderInfoAsaas(BaseModel):
    name: str
    email: Optional[str] = None # O Asaas mostra email no exemplo, vamos adicionar
    cpfCnpj: str
    postalCode: str
    address: Optional[str] = None # Nome da rua/logradouro
    addressNumber: str
    addressComplement: Optional[str] = None
    phone: Optional[str] = None # Telefone do titular
    mobilePhone: Optional[str] = None # Celular do titular (pode ser o mesmo que phone)
    # 'district' (bairro) também é um campo comum, embora não explicitamente no exemplo mais simples do Asaas.
    # Se o Asaas reclamar de campos ausentes, podemos adicioná-lo.
    # Para manter alinhado com o exemplo da documentação: https://docs.asaas.com/reference/tokenizacao-de-cartao-de-credito
    # City e State não estão no exemplo de creditCardHolderInfo, mas são importantes.
    # A API do Asaas para criação de cliente os tem. Vamos ver se são inferidos ou se precisamos adicioná-los.
    # A documentação de "Criar Assinatura com Cartão" não detalha todos os campos de creditCardHolderInfo,
    # mas a de tokenização sim.

# Modelo para requisição de criação de assinatura vindo do nosso frontend/cliente
class SubscriptionCreatePayload(BaseModel):
    billing_type: str
    next_due_date: str
    value: float
    cycle: str
    plan: str
    description: Optional[str] = None
    credit_card: Optional[CreditCardInfo] = None
    # Para a requisição da nossa API, vamos manter uma estrutura mais organizada para o endereço do titular
    # e depois transformar isso para o formato "flat" do Asaas na rota.
    credit_card_holder_name: Optional[str] = None
    credit_card_holder_cpf_cnpj: Optional[str] = None
    credit_card_holder_email: Optional[str] = None # Adicionado
    credit_card_holder_postal_code: Optional[str] = None
    credit_card_holder_address: Optional[str] = None # Rua
    credit_card_holder_address_number: Optional[str] = None
    credit_card_holder_address_complement: Optional[str] = None
    credit_card_holder_phone: Optional[str] = None # Adicionado
    # Adicionaremos district, city, state se o Asaas exigir.

# Modelo para resposta ao cancelar assinatura
class SubscriptionCancelResponse(BaseModel):
    message: str

# Modelo para resposta ao obter detalhes da assinatura (GET /subscriptions/{subscription_id})
class SubscriptionDetails(BaseModel):
     id: UUID
     user_id: UUID
     subscription_id: str
     status: str
     plan: str
     created_at: datetime
     updated_at: datetime 