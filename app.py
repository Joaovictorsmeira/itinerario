import os
import sys
import getpass
import secrets
import re
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    abort,
)
from sqlalchemy import or_, func

from config import Config
from database import (
    db_session,
    init_db,
    seed_demo_data,
    Administrador,
    Voluntario,
    normalize_phone,
    format_phone,
    format_datetime_br,
)
from supabase_auth import signup_supabase_user, login_supabase_user, is_supabase_auth_enabled

# Inicializa aplicação Flask
app = Flask(__name__)
app.config.from_object(Config)


# ==============================================================================
# Gerenciamento de Sessão de Banco e CSRF
# ==============================================================================

@app.teardown_appcontext
def shutdown_session(exception=None):
    """Fecha a sessão do banco de dados ao final de cada requisição."""
    db_session.remove()


def generate_csrf_token() -> str:
    """Gera ou recupera o token CSRF da sessão atual."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


@app.context_processor
def inject_template_globals():
    """Injeta funções e configurações acessíveis em todos os templates."""
    return {
        "csrf_token": generate_csrf_token,
        "format_phone": format_phone,
        "format_datetime_br": format_datetime_br,
        "config": Config,
        "current_year": datetime.now().year,
        "current_admin": session.get("admin_user"),
        "current_voluntario": session.get("voluntario_nome"),
    }


@app.before_request
def check_csrf_protection():
    """Valida o token CSRF em todas as requisições POST."""
    if request.method == "POST":
        token = request.form.get("csrf_token")
        session_token = session.get("_csrf_token")
        if not token or not session_token or not secrets.compare_digest(token, session_token):
            abort(400, description="Sessão expirada ou token de segurança inválido. Recarregue a página e tente novamente.")


@app.after_request
def set_security_headers(response):
    """Aplica cabeçalhos de segurança essenciais."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


