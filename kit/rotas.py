"""Resposta imediata, trabalho depois (solução 1) e status durante a espera (solução 2).

Cada frase da pessoa passa primeiro por:
  1. COMANDOS INSTANTÂNEOS — não vão ao modelo (parar, desfazer, mostrar). Respondem em milissegundos.
  2. TRIAGEM — decide em qual das 4 rotas a frase cai e devolve UMA frase curta para responder já:
       mudar     → altera o trabalho aberto (só a parte que muda)
       conversar → pergunta ou comentário sobre o trabalho aberto
       novo      → outro trabalho, do zero
       outro     → nada a ver com o trabalho aberto; segue para o assistente normal
O trabalho pesado roda depois, e enquanto roda a pessoa recebe uma frase de espera a cada ESPERA_S segundos.

A triagem aqui é por regras (funciona sem IA, serve de reserva). Para usar um modelo, passe
`triagem_modelo`: uma função que recebe a frase e devolve {"rota": ..., "resposta": ...} — e passe o
resultado pela guarda.barreira antes de confiar.
"""
from __future__ import annotations

import itertools
import re
import unicodedata

ESPERA_S = 10          # de quanto em quanto tempo dar sinal de vida durante um trabalho longo
ROTAS = ("mudar", "conversar", "novo", "outro")


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


INSTANTANEOS = {
    "parar": ("para", "pare", "parar", "chega", "stop", "espera"),
    "desfazer": ("desfaz", "desfazer", "volta como estava", "undo"),
    "mostrar": ("mostra", "mostrar", "abre o ultimo", "abrir o ultimo"),
}

_PALAVRAS = {
    "mudar": r"\b(muda|mude|troca|troque|aumenta|aumente|diminui|diminua|tira|tire|coloca|coloque|poe|ponha|acrescenta|acrescente|pinta|pinte|deixa .* mais)\b",
    "novo": r"\b(faz um novo|faca um novo|comeca outro|comece outro|outro trabalho|do zero|novo projeto)\b",
    "conversar": r"(\?$|\b(o que e|o que faz|por que|porque|quanto|qual|como funciona)\b)",
}

RESPOSTAS = {
    "mudar": "Certo, mexendo só nisso.",
    "conversar": "Boa pergunta, já te digo.",
    "novo": "Fechando este e começando o novo.",
    "outro": "",
}

FRASES_ESPERA = (
    "Ainda trabalhando, já vem.",
    "Quase lá, falta pouco.",
    "Conferindo a última parte.",
)


def instantaneo(frase: str) -> str | None:
    f = _norm(frase).strip(" .!")
    for cmd, gatilhos in INSTANTANEOS.items():
        if any(f == g or f.startswith(g + " ") for g in gatilhos):
            return cmd
    return None


def triagem_regras(frase: str, trabalho_aberto: bool) -> dict:
    f = _norm(frase).strip()
    if re.search(_PALAVRAS["novo"], f):
        rota = "novo"
    elif not trabalho_aberto:
        rota = "outro"
    elif re.search(_PALAVRAS["mudar"], f):
        rota = "mudar"          # "aumenta a sala e me diz o tamanho?" é mudança, não conversa
    elif re.search(_PALAVRAS["conversar"], f):
        rota = "conversar"
    else:
        rota = "outro"
    return {"rota": rota, "resposta": RESPOSTAS[rota]}


def rotear(frase: str, trabalho_aberto: bool, triagem_modelo=None) -> dict:
    """Devolve {"tipo": "instantaneo"|"rota", "valor": ..., "resposta": frase imediata}."""
    cmd = instantaneo(frase)
    if cmd:
        return {"tipo": "instantaneo", "valor": cmd, "resposta": ""}
    r = None
    if triagem_modelo is not None:
        try:
            r = triagem_modelo(frase)
            if r.get("rota") not in ROTAS:
                r = None
        except Exception:  # noqa: BLE001 — modelo fora do ar: cai na reserva por regras
            r = None
    r = r or triagem_regras(frase, trabalho_aberto)
    return {"tipo": "rota", "valor": r["rota"], "resposta": r.get("resposta") or RESPOSTAS[r["rota"]]}


def frases_de_espera(frase_do_modelo: str | None = None):
    """Gerador infinito: primeiro a frase que o próprio modelo mandou (##ESPERA), depois o reserva em rodízio."""
    if frase_do_modelo:
        yield frase_do_modelo
    yield from itertools.cycle(FRASES_ESPERA)


def agenda_espera(duracao_s: float, intervalo_s: float = ESPERA_S) -> list[float]:
    """Em que segundos falar a frase de espera, para um trabalho que levou `duracao_s`."""
    marcas, t = [], intervalo_s
    while t < duracao_s:
        marcas.append(t)
        t += intervalo_s
    return marcas
