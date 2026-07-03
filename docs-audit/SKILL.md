---
name: docs-audit
description: "Auditoria completa de documentação contra o código: encontra doc velha, corrige, verifica e abre PR (bom sob /loop, periódico)"
disable-model-invocation: true
---

Uma **auditoria** varre o codebase INTEIRO e garante que cada documento reflete a implementação
atual — é mais pesada que o `/wrap-up` (que cobre só a sessão), feita de tempos em tempos, e
boa de rodar sob `/loop`. Cada passo termina num critério **exaustivo**: "toda afirmação
verificada", não "uma lista de mudanças".

(Versão global genérica — vale em qualquer projeto. Se um projeto tiver um `.claude/skills/docs-audit`
próprio, aquele sobrescreve este.)

## 1. Inventariar as afirmações da doc
Enumere todos os documentos (`README`, o arquivo de instruções do projeto — `CLAUDE.md`/
`AGENTS.md`/`GEMINI.md` —, glossário `CONTEXT.md`, `docs/`, ADRs) e extraia as **afirmações
verificáveis** que fazem: comandos, caminhos de arquivo, contagens (ex.: nº de testes), nomes
de scripts/funções, fluxos descritos, decisões.
**Concluído quando:** existe um inventário de afirmações, cada uma com o documento de origem.

## 2. Verificar cada afirmação contra o código
Para cada afirmação, confirme no codebase (rodar o comando, `grep` o caminho/função, contar os
testes de fato). Marque **exata** ou **velha**, com a evidência.
**Concluído quando:** TODA afirmação do inventário está marcada exata/velha — nenhuma sem checar.

## 3. Corrigir a doc velha
Atualize cada afirmação velha para casar com a implementação. Onde a doc descreve algo que não
existe mais, corrija ou remova. Não invente comportamento — documente o que o código faz.
Preserve o histórico legítimo (ex.: seções de proposta/decisão num design doc ou ADR não são
reescritas para fingir que o plano original era o resultado final).
**Concluído quando:** não resta nenhuma afirmação marcada como velha.

## 4. Verificar
Rode a suíte de testes do projeto (**detecte o runner**: `pytest`, `npm test`, `cargo test`,
`go test ./...`, `make test`, etc.) e re-cheque as afirmações que você corrigiu (ex.: o comando
documentado roda; a contagem bate).
**Concluído quando:** testes verdes e cada correção re-confirmada contra o código.

## 5. Abrir o PR
Crie uma branch, commite as correções de doc (seguindo as convenções de commit do projeto — ex.
linha `Co-Authored-By` exigida) e abra o PR com o resumo da auditoria (o que estava velho, o que
foi corrigido). Não toque em código de produção — esta auditoria é só de documentação.
**Concluído quando:** o PR está aberto e referenciado na resposta ao usuário.

## 6. Recomendar o próximo passo: /clear ou /compact
Depois da auditoria o estado está externalizado por definição (docs = código, testes verdes),
então a recomendação default é **`/clear`** — com uma ressalva: o **PR da auditoria fica
aberto** e atravessa a fronteira da sessão. Inclua o merge na frase de abertura sugerida para
a próxima conversa (ex.: "faz merge do PR #N e vamos para a próxima pendência") — ou ofereça
mergear ainda nesta sessão, se o usuário quiser fechar tudo antes do clear. Recomende
**`/compact`** apenas se a auditoria rodou no MEIO de outra tarefa ainda incompleta (fio vivo
que o clear perderia). Siga os mesmos critérios do passo 6 da skill wrap-up
(`/root/.claude/skills/wrap-up/SKILL.md`).
**Concluído quando:** o usuário recebeu UMA recomendação clara com justificativa e a frase de
abertura da próxima conversa.

## Sob /loop
Para uma passada periódica autônoma:
`/loop Whenever a documentation pass is needed, run the docs-audit skill: review the whole
codebase, ensure every doc reflects the current implementation, fix stale docs, verify, and open
a PR.`
