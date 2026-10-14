# Blueprint — Portal de Voluntariado para Projeto de Extensão

## Instrução para a IA que vai implementar

Implemente o projeto completo descrito neste documento. Quero um sistema pequeno, bonito e funcional para um projeto de extensão universitária. A avaliação será focada no funcionamento e na utilidade para a comunidade. Priorize um fluxo completo, persistência real dos dados e facilidade de demonstração. **O backend pode ser enxuto; o frontend deve parecer um produto profissional, com identidade visual, composição cuidadosa e interações completas. Simplicidade de escopo não significa aparência básica.** Entregue os arquivos, execute o sistema, verifique os critérios de aceite e explique como iniciar e usar. Não pare em um plano ou em um protótipo visual.

Use as decisões deste documento como padrão. Resolva detalhes menores sem me interromper. Não invente uma organização real, parceria, endereço, estatística ou depoimento. Não acrescente funcionalidades além do escopo essencial. Se algum requisito não puder ser concluído, informe o bloqueio específico sem fingir que está funcionando.

## 1. Objetivo e tamanho do projeto

Criar um site para uma organização social apresentar suas atividades e receber inscrições de pessoas interessadas em atuar como voluntárias. A organização deve conseguir consultar os cadastros e acompanhar quem já foi contatado.

**Problema atendido:** contatos de interessados podem ficar espalhados em mensagens e redes sociais. O portal reúne os cadastros em um lugar, incluindo disponibilidade e área de interesse.

**Fluxo principal:** visitante conhece o projeto → preenche o formulário → recebe confirmação → responsável da organização acessa o painel → consulta o cadastro → entra em contato manualmente → atualiza o status.

É um portal para uma única organização. Não é necessário desenvolver uma plataforma para várias ONGs.

Enquanto não houver uma organização parceira definida, usar o nome **Conecta Voluntários** e exibir discretamente no rodapé: “Projeto demonstrativo de extensão universitária”. Todos os textos institucionais e contatos devem ficar em um arquivo de configuração fácil de editar. A parceria real será definida pelo responsável pelo trabalho.

## 2. Tecnologia e execução

- Backend: Python com Flask.
- Banco de dados: PostgreSQL gerenciado no Supabase (produção e desenvolvimento), acessado via SQLAlchemy 2.x e driver PostgreSQL (`psycopg2-binary`).
- Conexão com banco: configurada via variável de ambiente `DATABASE_URL`. Utiliza preferencialmente a conexão **Session Pooler** do Supabase (porta 5432) com SSL obrigatório (`sslmode=require`).
- Hospedagem de produção: Render (plano gratuito), servido com Gunicorn como servidor WSGI HTTP.
- Interface: templates Jinja, HTML5 semântico, CSS próprio (tokens, flexbox/grid responsivo) e JavaScript nativo progressivo apenas onde necessário.
- Não usar React, Docker ou microsserviços pesados.
- Não usar arquivo de banco de dados local (`.db` ou SQLite) como armazenamento em produção. Assegurar persistência real em banco relacional externo na nuvem para que os dados persistam após reinicializações ou novas publicações do serviço no Render.
- Credenciais e segredos (`DATABASE_URL`, `SECRET_KEY`, credenciais de admin) devem permanecer estritamente no backend / variáveis de ambiente, nunca expostos no frontend ou commitados no repositório.
- Evitar dependência de fontes, imagens e folhas de estilo por CDN externo obrigatório, garantindo funcionamento ágil e independente.
- Usar consultas parametrizadas via ORM SQLAlchemy. Não concatenar entradas do usuário em SQL.
- Separar templates, arquivos estáticos, modelos de dados e rotas de forma limpa e modular.

Rotina de instalação e inicialização local:

```bash
# 1. Criar e ativar o ambiente virtual:
# Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
# python -m venv .venv && source .venv/bin/activate

# 2. Instalar dependências:
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente (.env):
# Copiar .env.example para .env e preencher SECRET_KEY e DATABASE_URL (Supabase Session Pooler)
cp .env.example .env

# 4. Inicializar tabelas e criar administrador inicial:
python app.py --init-db
python app.py --create-admin

# 5. (Opcional) Popular dados de demonstração:
python app.py --seed-demo

# 6. Executar o servidor de desenvolvimento:
python app.py
```

