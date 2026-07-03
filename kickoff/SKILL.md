---
name: kickoff
description: "Abertura de sessão — espelho do /wrap-up: levanta as pendências do projeto, verifica cada uma contra a realidade, tria e despacha as que o usuário marcar no menu"
disable-model-invocation: true
---

Um **kickoff** abre a sessão que o `/wrap-up` fechou: monta a **pauta** de pendências do
projeto, confere o que ainda é real, tria item a item e **despacha** o que o usuário marcar.
Execute os passos em ordem; cada um termina num critério checável.

(Versão global — vale em qualquer projeto. Se um projeto tiver um `.claude/skills/kickoff`
próprio, aquele sobrescreve este.)

## 1. Levantar a pauta

Fontes, nesta ordem:

- **`next-steps.md`** na auto-memória do projeto (dir `memory/`; o índice `MEMORY.md` já está
  no contexto) — a fila canônica, ver contrato no fim deste arquivo. Se ainda não existir
  (primeiro kickoff do projeto), caia para os arquivos de memória que o índice aponte como
  tendo pendência/NEXT/aguardando/ideia.
- **Issues e PRs abertos** do repo (`gh issue list`, `gh pr list`), quando houver tracker.

Wiki e docs do repo NÃO são fonte de pauta — estado volátil não vive lá; se aparecer pendência
lá, é doc velha, não fila.
**Concluído quando:** existe uma lista única de itens candidatos, cada um com sua fonte.

## 2. Verificar contra a realidade

Memória reflete o momento em que foi escrita. Antes de qualquer item entrar na pauta, confira
o estado atual: o PR ainda está aberto? algum commit/merge já resolveu? a issue fechou? o
arquivo/flag/script citado ainda existe? (`gh pr list`, `gh issue view`, `git log`, ler o
código). Item já resolvido sai da pauta E a memória que o citava é corrigida NA HORA — não
deixe para o próximo wrap-up.
**Concluído quando:** todo item restante foi confirmado como realmente aberto e nenhuma
memória sabidamente velha ficou sem correção.

## 3. Triar

Cada item recebe exatamente UMA classe:

| Classe | Critério |
|---|---|
| **AUTÔNOMA** | bem-especificada; um agente executa sem o usuário |
| **DECISÃO** | falta uma escolha do usuário; decidida, vira AUTÔNOMA |
| **BLOQUEADA** | depende de dado/ação/credencial que só o usuário tem |
| **EXTERNA** | esperando terceiro; cabe no máximo cobrar/lembrar |
| **RECORRENTE** | não é item avulso — deveria virar rotina agendada |

**Concluído quando:** toda pendência tem classe e, se acionável, um despacho recomendado da
paleta do passo 5.

## 4. Montar o menu

Antes de perguntar, mostre a **pauta completa triada** — TODOS os itens, uma linha cada, com
classe — para o usuário ver que nada se perdeu antes de marcar (BLOQUEADA/EXTERNA aparecem
aqui; o detalhe delas fica para o relatório final).

Então um `AskUserQuestion` multiSelect com os itens acionáveis (AUTÔNOMA + RECORRENTE)
priorizados por impacto/urgência, recomendação em primeiro com "(Recomendado)". Itens DECISÃO
viram perguntas próprias — as opções são as escolhas em si, não "sim/não". Limite da
ferramenta: 4 perguntas × 4 opções; o que não couber vira linha do relatório final, não opção.
BLOQUEADA e EXTERNA nunca são opções.
**Concluído quando:** a pauta inteira foi exibida e a seleção do usuário está capturada.

## 5. Despachar

O check no menu É a autorização — execute na sequência, sem reconfirmar. Paleta:

| Situação do item marcado | Despacho | Quem dispara |
|---|---|---|
| Precisa de conversa/contexto desta sessão | inline, agora (plan mode se for grande) | a skill |
| Estado final verificável (testes verdes, fila zerada, tudo compila) | `/goal <condição>` — um avaliador fecha quando a condição vale | o usuário |
| Fila de fatias autônomas SEM condição única de término | `/loop` dinâmico (self-paced), uma fatia por iteração | a skill |
| Espera/poll de estado externo (CI, terceiro) | `/loop` com intervalo | a skill |
| Mesma operação sobre MUITOS itens (varredura, migração em massa) | dynamic workflow (`ultracode` / "use a workflow") | o usuário |
| RECORRENTE | `/schedule` (nuvem) ou cron local — propor a rotina | a skill |
| Independente do contexto e paralelizável | subagente em background (worktree isolado) | a skill |

Os despachos "o usuário" são comandos nativos que a skill não consegue invocar: não travam o
fluxo — entregue no relato final a linha pronta para colar, com a condição do `/goal` ou o
prompt do workflow já escritos. Se um mecanismo da tabela não existir na sessão, use o
vizinho mais próximo.
Feche com: (a) o que ficou rodando/agendado, (b) BLOQUEADAS com o que falta do usuário,
(c) EXTERNAS com quem cobrar — e regrave a fila resultante em `next-steps.md`.
**Concluído quando:** todo item marcado está em execução ou agendado, o relatório cobre (b) e
(c), e `next-steps.md` reflete a fila pós-kickoff.

## O contrato de `next-steps.md`

Fonte única da fila de pendências de um projeto. Vive na auto-memória do projeto
(`/root/.claude/projects/<slug-do-cwd>/memory/next-steps.md`, com ponteiro no `MEMORY.md`) e
é atualizado por QUALQUER sessão em que uma pendência nasça ou morra — o `/wrap-up` garante
isso no fechamento; o `/kickoff` regrava a fila verificada na abertura.

```markdown
---
name: next-steps
description: fila canônica de próximos passos do projeto — consumida pelo /kickoff
metadata:
  type: project
---

# Next steps

- [ ] <ação concreta> — contexto em 1 linha. **Classe:** AUTÔNOMA. **Fonte:** PR #12, 2026-07-01
```

Regras: um item por linha; datas absolutas; item resolvido SAI do arquivo (nada de riscado);
a classe gravada é palpite de quem escreveu — o kickoff sempre re-verifica e re-tria.
