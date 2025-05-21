from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import Client
# from gotrue.errors import AuthApiException # Remover importação específica que está falhando
# Pode ser necessário capturar uma exceção mais genérica ou específica do cliente Supabase/GoTrue

from .utils.supabase import supabase_client # Usar a instância global
from .models.user import UserProfile, UserDB

# Define o esquema OAuth2 para obter o token
# tokenUrl="auth/login" refere-se à rota onde o cliente pode obter um token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), supabase: Client = Depends(lambda: supabase_client)) -> UserProfile:
    """
    Dependency para obter o usuário logado com base no token JWT.
    Verifica o token no Supabase Auth e busca dados adicionais na tabela public.users.
    """
    try:
        try:
            # Obter o usuário usando o token JWT fornecido
            user_auth_response = supabase.auth.get_user(jwt=token)
        except Exception as e:
            error_detail = str(e).lower()
            # A biblioteca supabase-py pode levantar exceções específicas para erros de JWT.
            # Idealmente, importaríamos e capturaríamos essas exceções específicas (ex: gotrue.errors.AuthJWTError)
            # Por enquanto, continuamos analisando a string do erro.
            if "invalid" in error_detail or "expired" in error_detail or "unauthorized" in error_detail or "jwt" in error_detail:
                print(f"Erro de autenticação Supabase ao validar JWT: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido ou expirado",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                print(f"Erro inesperado ao chamar supabase.auth.get_user: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Erro interno ao validar token: {e}",
                )

        if not user_auth_response or not user_auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Não autenticado ou usuário não encontrado no token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = user_auth_response.user.id

        # Modificado para não usar .single() e tratar o caso de 0 ou múltiplas linhas
        response = supabase.from_('users').select('*').eq('id', str(user_id)).execute()

        if not response.data or len(response.data) == 0:
            print(f"Usuário {user_id} autenticado via JWT, mas não encontrado na tabela public.users")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dados do perfil do usuário não encontrados."
            )
        elif len(response.data) > 1:
            # Este caso indica uma inconsistência de dados (múltiplos perfis para o mesmo user_id)
            print(f"ERRO CRÍTICO: Múltiplos perfis encontrados para o user_id {user_id} na tabela public.users")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Inconsistência nos dados do usuário."
            )
        
        # Se chegou aqui, temos exatamente um usuário
        user_profile_data = response.data[0]
        return UserProfile(**user_profile_data)

    except HTTPException as e_http:
        raise e_http
    except Exception as e_general:
        # Esta captura genérica deve agora pegar menos casos, pois o PGRST116 foi tratado acima.
        print(f"Erro inesperado na dependência get_current_user: {e_general}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor ao processar autenticação: {e_general}"
        ) 