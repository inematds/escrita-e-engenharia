"""Testes do kit: python3 -m unittest -q (na raiz do repo)."""
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "kit"))

import blocos  # noqa: E402
import checar_prompt  # noqa: E402
import guarda  # noqa: E402
import recibo  # noqa: E402
import rotas  # noqa: E402

FLUXO = (
    "##TITULO Orçamento da revisão\n"
    "##ESPERA Separando as peças, já vem.\n"
    "##BLOCO tabela | lendo a tabela\n"
    "revisao simples = 120\n"
    "TEXTO: PEDAL CERTO\n"
    "##FIM\n"
    "texto solto que deve ser ignorado\n"
    "##BLOCO agenda | marcando horário\n"
    "sabado ate 12h\n"
    "##FIM\n"
    "##DIZ Pronto, orçamento e horário na tela.\n"
)


def ler_tudo(pedacos):
    l = blocos.LeitorBlocos()
    ev = []
    for p in pedacos:
        ev += l.feed(p)
    return ev + l.fim()


class TestBlocos(unittest.TestCase):
    def test_fluxo_inteiro(self):
        ev = ler_tudo([FLUXO])
        self.assertEqual([e.tipo for e in ev], ["titulo", "espera", "bloco", "bloco", "diz"])
        self.assertEqual(ev[2].valor.nome, "tabela")
        self.assertEqual(ev[2].valor.status, "lendo a tabela")
        self.assertIn("revisao simples = 120", ev[2].valor.conteudo)

    def test_corte_em_todo_caractere(self):
        esperado = [(e.tipo, getattr(e.valor, "conteudo", e.valor)) for e in ler_tudo([FLUXO])]
        for i in range(len(FLUXO) + 1):
            obtido = [(e.tipo, getattr(e.valor, "conteudo", e.valor)) for e in ler_tudo([FLUXO[:i], FLUXO[i:]])]
            self.assertEqual(obtido, esperado, f"corte na posição {i}")

    def test_um_caractere_por_vez(self):
        self.assertEqual(len(ler_tudo(list(FLUXO))), 5)

    def test_bloco_chega_assim_que_fecha(self):
        l = blocos.LeitorBlocos()
        self.assertEqual(l.feed("##BLOCO a | x\nconteudo\n"), [])
        self.assertEqual(l.bloco_aberto, "a")
        ev = l.feed("##FIM\n")
        self.assertEqual(ev[0].valor.nome, "a")

    def test_bloco_sem_fim_nao_executa(self):
        ev = ler_tudo(["##BLOCO a | x\nmetade do código\n"])
        self.assertEqual(ev, [])

    def test_bloco_novo_descarta_anterior_sem_fim(self):
        ev = ler_tudo(["##BLOCO a | x\nmetade\n##BLOCO b | y\ninteiro\n##FIM\n"])
        self.assertEqual([e.valor.nome for e in ev], ["b"])

    def test_crlf(self):
        ev = ler_tudo([FLUXO.replace("\n", "\r\n")])
        self.assertEqual(len(ev), 5)


class TestPalco(unittest.TestCase):
    def test_mesmo_nome_substitui(self):
        p = blocos.Palco()
        self.assertEqual(p.aplicar(blocos.Bloco("sala", "", "3x4")), "novo")
        p.aplicar(blocos.Bloco("cozinha", "", "2x3"))
        self.assertEqual(p.aplicar(blocos.Bloco("sala", "", "4x4")), "troca")
        self.assertEqual(p.blocos["sala"].conteudo, "4x4")
        self.assertEqual(len(p.blocos), 2)

    def test_textos_esquece_bloco_trocado(self):
        p = blocos.Palco()
        p.aplicar(blocos.Bloco("placa", "", "TEXTO: PEDAL CERTO"))
        p.aplicar(blocos.Bloco("placa", "", "TEXTO: PEDAL CERTO 2"))
        self.assertEqual(p.textos(), ["PEDAL CERTO 2"])

    def test_consertar_tenta_duas_vezes_e_segue(self):
        chamadas = []

        def gerar(nome, erro):
            chamadas.append(erro)
            return blocos.Bloco(nome, "", "x")

        def executar(b):
            raise RuntimeError("quebrou")

        b, usados = blocos.consertar("roda", gerar, executar)
        self.assertIsNone(b)
        self.assertEqual(len(chamadas), 3)       # original + 2 consertos, nunca mais
        self.assertIn("quebrou", chamadas[1])    # o conserto recebe o erro

    def test_consertar_para_quando_funciona(self):
        n = {"i": 0}

        def executar(b):
            n["i"] += 1
            if n["i"] == 1:
                raise ValueError("1ª falha")

        b, usados = blocos.consertar("roda", lambda nome, e: blocos.Bloco(nome, "", "x"), executar)
        self.assertIsNotNone(b)
        self.assertEqual(usados, 1)


