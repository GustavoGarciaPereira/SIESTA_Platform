# Relatório de Auditoria de Frontend — SIESTA Platform

**Data:** 11/09/2026
**Commit base:** `697fc02`
**Ferramenta:** Playwright MCP (Chrome), viewports 1440×900 (desktop) e 390×844 (mobile)
**Sessões testadas:** anônimo e autenticado (`qa_front`, staff) no servidor local `http://127.0.0.1:8000`
**Escopo:** interface renderizada (templates/CSS/JS). Não foram alterados arquivos de código nesta auditoria.

---

## 1. Resumo executivo

A plataforma está funcional, o tema visual é coerente e o visualizador 3D é o destaque positivo. Os principais problemas de polimento são de **consistência de idioma** (páginas misturam inglês e português na mesma tela), **UX do conversor** (formulário muito longo e visualmente ruidoso) e **detalhes globais** (favicon 404, links mortos, navbar sobrecarregada, barra de ações quebrada no mobile).

| Severidade | Qtd | IDs |
|------------|-----|-----|
| Alto | 4 | FR-01 a FR-04 |
| Médio | 8 | FR-05 a FR-12 |
| Baixo | 5 | FR-13 a FR-17 |

**Recomendação:** executar em 3 lotes (seção 6), começando pelos quick wins do Lote 1.

---

## 2. Metodologia e limitações

- Navegação real com Playwright MCP, captura de screenshot full-page e verificação de console.
- Teste de upload real de `.out` (`media/out_files/teste_3gHqpXJ.out`) e renderização do campo elétrico.
- Não foram cobertos: Firefox/Safari, leitores de tela, teste de formulário com erros, fluxo completo de password reset, Lighthouse/performance e páginas 404/500.

---

## 3. Páginas inspecionadas

| Página | URL | Estado | Idioma observado |
|--------|-----|--------|------------------|
| Home | `/` | anônimo e logado | misto (EN/PT) |
| Login | `/login/` | anônimo | misto |
| Cadastro | `/signup/` | anônimo | misto |
| Sobre | `/about/` | anônimo | PT (hardcoded) |
| Contato | `/contact/` | anônimo | misto |
| Conversor | `/converter/convert/` | logado | misto |
| Histórico (vazio) | `/converter/history/` | logado | misto |
| Minhas Configurações (vazio) | `/converter/config/my/` | logado | misto |
| Upload `.out` | `/visualizer/upload/` | logado | EN |
| Visualizador 3D | `/visualizer/19/` | logado | EN |
| Dashboard | `/dashboard/` | staff | PT (hardcoded) |
| Perfil | `/profile/` | logado | misto |

---

## 4. O que já está bom

- Tema consistente (Inter + JetBrains Mono, paleta azul/teal, cards com sombra suave).
- Home com fluxo em 3 passos e features claros; Sobre com layout bem resolvido.
- Login/cadastro com cards de recurso e validação visual de senha.
- Visualizador 3D funcional e bonito: átomos coloridos por carga, grid, eixos, vetores e linhas de campo; barra de status informativa.
- Navbar mobile com collapse funcional; mensagens de erro/sucesso consistentes.

---

## 5. Achados

### 5.1 Alto

#### FR-01 — Idioma misturado na mesma tela
**Evidência:** em navegador `en-US`, a home mostra "Welcome to SIESTA Platform / Our Workflow / Key Features" com parágrafos e botões em português ("Criar Conversão", "Transforme suas estruturas..."). Login tem cabeçalho EN ("Welcome back") e labels PT ("Nome de usuário", "Senha", "Entrar"). Contato tem heading PT e labels EN no formulário. Perfil mistura "Meu Perfil" com "Institution/Research Area/Profile Picture".
**Causa:** strings hardcoded em PT + ~29 traduções `en` vazias no catálogo.
**Arquivos:** `converter/templates/home.html:31-53`, `converter/templates/contact.html:62-137`, `user/templates/user/profile.html:57-104`, `converter/templates/converter/{login,signup,history,my_configs}.html`, `converter/templates/about.html`, `dashboard/templates/dashboard/dashboard.html`, `locale/en/LC_MESSAGES/django.po`.
**Recomendação:** envolver todo texto fixo em `{% trans %}`/`gettext` e completar as traduções `en`; ou assumir pt-BR como único idioma padrão e desabilitar o seletor até o catálogo EN estar completo. **Esforço: M.**

