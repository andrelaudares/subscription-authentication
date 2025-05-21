import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
ASAAS_API_KEY = os.getenv("ASAAS_API_KEY")

# Verificar se as variáveis essenciais estão definidas
if not SUPABASE_URL or not SUPABASE_KEY or not SUPABASE_SERVICE_KEY or not ASAAS_API_KEY:
    raise EnvironmentError("Uma ou mais variáveis de ambiente essenciais (SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY, ASAAS_API_KEY) não estão configuradas.") 