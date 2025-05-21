from fastapi import APIRouter, Depends, HTTPException, status, Request
from supabase import Client
import requests

from ..dependencies import get_current_user
from ..models.subscription import SubscriptionCreatePayload, SubscriptionDB, SubscriptionCancelResponse, SubscriptionDetails, CreditCardHolderInfoAsaas
from ..models.user import UserProfile
from ..utils.asaas import asaas_request
from ..utils.supabase import supabase_client

router = APIRouter()

@router.post("/create", summary="Cria uma nova assinatura no Asaas e registra no banco de dados")
async def create_subscription(
    request: Request,
    subscription_payload: SubscriptionCreatePayload,
    current_user: UserProfile = Depends(get_current_user),
    supabase: Client = Depends(lambda: supabase_client)
):
    """
    Cria uma nova assinatura no Asaas para o usuário autenticado
    e registra os detalhes no banco de dados.
    """
    if not current_user.asaas_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não possui um ID de cliente Asaas associado."
        )

    client_ip = request.client.host

    asaas_payload = {
        "customer": current_user.asaas_customer_id,
        "billingType": subscription_payload.billing_type,
        "nextDueDate": subscription_payload.next_due_date,
        "value": subscription_payload.value,
        "cycle": subscription_payload.cycle,
        "description": subscription_payload.description,
    }

    if subscription_payload.billing_type == "CREDIT_CARD":
        # Temporariamente, para teste, vamos mudar o billingType para UNDEFINED
        # se for CREDIT_CARD, para ver se o erro de CPF persiste.
        # Lembre-se de reverter isso depois do teste.
        asaas_payload["billingType"] = "UNDEFINED" # ALTERAÇÃO PARA TESTE

        if not subscription_payload.credit_card or \
           not subscription_payload.credit_card_holder_name or \
           not subscription_payload.credit_card_holder_cpf_cnpj or \
           not subscription_payload.credit_card_holder_postal_code or \
           not subscription_payload.credit_card_holder_address or \
           not subscription_payload.credit_card_holder_address_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para cartão de crédito, são necessários: dados do cartão, nome do titular, CPF/CNPJ, CEP, endereço (rua) e número do endereço."
            )
        
        # Construir o creditCardHolderInfo no formato flat esperado pelo Asaas
        credit_card_holder_info_asaas = CreditCardHolderInfoAsaas(
            name=subscription_payload.credit_card_holder_name,
            email=subscription_payload.credit_card_holder_email, # Pode ser None se não fornecido
            cpfCnpj=subscription_payload.credit_card_holder_cpf_cnpj,
            postalCode=subscription_payload.credit_card_holder_postal_code,
            address=subscription_payload.credit_card_holder_address,
            addressNumber=subscription_payload.credit_card_holder_address_number,
            addressComplement=subscription_payload.credit_card_holder_address_complement, # Pode ser None
            phone=subscription_payload.credit_card_holder_phone, # Pode ser None
            # mobilePhone pode ser o mesmo que phone, ou um campo separado se você tiver.
            # Se não tiver um campo específico para mobilePhone no seu payload de entrada e quiser enviar,
            # poderia usar o valor de credit_card_holder_phone também.
            mobilePhone=subscription_payload.credit_card_holder_phone 
        ).dict(exclude_none=True) # exclude_none para não enviar campos opcionais vazios

        asaas_payload["creditCard"] = subscription_payload.credit_card.dict()
        asaas_payload["creditCardHolderInfo"] = credit_card_holder_info_asaas
        asaas_payload["remoteIp"] = client_ip
        
    elif subscription_payload.billing_type != "BOLETO" and subscription_payload.billing_type != "PIX":
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
             detail="Tipo de cobrança inválido. Use BOLETO, CREDIT_CARD ou PIX."
         )

    try:
        print(f"DEBUG: Enviando payload para Asaas: {asaas_payload}")
        # Chamar a API do Asaas para criar a assinatura
        # O endpoint para criar assinatura é POST /v3/subscriptions
        # Ref: https://docs.asaas.com/reference/criar-nova-assinatura
        asaas_response = asaas_request("POST", "subscriptions", data=asaas_payload)
        asaas_subscription_data = asaas_response.json()
        asaas_subscription_id = asaas_subscription_data.get("id")
        asaas_subscription_status = asaas_subscription_data.get("status")

        if not asaas_subscription_id:
             print(f"Erro na resposta do Asaas ao criar assinatura: {asaas_response.text}")
             raise HTTPException(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 detail=f"Erro ao obter ID da assinatura do Asaas: {asaas_response.text}"
             )

        # Inserir os dados da assinatura na tabela public.subscriptions
        # Nota: A política RLS deve permitir que o usuário autenticado insira seus próprios dados (feito na RLS policy)
        # Assumimos que a coluna 'plan' na tabela subscriptions do Supabase existirá e será preenchida com o campo 'plan' do payload de entrada.
        response = supabase.from_('subscriptions').insert({
            'user_id': str(current_user.id),
            'subscription_id': asaas_subscription_id,
            'status': asaas_subscription_status, # Usar o status retornado pelo Asaas
            'plan': subscription_payload.plan # Usar o plano do payload de entrada
            # created_at e updated_at serão definidos automaticamente pelo banco de dados
        }).execute()

        # Verificar se a inserção no banco de dados foi bem-sucedida
        if not response.data:
            # Logar erro e considerar rollback no Asaas (mais complexo, fora do escopo simples do template)
            print(f"Erro ao inserir dados da assinatura {asaas_subscription_id} no banco de dados Supabase.")
            # Potencialmente, chamar a API do Asaas para cancelar a assinatura recém-criada aqui em caso de falha no DB
            # asaas_request("DELETE", f"subscriptions/{asaas_subscription_id}") # Exemplo de rollback no Asaas
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao salvar dados da assinatura no banco de dados."
            )

        # Retornar os dados da assinatura criada
        # A resposta da inserção geralmente retorna os dados inseridos.
        # Podemos retornar o objeto SubscriptionDB ou um subset relevante.
        # Para simplificar, retornaremos uma confirmação e o ID do Asaas e status.
        return {"subscription_id": asaas_subscription_id, "status": asaas_subscription_status}

    except requests.exceptions.RequestException as e:
        detail = f"Erro na comunicação com Asaas: {e}"
        status_code_val = status.HTTP_500_INTERNAL_SERVER_ERROR
        if hasattr(e, 'response') and e.response is not None:
             try:
                error_data = e.response.json()
                detail = f"Erro na comunicação com Asaas: {error_data}" 
             except ValueError: # Não é JSON
                detail = f"Erro na comunicação com Asaas: {e.response.text}"
             status_code_val = e.response.status_code if e.response.status_code else status_code_val
        
        print(f"RequestException ao criar assinatura Asaas: {detail}")
        raise HTTPException(status_code=status_code_val, detail=detail)
    except Exception as e:
        # Captura outras exceções inesperadas
        print(f"Erro inesperado ao criar assinatura: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno do servidor: {e}")

