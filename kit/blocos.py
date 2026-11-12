"""Leitor de blocos que chegam aos pedaços (solução 3) e palco que troca só o que mudou (solução 4).

Formato que o modelo escreve, e nada mais:

    ##TITULO Nome do trabalho
    ##BLOCO nome-do-bloco | o que estou fazendo agora
    (conteúdo do bloco: código, texto, JSON...)
    ##FIM
    ##DIZ Uma frase curta para quando terminar

O leitor recebe o texto em pedaços de qualquer tamanho (streaming) e devolve cada bloco
no instante em que a linha ##FIM dele chega. Um corte no meio de uma linha nunca quebra nada.
"""
from __future__ import annotations

from dataclasses import dataclass, field

MARCA = "##"


@dataclass
class Bloco:
    nome: str
    status: str
    conteudo: str


@dataclass
class Evento:
    tipo: str          # "titulo" | "bloco" | "diz" | "espera"
    valor: object


class LeitorBlocos:
    """Alimente com feed(pedaço); cada chamada devolve a lista de eventos completos até ali."""

    def __init__(self) -> None:
        self._resto = ""          # linha ainda incompleta
        self._aberto: Bloco | None = None
        self._linhas: list[str] = []

    def feed(self, pedaco: str) -> list[Evento]:
        self._resto += pedaco
        eventos: list[Evento] = []
        while "\n" in self._resto:
            linha, self._resto = self._resto.split("\n", 1)
            eventos.extend(self._linha(linha))
        return eventos

    def fim(self) -> list[Evento]:
        """Fim do fluxo: processa a última linha sem quebra. Bloco sem ##FIM é descartado (não executa pela metade)."""
        eventos = self._linha(self._resto) if self._resto else []
        self._resto = ""
        self._aberto = None
        self._linhas = []
        return eventos

    @property
    def bloco_aberto(self) -> str | None:
        return self._aberto.nome if self._aberto else None

    def _linha(self, linha: str) -> list[Evento]:
        limpa = linha.rstrip("\r")
        cmd = limpa.strip()
        if self._aberto is not None:
            if cmd == MARCA + "FIM":
                self._aberto.conteudo = "\n".join(self._linhas)
                b, self._aberto, self._linhas = self._aberto, None, []
                return [Evento("bloco", b)]
            if cmd.startswith(MARCA + "BLOCO "):
                # bloco novo sem ##FIM no anterior: o anterior é descartado, nunca executado pela metade
                self._aberto, self._linhas = None, []
            else:
                self._linhas.append(limpa)
                return []
        if cmd.startswith(MARCA + "BLOCO "):
            resto = cmd[len(MARCA + "BLOCO "):]
            nome, _, status = resto.partition("|")
            self._aberto = Bloco(nome.strip(), status.strip(), "")
            return []
        for chave, tipo in (("TITULO ", "titulo"), ("DIZ ", "diz"), ("ESPERA ", "espera")):
            if cmd.startswith(MARCA + chave):
                return [Evento(tipo, cmd[len(MARCA + chave):].strip())]
        return []  # texto solto fora de bloco é ignorado


@dataclass
class Palco:
    """Guarda os blocos por nome. Mandar o mesmo nome de novo SUBSTITUI só aquele bloco (solução 4).

    `textos` junta as palavras que cada bloco declara (linhas 'TEXTO: ...'), como quando a imagem final
    precisa receber a grafia exata. Bloco trocado esquece os textos antigos.
    """

    blocos: dict[str, Bloco] = field(default_factory=dict)
    trocas: list[str] = field(default_factory=list)

    def aplicar(self, bloco: Bloco) -> str:
        acao = "troca" if bloco.nome in self.blocos else "novo"
        self.blocos[bloco.nome] = bloco
        self.trocas.append(f"{acao}:{bloco.nome}")
        return acao

    def remover(self, nome: str) -> bool:
        return self.blocos.pop(nome, None) is not None

    def textos(self) -> list[str]:
        saida: list[str] = []
        for b in self.blocos.values():
            for linha in b.conteudo.splitlines():
                if linha.strip().upper().startswith("TEXTO:"):
                    saida.append(linha.split(":", 1)[1].strip())
        return saida


def consertar(nome: str, gerar, executar, tentativas: int = 2):
    """Roda um bloco; se falhar, pede o bloco de novo com o erro, no máximo `tentativas` vezes, e segue sem ele.

    gerar(nome, erro|None) -> Bloco      executar(Bloco) -> None (levanta exceção se falhar)
    Devolve (bloco|None, consertos_usados). Nunca refaz o trabalho inteiro por causa de um bloco.
    """
    erro = None
    for i in range(tentativas + 1):
        bloco = gerar(nome, erro)
        try:
            executar(bloco)
            return bloco, i
        except Exception as e:  # noqa: BLE001 — qualquer falha do bloco vira pedido de conserto
            erro = f"{type(e).__name__}: {e}"
    return None, tentativas