class TestGuarda(unittest.TestCase):
    def test_nan_e_infinito(self):
        self.assertEqual(guarda.numero_seguro(float("nan"))[0], 0.0)
        self.assertEqual(guarda.numero_seguro("inf")[0], 0.0)
        self.assertIsNotNone(guarda.numero_seguro(float("nan"))[1])

    def test_teto(self):
        v, aviso = guarda.numero_seguro(5e12)
        self.assertEqual(v, guarda.TETO_PADRAO)
        self.assertIn("teto", aviso)

    def test_numero_normal_passa_calado(self):
        self.assertEqual(guarda.numero_seguro("120"), (120.0, None))

    def test_json_com_conversa_em_volta(self):
        d = guarda.extrair_json('Claro! Aqui está:\n{"rota": "mudar", "resposta": "Certo"}\nQualquer coisa me diga.')
        self.assertEqual(d["rota"], "mudar")

    def test_json_cercado(self):
        self.assertEqual(guarda.extrair_json('```json\n{"a": 1}\n```'), {"a": 1})

    def test_sem_json_falha_alto(self):
        with self.assertRaises(ValueError):
            guarda.extrair_json("não sei responder")

    def test_barreira_campo_faltando(self):
        with self.assertRaises(ValueError):
            guarda.barreira('{"rota": "mudar"}', {"rota": str, "resposta": str})

    def test_barreira_limpa_numero(self):
        d, avisos = guarda.barreira('{"preco": NaN, "nome": "revisao"}', {"nome": str}, numericos=("preco",))
        self.assertEqual(d["preco"], 0.0)
        self.assertEqual(len(avisos), 1)


class TestRotas(unittest.TestCase):
    def test_instantaneo_nao_vai_ao_modelo(self):
        def modelo(_):
            raise AssertionError("não devia chamar o modelo")

        r = rotas.rotear("Para!", True, triagem_modelo=modelo)
        self.assertEqual((r["tipo"], r["valor"]), ("instantaneo", "parar"))

    def test_mudanca_com_pergunta_e_mudanca(self):
        self.assertEqual(rotas.rotear("aumenta a sala e me diz o tamanho?", True)["valor"], "mudar")

    def test_pergunta_sobre_o_trabalho(self):
        self.assertEqual(rotas.rotear("o que faz essa peça?", True)["valor"], "conversar")

    def test_sem_trabalho_aberto_vai_para_assistente(self):
        self.assertEqual(rotas.rotear("aumenta o volume", False)["valor"], "outro")

    def test_novo(self):
        self.assertEqual(rotas.rotear("faz um novo do zero, uma loja", True)["valor"], "novo")

    def test_resposta_imediata_existe(self):
        self.assertTrue(rotas.rotear("troca a cor da porta", True)["resposta"])

    def test_modelo_fora_do_ar_cai_na_reserva(self):
        def modelo(_):
            raise TimeoutError

        self.assertEqual(rotas.rotear("troca a cor", True, triagem_modelo=modelo)["valor"], "mudar")

    def test_modelo_com_rota_inventada_e_ignorado(self):
        r = rotas.rotear("troca a cor", True, triagem_modelo=lambda f: {"rota": "dançar", "resposta": "oba"})
        self.assertEqual(r["valor"], "mudar")

    def test_espera_primeiro_frase_do_modelo(self):
        g = rotas.frases_de_espera("Medindo a parede.")
        self.assertEqual(next(g), "Medindo a parede.")
        self.assertIn(next(g), rotas.FRASES_ESPERA)

    def test_agenda_espera(self):
        self.assertEqual(rotas.agenda_espera(35), [10, 20, 30])
        self.assertEqual(rotas.agenda_espera(5), [])


class TestRecibo(unittest.TestCase):
    def test_sem_recibo_nao_e_feito(self):
        self.assertIn("Não considere feito", recibo.feito("agendar a revisão", None))
        self.assertIn("Não considere feito", recibo.feito("agendar a revisão", "   "))

    def test_com_recibo(self):
        self.assertTrue(recibo.feito("agendar", "agenda.csv linha 14").startswith("Feito:"))

    def test_exigir(self):
        with self.assertRaises(recibo.SemRecibo):
            recibo.exigir("", "publicar")

    def test_caderno_soma(self):
        with tempfile.TemporaryDirectory() as d:
            c = recibo.Caderno(Path(d) / "gastos.jsonl")
            c.anotar("gerar", 0.12)
            c.anotar("gerar", 0.03)
            c.anotar("imagem", 0.04)
            self.assertAlmostEqual(c.total(), 0.19)
            self.assertAlmostEqual(c.total("gerar"), 0.15)
            self.assertIn("imagem", c.resumo())


