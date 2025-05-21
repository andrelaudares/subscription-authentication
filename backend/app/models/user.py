from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

# Modelos para a tabela users no banco de dados
class UserDB(BaseModel):
    id: UUID
    email: str
    username: str
    name: str
    cpf_cnpj: str
    asaas_customer_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # Compatibilidade com ORM, útil mesmo sem usar um ORM completo com Supabase

# Modelos para requisições da API
class UserRegister(BaseModel):
    email: str
    password: str
    name: str
    username: str
    cpf_cnpj: str
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

# Modelo para resposta da API (GET /users/me)
class UserProfile(BaseModel):
    id: UUID
    email: str
    username: str
    name: str
    cpf_cnpj: str
    asaas_customer_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None 