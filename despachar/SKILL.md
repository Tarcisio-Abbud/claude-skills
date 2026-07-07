---
name: despachar
description: "Despachar uma tarefa para o mecanismo certo — /goal, /loop, Monitor, dynamic workflow, /schedule ou subagente — entregando a linha pronta para colar. Use quando o usuário quer delegar, agendar ou automatizar algo e o mecanismo está em dúvida, ou quando outra skill precisa da paleta de despacho."
---

**Despachar** é casar a tarefa com o mecanismo que a executa sem o usuário — e entregar a
linha pronta para colar, nunca só o nome do mecanismo. Diagnostique a tarefa contra a
paleta, escolha UMA linha (na dúvida entre duas, a de menor custo) e escreva o
comando/prompt completo.

## A paleta

| Situação da tarefa | Despacho | Quem dispara |
|---|---|---|
| Precisa de conversa/contexto desta sessão | inline, agora (plan mode se for grande) | o agente |
| Estado final verificável (testes verdes, fila zerada, tudo compila) | `/goal` — linha pronta pela receita abaixo | o usuário |
| Fila de fatias autônomas SEM condição única de término | `/loop` puro sobre o `loop.md` do projeto (contrato abaixo), uma fatia por iteração | o agente |
| Espera de estado externo (CI, terceiro) | Monitor — script em background que streama o estado (sem polling); `/loop` com intervalo só se não houver comando observável | o agente |
| Mesma operação sobre MUITOS itens (varredura, migração em massa) | dynamic workflow (`ultracode` / "use a workflow") — pilotar numa fatia pequena antes da varredura completa | o usuário |
| Recorrente (rotina, não item avulso) | `/schedule` (nuvem) ou cron local — rascunhar a rotina COMPLETA: roda sem humano e sem permission prompts, então o prompt é autocontido, com o critério de done embutido e modelo recomendado (rotina mecânica → modelo menor) | o agente |
| Independente do contexto e paralelizável | subagente em background (worktree isolado) | o agente |

Os despachos "o usuário" são comandos nativos que o agente não invoca: entregue a linha
pronta para colar, com a condição do `/goal` ou o prompt do workflow já escritos. Se um
mecanismo não existir na sessão, use o vizinho mais próximo.

## Receita do `/goal`

O avaliador só lê a conversa, não roda comandos; a condição pronta carrega: um estado final
mensurável, o comando que o prova ("`npm test` sai 0"), as restrições ("sem tocar noutros
testes") e um cap ("ou pare após 20 turnos").

## Fronteiras dos mecanismos

`/loop` morre com a sessão e expira em 7 dias — fila que precisa sobreviver vai para
`/schedule`. Fires agendados só executam skills modelo-invocáveis: para agendar trabalho de
uma skill `disable-model-invocation: true` (kickoff, wrap-up), aponte o prompt para o
arquivo dela ("siga `/root/.claude/skills/wrap-up/SKILL.md`").

## O contrato de `loop.md`

`.claude/loop.md` na raiz do projeto substitui o prompt padrão do `/loop` puro — transforma
`/loop` (5 teclas) no despachador da fila `next-steps.md` (contrato da fila em
`/root/.claude/skills/kickoff/SKILL.md`). Ao despachar uma fila de fatias pela primeira vez
num projeto, crie o arquivo; nas vezes seguintes, confira se ainda casa com o contrato:

```markdown
Leia a fila em /root/.claude/projects/<slug-do-cwd>/memory/next-steps.md. Execute SOMENTE o
item AUTÔNOMA do topo — uma fatia por iteração — e verifique o resultado. Atualize a fila
(resolvido sai). Sem item AUTÔNOMA restante: encerre o loop e resuma o que ficou.
```

Edits no `loop.md` valem já na iteração seguinte; o arquivo é do projeto (versionável), a
fila continua na auto-memória.

**Concluído quando:** o usuário recebeu UM mecanismo (com o porquê em 1 frase) e a
linha/prompt completo pronto para disparar — ou a tarefa se revelou inline e isso foi dito.
