# Conecta Voluntários — Portal de Voluntariado para Projeto de Extensão

Sistema web profissional e moderno desenvolvido em **Python (Flask)** com persistência em **PostgreSQL no Supabase** e hospedagem no **Render (com Gunicorn)**.

Projetado para projetos de extensão universitária e organizações sociais centralizarem o recebimento de inscrições de voluntários, acompanharem contatos e organizarem disponibilidades em um único painel protegido, além de oferecer uma **Área do Voluntário** acolhedora e transparente.

---

## 🌟 Principais Recursos

### 1. Página Pública de Alto Padrão Visual (`/`)
- **Hero Responsivo:** Proposta de valor clara com ilustração vetorial SVG original sobre colaboração.
- **Cartões Interativos de Oportunidades:** Botões *"Quero ajudar nesta área"* preenchem automaticamente o formulário e rolam suavemente até ele.
- **Formulário em 3 Etapas Progressivas:**
  - *Etapa 1 — Sobre você* (Nome, WhatsApp com máscara inteligente, E-mail, Cidade).
  - *Etapa 2 — Como quer ajudar* (Área de interesse, Disponibilidade, Habilidades/Mensagem).
  - *Etapa 3 — Revisar e enviar* (Resumo dinâmico dos dados, edição rápida, autorização de contato obrigatória).
  - **Validação com `textContent.trim()`:** Garante que a abertura do site sempre inicie na Etapa 1, sem falso positivo de erro.
  - **Fallback Completo sem JavaScript:** Ativado via classe `.no-js` no HTML, permitindo navegação e envio normal se o JS estiver desligado.
- **FAQ em Acordeão Acessível:** Respostas diretas sobre o processo e horários.

### 2. Área Exclusiva do Voluntário (`/voluntario`)
- **Autenticação Real por E-mail e Senha:** Acesso protegido via Supabase Auth com fallback seguro em hash Werkzeug. Impede que terceiros acessem cadastros de outros voluntários apenas conhecendo o número de telefone.
- **Linha do Tempo Visual em 4 Fases:**
  1. *Inscrição Recebida*
  2. *Em Análise*
  3. *Contato Realizado*
  4. *Participação Confirmada*
  - Exibe visualmente qual etapa foi concluída, qual é a fase atual e um card explicativo de **"O que esperar nesta etapa"**.
- **Apresentação Própria para Status Encerrado:** Inscrições com status *"Encerrado"* possuem card e apresentação dedicada respeitosa, sem marcar indevidamente a fase de *"Participação Confirmada"*, esclarecendo o encerramento do ciclo e mantendo o recado da organização acessível.
- **Mensagem da Organização (Recado da Coordenação):** Um comunicado da equipe direto para o voluntário (ex: *"Sua reunião de apresentação será na terça-feira às 19h no auditório."*).
- **Canal Direto via WhatsApp:** Botão com atalho oficial da API do WhatsApp para conversar com a ONG em um clique, sem custos de API ou chat complexo.
- **Meu Perfil:** Permite ao voluntário atualizar cidade, WhatsApp, e-mail, área de interesse e disponibilidade de horários.

### 3. Painel Administrativo da Organização (`/admin`)
- Autenticação com sessão protegida, cookie `HttpOnly`, `SameSite=Lax` e hash de senha seguro via Werkzeug.
- Indicadores em tempo real: *Total de inscritos*, *Cadastros em triagem* e *Participações confirmadas*.
- Busca por nome, cidade ou telefone com filtro combinado por status.
- **Separação Rigorosa de Recados e Notas:**
  - **Recado para o Voluntário:** Mensagem pública enviada para a Área do Voluntário da pessoa.
  - **Observação Interna (PRIVADA):** Anotações restritas aos administradores, NUNCA expostas ao voluntário.
- Exclusão com confirmação em modal acessível.

### 4. Banco de Dados PostgreSQL no Supabase (Nuvem)
- Conexão via **Session Pooler** (porta `5432`) com **SSL obrigatório** (`sslmode=require`).
- **Autenticação Supabase Auth:** Suporte direto à API REST do GoTrue Auth (`/auth/v1/signup` e `/auth/v1/token`), vinculando o identificador `supabase_user_id` à inscrição.
- **Compatível com o Plano Gratuito do Render:** O `preDeployCommand` do Render é exclusivo de planos pagos. No plano gratuito, a preparação das tabelas e do administrador ocorre durante o build (`pip install -r requirements.txt && python app.py --setup`), garantindo inicialização limpa antes de subir os 2 workers do Gunicorn.

---

## 🛠️ Instalação e Execução Local

```powershell
# 1. Ativar o ambiente virtual:
.\.venv\Scripts\Activate.ps1

# 2. Inicializar tabelas e administrador (executado uma única vez):
python app.py --setup

# 3. (Opcional) Popular os dados de demonstração:
python app.py --seed-demo

# 4. Executar os testes automatizados:
python test_app.py

# 5. Iniciar o servidor local:
python app.py
```

- **Página Pública:** `http://127.0.0.1:5000`
- **Área do Voluntário:** `http://127.0.0.1:5000/voluntario/login`
- **Painel Administrativo:** `http://127.0.0.1:5000/admin/login` (Usuário: `admin` / Senha: `admin123_extensao`)

---

## ☁️ Implantação no Render Gratuito com Gunicorn

1. Conecte seu repositório GitHub ao [render.com](https://render.com).
2. Crie um **Web Service** com as seguintes configurações para o **Plano Gratuito**:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt && python app.py --setup`
   - **Start Command:** `gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT`
   - *(Deixe o campo Pre-Deploy Command em branco, pois é restrito a instâncias pagas)*.
3. Em **Environment Variables**, adicione:
   - `DATABASE_URL`: URI do Session Pooler do Supabase com SSL.
   - `SECRET_KEY`: Chave aleatória de 32+ caracteres.
   - `FLASK_ENV`: `production`
   - `ADMIN_USER`: `admin`
   - `ADMIN_PASSWORD`: Senha forte desejada.
   - `SUPABASE_URL`: URL do projeto Supabase (`https://oqwnohnvurmfnensnwlo.supabase.co`).
   - `SUPABASE_ANON_KEY`: *(Opcional)* Chave anônima `anon public` encontrada em *Project Settings -> API* no Supabase. Se omitida, o sistema opera de forma transparente com hash seguro local.
4. Clique em **Deploy**. Como o banco é PostgreSQL gerenciado no Supabase, todos os cadastros, senhas, recados e históricos continuam permanentemente disponíveis após qualquer reinicialização ou novo deploy no Render.
