from fastapi import APIRouter, Depends

from ..dependencies import get_current_user
from ..models.user import UserProfile
from ..utils.supabase import supabase_client

router = APIRouter()

@router.get("/me", response_model=UserProfile, summary="Retorna os dados do usuário logado")
async def read_users_me(current_user: UserProfile = Depends(get_current_user)):
    """
    Retorna os dados do perfil do usuário autenticado.
    """
    return current_user 