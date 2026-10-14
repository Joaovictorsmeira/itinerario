import requests
from config import Config

def is_supabase_auth_enabled() -> bool:
    """Verifica se a chave anon do Supabase Auth está configurada."""
    return bool(Config.SUPABASE_ANON_KEY and Config.SUPABASE_URL)


def signup_supabase_user(email: str, password: str, metadata: dict = None) -> tuple[bool, str | None, str | None]:
    """
    Registra um usuário no Supabase Auth via API REST.
    Retorna (sucesso, user_id, mensagem_erro).
    Se SUPABASE_ANON_KEY não estiver configurada, permite o fallback local com senha_hash.
    """
    if not is_supabase_auth_enabled():
        return True, None, None

    url = f"{Config.SUPABASE_URL.rstrip('/')}/auth/v1/signup"
    headers = {
        "apikey": Config.SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "email": email.strip().lower(),
        "password": password,
        "data": metadata or {},
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=8)
        data = response.json()

        if response.status_code in (200, 201):
            user_id = data.get("id") or (data.get("user") and data["user"].get("id"))
            return True, user_id, None
        else:
            error_msg = data.get("msg") or data.get("message") or data.get("error_description")
            if not error_msg and "error" in data:
                error_msg = data["error"]
            if error_msg and "already registered" in error_msg.lower():
                error_msg = "Já existe uma conta registrada com este e-mail no Supabase Auth."
            return False, None, error_msg or "Falha ao registrar no Supabase Auth."
    except Exception as exc:
        # Se houver falha de rede ou timeout com a API do Supabase, loga e avisa
        return False, None, f"Erro de comunicação com o Supabase Auth: {exc}"


def login_supabase_user(email: str, password: str) -> tuple[bool, str | None, str | None]:
    """
    Autentica um usuário no Supabase Auth com e-mail e senha.
    Retorna (sucesso, user_id, mensagem_erro).
    Se SUPABASE_ANON_KEY não estiver configurada, retorna (None, None, "no_anon_key")
    para indicar que a verificação deve ser feita via hash local no banco.
    """
    if not is_supabase_auth_enabled():
        return None, None, "no_anon_key"

    url = f"{Config.SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": Config.SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "email": email.strip().lower(),
        "password": password,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=8)
        data = response.json()

        if response.status_code == 200:
            user_id = data.get("user", {}).get("id")
            return True, user_id, None
        else:
            return False, None, "E-mail ou senha incorretos no Supabase Auth."
    except Exception as exc:
        return False, None, f"Erro ao conectar com o Supabase Auth: {exc}"