#### FR-02 — Barra de ações do conversor quebra no mobile
**Evidência:** em 390px, "Salvar Configuração" fica com texto cortado e "Pré-visualizar FDF" quebra em 3 linhas; o grupo de botões invade a margem.
**Arquivo:** `converter/templates/converter/upload.html:388-416`.
**Recomendação:** empilhar botões full-width no mobile (`d-grid gap-2` + `d-md-flex`) e/ou mover ações para uma barra sticky. **Esforço: P.**

#### FR-03 — Navbar sobrecarregada quando autenticado
**Evidência:** logado, a navbar tem Home, Converter, History, About Us, Contact, idioma, Dashboard, My Configurations, View .out, "Hello, qa_front" e Logout — 11 itens; no mobile o menu ocupa a tela inteira.
**Arquivo:** `converter/templates/base.html:73-100`.
**Recomendação:** manter 4 links principais e agrupar ações do usuário num dropdown ("Olá, X ▾" → Perfil, Histórico, Configurações, Visualizador, Dashboard, Logout). **Esforço: M.**

#### FR-04 — Links mortos no rodapé e no cadastro
**Evidência:** "Termos de Serviço" e "Política de Privacidade" apontam para `href="#"` em todas as páginas e no aceite do cadastro.
**Arquivos:** `converter/templates/base.html:128-129`, `converter/templates/converter/signup.html:191-192`.
**Recomendação:** criar duas páginas estáticas simples (ou remover os links até existirem). **Esforço: P.**

### 5.2 Médio

#### FR-05 — Favicon ausente (404 em toda página)
**Evidência:** console registra `GET /favicon.ico 404` no load.
**Arquivo:** `converter/templates/base.html:5-19` (sem `<link rel="icon">`).
**Recomendação:** adicionar `static/img/favicon.svg` + tag no `base.html`. **Esforço: P.**

#### FR-06 — Conversor longo e com "arco-íris" de seções
**Evidência:** 7 blocos com cabeçalhos azul-marinho, verde, teal, laranja, cinza e preto, cada um com campos de larguras diferentes. Em desktop a página tem ~2100px; no mobile passa de 4 telas. O botão de download fica no fim, sem barra fixa.
**Arquivo:** `converter/templates/converter/upload.html`.
**Recomendação:** cabeçalho único neutro para todas as seções; agrupar em accordion/tabs (Arquivo e Base, Malha, MD, SCF/DM, XC, Saída, Célula); barra de ação sticky com Preview/Download; botão desabilitado até haver `.xyz`; erros inline. **Esforço: G.**

#### FR-07 — Visualizador 3D sem legenda e com controles densos
**Evidência:** não há indicação de que vermelho = carga positiva, azul = negativa, nem das cores das flechas. `k (intensity)` e "3D Grid" são jargão sem tooltip; não há reset de câmera, exportar imagem nem feedback de carregamento. Default 8³ = 512 vetores polui a cena.
**Arquivo:** `visualizer/templates/visualizer/visualize.html`.
**Recomendação:** legenda fixa, tooltips, botão reset/export, spinner durante o cálculo, default com menos vetores (ou toggle), hover com símbolo/coordenadas do átomo. **Esforço: M/G.**

#### FR-08 — Empty states pobres
**Evidência:** histórico e configurações vazios exibem apenas uma faixa azul com texto; a página fica quase toda branca.
**Arquivos:** `converter/templates/converter/history.html:190-197`, `converter/templates/converter/my_configs.html:141-145`.
**Recomendação:** card central com ícone, texto e botão de CTA ("Nova Conversão"). **Esforço: P.**

