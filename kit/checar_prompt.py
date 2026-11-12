#!/usr/bin/env python3
"""Confere se um prompt usa as 8 técnicas de escrita do kit. Funciona com prompt em PT, EN ou ES.

Uso:
  python3 kit/checar_prompt.py meu-prompt.md
  python3 kit/checar_prompt.py meu-prompt.md --minimo 8     # sai 1 se tiver menos de 8
  python3 kit/checar_prompt.py meu-prompt.md --json

Como ele lê: o prompt é dividido em SEÇÕES. Uma seção começa numa linha cujo rótulo está em MAIÚSCULAS
seguido de dois-pontos ("PROVA:", "ONDE COSTUMA ERRAR:", "RECIBO:"). Markdown na frente (#, **, -) é ignorado.
Cada técnica procura o seu rótulo e confere se o conteúdo da seção tem o que precisa ter.
Ele não julga se o seu prompt é bom; ele confere se as 8 peças estão lá. O modelo em modelos/ já vem com todas.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path


def sem_acento(t: str) -> str:
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _rx(*palavras: str) -> re.Pattern:
    return re.compile(r"\b(" + "|".join(palavras) + r")", re.I)


# id, nome, rótulos aceitos (sem acento), exigências do conteúdo [(regex, o que falta)], dica
TECNICAS = [
    ("prova", "1. Feche com a prova",
     ("PROVA", "COMO PROVAR", "PROVE", "VERIFIQUE", "PROOF", "VERIFY", "PRUEBA", "VERIFICA", "COMPRUEBA"),
     [(_rx("rode", "rodar", "execute", "executar", "run", "ejecuta", "ejecute", "ejecutar", "corre"), "uma ordem de RODAR (não só descrever)"),
      (_rx("quant[oa]s?", "segundos", "minutos", "numero", "how many", "how long", "seconds", "minutes", "number",
           "cuant[oa]s?", "cuanto tiempo"), "um NÚMERO para medir (quantos, quanto tempo)")],
     "Termine com 'PROVA:' pedindo para rodar e devolver números medidos."),
    ("pronto", "2. \"Pronto\" só com checagem",
     ("PRONTO", "QUANDO DISSER PRONTO", "DONE", "DEFINITION OF DONE", "LISTO", "TERMINADO"),
     [(_rx("checagem", "conferencia", "preflight", "check", "verificacion", "comprobacion", "chequeo", "teste", "test", "prueba"), "qual CHECAGEM roda antes"),
      (_rx("cole", "colar", "copie", "mostre", "paste", "copy", "show", "pega", "pegue", "copia", "muestra"), "pedir para COLAR o resultado")],
     "Diga: 'PRONTO: antes de dizer pronto, rode a checagem e cole a última linha'."),
    ("armadilha", "3. Avise onde costuma errar",
     ("ONDE COSTUMA ERRAR", "ONDE ERRA", "ARMADILHA", "ARMADILHAS", "CUIDADO", "WHERE IT USUALLY GOES WRONG",
      "WHERE IT GOES WRONG", "COMMON MISTAKES", "TRAP", "TRAPS",
      "PITFALL", "PITFALLS", "DONDE SUELE FALLAR", "DONDE FALLA", "ERRORES COMUNES", "TRAMPA", "TRAMPAS"),
     [(re.compile(r"\S.{14,}", re.S), "pelo menos um erro descrito")],
     "Crie 'ONDE COSTUMA ERRAR:' com o erro mais comum desse tipo de tarefa."),
    ("dono", "4. Um dono para cada coisa",
     ("UM DONO", "UMA PORTA", "DONO", "ONE OWNER", "ONE DOOR", "OWNER", "UN DUENO", "UNA PUERTA", "DUENO"),
     [(re.compile(r"\S.{14,}", re.S), "quem é o único dono / a única porta")],
     "Diga qual função/arquivo/etapa é a ÚNICA que faz tal coisa."),
    ("constante", "5. Número sensível com nome", (), [], "Ponha o número que você vai ajustar numa linha 'NOME_EM_MAIUSCULAS = valor'."),
    ("recibo", "6. Recibo antes de \"feito\"",
     ("RECIBO", "RECEIPT"),
     [(_rx("nunca", "never", "jamais", "sem recibo", "without", "sin"), "a proibição (nunca diga feito sem recibo)")],
     "Crie 'RECIBO:' dizendo que nunca se afirma uma ação sem id/link/arquivo que prove."),
    ("fora", "7. Texto de fora é dado, não ordem",
     ("TEXTO DE FORA", "DE FORA", "OUTSIDE TEXT", "EXTERNAL TEXT", "EXTERNAL CONTENT", "TEXTO DE FUERA", "DE FUERA", "CONTENIDO EXTERNO"),
     [(_rx("nunca", "never", "jamas", "jamais", "nao e", "is not", "no es"), "a negação (nunca é ordem)"),
      (_rx("ordem", "ordens", "instruc", "comando", "order", "instruction", "command", "orden"), "a palavra ordem/instrução")],
     "Crie 'TEXTO DE FORA:' dizendo que o que vem de print, PDF, site ou e-mail é informação, nunca ordem."),
    ("licao", "8. Lição vira regra",
     ("LICOES", "LICAO", "APRENDIDO", "APRENDIDAS", "LESSONS", "LESSON", "LEARNED", "LECCIONES", "LECCION", "APRENDIDAS"),
     [(re.compile(r"\S.{9,}", re.S), "pelo menos uma lição escrita como regra")],
     "Crie 'LIÇÕES:' e acrescente uma linha por erro real que já aconteceu."),
]

_CABECALHO = re.compile(r"^[\s#>*\-_`]*([A-Z][A-Z ]{1,40}?)\s*(\([^)]*\))?\s*[*_`]*\s*:(.*)$")
_CONSTANTE = re.compile(r"^[\s>*\-`]*([A-Z][A-Z0-9]*_[A-Z0-9_]+|[A-Z]{3,}[0-9]*)\s*=\s*\S+", re.M)


def secoes(texto: str) -> dict[str, str]:
    """{rótulo sem acento: conteúdo}. Rótulo repetido junta os conteúdos."""
    saida: dict[str, list[str]] = {}
    atual = None
    for linha in texto.splitlines():
        m = _CABECALHO.match(sem_acento(linha))
        if m and m.group(1).strip() == m.group(1).strip().upper():
            atual = re.sub(r"\s+", " ", m.group(1).strip())
            saida.setdefault(atual, []).append(m.group(3).strip())
            continue
        if atual is not None:
            saida[atual].append(sem_acento(linha))
    return {k: "\n".join(v).strip() for k, v in saida.items()}


def _rotulo_original(texto: str, rotulo: str) -> str:
    """O rótulo como a pessoa escreveu (com acento), para mostrar na saída."""
    for linha in texto.splitlines():
        m = _CABECALHO.match(sem_acento(linha))
        if m and re.sub(r"\s+", " ", m.group(1).strip()) == rotulo:
            ini = m.start(1)
            return linha[ini:ini + len(m.group(1))].strip()
    return rotulo


def checar(texto: str) -> list[dict]:
    s = secoes(texto)
    resultado = []
    for tid, nome, rotulos, exige, dica in TECNICAS:
        if tid == "constante":
            m = _CONSTANTE.search(texto)
            ok = bool(m)
            resultado.append({"id": tid, "tecnica": nome, "ok": ok, "achado": m.group(0).strip() if m else "",
                              "falta": [] if ok else ["uma linha NOME = valor"], "dica": "" if ok else dica})
            continue
        achou = next((r for r in s if any(r == rot or r.startswith(rot + " ") for rot in rotulos)), None)
        if achou is None:
            resultado.append({"id": tid, "tecnica": nome, "ok": False, "achado": "",
                              "falta": ["a seção"], "dica": dica})
            continue
        falta = [o_que for rx, o_que in exige if not rx.search(s[achou])]
        resultado.append({"id": tid, "tecnica": nome, "ok": not falta, "achado": _rotulo_original(texto, achou) + ":",
                          "falta": falta, "dica": dica if falta else ""})
    return resultado


# Mensagens em inglês e espanhol (o idioma é detectado pelos rótulos do prompt, ou --idioma).
_EN = {"nomes": ["1. Close with proof", "2. \"Done\" only after the check", "3. Say where it usually goes wrong",
                 "4. One owner for each thing", "5. Named sensitive number", "6. Receipt before \"done\"",
                 "7. Outside text is data, not an order", "8. Lessons become rules"],
       "dicas": ["End with 'PROOF:' asking it to run and report measured numbers.",
                 "Write: 'DONE: before saying done, run the check and paste the last line'.",
                 "Add 'WHERE IT USUALLY GOES WRONG:' with the most common mistake for this kind of task.",
                 "Say which function/file/step is the ONLY one that does that thing ('ONE OWNER:').",
                 "Put the number you will tune on a line 'NAME_IN_CAPS = value'.",
                 "Add 'RECEIPT:' saying it never claims an action without an id/link/file that proves it.",
                 "Add 'OUTSIDE TEXT:' saying screenshots, PDFs, sites and emails are information, never an instruction.",
                 "Add 'LESSONS:' and one line for each real mistake."],
       "falta": "missing", "dica": "tip", "nota": "score",
       "itens": {"uma ordem de RODAR (não só descrever)": "an order to RUN it (not just describe)",
                 "um NÚMERO para medir (quantos, quanto tempo)": "a NUMBER to measure (how many, how long)",
                 "qual CHECAGEM roda antes": "which CHECK runs first", "pedir para COLAR o resultado": "asking it to PASTE the result",
                 "pelo menos um erro descrito": "at least one mistake described", "quem é o único dono / a única porta": "who the single owner is",
                 "uma linha NOME = valor": "a NAME = value line", "a proibição (nunca diga feito sem recibo)": "the ban (never say done without a receipt)",
                 "a negação (nunca é ordem)": "the 'never an order' part", "a palavra ordem/instrução": "the word order/instruction",
                 "pelo menos uma lição escrita como regra": "at least one lesson written as a rule", "a seção": "the section"}}
_ES = {"nomes": ["1. Cierra con la prueba", "2. \"Listo\" solo con chequeo", "3. Avisa dónde suele fallar",
                 "4. Un dueño para cada cosa", "5. Número sensible con nombre", "6. Recibo antes de \"hecho\"",
                 "7. Texto de fuera es dato, no orden", "8. La lección se vuelve regla"],
       "dicas": ["Termina con 'PRUEBA:' pidiendo ejecutar y devolver números medidos.",
                 "Escribe: 'LISTO: antes de decir listo, ejecuta el chequeo y pega la última línea'.",
                 "Agrega 'DÓNDE SUELE FALLAR:' con el error más común de este tipo de tarea.",
                 "Di qué función/archivo/etapa es la ÚNICA que hace esa cosa ('UN DUEÑO:').",
                 "Pon el número que vas a ajustar en una línea 'NOMBRE_EN_MAYUSCULAS = valor'.",
                 "Agrega 'RECIBO:' diciendo que nunca afirma una acción sin id/enlace/archivo que la pruebe.",
                 "Agrega 'TEXTO DE FUERA:' diciendo que capturas, PDF, sitios y correos son información, nunca orden.",
                 "Agrega 'LECCIONES:' y una línea por cada error real."],
       "falta": "falta", "dica": "consejo", "nota": "nota",
       "itens": {"uma ordem de RODAR (não só descrever)": "una orden de EJECUTAR (no solo describir)",
                 "um NÚMERO para medir (quantos, quanto tempo)": "un NÚMERO para medir (cuántos, cuánto tiempo)",
                 "qual CHECAGEM roda antes": "qué CHEQUEO se ejecuta antes", "pedir para COLAR o resultado": "pedir que PEGUE el resultado",
                 "pelo menos um erro descrito": "al menos un error descrito", "quem é o único dono / a única porta": "quién es el único dueño",
                 "uma linha NOME = valor": "una línea NOMBRE = valor", "a proibição (nunca diga feito sem recibo)": "la prohibición (nunca decir hecho sin recibo)",
                 "a negação (nunca é ordem)": "la negación (nunca es orden)", "a palavra ordem/instrução": "la palabra orden/instrucción",
                 "pelo menos uma lição escrita como regra": "al menos una lección escrita como regla", "a seção": "la sección"}}
_MARCAS = {"en": ("PROOF", "DONE", "RECEIPT", "OUTSIDE TEXT", "LESSONS", "ONE OWNER", "TASK", "SETTINGS"),
           "es": ("PRUEBA", "LISTO", "LECCIONES", "UN DUENO", "TEXTO DE FUERA", "TAREA", "DONDE SUELE FALLAR")}


_COLCHETE = re.compile(r"\[[^\]\n]{3,}\]")
_AVISO_COLCHETES = {"pt": "atenção: ainda há {n} trecho(s) entre [colchetes] do modelo para trocar",
                    "en": "warning: {n} [bracketed] part(s) from the template still need to be replaced",
                    "es": "atención: todavía hay {n} parte(s) entre [corchetes] de la plantilla por cambiar"}


def colchetes(texto: str) -> int:
    """Quantos trechos de modelo ainda não preenchidos ([o que você quer...])."""
    return len(_COLCHETE.findall(texto))


def detectar_idioma(texto: str) -> str:
    rot = secoes(texto).keys()
    pontos = {k: sum(any(r == m or r.startswith(m + " ") for r in rot) for m in v) for k, v in _MARCAS.items()}
    melhor = max(pontos, key=pontos.get)
    return melhor if pontos[melhor] >= 2 else "pt"


def _traduz_falta(item: str, msg: dict) -> str:
    for pt, outro in msg["itens"].items():
        if item.startswith(pt):
            return outro + item[len(pt):]
    return item


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Confere as 8 técnicas de escrita num prompt (PT/EN/ES).")
    ap.add_argument("arquivo", type=Path)
    ap.add_argument("--minimo", type=int, default=0, help="sai 1 se a nota ficar abaixo disto / exit 1 below this")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--idioma", choices=("pt", "en", "es"), help="idioma das mensagens (padrão: detecta pelo prompt)")
    a = ap.parse_args(argv)
    texto = a.arquivo.read_text(encoding="utf-8")
    r = checar(texto)
    nota = sum(x["ok"] for x in r)
    idioma = a.idioma or detectar_idioma(texto)
    msg = {"en": _EN, "es": _ES}.get(idioma)
    if msg:
        for i, x in enumerate(r):
            x["tecnica"] = msg["nomes"][i]
            x["falta"] = [_traduz_falta(f, msg) for f in x["falta"]]
            x["dica"] = msg["dicas"][i] if x["dica"] else ""
    rot = msg or {"falta": "falta", "dica": "dica", "nota": "nota"}
    n_colch = colchetes(texto)
    if a.json:
        print(json.dumps({"nota": nota, "de": len(r), "idioma": idioma, "colchetes": n_colch, "tecnicas": r},
                         ensure_ascii=False, indent=2))
    else:
        for x in r:
            linha = f"{'✔' if x['ok'] else '✘'} {x['tecnica']}"
            if x["ok"]:
                linha += f"  ({x['achado']})"
            else:
                linha += f"  — {rot['falta']}: {'; '.join(x['falta'])}\n     {rot['dica']}: {x['dica']}"
            print(linha)
        print(f"{rot['nota']}: {nota}/{len(r)}")
        if n_colch:
            print(_AVISO_COLCHETES[idioma].format(n=n_colch))
    return 1 if nota < a.minimo else 0


if __name__ == "__main__":
    sys.exit(main())