O endereço local padrão será `http://127.0.0.1:5000`. O carregamento do `.env` utiliza `python-dotenv`. Em produção no Render, o comando de inicialização é `gunicorn app:app`.

## 3. Aparência

Criar uma interface acolhedora e limpa, com fundo claro, texto escuro e verde como cor principal. Direção visual: uma plataforma social contemporânea, confiável e bem desenhada. O resultado deve parecer pronto para ser apresentado a uma organização, sem aspecto de exercício de HTML ou template padrão.

Usar verde `#167D65`, verde profundo `#123D32`, fundo off-white `#F7F9F8`, texto `#24352F` e um tom quente discreto para detalhes (`#D97706`). Definir tokens CSS para cores, espaçamento, tipografia, raios, sombras e estados. A largura máxima do conteúdo deve ficar próxima de 1.160px; usar uma escala consistente de espaçamento baseada em 8px, seções com respiro e cartões com bordas suaves. Diferenciar botões primários, secundários e ações de exclusão.

Usar uma família de fonte legível e moderna baseada em pilha de fontes do sistema com suporte completo a caracteres. Trabalhar hierarquia de títulos, subtítulos e textos de apoio; título principal grande e bem distribuído, com tamanho responsivo. Não usar todos os textos em negrito nem colocar cada parágrafo dentro de um cartão.

O primeiro bloco deve ter composição em duas colunas no desktop: texto e ações à esquerda; uma ilustração SVG local relacionada a colaboração e voluntariado à direita. No celular, reorganizar o conteúdo em uma coluna. Usar fundos levemente distintos para separar apresentação, oportunidades e formulário.

O site deve funcionar bem em celular e computador, sem rolagem horizontal. Usar labels visíveis nos formulários, foco de teclado perceptível e mensagens de erro próximas dos campos. Todos os textos devem estar em português do Brasil. Elementos decorativos são feitos com CSS ou SVG limpo.

### Tela pública — `/`

Uma página com as seguintes seções:

1. Cabeçalho com nome do projeto e links “Sobre”, “Como ajudar” e “Quero ser voluntário”.
2. Apresentação principal: título “Seu tempo pode fazer a diferença”, descrição curta e botão que leva ao formulário.
3. Sobre o projeto: explicar que o portal conecta interessados às atividades da organização, com texto facilmente substituível.
4. Como ajudar: cartões com áreas de interesse, descritas como possibilidades que serão confirmadas pela organização.
5. Como funciona: “Preencha o cadastro”, “Receba o contato da equipe” e “Combine sua participação”.
6. Formulário de inscrição em etapas, apresentado em um bloco com acabamento visual próprio.
7. Perguntas frequentes (FAQ) em acordeão interativo.
8. Rodapé com identificação do projeto, contato institucional e link discreto para a área administrativa.

### Interações públicas obrigatórias

- Cabeçalho fixo/sticky com menu adaptado para celular. O botão do menu deve abrir e fechar corretamente, refletir seu estado com `aria-expanded` e funcionar por teclado.
- Navegação até as seções com rolagem suave, respeitando `prefers-reduced-motion` e a altura do cabeçalho.
- Cartões das áreas de interesse com ícones SVG de uma mesma linguagem visual, descrição curta e botão “Quero ajudar nesta área”. Ao clicar, selecionar a área no formulário e levar o visitante até ele.
- Uma seção de perguntas frequentes em acordeão com três respostas: como funciona a inscrição, como a equipe entra em contato e como a disponibilidade é combinada.
- Transições discretas de 150 a 220ms em hover, foco e abertura de componentes.

## 4. Cadastro de voluntários

Campos:

