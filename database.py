import re
from datetime import datetime, timezone, timedelta
import zoneinfo
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    text,
)
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

# Configura o Engine do SQLAlchemy
engine_args = {
    "pool_pre_ping": True,  # Testa conexões antes do reuso (crucial para Supabase Session Pooler)
}

if Config.DATABASE_URL.startswith("postgresql"):
    # Configurações otimizadas para Session Pooler do PostgreSQL (Supabase / Nuvem)
    engine_args.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,  # Recicla conexões a cada 30 minutos
    })
elif Config.DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(Config.DATABASE_URL, **engine_args)

db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

Base = declarative_base()
Base.query = db_session.query_property()


# ==============================================================================
# Modelos de Dados
# ==============================================================================

class Administrador(Base):
    """Administrador com acesso restrito ao painel da organização."""
    __tablename__ = "administradores"

    id = Column(Integer, primary_key=True)
    usuario = Column(String(100), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    criado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def set_password(self, password: str) -> None:
        self.senha_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.senha_hash, password)

    def __repr__(self) -> str:
        return f"<Administrador {self.usuario}>"


class Voluntario(Base):
    """Cadastro de voluntário interessado em apoiar o projeto de extensão."""
    __tablename__ = "voluntarios"

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    telefone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(254), nullable=True)
    cidade = Column(String(100), nullable=False)
    area_interesse = Column(String(100), nullable=False)
    disponibilidade = Column(String(50), nullable=False)
    mensagem = Column(String(500), nullable=True)
    autorizacao_contato = Column(Integer, default=1, nullable=False)
    autorizado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    status = Column(
        String(50),
        default="recebido",
        nullable=False,
        index=True,
    )  # 'recebido', 'em_analise', 'contato_realizado', 'participacao_confirmada', 'encerrado'
    observacao_interna = Column(Text, nullable=True)  # Observação restrita da equipe
    recado_organizacao = Column(Text, nullable=True)  # Mensagem visível na Área do Voluntário
    supabase_user_id = Column(String(100), unique=True, nullable=True, index=True)  # Vínculo com Supabase Auth
    senha_hash = Column(String(255), nullable=True)  # Hash seguro de senha
    criado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    atualizado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def set_password(self, password: str) -> None:
        self.senha_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.senha_hash:
            return False
        return check_password_hash(self.senha_hash, password)

    def __repr__(self) -> str:
        return f"<Voluntario {self.nome} ({self.email}) - {self.status}>"


# ==============================================================================
# Funções Auxiliares de Validação e Formatação
# ==============================================================================

VALID_DDDS = {
    "11", "12", "13", "14", "15", "16", "17", "18", "19",
    "21", "22", "24", "27", "28",
    "31", "32", "33", "34", "35", "37", "38",
    "41", "42", "43", "44", "45", "46", "47", "48", "49",
    "51", "53", "54", "55",
    "61", "62", "63", "64", "65", "66", "67", "68", "69",
    "71", "73", "74", "75", "77", "79",
    "81", "82", "83", "84", "85", "86", "87", "88", "89",
    "91", "92", "93", "94", "95", "96", "97", "98", "99",
}


def normalize_phone(raw_phone: str) -> str:
    """
    Normaliza telefone brasileiro para o padrão canônico com código do país (DDI 55).
    Aceita 10 ou 11 dígitos nacionais com ou sem prefixo 55.
    Retorna no formato '55XXXXXXXXXXX' ou '55XXXXXXXXXX'.
    Lança ValueError caso o formato seja inválido.
    """
    if not raw_phone:
        raise ValueError("O telefone é obrigatório.")

    digits = re.sub(r"\D", "", raw_phone.strip())

    if digits.startswith("55") and len(digits) in (12, 13):
        national = digits[2:]
    elif len(digits) in (10, 11):
        national = digits
    else:
        raise ValueError(
            "Telefone inválido. Informe um número com DDD brasileiro (10 ou 11 dígitos)."
        )

    ddd = national[:2]
    if ddd not in VALID_DDDS:
        raise ValueError(f"DDD '{ddd}' não é um DDD válido no Brasil.")

    if len(national) == 11 and national[2] != "9":
        raise ValueError("Número de celular com 11 dígitos deve iniciar com 9 após o DDD.")

    return f"55{national}"


def format_phone(normalized_phone: str) -> str:
    """
    Formata o número normalizado '5511999998888' para visualização legível '(11) 99999-8888'.
    """
    if not normalized_phone:
        return ""
    digits = re.sub(r"\D", "", normalized_phone)
    if digits.startswith("55") and len(digits) in (12, 13):
        national = digits[2:]
    else:
        national = digits

    if len(national) == 11:
        return f"({national[:2]}) {national[2:7]}-{national[7:]}"
    elif len(national) == 10:
        return f"({national[:2]}) {national[2:6]}-{national[6:]}"
    return normalized_phone


def format_datetime_br(dt: datetime | None) -> str:
    """
    Formata datetime UTC para o fuso 'America/Sao_Paulo' no formato 'DD/MM/YYYY às HH:MM'.
    """
    if not dt:
        return "Não informado"
    try:
        tz_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
    except Exception:
        tz_br = timezone(timedelta(hours=-3))

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_local = dt.astimezone(tz_br)
    return dt_local.strftime("%d/%m/%Y às %H:%M")