@router.get("/{subscription_id}", response_model=SubscriptionDetails, summary="Retorna os detalhes de uma assinatura")
async def get_subscription_details(
    subscription_id: str,
    current_user: UserProfile = Depends(get_current_user),
    supabase: Client = Depends(lambda: supabase_client)
):
    """
    Retorna os detalhes de uma assinatura específica pertencente ao usuário autenticado.
    O ID da assinatura aqui se refere ao ID gerado pelo Asaas.
    """
    try:
        # Buscar a assinatura na tabela public.subscriptions pelo ID do Asaas e pelo ID do usuário logado
        # A RLS já protege contra acesso a assinaturas de outros usuários, mas filtrar na query é uma boa prática.
        response = supabase.from_('subscriptions')\
            .select('*')\
            .eq('subscription_id', subscription_id)\
            .eq('user_id', str(current_user.id))\
            .single()\
            .execute()

        # Verificar se a resposta da query foi bem-sucedida e contém dados
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assinatura não encontrada ou não pertence a este usuário."
            )

        subscription_data = response.data
        return SubscriptionDetails(**subscription_data)

    except Exception as e:
        print(f"Erro ao obter detalhes da assinatura {subscription_id}: {e}")
        # Se o erro for uma HTTPException, ela será relançada. Outros erros são convertidos em 500.
        if isinstance(e, HTTPException):
             raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {e}"
        )

