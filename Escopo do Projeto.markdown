# Escopo do Projeto: Template de Sistema SaaS com Autenticação e Assinatura

## Introdução

Este template fornece uma base para criar sistemas SaaS (Software as a Service) com autenticação gerenciada pelo [Supabase](https://supabase.com/) e um sistema de assinatura com pagamento via [Asaas](https://www.asaas.com/). O backend é desenvolvido em Python usando o framework [FastAPI](https://fastapi.tiangolo.com/), oferecendo uma API RESTful organizada e fácil de integrar com frontends. O objetivo é criar um repositório reutilizável no GitHub que sirva como ponto de partida para projetos SaaS com banco de dados e assinatura.

## Objetivos

- Fornecer um template funcional para sistemas SaaS com autenticação e assinatura.
- Garantir que o código seja modular, organizado e fácil de personalizar.
- Incluir documentação clara para facilitar o uso e a integração por outros desenvolvedores.

## Requisitos

### Funcionalidades

1. **Autenticação e Registro com Supabase**:
   - Registro de novos usuários usando Supabase Auth.
   - Login e logout com geração de tokens JWT.
   - Armazenamento de dados adicionais do usuário em uma tabela no schema `public`.

2. **Sistema de Assinatura com Asaas**:
   - Criação e gerenciamento de assinaturas.
   - Integração com a API do Asaas para processamento de pagamentos.
   - Criação de um cliente no Asaas durante o registro do usuário.
   - Tabela para gerenciar dados de assinatura com chave estrangeira para a tabela de usuários.

3. **Gerenciamento de Usuários e Pagamentos**:
   - Lógica para registrar usuários no banco de dados com Supabase.
   - Lógica para criar e gerenciar assinaturas com Asaas.
   - Fluxo claro: registro → criação de cliente no Asaas → login → criação de assinatura → acesso a informações.

4. **API RESTful com FastAPI**:
   - Todas as funcionalidades implementadas via rotas usando Python e FastAPI.
   - Rotas claras para autenticação, usuários e assinaturas.

5. **Template Organizado**:
   - Estrutura de pastas e arquivos bem definida.
   - Fácil integração com frontends através de rotas documentadas.

6. **Documentação**:
   - README.md completo com instruções de configuração, explicação do código, schemas das tabelas, rotas e sugestões de personalização.
   - Explicação detalhada do fluxo de usuário e integração com o Asaas.

### Tecnologias

| Tecnologia       | Finalidade                     |
|------------------|--------------------------------|
| Python, FastAPI  | Backend e API RESTful          |
| Supabase Auth    | Autenticação e gerenciamento de usuários |
| Supabase (PostgreSQL) | Banco de dados            |
| Asaas            | Gateway de pagamento           |
| Markdown         | Documentação (README.md)       |

## Fluxo do Usuário

O fluxo do usuário é essencial para entender como o sistema funciona:

1. **Registro**:
   - O usuário fornece email, senha, nome, username, CPF/CNPJ (obrigatório para brasileiros), endereço (opcional), telefone (opcional) e descrição (opcional).
   - O sistema cria o usuário no Supabase Auth com email e senha.
   - Um cliente é criado no Asaas usando nome e CPF/CNPJ (e outros dados disponíveis).
   - O ID do cliente do Asaas (`asaas_customer_id`) é armazenado na tabela `users`.
   - Dados adicionais do usuário são salvos na tabela `users`.

2. **Pagamento e Assinatura**:
   - Após o registro, o usuário pode criar uma assinatura.
   - O sistema usa o `asaas_customer_id` para criar uma assinatura no Asaas.
   - O usuário escolhe o tipo de cobrança ("BOLETO" ou "CREDIT_CARD"), data de vencimento, valor e ciclo.
   - Para cartões de crédito, os dados do cartão são enviados (recomenda-se tokenização no frontend).

3. **Login**:
   - O usuário faz login com email e senha, recebendo um token JWT.

4. **Acesso a Informações**:
   - Com o token JWT, o usuário acessa rotas protegidas para visualizar perfil e detalhes da assinatura.

## Integração com o Asaas

A integração com o Asaas segue estas etapas:

### 1. Criação de Cliente no Asaas
- **Quando**: Durante o registro do usuário, após criar a conta no Supabase.
- **Endpoint**: `POST /v3/customers` ([Criar novo cliente](https://docs.asaas.com/reference/criar-novo-cliente)).
- **Campos obrigatórios**:
  - `name`: Nome completo do usuário.
  - `cpfCnpj`: CPF ou CNPJ (obrigatório para brasileiros).
- **Campos opcionais**: email, telefone, endereço (se `postalCode` for fornecido, cidade e estado são preenchidos automaticamente).
- **Resposta**: O ID do cliente (`cus_XXXX`) é retornado e armazenado na tabela `users` como `asaas_customer_id`.

**Exemplo de requisição**:
```json
POST /v3/customers
{
  "name": "Nome Completo",
  "cpfCnpj": "12345678900",
  "email": "email@example.com",
  "mobilePhone": "(11) 99999-9999",
  "address": {
    "street": "Rua Exemplo",
    "number": "123",
    "district": "Bairro",
    "city": "Cidade",
    "state": "Estado",
    "postalCode": "00000-000",
    "country": "BRA"
  }
}
```

### 2. Criação de Assinatura no Asaas
- **Quando**: Quando o usuário cria uma assinatura via `/subscriptions/create`.
- **Endpoint**: `POST /v3/subscriptions` ([Criar nova assinatura](https://docs.asaas.com/reference/criar-nova-assinatura)).
- **Campos obrigatórios**:
  - `customer`: ID do cliente do Asaas (`asaas_customer_id`).
  - `billingType`: Tipo de cobrança ("BOLETO" ou "CREDIT_CARD").
  - `nextDueDate`: Data do primeiro vencimento (formato: "YYYY-MM-DD").
  - `value`: Valor da assinatura.
  - `cycle`: Frequência ("MONTHLY", "QUARTERLY", etc.).
- **Para cartão de crédito**: Incluir `creditCard` e `creditCardHolderInfo`.
- **Resposta**: O ID da assinatura é retornado e armazenado na tabela `subscriptions`.

**Exemplo de requisição (Boleto)**:
```json
POST /v3/subscriptions
{
  "customer": "cus_0T1mdomVMi39",
  "billingType": "BOLETO",
  "nextDueDate": "2023-10-15",
  "value": 19.9,
  "cycle": "MONTHLY",
  "description": "Assinatura Plano Pro"
}
```

**Exemplo de requisição (Cartão de Crédito)**:
```json
POST /v3/subscriptions
{
  "customer": "cus_0T1mdomVMi39",
  "billingType": "CREDIT_CARD",
  "nextDueDate": "2023-10-15",
  "value": 19.9,
  "cycle": "MONTHLY",
  "description": "Assinatura Plano Pro",
  "creditCard": {
    "number": "4111111111111111",
    "holderName": "Nome do Titular",
    "expirationMonth": 12,
    "expirationYear": 2025,
    "cvv": "123"
  },
  "creditCardHolderInfo": {
    "name": "Nome do Titular",
    "cpfCnpj": "12345678900",
    "address": {
      "street": "Rua Exemplo",
      "number": "123",
      "district": "Bairro",
      "city": "Cidade",
      "state": "Estado",
      "postalCode": "00000-000",
      "country": "BRA"
    }
  }
}
```

**Nota de Segurança**: Para assinaturas com cartão de crédito, é altamente recomendado usar bibliotecas frontend para tokenização dos dados do cartão antes de enviá-los ao backend, garantindo conformidade com PCI-DSS.

### 3. Gerenciamento de Assinaturas
- O ID da assinatura é armazenado na tabela `subscriptions` com o `user_id`.
- Rotas permitem consultar e cancelar assinaturas.

## Estrutura do Projeto

```
backend/
├── app/
│   ├── main.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── users.py
│   │   └── subscriptions.py
│   ├── models/
│   │   ├── user.py
│   │   └── subscription.py
│   ├── schemas/
│   │   ├── user.py
│   │   └── subscription.py
│   └── utils/
│       ├── supabase.py
│       └── asaas.py
└── README.md
```

- **app/main.py**: Configura o FastAPI e inclui os roteadores.
- **app/routers/**: Contém rotas para autenticação, usuários e assinaturas.
- **app/models/**: Modelos Pydantic para validação de dados.
- **app/schemas/**: Esquemas das tabelas do Supabase.
- **app/utils/**: Funções para conexão com Supabase e Asaas.
- **README.md**: Documentação detalhada.

## Detalhes Técnicos

### Tabelas no Supabase

#### Tabela `users`

| Coluna             | Tipo       | Descrição                              |
|--------------------|------------|----------------------------------------|
| `id`               | UUID       | Chave primária (o mesmo id do Supabase Auth users)         |
| `email`            | text       | Email único                            |
| `username`         | text       | Nome de usuário único                  |
| `name`             | text       | Nome completo                          |
| `cpf_cnpj`         | text       | CPF ou CNPJ único                      |
| `asaas_customer_id`| text       | ID do cliente no Asaas                 |
| `address`          | text       | Endereço (opcional)                    |
| `phone`            | text       | Telefone (opcional)                    |
| `description`      | text       | Descrição (opcional)                   |
| `created_at`       | timestamp  | Data de criação                        |
| `updated_at`       | timestamp  | Data de atualização                    |

#### Tabela `subscriptions`

| Coluna             | Tipo       | Descrição                              |
|--------------------|------------|----------------------------------------|
| `id`               | UUID       | Chave primária                         |
| `user_id`          | UUID       | Chave estrangeira para `users.id`      |
| `subscription_id`  | text       | ID da assinatura no Asaas              |
| `status`           | text       | Status (ex.: "active", "cancelled")    |
| `plan`             | text       | Plano (ex.: "basic", "premium")        |
| `created_at`       | timestamp  | Data de criação                        |
| `updated_at`       | timestamp  | Data de atualização                    |

### Rotas da API

#### Autenticação (`/auth`)

- **POST /auth/register**  
  - **Descrição**: Registra um usuário no Supabase Auth, cria um cliente no Asaas e armazena os dados.
  - **Payload**:
    ```json
    {
      "email": "string",
      "password": "string",
      "name": "string",
      "username": "string",
      "cpf_cnpj": "string",
      "address": "string",
      "phone": "string",
      "description": "string"
    }
    ```
  - **Resposta**:
    ```json
    { "message": "Usuário registrado com sucesso", "user_id": "uuid" }
    ```

- **POST /auth/login**  
  - **Descrição**: Faz login e retorna um token JWT.
  - **Payload**:
    ```json
    { "email": "string", "password": "string" }
    ```
  - **Resposta**:
    ```json
    { "access_token": "string", "token_type": "bearer" }
    ```

- **POST /auth/logout**  
  - **Descrição**: Faz logout do usuário.
  - **Headers**: `Authorization: Bearer <token>`
  - **Resposta**:
    ```json
    { "message": "Logout realizado com sucesso" }
    ```

#### Usuários (`/users`)

- **GET /users/me**  
  - **Descrição**: Retorna os dados do usuário logado.
  - **Headers**: `Authorization: Bearer <token>`
  - **Resposta**:
    ```json
    {
      "id": "uuid",
      "email": "string",
      "username": "string",
      "name": "string",
      "cpf_cnpj": "string",
      "asaas_customer_id": "string",
      "address": "string",
      "phone": "string",
      "description": "string"
    }
    ```

#### Assinaturas (`/subscriptions`)

- **POST /subscriptions/create**  
  - **Descrição**: Cria uma assinatura no Asaas para o cliente associado.
  - **Headers**: `Authorization: Bearer <token>`
  - **Payload (Boleto)**:
    ```json
    {
      "billing_type": "BOLETO",
      "next_due_date": "YYYY-MM-DD",
      "value": 19.9,
      "cycle": "MONTHLY"
    }
    ```
  - **Payload (Cartão de Crédito)**:
    ```json
    {
      "billing_type": "CREDIT_CARD",
      "next_due_date": "YYYY-MM-DD",
      "value": 19.9,
      "cycle": "MONTHLY",
      "credit_card": {
        "number": "4111111111111111",
        "holderName": "Nome do Titular",
        "expirationMonth": 12,
        "expirationYear": 2025,
        "cvv": "123"
      },
      "creditCardHolderInfo": {
        "name": "Nome do Titular",
        "cpfCnpj": "12345678900",
        "address": {
          "street": "Rua Exemplo",
          "number": "123",
          "district": "Bairro",
          "city": "Cidade",
          "state": "Estado",
          "postalCode": "00000-000",
          "country": "BRA"
        }
      }
    }
    ```
  - **Resposta**:
    ```json
    { "subscription_id": "string", "status": "string" }
    ```

- **GET /subscriptions/{subscription_id}**  
  - **Descrição**: Retorna os detalhes de uma assinatura.
  - **Headers**: `Authorization: Bearer <token>`
  - **Resposta**:
    ```json
    {
      "id": "uuid",
      "user_id": "uuid",
      "subscription_id": "string",
      "status": "string",
      "plan": "string",
      "created_at": "timestamp",
      "updated_at": "timestamp"
    }
    ```

- **POST /subscriptions/{subscription_id}/cancel**  
  - **Descrição**: Cancela uma assinatura no Asaas e atualiza o status.
  - **Headers**: `Authorization: Bearer <token>`
  - **Resposta**:
    ```json
    { "message": "Assinatura cancelada com sucesso" }
    ```

### Configuração e Uso

#### Pré-requisitos
- Contas no [Supabase](https://supabase.com/) e [Asaas](https://www.asaas.com/).
- Python 3.8+ instalado.
- Dependências: FastAPI, Uvicorn, Supabase Python Client, Requests.

#### Instalação
1. Clonar o repositório: `git clone <url-do-repositorio>`
2. Instalar dependências: `pip install -r requirements.txt`
3. Configurar variáveis de ambiente (`.env`):
   ```
   SUPABASE_URL=<sua-url-do-supabase>
   SUPABASE_KEY=<sua-chave-do-supabase>
   ASAAS_API_KEY=<sua-chave-do-asaas>
   ```

#### Configuração do Supabase
1. Criar um projeto no [Supabase Dashboard](https://supabase.com/).
2. Habilitar autenticação.
3. Criar as tabelas `users` e `subscriptions` com as colunas especificadas.

**SQL para criar tabelas**:
```sql
-- Tabela users
CREATE TABLE public.users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  username TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  cpf_cnpj TEXT UNIQUE NOT NULL,
  asaas_customer_id TEXT,
  address TEXT,
  phone TEXT,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabela subscriptions
CREATE TABLE public.subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  subscription_id TEXT NOT NULL,
  status TEXT NOT NULL,
  plan TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Configuração do Asaas
1. Criar uma conta no [Asaas](https://www.asaas.com/).
2. Obter a chave de API no painel.
3. Para clientes estrangeiros, contatar o gerente de conta do Asaas.

#### Executando o Backend
1. Iniciar o servidor: `uvicorn app.main:app --reload`
2. Acessar a documentação interativa em `http://localhost:8000/docs`.

### Personalizações e Extensões
- Adicionar campos às tabelas `users` ou `subscriptions`.
- Criar rotas como `/users/update` para edição de perfil.
- Integrar com serviços de e-mail ou notificações.
- Implementar planos predefinidos com valores e ciclos fixos.

### Notas Finais
- Este template é otimizado para usuários brasileiros, exigindo CPF/CNPJ.
- Para clientes estrangeiros, contatar o suporte do Asaas.
- Para cartões de crédito, usar métodos seguros de coleta de dados no frontend.

## Licença
Licença MIT, permitindo uso e modificação livres.