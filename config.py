import os
import re
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env se presente
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def get_database_url() -> str:
    """
    Obtém e normaliza a URL de conexão do PostgreSQL.
    Trata prefixos legados e assegura SSL para Supabase.
    """
    db_url = os.getenv("DATABASE_URL")
    flask_env = os.getenv("FLASK_ENV", "development").lower()
    is_render = os.getenv("RENDER") is not None

    if db_url:
        # SQLAlchemy 2.x prefere 'postgresql+psycopg2://' com psycopg2-binary
        if db_url.startswith("postgres://"):
            db_url = "postgresql+psycopg2://" + db_url[len("postgres://"):]
        elif db_url.startswith("postgresql://"):
            db_url = "postgresql+psycopg2://" + db_url[len("postgresql://"):]

        # Garante sslmode=require para conexões com Supabase / Cloud Postgres se não especificado
        if "supabase.com" in db_url and "sslmode=" not in db_url:
            separator = "&" if "?" in db_url else "?"
            db_url = f"{db_url}{separator}sslmode=require"

        return db_url

    # Em produção (Render), rejeita qualquer tentativa de usar banco local
    if flask_env == "production" or is_render:
        raise RuntimeError(
            "ERRO CRÍTICO: DATABASE_URL não configurada no ambiente de produção. "
            "Configure a variável DATABASE_URL com a conexão do Supabase Session Pooler."
        )

    # Apenas para desenvolvimento local antes da configuração do Supabase:
    instance_dir = BASE_DIR / "instance"
    instance_dir.mkdir(exist_ok=True)
    local_sqlite = f"sqlite:///{instance_dir / 'dev_voluntariado.db'}"
    return local_sqlite


class Config:
    """Configurações da aplicação Conecta Voluntários."""

    # Chave de segurança para sessões e CSRF
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)

    # Banco de dados PostgreSQL
    DATABASE_URL = get_database_url()

    # Configurações do Supabase Auth (E-mail e Senha)
    SUPABASE_URL = os.getenv("SUPABASE_URL", "https://oqwnohnvurmfnensnwlo.supabase.co")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

    # Ambiente
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    IS_PRODUCTION = FLASK_ENV.lower() == "production" or os.getenv("RENDER") is not None

    # Cookies de sessão seguros
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = IS_PRODUCTION

    # Credenciais do administrador inicial
    ADMIN_USER = os.getenv("ADMIN_USER", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

    # Textos institucionais e identidade da organização
    ORG_NAME = "Conecta Voluntários"
    ORG_TAGLINE = "Seu tempo pode fazer a diferença"
    ORG_SUBTITLE = (
        "Conectamos pessoas com vontade de ajudar a projetos sociais e ações "
        "comunitárias que transformam realidades."
    )
    ORG_ABOUT = (
        "O Conecta Voluntários é uma iniciativa criada para aproximar quem quer ajudar "
        "de causas que necessitam de apoio. Facilitamos o primeiro contato para que suas "
        "habilidades, sua disponibilidade e seu coração encontrem o lugar ideal para florescer."
    )
    ORG_FOOTER_NOTE = "Projeto demonstrativo de extensão universitária"
    ORG_EMAIL = "contato@conectavoluntarios.org"
    ORG_PHONE = "(11) 98765-4321"
    ORG_PHONE_DIGITS = "5511987654321"

    # Opções do formulário de voluntários
    AREAS_INTERESSE = [
        "Arrecadação e organização de doações",
        "Apoio em eventos",
        "Comunicação e divulgação",
        "Atividades administrativas",
        "Outra área",
    ]

    DISPONIBILIDADES = [
        "Manhã",
        "Tarde",
        "Noite",
        "Fins de semana",
        "A combinar",
    ]

    # Status de atendimento
    STATUS_VALIDOS = [
        "recebido",
        "em_analise",
        "contato_realizado",
        "participacao_confirmada",
        "encerrado",
    ]

    STATUS_LABELS = {
        "recebido": "Recebido",
        "em_analise": "Em Análise",
        "contato_realizado": "Contato Realizado",
        "participacao_confirmada": "Participação Confirmada",
        "encerrado": "Encerrado",
    }

    # Passos da Linha do Tempo para a Área do Voluntário
    TIMELINE_STEPS = [
        {
            "key": "recebido",
            "step_num": 1,
            "title": "Inscrição Recebida",
            "desc": "Sua inscrição foi recebida com sucesso pela nossa equipe e entrou na fila de acolhimento.",
            "next_info": "Nossa equipe irá analisar as informações fornecidas para identificar as melhores oportunidades.",
        },
        {
            "key": "em_analise",
            "step_num": 2,
            "title": "Em Análise",
            "desc": "Estamos avaliando as atividades disponíveis na sua área de interesse e disponibilidade de horários.",
            "next_info": "Em breve um coordenador entrará em contato via WhatsApp para conversarmos.",
        },
        {
            "key": "contato_realizado",
            "step_num": 3,
            "title": "Contato Realizado",
            "desc": "Nossa coordenação iniciou o contato via WhatsApp para tirar dúvidas e apresentar as ações.",
            "next_info": "Aguarde as orientações finais de data e local para confirmação da participação.",
        },
        {
            "key": "participacao_confirmada",
            "step_num": 4,
            "title": "Participação Confirmada",
            "desc": "Tudo pronto! Sua participação está confirmada nas ações do projeto. Seja muito bem-vindo(a)!",
            "next_info": "Acompanhe as reuniões e avisos enviados pela organização pelo WhatsApp.",
        },
    ]
