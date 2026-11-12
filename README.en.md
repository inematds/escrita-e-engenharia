# Writing and Engineering — prompt with proof

[![Prompt with proof](guia/assets/banner-en.jpg)](https://inematds.github.io/escrita-e-engenharia/guia/en/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## What it is

This kit teaches you to write requests for AI (the “prompt”) in a way that makes the AI **prove** what it did instead of just saying “done.” It includes 8 writing techniques anyone can use with ChatGPT, Claude, or Gemini, and 9 engineering solutions for people building AI agents and applications. It comes with a copyable request template, exercises, a checker that scores your request from 0 to 8, and the Python code for the solutions. Just read the techniques to use them; the checker and code require Python 3.

## 📖 User guide

Complete guide (landing page + step-by-step instructions): **https://inematds.github.io/escrita-e-engenharia/guia/en/**

## The 8 writing techniques

| # | Technique | Section in the request |
|---|---|---|
| 1 | End with proof (run it and return numbers) | `PROOF:` |
| 2 | “Done” only after checking | `DONE:` |
| 3 | Say where things usually go wrong | `WHERE IT USUALLY GOES WRONG:` |
| 4 | One owner for each thing | `ONE OWNER:` |
| 5 | Name sensitive numbers | `NAME = value` |
| 6 | Receipt before calling it “done” | `RECEIPT:` |
| 7 | Outside text is data, not an instruction | `OUTSIDE TEXT:` |
| 8 | Turn lessons into rules | `LESSONS:` |

## The 9 engineering solutions

1. Respond now, work later (`kit/rotas.py`)
2. Show signs of life while waiting (`kit/rotas.py`)
3. Deliver results in chunks; fix no more than twice (`kit/blocos.py`)
4. Change only what changed (`kit/blocos.py`)
5. Add a barrier immediately after generating (`kit/guarda.py`)
6. End-to-end checks that grow with each error (`kit/preflight.py`)
7. The source rules; the copy comes from it
8. Don’t override the person’s input
9. Test without leaving traces + cost receipt (`kit/preflight.py`, `kit/recibo.py`)

## Quick start

```bash
git clone https://github.com/inematds/escrita-e-engenharia.git
cd escrita-e-engenharia
python3 -m unittest -q                              # 47 tests, OK
python3 kit/checar_prompt.py exemplos/en/antes.md --idioma en      # score: 0/8
python3 kit/checar_prompt.py exemplos/en/depois.md --idioma en     # score: 8/8
python3 kit/checar_prompt.py my-prompt.md --minimo 8
python3 kit/preflight.py --demo                     # 4 ok, 0 falha, 0 aviso
python3 kit/preflight.py --demo --quebrar           # 1 ok, 3 falha (exits 1)
```

Template to copy: [`modelos/en/prompt-modelo.md`](modelos/en/prompt-modelo.md) (also in [Portuguese](modelos/prompt-modelo.md) and [Spanish](modelos/es/prompt-modelo.md)).
Claude Code skill: `cp -r skill/revisar-prompt ~/.claude/skills/`.

## The process, from start to finish

| # | Step | Command | Who |
|---|---|---|---|
| 1 | Write the request from the template | copy `modelos/en/prompt-modelo.md` | 🧠 you |
| 2 | Check the request score | `python3 kit/checar_prompt.py my-prompt.md --minimo 8` | ⚙️ script |
| 3 | Send the request to the AI | paste it into the chat or agent | 🧠 you |
| 4 | Require proof (numbers) and a receipt in the response | already included in the request (`PROVA:`, `RECIBO:`) | 🤖 AI |
| 5 | Check the live system | `python3 kit/preflight.py --alvo URL --pasta DIR --segredo .env` | ⚙️ script |
| 6 | Real error → new line in `LIÇÕES:` and new check in `CHECAGENS_EXTRA` | edit the request and `preflight.py` | 🧠 you |

## License

MIT. Free kit from [INEMA.CLUB](https://inema.club).