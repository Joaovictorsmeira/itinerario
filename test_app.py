import unittest
import re
from app import app
from database import db_session, Voluntario, Administrador, normalize_phone, format_phone, format_datetime_br

class ConectaVoluntariosTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def get_csrf_token(self, html_content: str) -> str:
        """Extrai o token CSRF de um formulário renderizado."""
        match = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html_content)
        if match:
            return match.group(1)
        match = re.search(r'value=["\']([^"\']+)["\']\s+name=["\']csrf_token["\']', html_content)
        if match:
            return match.group(1)
        raise ValueError("Token CSRF não encontrado no HTML retornado.")

    def test_01_public_index_loads_and_has_no_js_class(self):
        """1. A página pública abre com sucesso e possui o fallback sem JavaScript ativado na tag html."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("Conecta Voluntários", html)
        self.assertIn('<html lang="pt-BR" class="no-js">', html)
        self.assertIn("document.documentElement.classList.remove('no-js')", html)
        self.assertIn("Inscrição de Voluntário", html)

    def test_02_cadastro_valido_persiste_e_loga_voluntario(self):
        """2. Um cadastro válido com e-mail e senha é salvo no banco de dados e inicia a sessão do voluntário."""
        db_session.query(Voluntario).filter_by(telefone="5511999990001").delete()
        db_session.query(Voluntario).filter_by(email="candidato.teste@exemplo.com").delete()
        db_session.commit()

        get_resp = self.client.get("/")
        token = self.get_csrf_token(get_resp.data.decode("utf-8"))

        post_data = {
            "csrf_token": token,
            "nome": "Candidato de Teste Automatizado",
            "telefone": "(11) 99999-0001",
            "email": "candidato.teste@exemplo.com",
            "senha": "senhaSegura123!",
            "confirmar_senha": "senhaSegura123!",
            "cidade": "Campinas, SP",
            "area_interesse": "Apoio em eventos",
            "disponibilidade": "Fins de semana",
            "mensagem": "Gostaria muito de colaborar nas oficinas comunitárias.",
            "autorizacao_contato": "1",
        }

        resp = self.client.post("/voluntarios", data=post_data, follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.headers["Location"].endswith("/cadastro-concluido"))

        # Confirma tela de sucesso com link para Área do Voluntário
        success_resp = self.client.get("/cadastro-concluido")
        self.assertEqual(success_resp.status_code, 200)
        html_success = success_resp.data.decode("utf-8")
        self.assertIn("Cadastro recebido com sucesso!", html_success)
        self.assertIn("Acessar Minha Área do Voluntário", html_success)

        # Verifica persistência real no banco de dados e hash da senha
        voluntario = db_session.query(Voluntario).filter_by(telefone="5511999990001").first()
        self.assertIsNotNone(voluntario)
        self.assertEqual(voluntario.nome, "Candidato de Teste Automatizado")
        self.assertEqual(voluntario.email, "candidato.teste@exemplo.com")
        self.assertTrue(voluntario.check_password("senhaSegura123!"))
        self.assertFalse(voluntario.check_password("senha_incorreta"))
        self.assertEqual(voluntario.status, "recebido")

    def test_03_bloqueia_duplicidade_mesmo_com_mascaras_diferentes(self):
        """3. O mesmo telefone com máscaras diferentes não produz inscrições duplicadas."""
        get_resp = self.client.get("/")
        token = self.get_csrf_token(get_resp.data.decode("utf-8"))

        post_data = {
            "csrf_token": token,
            "nome": "Outro Nome com Mesmo Telefone",
            "telefone": "+55 11 99999-0001",
            "email": "outro@exemplo.com",
            "senha": "senhaSegura123!",
            "confirmar_senha": "senhaSegura123!",
            "cidade": "São Paulo, SP",
            "area_interesse": "Comunicação e divulgação",
            "disponibilidade": "Noite",
            "mensagem": "",
            "autorizacao_contato": "1",
        }

        resp = self.client.post("/voluntarios", data=post_data)
        self.assertEqual(resp.status_code, 400)
        html = resp.data.decode("utf-8")
        self.assertIn("Já existe um cadastro com este telefone", html)

    def test_04_recusa_cadastro_invalido_ou_sem_autorizacao(self):
        """4. Cadastro sem autorização, sem senha ou com campos inválidos é recusado com mensagens compreensíveis."""
        get_resp = self.client.get("/")
        token = self.get_csrf_token(get_resp.data.decode("utf-8"))

        post_data = {
            "csrf_token": token,
            "nome": "Al",
            "telefone": "123",
            "email": "email_invalido",
            "senha": "123",
            "confirmar_senha": "456",
            "cidade": "",
            "area_interesse": "",
            "disponibilidade": "",
        }

        resp = self.client.post("/voluntarios", data=post_data)
        self.assertEqual(resp.status_code, 400)
        html = resp.data.decode("utf-8")
        self.assertIn("O nome deve ter entre 3 e 100 caracteres", html)
        self.assertIn("Telefone inválido", html)
        self.assertIn("Informe um endereço de e-mail válido", html)
        self.assertIn("A senha deve ter no mínimo 6 caracteres", html)
        self.assertIn("As senhas não coincidem", html)
        self.assertIn("Informe sua cidade ou região", html)
        self.assertIn("Selecione uma área de interesse", html)
        self.assertIn("Selecione sua disponibilidade", html)
        self.assertIn("É necessário autorizar o contato da equipe", html)

    def test_05_csrf_protection(self):
        """5. Requisições POST sem token CSRF ou com token adulterado são rejeitadas com HTTP 400."""
        resp = self.client.post("/voluntarios", data={"nome": "Teste Sem CSRF"})
        self.assertEqual(resp.status_code, 400)

        resp2 = self.client.post("/voluntarios", data={"csrf_token": "token_falso_invalido"})
        self.assertEqual(resp2.status_code, 400)

    def test_06_autenticacao_administrativa_e_controle_de_acesso(self):
        """6. Login válido entra, login inválido falha, rotas protegidas barram visitantes sem login."""
        resp_admin = self.client.get("/admin", follow_redirects=False)
        self.assertEqual(resp_admin.status_code, 302)
        self.assertTrue(resp_admin.headers["Location"].startswith("/admin/login"))

        login_page = self.client.get("/admin/login")
        token = self.get_csrf_token(login_page.data.decode("utf-8"))

        resp_fail = self.client.post("/admin/login", data={
            "csrf_token": token,
            "usuario": "admin",
            "senha": "senha_completamente_errada",
        }, follow_redirects=True)
        self.assertIn("Usuário ou senha incorretos", resp_fail.data.decode("utf-8"))

        resp_success = self.client.post("/admin/login", data={
            "csrf_token": token,
            "usuario": "admin",
            "senha": "admin123_extensao",
        }, follow_redirects=True)
        self.assertEqual(resp_success.status_code, 200)
        html_painel = resp_success.data.decode("utf-8")
        self.assertIn("Visão Geral dos Voluntários", html_painel)

        token_painel = self.get_csrf_token(html_painel)
        resp_logout = self.client.post("/admin/logout", data={"csrf_token": token_painel}, follow_redirects=True)
        self.assertEqual(resp_logout.status_code, 200)

    def test_07_area_do_voluntario_timeline_recado_e_edicao(self):
        """7. Área do Voluntário: login com e-mail e senha, rejeição de senha incorreta, recados e status Encerrado."""
        voluntario = db_session.query(Voluntario).filter_by(telefone="5511999990001").first()

        # Tentativa de login com senha errada
        login_page = self.client.get("/voluntario/login")
        token = self.get_csrf_token(login_page.data.decode("utf-8"))

        resp_fail = self.client.post(
            "/voluntario/login",
            data={
                "csrf_token": token,
                "email": "candidato.teste@exemplo.com",
                "senha": "senha_totalmente_errada",
            },
            follow_redirects=True,
        )
        self.assertIn("E-mail ou senha incorretos", resp_fail.data.decode("utf-8"))

        # Login correto com e-mail e senha
        token_retry = self.get_csrf_token(resp_fail.data.decode("utf-8"))
        resp_login = self.client.post(
            "/voluntario/login",
            data={
                "csrf_token": token_retry,
                "email": "candidato.teste@exemplo.com",
                "senha": "senhaSegura123!",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp_login.status_code, 200)
        html_area = resp_login.data.decode("utf-8")
        self.assertIn("Candidato de Teste Automatizado", html_area)
        self.assertIn("Linha do Tempo", html_area)
        self.assertIn("Inscrição Recebida", html_area)
        self.assertIn("Fale com a Coordenação", html_area)
        self.assertIn("Meu Perfil", html_area)

        # Atualiza perfil pelo voluntário
        token_area = self.get_csrf_token(html_area)
        resp_update_perfil = self.client.post(
            "/voluntario/perfil/atualizar",
            data={
                "csrf_token": token_area,
                "telefone": "(11) 99999-0001",
                "email": "novo.email@exemplo.com",
                "cidade": "Valinhos, SP",
                "area_interesse": "Comunicação e divulgação",
                "disponibilidade": "Tarde",
                "mensagem": "Atualizei meus horários para tarde.",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp_update_perfil.status_code, 200)
        self.assertIn("Seus dados foram atualizados com sucesso!", resp_update_perfil.data.decode("utf-8"))

        # Confirma atualização no banco
        db_session.expire_all()
        v_atualizado = db_session.get(Voluntario, voluntario.id)
        self.assertEqual(v_atualizado.cidade, "Valinhos, SP")
        self.assertEqual(v_atualizado.email, "novo.email@exemplo.com")
        self.assertEqual(v_atualizado.disponibilidade, "Tarde")

        # Admin atualiza status, escreve recado e observação interna privada
        with self.client.session_transaction() as sess:
            sess["admin_id"] = 1
            sess["admin_user"] = "admin"

        detalhes_page = self.client.get(f"/admin/voluntarios/{voluntario.id}")
        token_admin = self.get_csrf_token(detalhes_page.data.decode("utf-8"))

        resp_admin_update = self.client.post(
            f"/admin/voluntarios/{voluntario.id}/atualizar",
            data={
                "csrf_token": token_admin,
                "status": "contato_realizado",
                "recado_organizacao": "Sua reunião de apresentação será na terça-feira às 19h no auditório.",
                "observacao_interna": "ESTA É UMA NOTA INTERNA RESTRITA DA ORGANIZAÇÃO",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp_admin_update.status_code, 200)

        # Agora o voluntário acessa sua área novamente
        with self.client.session_transaction() as sess:
            sess["voluntario_id"] = voluntario.id
            sess["voluntario_nome"] = voluntario.nome

        resp_vol_novo = self.client.get("/voluntario")
        html_vol = resp_vol_novo.data.decode("utf-8")
        # Deve exibir o recado da coordenação
        self.assertIn("Sua reunião de apresentação será na terça-feira às 19h no auditório.", html_vol)
        # NUNCA deve expor a observação interna privada
        self.assertNotIn("ESTA É UMA NOTA INTERNA RESTRITA DA ORGANIZAÇÃO", html_vol)
        # Deve refletir o status "Contato Realizado"
        self.assertIn("Contato Realizado", html_vol)

        # Teste do status Encerrado: Não deve parecer como confirmação de participação
        resp_admin_close = self.client.post(
            f"/admin/voluntarios/{voluntario.id}/atualizar",
            data={
                "csrf_token": token_admin,
                "status": "encerrado",
                "recado_organizacao": "Ciclo de voluntariado encerrado para este semestre.",
                "observacao_interna": "Inscrição arquivada.",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp_admin_close.status_code, 200)

        # Voluntário acessa área com status "encerrado"
        with self.client.session_transaction() as sess:
            sess["voluntario_id"] = voluntario.id
            sess["voluntario_nome"] = voluntario.nome

        resp_vol_closed = self.client.get("/voluntario")
        html_vol_closed = resp_vol_closed.data.decode("utf-8")
        # Deve exibir apresentação própria para Encerrado
        self.assertIn("Processo de Inscrição Encerrado", html_vol_closed)
        self.assertIn("Encerrado", html_vol_closed)
        # Não deve mostrar a badge "Etapa Atual" de confirmação de participação
        self.assertNotIn("current-phase-badge", html_vol_closed)

        # Exclui pelo admin para limpeza
        with self.client.session_transaction() as sess:
            sess["admin_id"] = 1
            sess["admin_user"] = "admin"

        resp_del = self.client.post(f"/admin/voluntarios/{voluntario.id}/excluir", data={"csrf_token": token_admin}, follow_redirects=True)
        self.assertEqual(resp_del.status_code, 200)

    def test_08_xss_protection_and_escaping(self):
        """8. Proteção contra XSS: tags HTML no nome e observação são escapadas no Jinja."""
        db_session.query(Voluntario).filter_by(telefone="5511988887777").delete()
        db_session.query(Voluntario).filter_by(email="seguro@exemplo.com").delete()
        db_session.commit()

        get_resp = self.client.get("/")
        token = self.get_csrf_token(get_resp.data.decode("utf-8"))

        malicious_name = "<script>alert('xss')</script> Voluntário Seguro"
        post_data = {
            "csrf_token": token,
            "nome": malicious_name,
            "telefone": "(11) 98888-7777",
            "email": "seguro@exemplo.com",
            "senha": "senhaSegura123!",
            "confirmar_senha": "senhaSegura123!",
            "cidade": "<b>Brasília</b>",
            "area_interesse": "Comunicação e divulgação",
            "disponibilidade": "Manhã",
            "mensagem": "<img src=x onerror=alert(1)>",
            "autorizacao_contato": "1",
        }

        resp = self.client.post("/voluntarios", data=post_data, follow_redirects=False)
        self.assertEqual(resp.status_code, 302)

        with self.client.session_transaction() as sess:
            sess["admin_id"] = 1
            sess["admin_user"] = "admin"

        resp_admin = self.client.get("/admin")
        html = resp_admin.data.decode("utf-8")
        self.assertNotIn("<script>alert('xss')</script>", html)
        self.assertIn("&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;", html)

        # Limpa registro
        v_mal = db_session.query(Voluntario).filter_by(telefone="5511988887777").first()
        if v_mal:
            db_session.delete(v_mal)
            db_session.commit()

    def test_09_pagina_404_para_voluntario_inexistente(self):
        """9. Acesso a voluntário inexistente retorna página 404 personalizada sem erro 500."""
        with self.client.session_transaction() as sess:
            sess["admin_id"] = 1
            sess["admin_user"] = "admin"

        resp = self.client.get("/admin/voluntarios/999999")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Página Não Encontrada", resp.data.decode("utf-8"))

    def test_10_persistencia_real_apos_fechar_e_reabrir_conexao(self):
        """10. Comprova que os dados persistem no PostgreSQL após fechar e reabrir conexão."""
        count_antes = db_session.query(Voluntario).count()
        self.assertGreater(count_antes, 0)

        db_session.remove()

        count_depois = db_session.query(Voluntario).count()
        self.assertEqual(count_antes, count_depois)


if __name__ == "__main__":
    unittest.main()