def init_db() -> None:
    """Inicializa as tabelas no banco de dados e aplica colunas adicionais de forma idempotente."""
    Base.metadata.create_all(bind=engine)
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE voluntarios ADD COLUMN IF NOT EXISTS recado_organizacao TEXT;"))
            conn.execute(text("ALTER TABLE voluntarios ADD COLUMN IF NOT EXISTS supabase_user_id VARCHAR(100);"))
            conn.execute(text("ALTER TABLE voluntarios ADD COLUMN IF NOT EXISTS senha_hash VARCHAR(255);"))
            conn.execute(text("ALTER TABLE voluntarios ALTER COLUMN status TYPE VARCHAR(50);"))
            conn.commit()
    except Exception:
        pass


def seed_demo_data() -> int:
    """
    Insere cadastros demonstrativos com recados da organização e senha padrão 'voluntario123', se não existirem.
    Retorna o número de registros inseridos.
    """
    demo_voluntarios = [
        {
            "nome": "Voluntário demonstrativo 01",
            "telefone": "5511987654321",
            "email": "voluntario01@exemplo.com",
            "cidade": "São Paulo, SP",
            "area_interesse": "Arrecadação e organização de doações",
            "disponibilidade": "Fins de semana",
            "mensagem": "Tenho experiência com triagem e empacotamento de cestas básicas.",
            "status": "recebido",
            "observacao_interna": "Aguardando primeiro contato telefônico da coordenação.",
            "recado_organizacao": "Obrigado por se inscrever! Nossa equipe entrará em contato em breve para apresentar os projetos.",
        },
        {
            "nome": "Voluntário demonstrativo 02",
            "telefone": "5521976543210",
            "email": "voluntario02@exemplo.com",
            "cidade": "Rio de Janeiro, RJ",
            "area_interesse": "Apoio em eventos",
            "disponibilidade": "Sábado pela manhã",
            "mensagem": "Posso ajudar na recepção e credenciamento dos participantes.",
            "status": "em_analise",
            "observacao_interna": "Avaliando alocação na oficina do próximo sábado.",
            "recado_organizacao": "Estamos alinhando as vagas na oficina comunitária e retornaremos nesta quinta-feira.",
        },
        {
            "nome": "Voluntário demonstrativo 03",
            "telefone": "5531965432109",
            "email": "voluntario03@exemplo.com",
            "cidade": "Belo Horizonte, MG",
            "area_interesse": "Comunicação e divulgação",
            "disponibilidade": "Noite",
            "mensagem": "Faço design gráfico e edição de posts para redes sociais.",
            "status": "contato_realizado",
            "observacao_interna": "Conversamos por WhatsApp em 08/10. Confirmou interesse nas mídias sociais.",
            "recado_organizacao": "Sua reunião de apresentação com a equipe de comunicação será na terça-feira às 19h pelo Google Meet.",
        },
        {
            "nome": "Voluntário demonstrativo 04",
            "telefone": "5561954321098",
            "email": "voluntario04@exemplo.com",
            "cidade": "Brasília, DF",
            "area_interesse": "Atividades administrativas",
            "disponibilidade": "Tarde",
            "mensagem": "Experiência com organização de planilhas e arquivos digitais.",
            "status": "participacao_confirmada",
            "observacao_interna": "Integrado à equipe administrativa; escala semanal confirmada.",
            "recado_organizacao": "Participação confirmada! Seu termo de voluntariado e crachá estão prontos na recepção da sede.",
        },
        {
            "nome": "Voluntário demonstrativo 05",
            "telefone": "5541943210987",
            "email": "voluntario05@exemplo.com",
            "cidade": "Curitiba, PR",
            "area_interesse": "Outra área",
            "disponibilidade": "A combinar",
            "mensagem": "Gostaria de dar aulas de apoio de informática para jovens.",
            "status": "contato_realizado",
            "observacao_interna": "Contato feito; avaliando montagem de laboratório de informática.",
            "recado_organizacao": "Estamos definindo os horários das turmas e entraremos em contato na próxima semana.",
        },
        {
            "nome": "Voluntário demonstrativo 06",
            "telefone": "5571932109876",
            "email": "voluntario06@exemplo.com",
            "cidade": "Salvador, BA",
            "area_interesse": "Apoio em eventos",
            "disponibilidade": "Manhã",
            "mensagem": "Disponível durante a semana.",
            "status": "encerrado",
            "observacao_interna": "Mudou de cidade e encerrou as atividades temporariamente.",
            "recado_organizacao": "Agradecemos profundamente pela sua dedicação durante o período em que colaborou conosco!",
        },
    ]

    inserted = 0
    now = datetime.now(timezone.utc)

    for data in demo_voluntarios:
        existing = db_session.query(Voluntario).filter_by(telefone=data["telefone"]).first()
        if not existing:
            v = Voluntario(
                nome=data["nome"],
                telefone=data["telefone"],
                email=data["email"],
                cidade=data["cidade"],
                area_interesse=data["area_interesse"],
                disponibilidade=data["disponibilidade"],
                mensagem=data["mensagem"],
                autorizacao_contato=1,
                autorizado_em=now,
                status=data["status"],
                observacao_interna=data["observacao_interna"],
                recado_organizacao=data["recado_organizacao"],
                criado_em=now,
                atualizado_em=now,
            )
            v.set_password("voluntario123")
            db_session.add(v)
            inserted += 1
        elif not existing.senha_hash:
            existing.set_password("voluntario123")
            if not existing.email and data["email"]:
                existing.email = data["email"]
            db_session.add(existing)
            inserted += 1

    if inserted > 0:
        db_session.commit()

    return inserted