#### FR-09 — Logs de debug no console
**Evidência:** `static/js/upload.js` imprime 7 mensagens com emoji (`🔍 Inicializando...`, `✅ ...`) a cada interação.
**Arquivo:** `static/js/upload.js:106-190`.
**Recomendação:** remover ou condicionar a um flag de debug. **Esforço: P.**

#### FR-10 — Inputs de arquivo nativos sem estilo
**Evidência:** "Choose File / No file chosen" com aparência padrão do navegador no conversor, visualizador e perfil.
**Arquivos:** `converter/templates/converter/upload.html:57-60`, `visualizer/templates/visualizer/upload.html:29-34`, `user/templates/user/profile.html:88`.
**Recomendação:** customizar com `form-control`/`.form-control[type=file]` e texto de ajuda. **Esforço: P.**

#### FR-11 — Hierarquia de botões no Dashboard
**Evidência:** todas as linhas têm botão verde sólido "Acessar", competindo com o conteúdo; o destaque deveria ser o dado, não a ação repetida.
**Arquivo:** `dashboard/templates/dashboard/dashboard.html:96-101`.
**Recomendação:** usar `btn-outline-primary`/link discreto e reservar cor forte para ações primárias. **Esforço: P.**

#### FR-12 — Títulos de página inconsistentes
**Evidência:** "XYZ to FDF Converter — SIESTA Platform" (EN) vs "Histórico de Conversões - SIESTA Platform" (PT) vs "Upload .out — SIESTA Platform".
**Arquivos:** blocos `{% block title %}` nos templates.
**Recomendação:** padronizar (`{% trans %}` + separador) e revisar os títulos. **Esforço: P.**

### 5.3 Baixo

#### FR-13 — Sem meta description/Open Graph
**Evidência:** `base.html` não define `description`, `og:title`, `og:image`; compartilhamentos em redes/WhatsApp ficam sem preview.
**Recomendação:** adicionar metatags e imagem padrão. **Esforço: P.**

#### FR-14 — Dependências de CDN sem SRI/fallback
**Evidência:** Bootstrap, Bootstrap Icons, 3Dmol, Three.js e Google Fonts vêm de CDNs externas sem `integrity` nem fallback local.
**Recomendação:** avaliar vendorização das libs críticas (Three/3Dmol) e usar SRI nas demais. **Esforço: M.**

#### FR-15 — Imagens da equipe hospedadas fora do projeto
**Evidência:** fotos vêm de `lasimon.vercel.app` e `avatars.githubusercontent.com`; se caírem, a página Sobre fica sem imagens.
**Arquivo:** `user/views.py` (`team_members`).
**Recomendação:** baixar para `static/img/team/` com fallback local. **Esforço: P.**

#### FR-16 — Acessibilidade
**Evidência:** teal `#17a2b8` sobre branco tem contraste ~2.9:1 (abaixo de 4.5:1 para texto pequeno); `aria-label`s misturam PT/EN; foco visível depende do navegador.
**Arquivos:** `static/css/base.css:5`, templates de alertas.
**Recomendação:** escurecer o teal para texto, revisar `aria-label`s e padronizar `:focus-visible`. **Esforço: M.**

#### FR-17 — Excesso de variantes de botão
**Evidência:** `primary`, `success`, `info`, `accent`, `outline-primary`, `outline-secondary`, `outline-success` coexistindo em telas próximas.
**Recomendação:** consolidar em primário, secundário e outline, com cores semânticas apenas para estados. **Esforço: M.**

---

## 6. Proposta de execução em lotes

