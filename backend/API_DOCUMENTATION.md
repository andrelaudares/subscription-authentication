# Documentação da API: Template SaaS com Supabase e Asaas

Esta documentação descreve os endpoints da API backend para o template de sistema SaaS, utilizando FastAPI, Supabase para autenticação e Asaas para gerenciamento de assinaturas e pagamentos.

O backend está configurado para rodar localmente (para desenvolvimento/teste). As URLs de exemplo abaixo consideram que a API está rodando em `http://localhost:8000`.

**Base URL:** `http://localhost:8000`

**Autenticação:** As rotas protegidas exigem um token JWT válido no cabeçalho `Authorization: Bearer <token>`. O token é obtido através da rota de login (`POST /auth/login`).

---

## 1. Autenticação (`/auth`)

### `POST /auth/register`
Registra um novo usuário no Supabase Auth, cria um cliente correspondente no Asaas e armazena dados adicionais na tabela `public.users`.

- **Endpoint:** `/auth/register`
- **Método:** `POST`

**Header Parameters:**
- `Content-Type`: `application/json`

**Request Body:**
```json
{
  "email": "usuario.teste@example.com",
  "password": "senhaSegura123",
  "name": "Usuário de Teste",
  "username": "usuario_teste",
  "cpf_cnpj": "12345678900",
  "address": "Rua de Exemplo, 123",
  "phone": "11987654321",
  "description": "Cliente de teste via API"
}
```

**Exemplo de Requisição (`curl`):**
```bash
curl -X POST "http://localhost:8000/auth/register" \
-H "Content-Type: application/json" \
-d '{
  "email": "usuario.teste@example.com",
  "password": "senhaSegura123",
  "name": "Usuário de Teste",
  "username": "usuario_teste",
  "cpf_cnpj": "12345678900",
  "address": "Rua de Exemplo, 123",
  "phone": "11987654321",
  "description": "Cliente de teste via API"
}'
```

**Responses:**
- `201 Created`: Usuário registrado com sucesso.
```json
{
  "message": "Usuário registrado com sucesso",
  "user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```
- `400 Bad Request`: Dados inválidos na requisição.
- `500 Internal Server Error`: Erro ao registrar o usuário ou criar cliente Asaas.

---

### `POST /auth/login`
Autentica um usuário existente e retorna um token JWT para acesso a rotas protegidas.

- **Endpoint:** `/auth/login`
- **Método:** `POST`

**Header Parameters:**
- `Content-Type`: `application/json`

**Request Body:**
```json
{
  "email": "usuario.teste@example.com",
  "password": "senhaSegura123"
}
```

**Exemplo de Requisição (`curl`):**
```bash
curl -X POST "http://localhost:8000/auth/login" \
-H "Content-Type: application/json" \
-d '{
  "email": "usuario.teste@example.com",
  "password": "senhaSegura123"
}'
```

