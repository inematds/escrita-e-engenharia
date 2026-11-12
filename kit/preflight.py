#!/usr/bin/env python3
"""Checagem de ponta a ponta (solução 6): roda os caminhos de verdade e dá o veredito numa linha.

Não é teste de unidade nem simulação: faz pedidos reais ao sistema no ar.
Regra de uso (técnica 2): ninguém diz "pronto" sem colar a última linha deste script.

Uso:
  python3 kit/preflight.py --demo                 # sobe um site pequeno do próprio kit e confere
  python3 kit/preflight.py --demo --quebrar       # mesmo, com um defeito de propósito (tem que sair 1)
  python3 kit/preflight.py --alvo URL --pasta DIR [--segredo .env --segredo config.json] [--sem-rastro DIR]

O que confere:
  1. o endereço responde
  2. cada arquivo da pasta que o site serve é IGUAL ao que está no disco (arquivo velho servido é a causa
     nº 1 de "eu corrigi e nada mudou")
  3. nenhum segredo pode ser baixado pelo navegador (tem que FALHAR alto)
  4. nenhum resto de teste ficou para trás (arquivos que começam com "teste-")
Cada incidente real vira uma checagem nova: acrescente uma função em CHECAGENS_EXTRA.
Última linha: "N ok, N falha, N aviso". Sai 1 se houver qualquer falha.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import shutil
import socketserver
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TEMPO_LIMITE_S = 8          # quanto esperar cada pedido antes de dar falha
MAX_ARQUIVOS = 200          # teto de arquivos comparados (site grande: confere os primeiros)
IGNORAR = {".git", "node_modules", "__pycache__"}

OK, FALHA, AVISO = "ok", "falha", "aviso"
SIMBOLO = {OK: "✔", FALHA: "✘", AVISO: "!"}


def baixar(url: str) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(url, timeout=TEMPO_LIMITE_S) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


def md5(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


def chk_no_ar(alvo: str, **_):
    try:
        st, _b = baixar(alvo)
    except Exception as e:  # noqa: BLE001
        return FALHA, f"não respondeu: {e}"
    return (OK, f"respondeu {st}") if st == 200 else (FALHA, f"respondeu {st}")


def chk_servido_igual_disco(alvo: str, pasta: Path | None, **_):
    if not pasta:
        return AVISO, "sem --pasta: não comparei o servido com o disco"
    arquivos = [p for p in sorted(pasta.rglob("*")) if p.is_file() and not (IGNORAR & set(p.parts))][:MAX_ARQUIVOS]
    diferentes = []
    for p in arquivos:
        rel = p.relative_to(pasta).as_posix()
        st, corpo = baixar(urllib.parse.urljoin(alvo, urllib.parse.quote(rel)))
        if st != 200 or md5(corpo) != md5(p.read_bytes()):
            diferentes.append(f"{rel} ({st})")
    if diferentes:
        return FALHA, f"{len(diferentes)} de {len(arquivos)} servidos diferentes do disco: " + ", ".join(diferentes[:5])
    return OK, f"{len(arquivos)} arquivos servidos iguais ao disco"


def chk_segredos_fechados(alvo: str, segredos: list[str], **_):
    if not segredos:
        return AVISO, "sem --segredo: não conferi se algum segredo vaza"
    abertos = []
    for s in segredos:
        for caminho in (s, "../" + s, "%2e%2e/" + s):
            st, corpo = baixar(urllib.parse.urljoin(alvo, caminho)) if "%" not in caminho else baixar(alvo.rstrip("/") + "/" + caminho)
            if st == 200 and corpo:
                abertos.append(caminho)
    if abertos:
        return FALHA, "SEGREDO ABERTO NO NAVEGADOR: " + ", ".join(abertos)
    return OK, f"{len(segredos)} segredo(s) fechados"


def chk_sem_rastro(sem_rastro: Path | None, **_):
    if not sem_rastro:
        return AVISO, "sem --sem-rastro: não conferi restos de teste"
    restos = [p.name for p in sem_rastro.rglob("teste-*")]
    return (FALHA, "restos de teste: " + ", ".join(restos[:5])) if restos else (OK, "nenhum resto de teste")


CHECAGENS = [
    ("o endereço responde", chk_no_ar),
    ("servido = disco", chk_servido_igual_disco),
    ("segredos fechados", chk_segredos_fechados),
    ("ensaio sem rastro", chk_sem_rastro),
]
CHECAGENS_EXTRA: list = []   # cada incidente real vira uma linha aqui: ("nome", função(**ctx) -> (status, msg))


def rodar(ctx: dict) -> int:
    cont = {OK: 0, FALHA: 0, AVISO: 0}
    for nome, fn in CHECAGENS + CHECAGENS_EXTRA:
        try:
            st, msg = fn(**ctx)
        except Exception as e:  # noqa: BLE001 — checagem que quebra é falha, nunca silêncio
            st, msg = FALHA, f"a checagem quebrou: {e}"
        cont[st] += 1
        print(f"{SIMBOLO[st]} {nome}: {msg}")
    print(f"{cont[OK]} ok, {cont[FALHA]} falha, {cont[AVISO]} aviso")
    return 1 if cont[FALHA] else 0


def _servidor(raiz: Path):
    class Calado(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):  # sem log de cada pedido
            pass

    handler = functools.partial(Calado, directory=str(raiz))
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def demo(quebrar: bool) -> int:
    """Monta um site pequeno numa pasta temporária, serve uma CÓPIA dele (como um cache/build) e confere."""
    base = Path(tempfile.mkdtemp(prefix="preflight-demo-"))
    try:
        pasta = base / "site"
        pasta.mkdir()
        (pasta / "index.html").write_text("<h1>Bicicletaria Pedal Certo</h1>", encoding="utf-8")
        (pasta / "precos.json").write_text('{"revisao": 120}', encoding="utf-8")
        (base / "segredo.json").write_text('{"chave": "nao-deveria-vazar"}', encoding="utf-8")
        servida = base / "servida"
        shutil.copytree(pasta, servida)            # o que o servidor entrega é uma cópia (build/cache)
        saida = base / "saida"
        saida.mkdir()
        if quebrar:
            (pasta / "precos.json").write_text('{"revisao": 135}', encoding="utf-8")  # corrigi no disco...
            shutil.copy(base / "segredo.json", servida / "segredo.json")              # ...e um segredo foi junto
            (saida / "teste-rascunho.txt").write_text("sobrou", encoding="utf-8")
        srv = _servidor(servida)
        alvo = f"http://127.0.0.1:{srv.server_address[1]}/"
        print(f"demo: {alvo} (pasta {pasta})" + (" — com defeitos de propósito" if quebrar else ""))
        try:
            return rodar({"alvo": alvo, "pasta": pasta, "segredos": ["segredo.json"], "sem_rastro": saida})
        finally:
            srv.shutdown()
            srv.server_close()
    finally:
        shutil.rmtree(base, ignore_errors=True)   # a própria demo não deixa rastro


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--quebrar", action="store_true")
    ap.add_argument("--alvo")
    ap.add_argument("--pasta", type=Path)
    ap.add_argument("--segredo", action="append", default=[])
    ap.add_argument("--sem-rastro", type=Path)
    a = ap.parse_args(argv)
    if a.demo:
        return demo(a.quebrar)
    if not a.alvo:
        ap.error("use --demo ou --alvo URL")
    alvo = a.alvo if a.alvo.endswith("/") else a.alvo + "/"
    return rodar({"alvo": alvo, "pasta": a.pasta, "segredos": a.segredo, "sem_rastro": a.sem_rastro})


if __name__ == "__main__":
    sys.exit(main())