class TestChecarPrompt(unittest.TestCase):
    def nota(self, caminho):
        return sum(x["ok"] for x in checar_prompt.checar((RAIZ / caminho).read_text(encoding="utf-8")))

    def test_antes_e_depois_pt(self):
        self.assertLessEqual(self.nota("exemplos/antes.md"), 1)
        self.assertEqual(self.nota("exemplos/depois.md"), 8)

    def test_modelo_pt_completo(self):
        self.assertEqual(self.nota("modelos/prompt-modelo.md"), 8)

    def test_idiomas(self):
        for idioma in ("en", "es"):
            for nome, minimo in (("depois.md", 8), ("../../modelos/%s/prompt-modelo.md" % idioma, 8)):
                caminho = RAIZ / "exemplos" / idioma / nome
                if not caminho.exists():
                    self.skipTest(f"{caminho} ainda não traduzido")
                texto = caminho.read_text(encoding="utf-8")
                self.assertEqual(sum(x["ok"] for x in checar_prompt.checar(texto)), minimo, str(caminho))
            antes = (RAIZ / "exemplos" / idioma / "antes.md").read_text(encoding="utf-8")
            self.assertLessEqual(sum(x["ok"] for x in checar_prompt.checar(antes)), 1, idioma)

    def test_colchetes_do_modelo_avisam(self):
        self.assertGreater(checar_prompt.colchetes((RAIZ / "modelos/prompt-modelo.md").read_text(encoding="utf-8")), 5)
        self.assertEqual(checar_prompt.colchetes((RAIZ / "exemplos/depois.md").read_text(encoding="utf-8")), 0)
        p = subprocess.run([sys.executable, "-I", str(RAIZ / "kit/checar_prompt.py"), str(RAIZ / "modelos/prompt-modelo.md")],
                           capture_output=True, text=True)
        self.assertIn("[colchetes]", p.stdout)

    def test_rotulo_minusculo_nao_conta(self):
        r = checar_prompt.checar("prova: rode e diga quantos")
        self.assertFalse(r[0]["ok"])

    def test_secao_sem_conteudo_exigido_falha(self):
        r = {x["id"]: x for x in checar_prompt.checar("PROVA: descreva o que acontece.")}
        self.assertFalse(r["prova"]["ok"])
        self.assertEqual(len(r["prova"]["falta"]), 2)

    def test_markdown_na_frente(self):
        r = {x["id"]: x for x in checar_prompt.checar("## **RECIBO:** nunca diga feito sem o link")}
        self.assertTrue(r["recibo"]["ok"])

    def test_cli_minimo_sai_1(self):
        p = subprocess.run([sys.executable, "-I", str(RAIZ / "kit/checar_prompt.py"), str(RAIZ / "exemplos/antes.md"),
                            "--minimo", "8"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        self.assertIn("nota: 0/8", p.stdout)

    def test_cli_json(self):
        p = subprocess.run([sys.executable, "-I", str(RAIZ / "kit/checar_prompt.py"), str(RAIZ / "exemplos/depois.md"),
                            "--json"], capture_output=True, text=True)
        self.assertEqual(json.loads(p.stdout)["nota"], 8)


class TestIdiomaChecador(unittest.TestCase):
    def test_detecta_en_es_pt(self):
        for idioma in ("en", "es"):
            texto = (RAIZ / "exemplos" / idioma / "depois.md").read_text(encoding="utf-8")
            self.assertEqual(checar_prompt.detectar_idioma(texto), idioma)
        self.assertEqual(checar_prompt.detectar_idioma((RAIZ / "exemplos/depois.md").read_text(encoding="utf-8")), "pt")

    def test_mensagens_em_ingles(self):
        p = subprocess.run([sys.executable, "-I", str(RAIZ / "kit/checar_prompt.py"), str(RAIZ / "exemplos/en/antes.md"),
                            "--idioma", "en"], capture_output=True, text=True)
        self.assertIn("score: 0/8", p.stdout)
        self.assertNotIn("dica", p.stdout)
        self.assertNotIn("seção", p.stdout)


class TestPreflight(unittest.TestCase):
    def rodar(self, *args):
        return subprocess.run([sys.executable, "-I", str(RAIZ / "kit/preflight.py"), *args],
                              capture_output=True, text=True, timeout=60)

    def test_demo_limpa_sai_0(self):
        p = self.rodar("--demo")
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertTrue(p.stdout.strip().endswith("4 ok, 0 falha, 0 aviso"))

    def test_demo_quebrada_sai_1(self):
        p = self.rodar("--demo", "--quebrar")
        self.assertEqual(p.returncode, 1)
        self.assertIn("SEGREDO ABERTO", p.stdout)
        self.assertIn("precos.json", p.stdout)
        self.assertIn("teste-rascunho.txt", p.stdout)

    def test_endereco_fora_do_ar_e_falha(self):
        p = self.rodar("--alvo", "http://127.0.0.1:9/")
        self.assertEqual(p.returncode, 1)


if __name__ == "__main__":
    unittest.main()
