"""Barreira logo depois de gerar (solução 5).

Um valor ruim que nasce calado (NaN, infinito, campo faltando, JSON com texto em volta) se espalha
pelas etapas seguintes e só aparece lá no fim, sem erro nenhum. A barreira fica logo depois de quem gera:
limpa o que dá para limpar, recusa o que não dá, e diz o que fez.
"""
from __future__ import annotations

import json
import math
import re

TETO_PADRAO = 1e9  # número acima disso é tratado como lixo de geração


def numero_seguro(v, teto: float = TETO_PADRAO, padrao: float = 0.0) -> tuple[float, str | None]:
    """Devolve (número limpo, aviso|None). NaN e infinito viram `padrao`; acima do teto vira o teto."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return padrao, f"não é número: {v!r}"
    if math.isnan(x) or math.isinf(x):
        return padrao, f"valor inválido ({v!r}) trocado por {padrao}"
    if abs(x) > teto:
        return math.copysign(teto, x), f"{x} passou do teto {teto}"
    return x, None


_JSON_RE = re.compile(r"\{.*\}|\[.*\]", re.S)


def extrair_json(texto: str):
    """Modelo devolveu JSON com conversa em volta ou cercado de ```? Pega só o JSON. Falha alto se não houver."""
    t = texto.strip()
    if t.startswith("```"):
        t = t.strip("`")
        t = t.split("\n", 1)[1] if "\n" in t else t
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = _JSON_RE.search(t)
        if not m:
            raise ValueError("a resposta não traz JSON nenhum") from None
        return json.loads(m.group(0))


def conferir(dado: dict, campos: dict[str, type]) -> list[str]:
    """Confere campos obrigatórios e tipos. Devolve a lista de problemas (vazia = passou)."""
    problemas = []
    for nome, tipo in campos.items():
        if nome not in dado:
            problemas.append(f"falta o campo '{nome}'")
        elif not isinstance(dado[nome], tipo):
            problemas.append(f"'{nome}' devia ser {tipo.__name__}, veio {type(dado[nome]).__name__}")
    return problemas


def barreira(texto: str, campos: dict[str, type], numericos: tuple[str, ...] = ()) -> tuple[dict, list[str]]:
    """Tudo junto: extrai o JSON, confere os campos e limpa os números. Levanta ValueError se não der para seguir."""
    dado = extrair_json(texto)
    if not isinstance(dado, dict):
        raise ValueError("esperava um objeto JSON")
    problemas = conferir(dado, campos)
    if problemas:
        raise ValueError("; ".join(problemas))
    avisos = []
    for n in numericos:
        if n in dado:
            dado[n], aviso = numero_seguro(dado[n])
            if aviso:
                avisos.append(f"{n}: {aviso}")
    return dado, avisos
