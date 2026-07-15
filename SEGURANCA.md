# Segurança — Correcções Aplicadas

Este documento regista as correcções de segurança aplicadas ao MVP, complementando a secção
*"Limitações de segurança conhecidas"* da `DOCUMENTACAO_TECNICA.md` (secção 12).

---

## 1. O que foi implementado

### 1.1 Protecção CSRF

**Limitação original:** nenhum formulário validava a origem do pedido — um atacante podia
criar uma página externa que submetia pedidos POST para a aplicação usando a sessão
autenticada da vítima (ex: criar utilizadores, alterar não conformidades).

**Solução:** `Flask-WTF` (`CSRFProtect`), inicializado em [app/__init__.py](app/__init__.py).

- Cada resposta inclui um token de sessão (`csrf_token()`), embutido como campo oculto em
  todos os 12 formulários POST da aplicação: login, novo utilizador, editar limiar/regra,
  activar/desactivar utilizador e regra, os 4 formulários de importação CSV, nova auditoria
  e actualização de não conformidade.
- Pedidos POST sem token válido são recusados (`CSRFError`) e redireccionados com uma
  mensagem — em vez de um erro genérico 400.

**Ficheiros alterados:** `app/__init__.py`, e os 10 templates com formulários POST.

### 1.2 Rate limiting no login

**Limitação original:** o endpoint `/auth/login` aceitava tentativas ilimitadas de password,
permitindo ataques de força bruta.

**Solução:** `Flask-Limiter`, aplicado ao endpoint de login.

- `/auth/login` (POST): máximo de **10 tentativas por minuto** por IP.
- Limite geral da aplicação como rede de segurança adicional: 200/dia, 50/hora por IP.
- Ao exceder o limite, o utilizador recebe HTTP 429 com mensagem "Demasiadas tentativas.
  Aguarde um momento antes de tentar novamente."

**Ficheiros alterados:** `app/__init__.py`, `app/routes/auth.py`.

### 1.3 Headers de segurança HTTP

**Limitação original:** ausência de `X-Frame-Options`, `Content-Security-Policy`, etc. —
exposição a clickjacking e XSS.

**Solução:** hook `after_request` em `app/__init__.py` que define em todas as respostas:

| Header | Valor | Protege contra |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | MIME-sniffing |
| `X-Frame-Options` | `DENY` | Clickjacking (embutir a app num iframe) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Fuga de URLs internos |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` | Acesso indevido a APIs do browser |
| `Content-Security-Policy` | restrita a `'self'` + `cdn.jsdelivr.net` | XSS via scripts/estilos injectados |
| `Strict-Transport-Security` | condicional (só se HTTPS) | Downgrade attacks |

O CSP usa **nonce por pedido** para os `<script>` inline (em vez de `'unsafe-inline'`),
gerado em `before_request` e injectado nos templates via `csp_nonce`.

> Nota: a documentação técnica sugeria `Flask-Talisman`. Optou-se por implementação manual
> porque o Talisman força redirecionamento HTTPS por omissão, o que quebraria o ambiente de
> desenvolvimento local (HTTP). O resultado é equivalente.

**Ficheiros alterados:** `app/__init__.py`, `app/templates/base.html`,
`app/templates/index.html`, `app/templates/aquisicao/index.html` (nonces).

### 1.4 `SECRET_KEY` sem valor por omissão *(fora da lista original, identificado durante a revisão)*

**Problema:** `app/config.py` tinha um fallback fixo (`'chave-secreta-temporaria'`) caso a
variável de ambiente não existisse. Numa implantação sem `.env` correctamente configurado, a
aplicação arrancava "com sucesso" mas com uma chave secreta pública e previsível — o que
compromete sessões, cookies assinados e o próprio CSRF (que depende da `SECRET_KEY`).

**Solução:** `app/config.py` agora falha o arranque (`RuntimeError`) se `SECRET_KEY` não
estiver definida, em vez de arrancar silenciosamente insegura.

### 1.5 Modo debug activo por omissão *(fora da lista original, identificado durante a revisão)*

**Problema:** `run.py` chamava `app.run(debug=True)` de forma fixa. O modo debug do Flask
expõe a consola interactiva do Werkzeug em qualquer erro 500 — se acessível externamente,
permite execução remota de código.

**Solução:** `run.py` agora lê `FLASK_DEBUG` do ambiente (`.env`), com omissão seguro em
`False`. Foi adicionado `FLASK_DEBUG=1` ao `.env` local para manter o auto-reload em
desenvolvimento; este ficheiro não é versionado, por isso uma implantação nova arranca em
modo seguro por omissão.

---

## 2. Como foi validado

Testado ao vivo contra o servidor de desenvolvimento (`python run.py`):

- **CSRF:** POST sem `csrf_token` → bloqueado e redireccionado; POST com token válido →
  processado normalmente.
- **Rate limiting:** 10 primeiros POSTs a `/auth/login` → `200`; 11º e 12º → `429`.
- **Headers:** confirmados por inspecção directa da resposta HTTP (`curl -D -`).
- **`SECRET_KEY`:** confirmado que a lógica de fail-fast dispara quando a variável não está
  definida.
- **Debug mode:** confirmado que `FLASK_DEBUG=1` no `.env` activa o modo debug e que a
  omissão (sem a variável) é `False`.

---

## 3. O que fica por fazer (não implementado nesta ronda)

Estes pontos não fazem parte do pedido original, mas foram identificados como oportunidades
de reforço adicional. Ficam registados para decisão futura:

| Item | Risco actual | Esforço estimado |
|---|---|---|
| Flags de cookie de sessão (`SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE`) | Cookies de sessão sem `Secure`/`SameSite` explícitos | Baixo — 3 linhas em `config.py` |
| Política de password (comprimento mínimo, complexidade) no formulário de novo utilizador | Passwords fracas aceites sem restrição | Baixo — validação no `novo_utilizador` |
| Validação do conteúdo dos ficheiros CSV importados (tamanho máximo, sanitização) | Ficheiros grandes ou malformados podem causar erro não tratado | Médio |
| Log de auditoria de acções dos utilizadores | Já listado na `DOCUMENTACAO_TECNICA.md` como trabalho futuro (não é uma falha de segurança per se, mas afecta a auditabilidade) | Médio — nova tabela + hooks |
| Autenticação multi-factor (2FA) para administradores | Já listado na `DOCUMENTACAO_TECNICA.md` como funcionalidade futura | Alto |

Nenhum destes é urgente para o âmbito de um MVP académico — ficam aqui apenas para que a
decisão de os deixar de fora seja consciente e documentada, tal como a abordagem já adoptada
na secção 12 da documentação técnica.