@router.post("/{subscription_id}/cancel", response_model=SubscriptionCancelResponse, summary="Cancela uma assinatura no Asaas e atualiza o status no banco de dados")
async def cancel_subscription(
    subscription_id: str,
    current_user: UserProfile = Depends(get_current_user),
    supabase: Client = Depends(lambda: supabase_client)
):
    """
    Cancela uma assinatura no Asaas e atualiza o status no banco de dados local.
    O ID da assinatura aqui se refere ao ID gerado pelo Asaas.
    """
    try:
        # 1. Verificar se a assinatura existe e pertence ao usuário autenticado no banco de dados local
        response = supabase.from_('subscriptions')\
            .select('*')\
            .eq('subscription_id', subscription_id)\
            .eq('user_id', str(current_user.id))\
            .single()\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assinatura não encontrada ou não pertence a este usuário."
            )

        subscription_db_data = response.data # Dados da assinatura no nosso DB

        # 2. Chamar a API do Asaas para cancelar a assinatura
        # O endpoint para cancelar assinatura é DELETE /v3/subscriptions/{id}
        # Ref: https://docs.asaas.com/reference/remover-assinatura
        try:
            asaas_response = asaas_request("DELETE", f"subscriptions/{subscription_id}")
            # A API do Asaas retorna 200 OK em caso de sucesso na exclusão (cancelamento)
            if asaas_response.status_code != 200:
                 # Se a API do Asaas retornar um erro diferente de 200, levantar exceção
                 print(f"Erro na API do Asaas ao cancelar assinatura {subscription_id}: {asaas_response.text}")
                 raise HTTPException(status_code=asaas_response.status_code, detail=f"Erro ao cancelar assinatura no Asaas: {asaas_response.text}")

            # Opcional: Verificar o corpo da resposta do Asaas se ele indicar o status (geralmente não necessário para DELETE)
            # asaas_cancel_data = asaas_response.json()
            # Verificar um campo de status na resposta se houver

        except requests.exceptions.RequestException as e:
            # Erro na comunicação com a API do Asaas
            print(f"Erro na comunicação com Asaas ao cancelar assinatura {subscription_id}: {e}")
            detail = f"Erro na comunicação com Asaas: {e}"
            if hasattr(e, 'response') and e.response is not None:
                 detail = f"Erro na comunicação com Asaas: {e.response.text}"
                 status_code = e.response.status_code
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

            raise HTTPException(status_code=status_code, detail=detail)

        # 3. Atualizar o status da assinatura no banco de dados local para 'cancelled'
        # Nota: A política RLS deve permitir que o usuário autenticado atualize seus próprios dados (feito na RLS policy)
        update_response = supabase.from_('subscriptions')\
             .update({'status': 'cancelled'})\
             .eq('subscription_id', subscription_id)\
             .eq('user_id', str(current_user.id))\
             .execute()

        # Verificar se a atualização no banco de dados foi bem-sucedida
        if not update_response.data:
             # Isso é um estado inconsistente. A assinatura foi cancelada no Asaas, mas não atualizada no DB.
             print(f"Erro ao atualizar status da assinatura {subscription_id} no banco de dados Supabase após cancelar no Asaas.")
             # Podemos lançar um erro 500 ou retornar sucesso com um aviso no log. Um erro 500 é mais seguro.
             raise HTTPException(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 detail="Assinatura cancelada no Asaas, mas falha ao atualizar o status no banco de dados local."
             )

        return {"message": "Assinatura cancelada com sucesso"}

    except HTTPException as e:
         # Re-lança HTTPExceptions que já foram criadas acima
         raise e
    except Exception as e:
        # Captura quaisquer outros erros inesperados
        print(f"Erro inesperado ao cancelar assinatura {subscription_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {e}"
        ) 