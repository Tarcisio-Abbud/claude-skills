# claude-skills

Skills globais de autoria própria para o Claude Code, instaladas em `/root/.claude/skills/`
(o próprio diretório é o clone deste repo; um `.gitignore` allowlist deixa as skills de
terceiros fora do versionamento).

| Skill | O que faz |
|---|---|
| `/wrap-up` | Fechamento de sessão: memória + docs + testes + resumo + recomendação (/clear, /compact, /docs-audit) |
| `/kickoff` | Abertura de sessão (espelho do /wrap-up): pauta de pendências verificada contra a realidade, triada e despachada via menu |
| `/despachar` | Casa uma tarefa com o mecanismo de execução (/goal, /loop, Monitor, workflow, /schedule, subagente) e entrega a linha pronta — model-invoked, dispara sozinha em conversa |
| `/docs-audit` | Auditoria de documentação contra o código: acha doc velha, corrige, verifica, abre PR |

O par `/kickoff` ↔ `/wrap-up` compartilha o contrato da fila canônica `next-steps.md`
(definido em `kickoff/SKILL.md`): um arquivo por projeto na auto-memória com os próximos
passos — o wrap-up grava, o kickoff verifica e despacha. A paleta de despacho (mecanismo
certo por tipo de tarefa, receita do `/goal`, contrato do `.claude/loop.md` que transforma
`/loop` puro no despachador da fila) é fonte única em `despachar/SKILL.md` — o kickoff a
consome no passo 5.

Projetos podem ter variantes locais tunadas em `.claude/skills/` (versionadas no repo do
próprio projeto); a local sobrescreve a global de mesmo nome.

Nova skill própria: criar o diretório aqui e **adicionar a exceção no `.gitignore`**.