| Campo | Obrigatório | Comportamento |
|---|---|---|
| Nome completo | Sim | Texto, de 3 a 100 caracteres. |
| WhatsApp/telefone | Sim | Aceitar entrada com ou sem máscara; normalizar no backend com DDI 55. |
| E-mail | Não | Validar o formato quando preenchido; limite de 254 caracteres. |
| Cidade ou região | Sim | Texto de até 100 caracteres; exemplo: “Guará, Brasília”. |
| Área de interesse | Sim | Uma opção da lista configurada. |
| Disponibilidade | Sim | Uma opção da lista configurada. |
| Mensagem | Não | Até 500 caracteres para habilidades, dúvidas ou observações. |
| Autorização de contato | Sim | Checkbox inicialmente desmarcado. |

Áreas iniciais:
- Arrecadação e organização de doações
- Apoio em eventos
- Comunicação e divulgação
- Atividades administrativas
- Outra área

Disponibilidades iniciais:
- Manhã
- Tarde
- Noite
- Fins de semana
- A combinar

Texto do checkbox: “Autorizo a organização a usar os dados deste formulário para entrar em contato comigo sobre oportunidades de voluntariado.”

### Formulário em três etapas

1. **Sobre você:** nome, telefone, e-mail e cidade/região.
2. **Como quer ajudar:** área de interesse, disponibilidade e mensagem opcional.
3. **Revisar e enviar:** resumo legível dos dados, botão para voltar e editar, autorização de contato e envio final.

Comportamento obrigatório:
- Validar no frontend para ajudar o usuário e novamente no backend.
- Remover espaços desnecessários das entradas.
- Para telefone brasileiro, aceitar 10 ou 11 dígitos nacionais; aceitar também prefixo `55`, normalizando para representação canônica (`55` + DDD + número). Rejeitar entradas fora desse padrão com mensagem clara.
- Impedir cadastro duplicado com o mesmo telefone por restrição `UNIQUE` no PostgreSQL. Informar: “Já existe um cadastro com este telefone. Para atualizar suas informações, procure a equipe.”
- Salvar no PostgreSQL do Supabase antes de exibir sucesso.
- Em caso de erro, preservar os campos preenchidos.
- Desabilitar o botão enquanto a solicitação estiver em andamento.
- Após sucesso, usar redirecionamento para `/cadastro-concluido` (PRG pattern), evitando reenvio ao atualizar a página.
- Funcionar perfeitamente mesmo se o JavaScript estiver desativado no navegador.

Confirmação: “Cadastro recebido! A equipe poderá entrar em contato para conhecer sua disponibilidade e combinar os próximos passos.”

## 5. Área da organização

### Login — `/admin/login`

- Autenticação com usuário e senha.
- Criar o administrador inicial via CLI (`python app.py --create-admin`) ou automaticamente via variáveis `ADMIN_USER` e `ADMIN_PASSWORD`.
- Guardar hash de senha usando `werkzeug.security.generate_password_hash` (scrypt / pbkdf2); nunca em texto puro.
- Sessão de login com chave secreta `SECRET_KEY`. Cookies HttpOnly, SameSite=Lax e Secure condicional para HTTPS.
- Mensagem de erro padrão: “Usuário ou senha incorretos”.
- Logout deve invalidar a sessão via requisição POST protegida por CSRF.

### Painel — `/admin`

Painel administrativo com três indicadores calculados no PostgreSQL:
1. Total de inscritos.
2. Cadastros novos (`status = 'novo'`).
3. Voluntários ativos (`status = 'ativo'`).

Lista ordenada pelos mais recentes, exibindo nome, área de interesse, disponibilidade, data brasileira, status com badges coloridos e ação “Ver detalhes”.

Busca por nome, telefone ou cidade, combinada com filtro por status. Manter parâmetros na URL (`?q=...&status=...`). Exibir quantidade de resultados encontrados, ação “Limpar filtros” e estados vazios desenhados.

### Detalhes — `/admin/voluntarios/<id>`

Organizado em blocos “Contato”, “Interesse e disponibilidade” e “Acompanhamento”.
- Status: Novo, Contatado, Ativo, Encerrado.
- Observação interna: até 1.000 caracteres.
- Link direto para WhatsApp: `https://wa.me/<telefone_normalizado>`.
- Link `mailto:` para e-mail, quando preenchido.
- Exclusão com modal de confirmação acessível (Escape, gerenciamento de foco) via POST.