def admin_required(f):
    """Decorator para exigir autenticação administrativa."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Acesso restrito. Faça login para continuar.", "warning")
            return redirect(url_for("admin_login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def voluntario_required(f):
    """Decorator para exigir acesso autenticado do voluntário à sua área."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("voluntario_id"):
            flash("Informe seu número de WhatsApp para acessar sua área de acompanhamento.", "info")
            return redirect(url_for("voluntario_login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


# ==============================================================================
# Rotas Públicas
# ==============================================================================

@app.route("/", methods=["GET"])
def index():
    """Página pública de apresentação e formulário de inscrição."""
    return render_template(
        "index.html",
        areas=Config.AREAS_INTERESSE,
        disponibilidades=Config.DISPONIBILIDADES,
        form_data={},
        errors={},
    )


@app.route("/voluntarios", methods=["POST"])
def cadastrar_voluntario():
    """Valida e processa o cadastro de novo voluntário com autenticação segura."""
    form_data = {
        "nome": request.form.get("nome", "").strip(),
        "telefone": request.form.get("telefone", "").strip(),
        "email": request.form.get("email", "").strip(),
        "senha": request.form.get("senha", ""),
        "confirmar_senha": request.form.get("confirmar_senha", ""),
        "cidade": request.form.get("cidade", "").strip(),
        "area_interesse": request.form.get("area_interesse", "").strip(),
        "disponibilidade": request.form.get("disponibilidade", "").strip(),
        "mensagem": request.form.get("mensagem", "").strip(),
        "autorizacao_contato": request.form.get("autorizacao_contato"),
    }

    errors = {}

    # Validação do Nome
    if not form_data["nome"]:
        errors["nome"] = "Informe seu nome completo."
    elif len(form_data["nome"]) < 3 or len(form_data["nome"]) > 100:
        errors["nome"] = "O nome deve ter entre 3 e 100 caracteres."

    # Validação e normalização do Telefone
    normalized_phone = ""
    try:
        normalized_phone = normalize_phone(form_data["telefone"])
    except ValueError as e:
        errors["telefone"] = str(e)

    # Validação do E-mail (obrigatório)
    if not form_data["email"]:
        errors["email"] = "Informe seu endereço de e-mail."
    elif len(form_data["email"]) > 254:
        errors["email"] = "O e-mail pode ter no máximo 254 caracteres."
    elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", form_data["email"]):
        errors["email"] = "Informe um endereço de e-mail válido."

    # Validação da Senha
    if not form_data["senha"]:
        errors["senha"] = "Crie uma senha de acesso."
    elif len(form_data["senha"]) < 6:
        errors["senha"] = "A senha deve ter no mínimo 6 caracteres."

    if not form_data["confirmar_senha"]:
        errors["confirmar_senha"] = "Confirme sua senha."
    elif form_data["senha"] != form_data["confirmar_senha"]:
        errors["confirmar_senha"] = "As senhas não coincidem."

    # Validação da Cidade
    if not form_data["cidade"]:
        errors["cidade"] = "Informe sua cidade ou região."
    elif len(form_data["cidade"]) > 100:
        errors["cidade"] = "A cidade/região deve ter no máximo 100 caracteres."

    # Validação da Área de Interesse
    if not form_data["area_interesse"]:
        errors["area_interesse"] = "Selecione uma área de interesse."
    elif form_data["area_interesse"] not in Config.AREAS_INTERESSE:
        errors["area_interesse"] = "Área de interesse inválida."

    # Validação da Disponibilidade
    if not form_data["disponibilidade"]:
        errors["disponibilidade"] = "Selecione sua disponibilidade."
    elif form_data["disponibilidade"] not in Config.DISPONIBILIDADES:
        errors["disponibilidade"] = "Opção de disponibilidade inválida."

    # Validação da Mensagem (opcional)
    if form_data["mensagem"] and len(form_data["mensagem"]) > 500:
        errors["mensagem"] = "A mensagem pode ter no máximo 500 caracteres."

    # Validação da Autorização
    if not form_data["autorizacao_contato"]:
        errors["autorizacao_contato"] = "É necessário autorizar o contato da equipe para prosseguir."

    # Verificação de unicidade do telefone se não houver erro de formato
    if "telefone" not in errors and normalized_phone:
        existing_tel = db_session.query(Voluntario).filter_by(telefone=normalized_phone).first()
        if existing_tel:
            errors["telefone"] = "Já existe um cadastro com este telefone. Para atualizar suas informações, acesse a Área do Voluntário."

    # Verificação de unicidade do e-mail no banco local
    if "email" not in errors and form_data["email"]:
        clean_email = form_data["email"].strip().lower()
        existing_email = db_session.query(Voluntario).filter(func.lower(Voluntario.email) == clean_email).first()
        if existing_email:
            errors["email"] = "Já existe uma conta cadastrada com este e-mail. Acesse a Área do Voluntário ou use outro e-mail."

    # Em caso de erro, renderiza o formulário preservando os dados preenchidos (exceto senhas)
    if errors:
        form_data_safe = dict(form_data)
        form_data_safe["senha"] = ""
        form_data_safe["confirmar_senha"] = ""
        return (
            render_template(
                "index.html",
                areas=Config.AREAS_INTERESSE,
                disponibilidades=Config.DISPONIBILIDADES,
                form_data=form_data_safe,
                errors=errors,
            ),
            400,
        )

    # Registro no Supabase Auth se a API estiver configurada
    supabase_uid = None
    auth_ok, auth_uid, auth_err = signup_supabase_user(
        email=form_data["email"],
        password=form_data["senha"],
        metadata={"nome": form_data["nome"], "telefone": normalized_phone},
    )
    if not auth_ok:
        errors["email"] = auth_err or "Não foi possível registrar o usuário no Supabase Auth."
        form_data_safe = dict(form_data)
        form_data_safe["senha"] = ""
        form_data_safe["confirmar_senha"] = ""
        return (
            render_template(
                "index.html",
                areas=Config.AREAS_INTERESSE,
                disponibilidades=Config.DISPONIBILIDADES,
                form_data=form_data_safe,
                errors=errors,
            ),
            400,
        )
    supabase_uid = auth_uid

    # Persistência real no banco de dados
    try:
        now = datetime.now(timezone.utc)
        voluntario = Voluntario(
            nome=form_data["nome"],
            telefone=normalized_phone,
            email=form_data["email"].strip().lower(),
            cidade=form_data["cidade"],
            area_interesse=form_data["area_interesse"],
            disponibilidade=form_data["disponibilidade"],
            mensagem=form_data["mensagem"] or None,
            autorizacao_contato=1,
            autorizado_em=now,
            status="recebido",
            observacao_interna=None,
            recado_organizacao=None,
            supabase_user_id=supabase_uid,
            criado_em=now,
            atualizado_em=now,
        )
        voluntario.set_password(form_data["senha"])
        db_session.add(voluntario)
        db_session.commit()

        # Vincula sessão do voluntário para acesso imediato à sua área
        session["voluntario_id"] = voluntario.id
        session["voluntario_nome"] = voluntario.nome

    except Exception as exc:
        db_session.rollback()
        errors["geral"] = "Não foi possível salvar o cadastro no momento. Tente novamente em instantes."
        form_data_safe = dict(form_data)
        form_data_safe["senha"] = ""
        form_data_safe["confirmar_senha"] = ""
        return (
            render_template(
                "index.html",
                areas=Config.AREAS_INTERESSE,
                disponibilidades=Config.DISPONIBILIDADES,
                form_data=form_data_safe,
                errors=errors,
            ),
            500,
        )

    # Redirecionamento após sucesso (Padrão Post-Redirect-Get)
    return redirect(url_for("cadastro_concluido"))


@app.route("/cadastro-concluido", methods=["GET"])
def cadastro_concluido():
    """Página de confirmação de cadastro recebido."""
    return render_template("cadastro_concluido.html")


# ==============================================================================
# Rotas da Área do Voluntário
# ==============================================================================

@app.route("/voluntario/login", methods=["GET", "POST"])
def voluntario_login():
    """Acesso seguro à Área do Voluntário por e-mail e senha cadastrados."""
    if session.get("voluntario_id"):
        return redirect(url_for("voluntario_area"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not email or not senha:
            flash("Informe seu e-mail e sua senha para entrar.", "danger")
            return render_template("voluntario_login.html")

        # Busca voluntário no banco de dados por e-mail
        v = db_session.query(Voluntario).filter(func.lower(Voluntario.email) == email).first()

        authenticated = False
        supabase_uid = None

        if is_supabase_auth_enabled():
            # Autenticação primária via Supabase Auth REST API
            auth_ok, sb_uid, auth_err = login_supabase_user(email, senha)
            if auth_ok:
                authenticated = True
                supabase_uid = sb_uid
            elif v and v.check_password(senha):
                # Fallback se usuário já tinha hash local válido
                authenticated = True
        else:
            # Fallback seguro por hash de senha no PostgreSQL
            if v and v.check_password(senha):
                authenticated = True

        if authenticated and v:
            if supabase_uid and not v.supabase_user_id:
                v.supabase_user_id = supabase_uid
                db_session.commit()

            session["voluntario_id"] = v.id
            session["voluntario_nome"] = v.nome
            flash(f"Bem-vindo(a), {v.nome}!", "success")
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/voluntario"):
                return redirect(next_url)
            return redirect(url_for("voluntario_area"))
        else:
            flash("E-mail ou senha incorretos. Verifique suas credenciais ou realize sua inscrição.", "danger")

    return render_template("voluntario_login.html")


@app.route("/voluntario/logout", methods=["POST"])
def voluntario_logout():
    """Encerra a sessão do voluntário."""
    session.pop("voluntario_id", None)
    session.pop("voluntario_nome", None)
    flash("Sessão finalizada com sucesso.", "info")
    return redirect(url_for("index"))


@app.route("/voluntario", methods=["GET"])
@voluntario_required
def voluntario_area():
    """Área exclusiva do voluntário com status, linha do tempo, recados e perfil."""
    v = db_session.get(Voluntario, session["voluntario_id"])
    if not v:
        session.pop("voluntario_id", None)
        session.pop("voluntario_nome", None)
        flash("Cadastro não localizado.", "warning")
        return redirect(url_for("voluntario_login"))

    # Mapeamento do número da etapa da linha do tempo
    # "encerrado" possui apresentação própria e NÃO deve marcar a etapa 4 ("Participação Confirmada")
    step_mapping = {
        "recebido": 1,
        "em_analise": 2,
        "contato_realizado": 3,
        "participacao_confirmada": 4,
    }
    is_encerrado = (v.status == "encerrado")
    current_step_num = 0 if is_encerrado else step_mapping.get(v.status, 1)

    # Informações da etapa atual
    step_info_mapping = {
        "recebido": "Sua inscrição foi recebida e está aguardando análise pela equipe de triagem.",
        "em_analise": "Estamos avaliando as atividades disponíveis e sua disponibilidade de horários.",
        "contato_realizado": "A coordenação iniciou contato com você via WhatsApp para apresentar o projeto.",
        "participacao_confirmada": "Tudo alinhado! Sua participação está confirmada nas ações do projeto.",
        "encerrado": "O ciclo de participação para esta inscrição foi encerrado pela coordenação. Agradecemos sua colaboração e entusiasmo.",
    }
    current_step_info = step_info_mapping.get(v.status, "Acompanhe as atualizações da coordenação.")
    status_label = Config.STATUS_LABELS.get(v.status, v.status.capitalize())

    return render_template(
        "voluntario_area.html",
        v=v,
        timeline_steps=Config.TIMELINE_STEPS,
        current_step_num=current_step_num,
        current_step_info=current_step_info,
        status_label=status_label,
        is_encerrado=is_encerrado,
    )


@app.route("/voluntario/perfil/atualizar", methods=["POST"])
@voluntario_required
def voluntario_atualizar_perfil():
    """Permite ao voluntário atualizar seus próprios dados de contato, interesse e disponibilidade."""
    v = db_session.get(Voluntario, session["voluntario_id"])
    if not v:
        abort(404)

    novo_telefone = request.form.get("telefone", "").strip()
    novo_email = request.form.get("email", "").strip().lower()
    nova_cidade = request.form.get("cidade", "").strip()
    nova_area = request.form.get("area_interesse", "").strip()
    nova_disp = request.form.get("disponibilidade", "").strip()
    nova_mensagem = request.form.get("mensagem", "").strip()

    # Validação do telefone
    try:
        norm_tel = normalize_phone(novo_telefone)
        if norm_tel != v.telefone:
            existing_tel = db_session.query(Voluntario).filter_by(telefone=norm_tel).first()
            if existing_tel:
                flash("Já existe outro cadastro utilizando este número de telefone.", "danger")
                return redirect(url_for("voluntario_area"))
            v.telefone = norm_tel
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("voluntario_area"))

    # Validação de e-mail (obrigatório para manter acesso)
    if not novo_email:
        flash("O e-mail é obrigatório para acessar sua conta.", "danger")
        return redirect(url_for("voluntario_area"))
    elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", novo_email):
        flash("Informe um endereço de e-mail válido.", "danger")
        return redirect(url_for("voluntario_area"))
    elif novo_email != (v.email or "").lower():
        existing_mail = db_session.query(Voluntario).filter(func.lower(Voluntario.email) == novo_email, Voluntario.id != v.id).first()
        if existing_mail:
            flash("Já existe outro cadastro utilizando este endereço de e-mail.", "danger")
            return redirect(url_for("voluntario_area"))
        v.email = novo_email

    if not nova_cidade:
        flash("A cidade ou região é obrigatória.", "danger")
        return redirect(url_for("voluntario_area"))

    if nova_area not in Config.AREAS_INTERESSE:
        flash("Área de interesse inválida.", "danger")
        return redirect(url_for("voluntario_area"))

    if nova_disp not in Config.DISPONIBILIDADES:
        flash("Disponibilidade inválida.", "danger")
        return redirect(url_for("voluntario_area"))

    v.cidade = nova_cidade
    v.area_interesse = nova_area
    v.disponibilidade = nova_disp
    v.mensagem = nova_mensagem or None
    v.atualizado_em = datetime.now(timezone.utc)

    try:
        db_session.commit()
        flash("Seus dados foram atualizados com sucesso!", "success")
    except Exception:
        db_session.rollback()
        flash("Erro ao salvar alterações no banco de dados.", "danger")

    return redirect(url_for("voluntario_area"))


# ==============================================================================
# Rotas Administrativas (Área da Organização)
# ==============================================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Autenticação de administrador da organização."""
    if session.get("admin_id"):
        return redirect(url_for("admin_painel"))

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()

        admin = db_session.query(Administrador).filter_by(usuario=usuario).first()
        if admin and admin.check_password(senha):
            session.clear()
            session["admin_id"] = admin.id
            session["admin_user"] = admin.usuario
            session.permanent = True
            flash("Login realizado com sucesso!", "success")
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/admin"):
                return redirect(next_url)
            return redirect(url_for("admin_painel"))

        flash("Usuário ou senha incorretos.", "danger")

    return render_template("admin_login.html")


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    """Encerra a sessão administrativa."""
    session.clear()
    flash("Sessão finalizada com sucesso.", "info")
    return redirect(url_for("admin_login"))


@app.route("/admin", methods=["GET"])
@admin_required
def admin_painel():
    """Painel principal da organização com indicadores, busca e filtros."""
    termo_busca = request.args.get("q", "").strip()
    status_filtro = request.args.get("status", "todos").strip().lower()

    # Indicadores calculados a partir do banco de dados
    total_inscritos = db_session.query(Voluntario).count()
    cadastros_novos = db_session.query(Voluntario).filter(Voluntario.status.in_(["recebido", "em_analise"])).count()
    voluntarios_ativos = db_session.query(Voluntario).filter_by(status="participacao_confirmada").count()

    query = db_session.query(Voluntario)

    # Filtro por busca de texto (Nome, Cidade ou Telefone)
    if termo_busca:
        condicoes = [
            Voluntario.nome.ilike(f"%{termo_busca}%"),
            Voluntario.cidade.ilike(f"%{termo_busca}%"),
            Voluntario.telefone.ilike(f"%{termo_busca}%"),
        ]
        termo_digitos = re.sub(r"\D", "", termo_busca)
        if len(termo_digitos) >= 4:
            condicoes.append(Voluntario.telefone.ilike(f"%{termo_digitos}%"))
        query = query.filter(or_(*condicoes))

    # Filtro por status
    if status_filtro and status_filtro != "todos" and status_filtro in Config.STATUS_VALIDOS:
        query = query.filter(Voluntario.status == status_filtro)

    # Ordenação decrescente pelos mais recentes
    voluntarios = query.order_by(Voluntario.criado_em.desc()).all()

    return render_template(
        "admin_painel.html",
        voluntarios=voluntarios,
        total_inscritos=total_inscritos,
        cadastros_novos=cadastros_novos,
        voluntarios_ativos=voluntarios_ativos,
        q=termo_busca,
        status_filtro=status_filtro,
        total_filtrados=len(voluntarios),
    )


@app.route("/admin/voluntarios/<int:id>", methods=["GET"])
@admin_required
def admin_detalhes(id: int):
    """Visualização detalhada dos dados e histórico de um voluntário."""
    voluntario = db_session.get(Voluntario, id)
    if not voluntario:
        abort(404)
    return render_template("admin_detalhes.html", v=voluntario, status_opcoes=Config.STATUS_VALIDOS)


@app.route("/admin/voluntarios/<int:id>/atualizar", methods=["POST"])
@admin_required
def admin_atualizar(id: int):
    """Atualiza o status, recado para o voluntário e a observação interna."""
    voluntario = db_session.get(Voluntario, id)
    if not voluntario:
        abort(404)

    novo_status = request.form.get("status", "").strip().lower()
    observacao = request.form.get("observacao_interna", "").strip()
    recado = request.form.get("recado_organizacao", "").strip()

    if novo_status not in Config.STATUS_VALIDOS:
        flash("Status selecionado inválido.", "danger")
        return redirect(url_for("admin_detalhes", id=id))

    if len(observacao) > 1000:
        flash("A observação interna não pode exceder 1.000 caracteres.", "danger")
        return redirect(url_for("admin_detalhes", id=id))

    if len(recado) > 1000:
        flash("O recado para o voluntário não pode exceder 1.000 caracteres.", "danger")
        return redirect(url_for("admin_detalhes", id=id))

    voluntario.status = novo_status
    voluntario.observacao_interna = observacao or None
    voluntario.recado_organizacao = recado or None
    voluntario.atualizado_em = datetime.now(timezone.utc)

    try:
        db_session.commit()
        flash("Cadastro atualizado com sucesso!", "success")
    except Exception:
        db_session.rollback()
        flash("Erro ao salvar alterações no banco de dados.", "danger")

    return redirect(url_for("admin_detalhes", id=id))


@app.route("/admin/voluntarios/<int:id>/excluir", methods=["POST"])
@admin_required
def admin_excluir(id: int):
    """Remove permanentemente o cadastro do voluntário após confirmação."""
    voluntario = db_session.get(Voluntario, id)
    if not voluntario:
        abort(404)

    nome_removido = voluntario.nome
    try:
        db_session.delete(voluntario)
        db_session.commit()
        flash(f"Cadastro de '{nome_removido}' excluído com sucesso.", "success")
    except Exception:
        db_session.rollback()
        flash("Erro ao excluir cadastro do banco de dados.", "danger")

    return redirect(url_for("admin_painel"))


# ==============================================================================
# Tratamento de Erros
# ==============================================================================

@app.errorhandler(400)
def bad_request_error(e):
    return render_template("404.html", mensagem="Requisição inválida ou token CSRF expirado.", titulo="400 — Requisição Inválida"), 400


@app.errorhandler(404)
def not_found_error(e):
    return render_template("404.html", mensagem="A página ou registro solicitado não foi encontrado.", titulo="404 — Página Não Encontrada"), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template("404.html", mensagem="Ocorreu uma instabilidade momentânea no servidor. Tente novamente em instantes.", titulo="500 — Erro Interno"), 500


# ==============================================================================
# Utilitários de Inicialização e CLI
# ==============================================================================

def ensure_admin_configured():
    """Garante a existência do administrador padrão configurado por variáveis de ambiente."""
    if Config.ADMIN_USER and Config.ADMIN_PASSWORD:
        admin = db_session.query(Administrador).filter_by(usuario=Config.ADMIN_USER).first()
        if not admin:
            novo_admin = Administrador(usuario=Config.ADMIN_USER)
            novo_admin.set_password(Config.ADMIN_PASSWORD)
            db_session.add(novo_admin)
            db_session.commit()
            print(f"[INIT] Administrador '{Config.ADMIN_USER}' configurado com sucesso via variáveis de ambiente.")
        else:
            admin.set_password(Config.ADMIN_PASSWORD)
            db_session.commit()


# AJUSTE 3: A inicialização NÃO roda mais no import do módulo para evitar concorrência entre workers.
# Deve ser executada explicitamente via CLI: python app.py --setup ou python app.py --init-db

if __name__ == "__main__":
    args = sys.argv[1:]

    if "--setup" in args or "--init-db" in args:
        print("Criando e verificando tabelas no banco de dados...")
        init_db()
        ensure_admin_configured()
        print("Tabelas e administrador inicializados com sucesso!")
        sys.exit(0)

    if "--create-admin" in args:
        init_db()
        username = os.getenv("ADMIN_USER")
        password = os.getenv("ADMIN_PASSWORD")

        if not username:
            username = input("Digite o nome de usuário do administrador: ").strip()

        if not password:
            password = getpass.getpass("Digite a senha do administrador: ").strip()
            confirmacao = getpass.getpass("Confirme a senha: ").strip()
            if password != confirmacao:
                print("ERRO: As senhas digitadas não coincidem.")
                sys.exit(1)

        if not username or not password:
            print("ERRO: Usuário e senha não podem ser vazios.")
            sys.exit(1)

        admin = db_session.query(Administrador).filter_by(usuario=username).first()
        if admin:
            admin.set_password(password)
            print(f"Senha do administrador '{username}' atualizada com sucesso!")
        else:
            novo_admin = Administrador(usuario=username)
            novo_admin.set_password(password)
            db_session.add(novo_admin)
            print(f"Administrador '{username}' criado com sucesso!")

        db_session.commit()
        sys.exit(0)

    if "--seed-demo" in args:
        init_db()
        qtd = seed_demo_data()
        print(f"Dados demonstrativos inseridos com sucesso! Total adicionado: {qtd}")
        sys.exit(0)

    # Execução local direta
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