### Lote 1 — Quick wins (baixo risco, alto impacto)
Itens: **FR-01 (parcial: strings hardcoded + traduções), FR-02, FR-04, FR-05, FR-09, FR-12, FR-15.**
Entregável: telas consistentes em idioma, mobile utilizável, sem 404 de favicon, sem links mortos, console limpo.
Critério de aceite: suíte 111 testes verde; `python manage.py collectstatic`; navegação manual nas 12 páginas sem erros de console.

### Lote 2 — Estruturais (UX)
Itens: **FR-03, FR-06, FR-07, FR-08, FR-10, FR-11.**
Entregável: navbar enxuta com dropdown de usuário; conversor reorganizado (accordion + barra sticky); visualizador com legenda/controles/loading; empty states com CTA; inputs de arquivo estilizados.
Critério de aceite: testes de converter/visualizer verdes (ajustar templates/JS), navegação mobile validada em 390px.

### Lote 3 — Polimento (médio prazo)
Itens: **FR-13, FR-14, FR-16, FR-17.**
Entregável: metatags/OG, decisão sobre vendorização de CDN, contraste e foco acessíveis, padronização de botões.

---

## 7. Observações

- O usuário de teste `qa_front` (staff) foi criado no `db.sqlite3` local apenas para esta auditoria; pode ser removido com `python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='qa_front').delete()"`.
- Os screenshots usados na análise não foram versionados (removidos da raiz ao final).

---

## 8. Status de implementação (11/09/2026)

| ID | Status | Detalhe |
|----|--------|---------|
| FR-01 | Concluído | `DefaultLanguageMiddleware` fixa pt-BR até escolha explícita; strings hardcoded envolvidas em `trans`; catálogo `en` com **0 msgstr vazios** |
| FR-02 | Concluído | Barra de ações do conversor virou `sticky-actions` com empilhamento full-width no mobile |
| FR-03 | Concluído | Navbar com dropdown "Olá, usuário" (Perfil, Configurações, Visualizador, Dashboard, Logout) |
| FR-04 | Concluído | Links mortos de Termos/Privacidade removidos (rodapé e cadastro) |
| FR-05 | Concluído | `static/img/favicon.svg` + `<link rel="icon">`; sem 404 |
| FR-06 | Concluído | Parâmetros agrupados em accordion (6 seções) com Expandir/Recolher tudo, seções com erro abertas automaticamente e barra de ação sticky |
| FR-07 | Concluído | Legenda de cores, reset de câmera, exportar PNG, estado "Calculando...", grade padrão 6³ |
| FR-08 | Concluído | Empty states com ícone, texto e CTA em histórico e configurações |
| FR-09 | Concluído | `console.log` de debug removidos de `static/js/upload.js` |
| FR-10 | Concluído | Inputs de arquivo com `form-control` e `::file-selector-button` estilizado |
| FR-11 | Concluído | Botões do dashboard em outline discreto |
| FR-12 | Concluído | Títulos padronizados em `<página> — SIESTA Platform` |
| FR-13 | Concluído | `meta description` e Open Graph adicionados ao `base.html` |
| FR-14 | Concluído | Bootstrap (CSS/JS), Bootstrap Icons, 3Dmol e Three.js/OrbitControls vendorizados em `static/vendor/`; restam apenas as Google Fonts (com fallback local) |
| FR-15 | Concluído | Fotos da equipe baixadas para `static/img/team/` e servidas localmente |
| FR-16 | Parcial | `--color-accent-dark` para contraste AA, `:focus-visible`, skip-link, `aria-label` em botões de ícone, `scope="col"` nas tabelas e `aria-current` na navbar; auditoria completa de a11y pendente |
| FR-17 | Parcial | Ações principais consolidadas (dashboard, histórico, configs, hero); revisão global de variantes ainda pendente |
| Extra | Concluído | Tooltip no hover dos átomos no visualizador (símbolo, coordenadas e carga) |

Validação: **131 testes Django** e **7 testes Rust** verdes, `manage.py check` limpo, `collectstatic` executado, `msgfmt --check-format` OK nos dois idiomas.
