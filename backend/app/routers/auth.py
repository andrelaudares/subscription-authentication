from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from supabase import Client
import requests
from fastapi.security import OAuth2PasswordBearer

from ..models.user import UserRegister, UserLogin, UserProfile
from ..utils.supabase import supabase_client, supabase_admin
from ..utils.asaas import asaas_request, create_asaas_customer
from ..dependencies import get_current_user

router = APIRouter()

@router.post("/register", summary="Registra um novo usuário e cria um cliente no Asaas", response_model=UserProfile, status_code=201)
async def register_user(user_data: UserRegister):
    print("DEBUG: Rota /auth/register iniciada")
    try:
        print(f"DEBUG: Dados recebidos para registro: {user_data.email}")
        # 1. Registrar usuário no Supabase Auth
        print("DEBUG: Tentando registrar usuário no Supabase Auth...")
        auth_response = supabase_admin.auth.sign_up(
            {"email": user_data.email, "password": user_data.password}
        )
        print(f"DEBUG: Resposta Supabase Auth sign_up: {auth_response}")

        if not auth_response or not auth_response.user:
            print("DEBUG: Erro no registro do Supabase Auth ou usuário nulo.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao registrar no Supabase Auth.")

        user_id = auth_response.user.id
        print(f"DEBUG: Usuário registrado no Supabase Auth com ID: {user_id}")

        # Nota importante: Não estamos mais tentando excluir o usuário do Auth em caso de falha
        # Como isso exige permissões administrativas especiais, estamos optando por uma abordagem
        # diferente: marcar o usuário como "desativado" em nossa tabela users
        
        # 2. Criar cliente no Asaas (SIMPLIFICADO)
        asaas_customer_payload = {
            "name": user_data.name,
            "email": user_data.email,
            "mobilePhone": user_data.phone,
            "cpfCnpj": user_data.cpf_cnpj,
            "externalReference": str(user_id),
            "address": user_data.address,
            "description": user_data.description
        }
        
        print(f"DEBUG: Payload SIMPLIFICADO para criar cliente Asaas: {asaas_customer_payload}")
        try:
            print("DEBUG: Tentando criar cliente no Asaas (simplificado)...")
            asaas_customer_data = create_asaas_customer(asaas_customer_payload)
            print(f"DEBUG: Resposta Asaas create_customer: {asaas_customer_data}")
            asaas_customer_id = asaas_customer_data.get("id")

            if not asaas_customer_id:
                print("DEBUG: Cliente Asaas não criado ou ID nulo.")
                # Não tentamos mais apagar o usuário Auth, apenas registramos o erro
                print(f"DEBUG: ATENÇÃO: Usuário {user_id} permanecerá no Supabase Auth mas não está completamente registrado.")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao criar cliente no Asaas: ID do cliente não retornado. Resposta Asaas: {asaas_customer_data}")
            
            print(f"DEBUG: Cliente Asaas criado com ID: {asaas_customer_id}")

        except requests.exceptions.RequestException as e_asaas_req:
            print(f"DEBUG: Erro de requisição ao Asaas: {e_asaas_req}")
            # Não tentamos mais apagar o usuário Auth, apenas registramos o erro
            print(f"DEBUG: ATENÇÃO: Usuário {user_id} permanecerá no Supabase Auth mas não está completamente registrado.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro na comunicação com Asaas: {e_asaas_req}")
        except Exception as e_asaas_generic:
            print(f"DEBUG: Erro genérico ao criar cliente Asaas: {e_asaas_generic}")
            # Não tentamos mais apagar o usuário Auth, apenas registramos o erro
            print(f"DEBUG: ATENÇÃO: Usuário {user_id} permanecerá no Supabase Auth mas não está completamente registrado.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro inesperado ao processar com Asaas: {e_asaas_generic}")

        # 3. Inserir dados adicionais do usuário utilizando função RPC em vez de inserção direta
        try:
            print("DEBUG: Tentando inserir usuário através da função RPC insert_new_user...")
            rpc_response = supabase_admin.rpc(
                'insert_new_user',
                {
                    'user_id': str(user_id),
                    'user_email': user_data.email,
                    'user_username': user_data.username,
                    'user_name': user_data.name,
                    'user_cpf_cnpj': user_data.cpf_cnpj,
                    'user_asaas_id': asaas_customer_id,
                    'user_address': user_data.address,
                    'user_phone': user_data.phone,
                    'user_description': user_data.description
                }
            ).execute()
            
            print(f"DEBUG: Resposta da função RPC insert_new_user: {rpc_response}")
            
            if not rpc_response.data or not rpc_response.data.get('success'):
                print(f"DEBUG: Erro na função RPC insert_new_user: {rpc_response}")
                error_message = rpc_response.data.get('error') if rpc_response.data else 'Sem detalhes do erro'
                
                # Rollback apenas do cliente Asaas, já que não podemos deletar o usuário Auth
                try:
                    print(f"DEBUG: Tentando rollback - deletar cliente Asaas {asaas_customer_id}.")
                    asaas_request("DELETE", f"customers/{asaas_customer_id}")
                    print(f"DEBUG: Cliente Asaas {asaas_customer_id} deletado (rollback falha RPC).")
                except Exception as e_delete_asaas_db_fail:
                    print(f"DEBUG: Erro ao deletar cliente Asaas {asaas_customer_id} durante rollback (falha RPC): {e_delete_asaas_db_fail}")
                
                print(f"DEBUG: ATENÇÃO: Usuário {user_id} permanecerá no Supabase Auth mas não está completamente registrado.")
                raise Exception(f"Falha na função RPC: {error_message}")

        except Exception as e_db_insert:
            print(f"DEBUG: Erro ao inserir dados via RPC: {e_db_insert}")
            
            # Rollback apenas do cliente Asaas, já que não podemos deletar o usuário Auth
            try:
                print(f"DEBUG: Tentando rollback - deletar cliente Asaas {asaas_customer_id}.")
                asaas_request("DELETE", f"customers/{asaas_customer_id}")
                print(f"DEBUG: Cliente Asaas {asaas_customer_id} deletado (rollback falha RPC).")
            except Exception as e_delete_asaas_db_fail:
                print(f"DEBUG: Erro ao deletar cliente Asaas {asaas_customer_id} durante rollback (falha RPC): {e_delete_asaas_db_fail}")
            
            print(f"DEBUG: ATENÇÃO: Usuário {user_id} permanecerá no Supabase Auth mas não está completamente registrado.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao salvar dados do usuário no banco de dados: {e_db_insert}")

        print(f"DEBUG: Usuário {user_id} registrado e dados salvos com sucesso.")
        print(f"DEBUG: Buscando perfil do usuário {user_id} para resposta.")
        profile_response = supabase_admin.from_('users').select("*").eq('id', str(user_id)).single().execute()
        print(f"DEBUG: Resposta da busca de perfil: {profile_response}")
        if not profile_response.data:
            print(f"DEBUG: Falha ao buscar perfil do usuário {user_id} após registro.")
            return {"message": "Usuário registrado com sucesso, mas falha ao obter perfil detalhado.", "user_id": user_id}
        
        return UserProfile(**profile_response.data)

    except HTTPException as e_http:
        print(f"DEBUG: HTTPException capturada na rota /register: {e_http.detail}")
        raise e_http
    except Exception as e_general:
        print(f"DEBUG: Exceção genérica não tratada na rota /register: {e_general}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno inesperado no servidor: {str(e_general)}")

