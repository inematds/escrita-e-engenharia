# Escrita e Engenharia — prompt com prova

[![Prompt com prova](guia/assets/banner.jpg)](https://inematds.github.io/escrita-e-engenharia/guia/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## O que é

Este kit ensina a escrever pedidos para a IA (o “prompt”) de um jeito que obriga a IA a **provar** o que fez, em vez de só dizer “pronto”. São 8 técnicas de escrita que qualquer pessoa usa no ChatGPT, no Claude ou no Gemini, e 9 soluções de engenharia para quem monta agentes e aplicativos com IA. Vem com um modelo de pedido para copiar, exercícios, um checador que dá nota de 0 a 8 ao seu pedido e o código das soluções em Python. Para usar as técnicas basta ler; para o checador e o código, só Python 3.

## 📖 Guia de uso

Guia completo (landing + passo a passo): **https://inematds.github.io/escrita-e-engenharia/guia/**

## As 8 técnicas de escrita

| # | Técnica | Seção no pedido |
|---|---|---|
| 1 | Feche com a prova (rodar e devolver números) | `PROVA:` |
| 2 | “Pronto” só com checagem | `PRONTO:` |
| 3 | Avise onde costuma errar | `ONDE COSTUMA ERRAR:` |
| 4 | Um dono para cada coisa | `UM DONO:` |
| 5 | Número sensível com nome | `NOME = valor` |
| 6 | Recibo antes de “feito” | `RECIBO:` |
| 7 | Texto de fora é dado, não ordem | `TEXTO DE FORA:` |
| 8 | Lição vira regra | `LIÇÕES:` |

## As 9 soluções de engenharia

1. Resposta na hora, trabalho depois (`kit/rotas.py`)
2. Sinal de vida durante a espera (`kit/rotas.py`)
3. Resultado em blocos que chegam aos pedaços, conserto de no máximo 2 vezes (`kit/blocos.py`)
4. Mudar só o que mudou (`kit/blocos.py`)
5. Barreira logo depois de gerar (`kit/guarda.py`)
6. Checagem de ponta a ponta que cresce com cada erro (`kit/preflight.py`)
7. A fonte manda, a cópia sai dela
8. Não passar por cima da mão da pessoa
9. Ensaio sem rastro + recibo de custo (`kit/preflight.py`, `kit/recibo.py`)

## Uso rápido

```bash
git clone https://github.com/inematds/escrita-e-engenharia.git
cd escrita-e-engenharia
python3 -m unittest -q                              # 47 testes, OK
python3 kit/checar_prompt.py exemplos/antes.md      # nota: 0/8
python3 kit/checar_prompt.py exemplos/depois.md     # nota: 8/8
python3 kit/checar_prompt.py meu-prompt.md --minimo 8
python3 kit/preflight.py --demo                     # 4 ok, 0 falha, 0 aviso
python3 kit/preflight.py --demo --quebrar           # 1 ok, 3 falha (sai 1)
```

Modelo para copiar: [`modelos/prompt-modelo.md`](modelos/prompt-modelo.md) (também em [`modelos/en/`](modelos/en/prompt-modelo.md) e [`modelos/es/`](modelos/es/prompt-modelo.md)).
Skill para o Claude Code: `cp -r skill/revisar-prompt ~/.claude/skills/`.

## O processo, do início ao fim

| # | Passo | Comando | Quem |
|---|---|---|---|
| 1 | Escrever o pedido a partir do modelo | copiar `modelos/prompt-modelo.md` | 🧠 você |
| 2 | Conferir a nota do pedido | `python3 kit/checar_prompt.py meu-prompt.md --minimo 8` | ⚙️ script |
| 3 | Mandar o pedido para a IA | colar no chat ou no agente | 🧠 você |
| 4 | Exigir a prova (números) e o recibo na resposta | já está no pedido (`PROVA:`, `RECIBO:`) | 🤖 IA |
| 5 | Conferir o sistema no ar | `python3 kit/preflight.py --alvo URL --pasta DIR --segredo .env` | ⚙️ script |
| 6 | Erro real → linha nova em `LIÇÕES:` e checagem nova em `CHECAGENS_EXTRA` | editar o pedido e o `preflight.py` | 🧠 você |

## Licença

MIT. Kit grátis do [INEMA.CLUB](https://inema.club).