## 6. Banco de dados e rotas

### Tabela `administradores`

```sql
CREATE TABLE administradores (
    id SERIAL PRIMARY KEY,
    usuario VARCHAR(100) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### Tabela `voluntarios`

```sql
CREATE TABLE voluntarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    telefone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(254),
    cidade VARCHAR(100) NOT NULL,
    area_interesse VARCHAR(100) NOT NULL,
    disponibilidade VARCHAR(50) NOT NULL,
    mensagem VARCHAR(500),
    autorizacao_contato INTEGER NOT NULL DEFAULT 1,
    autorizado_em TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'novo',
    observacao_interna TEXT,
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE NOT NULL
);
```

Apresentar as datas para o usuário formatadas no fuso `America/Sao_Paulo` (ex: `09/10/2026 às 20:30`).

### Rotas mínimas

| Método | Caminho | Função |
|---|---|---|
| GET | `/` | Página pública e formulário. |
| POST | `/voluntarios` | Validar e salvar inscrição. |
| GET | `/cadastro-concluido` | Confirmação de inscrição. |
| GET, POST | `/admin/login` | Exibir login e autenticar. |
| POST | `/admin/logout` | Encerrar sessão. |
| GET | `/admin` | Indicadores, busca, filtros e lista. |
| GET | `/admin/voluntarios/<id>` | Consultar detalhes. |
| POST | `/admin/voluntarios/<id>/atualizar` | Alterar status e observação interna. |
| POST | `/admin/voluntarios/<id>/excluir` | Excluir após confirmação. |

Proteção CSRF obrigatória em todas as rotas POST. Tratamento de erro 404 e 500 sem expor mensagens técnicas ou credenciais.

## 7. Hospedagem e Configuração (Supabase + Render)

### Supabase (Banco de Dados PostgreSQL)
1. Crie um projeto no Supabase (gratuito).
2. Vá em **Project Settings** → **Database** → **Connection string**.
3. Selecione **Connection Pooler** com **Mode: Session** (Porta 5432).
4. Copie a URI de conexão (ex: `postgresql://postgres.[REF]:[SENHA]@aws-0-[REGIAO].pooler.supabase.com:5432/postgres?sslmode=require`).
5. As credenciais residem apenas no backend via variável `DATABASE_URL`.

### Render (Hospedagem Web Service gratuita)
1. Conecte o repositório GitHub ao Render.
2. Crie um novo **Web Service**.
3. Configurações:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
4. Adicione as variáveis de ambiente em **Environment Variables**:
   - `DATABASE_URL`: URI do Session Pooler do Supabase.
   - `SECRET_KEY`: Chave secreta aleatória de 32+ caracteres.
   - `ADMIN_USER`: Usuário do administrador (ex: `admin`).
   - `ADMIN_PASSWORD`: Senha forte do administrador.
   - `FLASK_ENV`: `production`
5. Graças ao banco PostgreSQL persistido no Supabase, quaisquer reinicializações do contêiner ou novas publicações (redeploy) preservam 100% dos voluntários e dados cadastrados.

## 8. Critérios de aceite

1. A página pública abre no computador e no celular sem rolagem horizontal.
2. Um cadastro válido é salvo de verdade no PostgreSQL do Supabase e aparece no painel.
3. Os dados continuam disponíveis após reiniciar o servidor ou republicar o serviço.
4. Cadastro sem autorização ou com campos inválidos é recusado com mensagens claras.
5. O mesmo telefone com máscaras diferentes é bloqueado por unicidade.
6. Login válido entra; login inválido apresenta erro; logout encerra a sessão.
7. Acesso ao painel e ações administrativas sem sessão é estritamente bloqueado.
8. Busca e filtro combinam e exibem os resultados corretos.
9. Alterações de status e observações refletem no banco de dados.
10. Exclusão exige confirmação e remove o registro no banco.
11. Proteção CSRF ativa e sem vazamento de erros técnicos.
12. O frontend possui acabamento profissional, contraste adequado e responsividade completa.