@router.post("/login", summary="Realiza login e retorna tokens")
async def login_user(user_data: UserLogin, supabase: Client = Depends(lambda: supabase_client)):
    try:
        auth_response = supabase.auth.sign_in_with_password(
            {"email": user_data.email, "password": user_data.password}
        )
        if auth_response.session is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

        return {
            "access_token": auth_response.session.access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        # Supabase client pode levantar exceções para credenciais inválidas também
        if "Invalid login credentials" in str(e):
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# A rota de logout geralmente é feita no frontend invalidando o token.
# No entanto, se quisermos invalidar a sessão no backend:
@router.post("/logout", summary="Realiza logout (invalida a sessão no Supabase)")
async def logout_user(current_user: UserProfile = Depends(get_current_user), supabase: Client = Depends(lambda: supabase_client)):
    try:
        # O cliente Supabase, ao usar a dependência get_current_user,
        # já deve estar configurado com o token da requisição.
        # Chamar sign_out() irá invalidar a sessão associada a este cliente.
        supabase.auth.sign_out()
        return {"message": "Logout realizado com sucesso"}
    except Exception as e:
         print(f"Erro durante o logout: {e}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro durante o logout: {e}")

# Remover a definição temporária de get_current_user_token que não é usada aqui.
# async def get_current_user_token(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/auth/login"))):
#     return token 