---
name: wrap-up
description: "Fechamento de sessão antes do /compact ou /clear: atualiza memória, docs e artefatos de status, roda os testes, resume o que ficou pendente e recomenda o próximo passo"
disable-model-invocation: true
---

Um **wrap-up** deixa o estado externo (memória + docs + testes) refletindo o que esta sessão
fez, para que o /compact não perca nada e a próxima sessão comece alinhada. Execute os passos
em ordem; cada um termina num critério checável.

(Versão global genérica — vale em qualquer projeto. Se um projeto tiver um `.claude/skills/wrap-up`
próprio, aquele sobrescreve este.)

## 1. Inventariar as mudanças da sessão
Levante TUDO que mudou desde o último wrap-up. A sessão pode ter commitado em **branches com PR
aberto**, então `git status`/`git diff` da branch atual não basta: olhe também
`git log --branches --not <default> --oneline` (commits ainda fora da branch default) e, se
houver `gh`/CLI do forge, os PRs abertos. Some os **fatos/decisões/aprendizados** da conversa
(não só código — escolhas do usuário, descobertas, pendências externas).
**Concluído quando:** existe uma lista concreta de arquivos/commits tocados, das branches/PRs
em jogo, e das decisões/fatos novos — sem omitir nada material.

## 2. Atualizar a memória
Para cada fato durável e **não óbvio** do passo 1, crie/atualize UM arquivo na auto-memória do
projeto (dir `memory/`, índice `MEMORY.md`), com o frontmatter e o tipo certo
(`user`/`feedback`/`project`/`reference`). Prefira atualizar um arquivo existente a duplicar;
apague o que se provou errado. Converta datas relativas em absolutas. Ligue com `[[slug]]`.
**Pendências vão para a fila canônica:** atualize também o `next-steps.md` da memória do
projeto — itens novos entram, resolvidos saem (contrato e formato:
`/root/.claude/skills/kickoff/SKILL.md`). É essa fila que o `/kickoff` despacha na abertura
da sessão seguinte.
**Codifique no sistema:** correção que o usuário repetiu ou verificação que ele fez à mão é
sinal de sistema, não de instância — proponha encodá-la (skill do projeto, regra hookify,
teste) para valer em toda iteração futura.
**Concluído quando:** todo fato durável da sessão tem arquivo de memória (com ponteiro no
`MEMORY.md`), `next-steps.md` reflete as pendências pós-sessão — ou o fato foi
conscientemente descartado por já estar no repo/ser efêmero — e toda correção recorrente tem
encoding proposto ou descartado.

## 3. Atualizar a documentação do repo
Faça a documentação refletir a implementação atual: `README`, o arquivo de instruções do projeto
(`CLAUDE.md`/`AGENTS.md`/`GEMINI.md`, o que existir), glossário (`CONTEXT.md`), `docs/` e ADRs.
Comandos novos, contagem de testes, seções de design, decisões — nenhum comando/contagem/caminho
pode ficar velho.
**Atualize também a LLM-Wiki** (`/workspace/projects/_wiki/`): se a sessão mudou conhecimento
canônico (decisões, arquitetura, entidades, empresas, pessoas, visão estável de um projeto),
reflita nas páginas afetadas — ver `_wiki/README.md` para a fronteira canônico × volátil.
Estado volátil fica na memória (passo 2), não na wiki.
**Atualize o(s) artefato(s) de status do projeto**, se existirem: verifique o registro da
skill `/project-artifact` (`$CLAUDE_PLUGIN_DATA/artifacts/<slug>/config.md` — em geral
`/root/.claude/plugins/data/project-artifact-claude-plugins-official/artifacts/`) e a memória
do projeto (referência tipo `reference` com URL `claude.ai/code/artifact/...`). Se a sessão
mudou algo que a página espelha (frentes, PRs, próximos passos, decisões), refresque pelo
fluxo da própria skill: re-gather, editar o HTML existente no lugar, republicar o MESMO
caminho/URL e reportar só o delta. Sessão sem impacto no que a página mostra = diga isso e
não republique.
**Concluído quando:** todo comportamento alterado na sessão está refletido na doc e na wiki,
nenhuma afirmação ficou desatualizada — ou nada canônico mudou e isso foi dito — e o artefato
de status (se houver) reflete a sessão ou foi declarado sem delta.

## 4. Verificar
Rode a suíte de testes do projeto. **Detecte o runner** pelo manifesto/arquivos: `pytest`/
`python3 -m pytest`, `npm test`/`pnpm test`/`yarn test`, `cargo test`, `go test ./...`,
`make test`, etc. Se houve mudança de código, ela tem de estar verde. Mudou comportamento de
runtime e o projeto tem skill de verificação end-to-end (ex. `verify`)? Rode-a também — teste
verde não prova que o fluxo real funciona.
**Concluído quando:** os testes passam — ou as falhas estão reportadas ao usuário com a saída
(ou, se o projeto não tiver suíte, isso é dito explicitamente).

## 5. Resumir e (sob pedido) versionar
Entregue um resumo curto: o que mudou, o que foi verificado, o que ficou **pendente de decisão
do usuário**. Commit/push/PR **só quando o usuário pedir** (siga as convenções do projeto — ex.
linha `Co-Authored-By` exigida); se estiver na branch default, crie branch antes.
**Concluído quando:** o usuário tem o resumo e nenhum efeito externo (commit/push) foi feito
sem pedido explícito.

## 6. Recomendar o próximo passo: /docs-audit, /clear ou /compact
Feche SEMPRE recomendando explicitamente UM caminho, com o porquê em 1–2 frases. Critérios:

- **`/clear`** — é o default quando o wrap-up terminou limpo: estado 100% externalizado
  (memória + docs + testes verdes), nada em andamento no meio, e a próxima tarefa é discreta
  (começa do zero só com `MEMORY.md` + repo). Compactar aqui pagaria para resumir o que já
  está salvo. Ao recomendar, **dê 1–3 frases prontas para abrir a próxima conversa** (ex.:
  "vamos para a próxima pendência", ou a pendência específica mais madura).
- **`/compact`** — quando existe fio vivo que NÃO é fato durável de memória: tarefa incompleta
  no meio, debugging com hipóteses abertas, negociação/decisão semi-tomada, ou nuances da
  conversa que a próxima etapa ainda precisa e que não fazem sentido como arquivo de memória.
  Compact preserva o fio; clear o perderia.
- **`/docs-audit` (antes do clear)** — quando há sinal de *drift* além do escopo da sessão:
  o passo 3 esbarrou em afirmações velhas que esta sessão NÃO causou, ou acumulou-se muito
  código desde a última auditoria (várias sessões/loops sem `docs-audit`). Audite primeiro,
  depois `/clear`.
- **Nenhum (continuar)** — só quando o usuário vai emendar AGORA tarefa relacionada e o
  contexto atual ainda é curto o bastante para valer mais que um recomeço limpo.

Cite também qualquer pendência que atravessa a fronteira da sessão (ex.: PR aberto aguardando
merge) — ela entra na frase de abertura sugerida.
**Concluído quando:** o usuário recebeu UMA recomendação clara (não um menu neutro), a
justificativa, e as frases de abertura da próxima conversa quando o caminho for `/clear`.
