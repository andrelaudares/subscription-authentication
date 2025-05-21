# Template de Sistema SaaS com Autenticação Supabase e Assinatura Asaas

Este repositório serve como um template para construir sistemas SaaS com autenticação gerenciada pelo Supabase e um sistema de assinatura integrado ao Asaas para processamento de pagamentos. O backend é desenvolvido em Python utilizando o framework FastAPI, oferecendo uma API RESTful modular e fácil de estender.

## Visão Geral

O objetivo deste template é fornecer um ponto de partida funcional para projetos SaaS que necessitam de um fluxo de usuário que inclui registro, autenticação e a contratação de planos de assinatura com pagamento.

### Tecnologias Utilizadas

- **Python:** Linguagem de programação principal.
- **FastAPI:** Framework para construção da API RESTful.
- **Uvicorn:** Servidor ASGI para rodar a aplicação FastAPI.
- **Supabase:** Plataforma BaaS (Backend as a Service) utilizada para Autenticação (Supabase Auth) e Banco de Dados (PostgreSQL).
- **Asaas:** Gateway de pagamento para criação e gerenciamento de clientes e assinaturas.
- **Pydantic:** Para validação de dados e modelagem.
- **python-dotenv:** Para carregar variáveis de ambiente.
- **requests:** Para fazer requisições HTTP (principalmente para a API do Asaas).

## Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python 3.8+:** Baixe e instale em [python.org](https://www.python.org/).
- **Git:** Baixe e instale em [git-scm.com](https://git-scm.com/).
- **Conta Supabase:** Crie uma conta gratuita em [supabase.com](https://supabase.com/).
- **Conta Asaas:** Crie uma conta gratuita ou de Sandbox em [asaas.com](https://www.asaas.com/).

## Configuração do Projeto

1.  **Clone o repositório:**

    ```bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd <pasta_do_repositorio>
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**

    ```bash
    python -m venv .venv
    # No Windows:
    # .venv\Scripts\activate
    # No macOS/Linux:
    # source .venv/bin/activate
    ```

3.  **Instale as dependências:**

    Navegue até o diretório `backend/` e instale as bibliotecas listadas em `requirements.txt`:

    ```bash
    cd backend/
    pip install -r requirements.txt
    ```

4.  **Configurar Variáveis de Ambiente:**

    Crie um arquivo chamado `.env` na raiz do diretório `backend/` (ao lado da pasta `app/` e do `requirements.txt`). Copie o conteúdo de `.env.example` e substitua os valores pelos seus dados de configuração do Supabase e Asaas.

    Exemplo de `.env`:

    ```dotenv
    # Variáveis de Ambiente para o Backend

    SUPABASE_URL="SUA_URL_DO_PROJETO_SUPABASE"
    SUPABASE_KEY="SUA_ANON_KEY_DO_SUPABASE" # Geralmente a chave anon para acesso público (seguro com RLS)
    ASAAS_API_KEY="SUA_CHAVE_DE_API_DO_ASAAS" # Use a chave de Sandbox ou Produção do Asaas
    ```

    - Obtenha a **URL do Supabase** e a **Anon Key** no Dashboard do Supabase, em `Project Settings > API`. Para este template, a Anon Key é suficiente se as políticas RLS estiverem configuradas corretamente.
    - Obtenha a **Chave de API do Asaas** no Dashboard do Asaas. Para testes, use a chave de Sandbox.

5.  **Configurar o Banco de Dados Supabase:**

    No Dashboard do Supabase, execute o script SQL fornecido em `Script SQL para Aplicação no Supabase.txt` para criar as tabelas `users` e `subscriptions` e configurar as políticas de Row Level Security (RLS).

    **Importante:** O script SQL também inclui a criação de funções RPC `create_user_with_asaas_id` e `delete_user_by_id` que são utilizadas nas rotas de autenticação para garantir a consistência entre Supabase Auth, a tabela `public.users` e a criação do cliente Asaas. Certifique-se de que essas funções sejam criadas corretamente no seu projeto Supabase.

## Como Rodar o Backend

1.  Certifique-se de estar no diretório `backend/`.
2.  Ative seu ambiente virtual, se ainda não estiver ativo.
3.  Execute o servidor Uvicorn:

    ```bash
    uvicorn app.main:app --reload
    ```

    - `app.main:app`: Indica para o Uvicorn que a aplicação FastAPI (`app`) está no módulo `main` dentro do pacote `app`.
    - `--reload`: Faz o servidor reiniciar automaticamente ao detectar mudanças no código.

4.  A API estará rodando em `http://localhost:8000`.

## Documentação da API

A documentação detalhada de todos os endpoints da API (com exemplos de requisição e resposta para teste no Postman ou ferramentas similares) pode ser encontrada no arquivo `backend/API_DOCUMENTATION.md`.

Além disso, ao rodar o backend, a documentação interativa do Swagger UI (gerada automaticamente pelo FastAPI) estará disponível em `http://localhost:8000/docs`.

## Fluxo do Usuário Implementado

O backend suporta o seguinte fluxo:

1.  **Registro:** Criação de conta no Supabase Auth e cliente no Asaas, salvando dados na tabela `public.users`.
2.  **Login:** Autenticação via Supabase Auth, retornando um token JWT.
3.  **Obter Perfil:** Acesso a dados do usuário logado (`/users/me`).
4.  **Criação de Assinatura:** Utilizando o ID do cliente Asaas do usuário logado para criar uma assinatura no Asaas e registrar no banco de dados (`/subscriptions/create`). Suporta BOLETO, PIX e CARTÃO DE CRÉDITO.
5.  **Obter Detalhes da Assinatura:** Consulta detalhes de uma assinatura específica (`/subscriptions/{subscription_id}`).
6.  **Cancelar Assinatura:** Cancela uma assinatura no Asaas e atualiza o status no banco de dados (`/subscriptions/{subscription_id}/cancel`).

## Próximos Passos e Personalização

Este template fornece a estrutura básica. Você pode estendê-lo para:

- Adicionar webhooks do Asaas para receber atualizações de status de pagamento e assinatura (recomendado).
- Implementar gerenciamento de planos (criar, editar, listar).
- Adicionar mais validações e tratamento de erros.
- Integrar um frontend.
- Adicionar testes unitários e de integração.
- Configurar deploy em um serviço de hospedagem.

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests no GitHub.

## Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo `LICENSE` para mais detalhes.