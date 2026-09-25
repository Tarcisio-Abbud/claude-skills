#!/usr/bin/env python3
"""Assemble `achados-brutos.{md,json}` from the files each lens wrote to `<saida>/brutos/`.

    python3 brutos.py <saida>

Each lens writes its own result as it finishes, so a run stopped by the quota wall still
leaves what the finished lenses found. Ids are `<lens>-<n>`, the same the workflow assigns.
Exit 0 on success, 2 when there is nothing to assemble or a file does not parse.
"""

import glob
import json
import os
import sys

MARK = "<!-- revisao-contrato: brutos.py -->"
GERADO_POR = "revisao-contrato brutos.py"


def json_is_ours(path):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            data = json.loads(fh.read().replace("\ufeff", ""))
    except (OSError, UnicodeDecodeError, ValueError):
        return False
    return isinstance(data, dict) and data.get("gerado_por") == GERADO_POR


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    saida = argv[0]
    files = sorted(f for f in glob.glob(os.path.join(saida, "brutos", "*.json")) if os.path.isfile(f))
    if not files:
        print(f"erro: nenhum {saida}/brutos/*.json", file=sys.stderr)
        return 2
    lenses, achados = [], []
    for path in files:
        key = os.path.splitext(os.path.basename(path))[0]
        try:
            with open(path, encoding="utf-8-sig") as fh:
                data = json.loads(fh.read().replace("﻿", ""))
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            print(f"erro em {path}: {exc}", file=sys.stderr)
            return 2
        findings = data.get("findings", []) if isinstance(data, dict) else []
        lenses.append((key, data.get("resumo", "") if isinstance(data, dict) else "", len(findings)))
        for i, f in enumerate(findings):
            achados.append({**f, "id": f"{key}-{i + 1}", "lente": key})
    md_path = os.path.join(saida, "achados-brutos.md")
    json_path = os.path.join(saida, "achados-brutos.json")
    # Both files are checked before either is written: each carries this script's mark.
    if os.path.exists(md_path):
        with open(md_path, encoding="utf-8-sig") as fh:
            if not fh.read().startswith(MARK):
                print(f"erro: {md_path} existe e não foi escrito por este script", file=sys.stderr)
                return 2
    if os.path.exists(json_path) and not json_is_ours(json_path):
        print(f"erro: {json_path} existe e não foi escrito por este script", file=sys.stderr)
        return 2
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump({"gerado_por": GERADO_POR, "achados": achados}, fh, ensure_ascii=False, indent=1)
    out = [MARK, "", "# Achados brutos", "", f"{len(achados)} achados de {len(lenses)} lentes, antes da consolidação.", ""]
    for key, resumo, n in lenses:
        out += [f"## {key} ({n})", "", resumo, ""]
        for f in (x for x in achados if x["lente"] == key):
            out += [f"### {f['id']} · [{f.get('severidade', '?')}] {f.get('clausula', '?')} — {f.get('titulo', '')}", "",
                    f"**Problema.** {f.get('problema', '')}", "", f"**Proposta.** {f.get('proposta', '')}", ""]
            if f.get("fontes"):
                out += ["Fontes: " + "; ".join(f["fontes"]), ""]
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print(f"{len(achados)} achados de {len(lenses)} lentes → {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
