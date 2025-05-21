from fastapi import FastAPI
from .routers import auth, users, subscriptions

app = FastAPI(title="Template SaaS com Supabase e Asaas", version="1.0.0")

# Incluir os roteadores
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])

@app.get("/", summary="Health Check")
async def read_root():
    return {"status": "API está online"}

# Nota: Para rodar esta aplicação, você precisará de um arquivo .env
# com as variáveis SUPABASE_URL, SUPABASE_KEY e ASAAS_API_KEY.
# Use `uvicorn app.main:app --reload` no diretório backend/app 