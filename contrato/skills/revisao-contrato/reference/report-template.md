# Report template — `revisao.md`

The report agent follows this file. The report is pt-BR, at most **400 lines**, for a cold
reader who did not watch the review. `.docx` and `.pdf` converters drop `<details>` blocks and
multi-line cells, so wording lives in plain blocks, never inside a table cell.

Section 2's title, the wording form and section 4's columns depend on `autoria`:

| | `autoria: nossa` | `autoria: deles` |
|---|---|---|
| section 2 | *Corrigir antes de enviar* | *Contraproposta e redlines* |
| wording form | replacement text | redline: `~~texto atual~~` then **texto proposto** |
| section 4 | FIRME / TROCÁVEL / SUPÉRFLUO | pedir / trocar / walk-away |

## 1. Veredito

One paragraph. Close it with how many altas carry `n/d` as value at risk.

## 2. Corrigir antes de enviar — or — Contraproposta e redlines

One table of every published alta, ranked by `valor_em_risco` **band** (milhões ·
centenas de milhares · dezenas de milhares · n/d), then by convergence, then by clause:

| id | cláusula | problema em uma linha | faixa | convergência |
|---|---|---|---|---|

Then one block per alta, in clause order, headed exactly `### <id> · cláusula <clausula>` —
the apply step finds ids by that heading:

- the problem in at most two sentences;
- the ready-to-paste wording (redline form under `autoria: deles`);
- the exact estimate and its base;
- the sources.

## 3. Perguntas ao advogado

At most **10**, ranked by value at stake, each written as the exact question to ask. The
remaining medias go to `medias.md` in the same folder, one `### <id> · cláusula <clausula>`
block each with problem and proposal; the report carries one line naming that file.

## 4. Mesa

One table from the `mesa` lens, with the columns of the table above.

## 5. Clareza

The measurements and the restructuring plan with estimated reduction. No worked rewrites.

## 6. Menores e descartadas

One line per baixa. One line per refuted alta, naming the angle that refuted it.

## 7. Método

At most 10 lines: lenses run, critic additions and rejections, counts raw → merged → verified
→ refuted, models, date, number of agents, and the pointer to `achados-brutos.md`.
