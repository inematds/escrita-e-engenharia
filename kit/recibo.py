"""Recibo antes de "feito" (técnica 6) e recibo de custo (solução 9).

Regra: o sistema só pode dizer que algo aconteceu se o código que fez a coisa devolveu um recibo
(id, link, caminho do arquivo, linha de log). Sem recibo, a frase vira "tentei, mas não tenho confirmação".
"""
from __future__ import annotations

import json
import time
from pathlib import Path


class SemRecibo(Exception):
    pass


def feito(acao: str, recibo: str | None) -> str:
    """Frase para a pessoa. Sem recibo não existe 'pronto'."""
    if not recibo or not str(recibo).strip():
        return f"Tentei {acao}, mas não recebi confirmação. Não considere feito."
    return f"Feito: {acao} ({recibo})."


def exigir(recibo: str | None, acao: str) -> str:
    """Versão para código: levanta erro se não houver recibo."""
    if not recibo or not str(recibo).strip():
        raise SemRecibo(f"'{acao}' sem recibo")
    return str(recibo)


class Caderno:
    """Anota o custo de cada chamada (do uso que a própria ferramenta devolve) num arquivo JSONL."""

    def __init__(self, arquivo: str | Path) -> None:
        self.arquivo = Path(arquivo)

    def anotar(self, etapa: str, custo: float, detalhe: str = "", recibo: str = "") -> dict:
        linha = {"quando": time.strftime("%Y-%m-%d %H:%M:%S"), "etapa": etapa, "custo": round(float(custo), 6),
                 "detalhe": detalhe, "recibo": recibo}
        self.arquivo.parent.mkdir(parents=True, exist_ok=True)
        with self.arquivo.open("a", encoding="utf-8") as f:
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")
        return linha

    def linhas(self) -> list[dict]:
        if not self.arquivo.exists():
            return []
        return [json.loads(l) for l in self.arquivo.read_text(encoding="utf-8").splitlines() if l.strip()]

    def total(self, etapa: str | None = None) -> float:
        return round(sum(l["custo"] for l in self.linhas() if etapa is None or l["etapa"] == etapa), 6)

    def resumo(self) -> str:
        por: dict[str, float] = {}
        for l in self.linhas():
            por[l["etapa"]] = por.get(l["etapa"], 0) + l["custo"]
        partes = [f"{k}: {v:.4f}" for k, v in sorted(por.items())]
        return f"total {self.total():.4f} (" + ", ".join(partes) + ")" if partes else "nenhum gasto anotado"