**Responses:**
- `200 OK`: Login bem-sucedido, retorna token JWT.
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```
- `401 Unauthorized`: Credenciais inválidas.
- `500 Internal Server Error`: Erro interno no servidor.

---

### `POST /auth/logout`
Invalida a sessão atual do usuário no Supabase Auth. Requer autenticação.

- **Endpoint:** `/auth/logout`
- **Método:** `POST`

**Header Parameters:**
- `Authorization`: `Bearer <token>`

**Exemplo de Requisição (`curl`):**
```bash
# Substitua <SEU_TOKEN_JWT> pelo token obtido no login
curl -X POST "http://localhost:8000/auth/logout" \
-H "Authorization: Bearer <SEU_TOKEN_JWT>"
```

**Responses:**
- `200 OK`: Logout realizado com sucesso.
```json
{
  "message": "Logout realizado com sucesso"
}
```
- `401 Unauthorized`: Token inválido ou ausente.
- `500 Internal Server Error`: Erro durante o logout.

---

## 2. Usuários (`/users`)

### `GET /users/me`
Retorna os dados do perfil do usuário autenticado. Requer autenticação.

- **Endpoint:** `/users/me`
- **Método:** `GET`

**Header Parameters:**
- `Authorization`: `Bearer <token>`

**Exemplo de Requisição (`curl`):**
```bash
# Substitua <SEU_TOKEN_JWT> pelo token obtido no login
curl -X GET "http://localhost:8000/users/me" \
-H "Authorization: Bearer <SEU_TOKEN_JWT>"
```

**Responses:**
- `200 OK`: Dados do perfil do usuário.
```json
{
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "email": "usuario.teste@example.com",
  "username": "usuario_teste",
  "name": "Usuário de Teste",
  "cpf_cnpj": "12345678900",
  "asaas_customer_id": "cus_abcdef123456789",
  "address": "Rua de Exemplo, 123",
  "phone": "11987654321",
  "description": "Cliente de teste via API",
  "created_at": "2023-10-27T10:00:00+00:00",
  "updated_at": "2023-10-27T10:00:00+00:00"
}
```
- `401 Unauthorized`: Token inválido ou ausente.
- `404 Not Found`: Dados do usuário não encontrados no banco de dados.
- `500 Internal Server Error`: Erro ao buscar dados do perfil.

---

## 3. Assinaturas (`/subscriptions`)

### `POST /subscriptions/create`
Cria uma nova assinatura no Asaas para o usuário logado e registra a assinatura no banco de dados. Requer autenticação.

- **Endpoint:** `/subscriptions/create`
- **Método:** `POST`

**Header Parameters:**
- `Authorization`: `Bearer <token>`
- `Content-Type`: `application/json`

**Request Body:**
A estrutura do corpo varia dependendo do `billing_type`.

**Para `billing_type` = "BOLETO" ou "PIX":**
```json
{
  "billing_type": "BOLETO",
  "next_due_date": "YYYY-MM-DD",
  "value": 59.90,
  "cycle": "MONTHLY",
  "plan": "premium",
  "description": "Assinatura Plano Premium"
}
```

**Exemplo de Requisição (`curl` para BOLETO):**
```bash
# Substitua <SEU_TOKEN_JWT> pelo token obtido no login
# Substitua YYYY-MM-DD pela data de vencimento desejada
curl -X POST "http://localhost:8000/subscriptions/create" \
-H "Authorization: Bearer <SEU_TOKEN_JWT>" \
-H "Content-Type: application/json" \
-d '{
  "billing_type": "BOLETO",
  "next_due_date": "2024-12-01",
  "value": 59.90,
  "cycle": "MONTHLY",
  "plan": "premium",
  "description": "Assinatura Plano Premium (Boleto)"
}'
```

**Para `billing_type` = "CREDIT_CARD":**
```json
{
  "billing_type": "CREDIT_CARD",
  "next_due_date": "YYYY-MM-DD",
  "value": 99.90,
  "cycle": "MONTHLY",
  "plan": "exclusive",
  "description": "Assinatura Plano Exclusive",
  "credit_card": {
    "number": "4111111111111111",
    "holderName": "NOME DO TITULAR",
    "expirationMonth": 12,
    "expirationYear": 2025,
    "cvv": "123"
  },
  "creditCardHolderInfo": {
    "name": "Nome Completo do Titular",
    "cpfCnpj": "12345678900",
    "address": {
      "street": "Rua do Cartão",
      "number": "456",
      "district": "Bairro do Cartão",
      "city": "Cidade do Cartão",
      "state": "Estado do Cartão",
      "postalCode": "01000-000",
      "country": "BRA"
    }
  }
}
```

**Exemplo de Requisição (`curl` para CREDIT_CARD):**
```bash
# Substitua <SEU_TOKEN_JWT> pelo token obtido no login
# Substitua YYYY-MM-DD pela data de vencimento desejada
# Substitua os dados do cartão e do titular por dados válidos (para sandbox)
curl -X POST "http://localhost:8000/subscriptions/create" \
-H "Authorization: Bearer <SEU_TOKEN_JWT>" \
-H "Content-Type: application/json" \
-d '{
  "billing_type": "CREDIT_CARD",
  "next_due_date": "2025-12-01",
  "value": 99.90,
  "cycle": "MONTHLY",
  "plan": "exclusive",
  "description": "Assinatura Plano Exclusive (Cartão)",
  "credit_card": {
    "number": "5540047627804849",
    "holderName": "ANDRE L SOARES",
    "expirationMonth": 10,
    "expirationYear": 2025,
    "cvv": "247"
  },
  "credit_card_holder_name": "ANDRE L SOARES",
  "credit_card_holder_cpf_cnpj": "45306353843",
  "credit_card_holder_email": "emaildotitular@example.com",
  "credit_card_holder_postal_code": "01000000",
  "credit_card_holder_address": "Rua do Cartão",
  "credit_card_holder_address_number": "456",
  "credit_card_holder_address_complement": "Sala 101",
  "credit_card_holder_phone": "1132850099"
}'
```

**Responses:**
- `200 OK`: Assinatura criada com sucesso.
```json
{
  "subscription_id": "sub_abcdef123456789",
  "status": "ACTIVE"
}
```
- `400 Bad Request`: Dados inválidos ou usuário sem ID Asaas.
- `401 Unauthorized`: Token inválido ou ausente.
- `500 Internal Server Error`: Erro ao criar assinatura no Asaas ou salvar no DB.

---

### `GET /subscriptions/{subscription_id}`
Retorna os detalhes de uma assinatura específica pertencente ao usuário logado. Requer autenticação.

- **Endpoint:** `/subscriptions/{subscription_id}`
- **Método:** `GET`

**Header Parameters:**
- `Authorization`: `Bearer <token>`

**Path Parameters:**
- `subscription_id` (string): O ID da assinatura gerado pelo Asaas.

**Exemplo de Requisição (`curl`):**
```bash
# Substitua <SEU_TOKEN_JWT> pelo token obtido no login
# Substitua <ID_DA_ASSINATURA_ASAAS> pelo ID da assinatura desejada
curl -X GET "http://localhost:8000/subscriptions/<ID_DA_ASSINATURA_ASAAS>" \
-H "Authorization: Bearer <SEU_TOKEN_JWT>"
```

**Responses:**
- `200 OK`: Detalhes da assinatura.
```json
{
  "id": "f9a8e7d6-c5b4-3a21-9876-543210fedcba",
  "user_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "subscription_id": "sub_abcdef123456789",
  "status": "ACTIVE",
  "plan": "premium",
  "created_at": "2023-10-27T10:30:00+00:00",
  "updated_at": "2023-10-27T10:30:00+00:00"
}
```
- `401 Unauthorized`: Token inválido ou ausente.
- `404 Not Found`: Assinatura não encontrada ou não pertence ao usuário.
- `500 Internal Server Error`: Erro ao buscar detalhes da assinatura.

---

### `POST /subscriptions/{subscription_id}/cancel`
Cancela uma assinatura específica no Asaas e atualiza o status no banco de dados local. Requer autenticação.

- **Endpoint:** `/subscriptions/{subscription_id}/cancel`
- **Método:** `POST`

**Header Parameters:**
- `Authorization`: `Bearer <token>`

**Path Parameters:**
- `subscription_id` (string): O ID da assinatura gerado pelo Asaas.

**Exemplo de Requisição (`curl`):**
```bash
# Substitua <SEU_TOKEN_JWT> pelo token obtido no login
# Substitua <ID_DA_ASSINATURA_ASAAS> pelo ID da assinatura a ser cancelada
curl -X POST "http://localhost:8000/subscriptions/<ID_DA_ASSINATURA_ASAAS>/cancel" \
-H "Authorization: Bearer <SEU_TOKEN_JWT>"
```

**Responses:**
- `200 OK`: Assinatura cancelada com sucesso.
```json
{
  "message": "Assinatura cancelada com sucesso"
}
```
- `401 Unauthorized`: Token inválido ou ausente.
- `404 Not Found`: Assinatura não encontrada ou não pertence ao usuário.
- `500 Internal Server Error`: Erro ao cancelar assinatura no Asaas ou atualizar no DB.

---

## Considerações Adicionais

- Certifique-se de ter as variáveis de ambiente `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY` e `ASAAS_API_KEY` configuradas em um arquivo `.env` na raiz do projeto para rodar a API.
- A criação das funções RPC `create_user_with_asaas_id` e `delete_user_by_id` (ou métodos equivalentes) no seu projeto Supabase é essencial para o fluxo de registro.
- A tokenização de dados de cartão de crédito no frontend é altamente recomendada por razões de segurança e conformidade com PCI-DSS.
- A documentação interativa do FastAPI estará disponível em `http://localhost:8000/docs` ao rodar a aplicação, fornecendo uma interface web para testar os endpoints (além do Postman). 