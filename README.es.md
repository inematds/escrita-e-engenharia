# Escritura e Ingeniería — prompt con evidencia

[![Prompt con evidencia](guia/assets/banner-es.jpg)](https://inematds.github.io/escrita-e-engenharia/guia/es/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## Qué es

Este kit enseña a escribir pedidos para la IA (el “prompt”) de una manera que obliga a la IA a **demostrar** lo que hizo, en vez de solo decir “listo”. Son 8 técnicas de escritura que cualquiera puede usar en ChatGPT, Claude o Gemini, y 9 soluciones de ingeniería para quienes crean agentes y aplicaciones con IA. Incluye un modelo de pedido para copiar, ejercicios, un verificador que califica tu pedido de 0 a 8 y el código de las soluciones en Python. Para usar las técnicas basta con leer; para el verificador y el código, solo necesitas Python 3.

## 📖 Guía de uso

Guía completa (landing + paso a paso): **https://inematds.github.io/escrita-e-engenharia/guia/es/**

## Las 8 técnicas de escritura

| # | Técnica | Sección en el pedido |
|---|---|---|
| 1 | Termina con la prueba (ejecutar y devolver números) | `PRUEBA:` |
| 2 | “Listo” solo después de verificar | `LISTO:` |
| 3 | Avisa dónde suele fallar | `DÓNDE SUELE FALLAR:` |
| 4 | Un dueño para cada cosa | `UN DUEÑO:` |
| 5 | Número sensible con nombre | `NOMBRE = valor` |
| 6 | Recibo antes de “hecho” | `RECIBO:` |
| 7 | El texto externo es un dato, no una orden | `TEXTO DE FUERA:` |
| 8 | Una lección se convierte en regla | `LECCIONES:` |

## Las 9 soluciones de ingeniería

1. Respuesta inmediata, trabajo después (`kit/rotas.py`)
2. Señal de vida durante la espera (`kit/rotas.py`)
3. Resultado en bloques que llegan por partes, reparación de como máximo 2 veces (`kit/blocos.py`)
4. Cambiar solo lo que cambió (`kit/blocos.py`)
5. Barrera justo después de generar (`kit/guarda.py`)
6. Verificación de punta a punta que crece con cada error (`kit/preflight.py`)
7. La fuente manda; la copia se genera a partir de ella
8. No pasar por encima de la persona
9. Ensayo sin rastro + recibo de costo (`kit/preflight.py`, `kit/recibo.py`)

## Uso rápido

```bash
git clone https://github.com/inematds/escrita-e-engenharia.git
cd escrita-e-engenharia
python3 -m unittest -q                              # 47 pruebas, OK
python3 kit/checar_prompt.py exemplos/es/antes.md --idioma es      # nota: 0/8
python3 kit/checar_prompt.py exemplos/es/depois.md     # nota: 8/8
python3 kit/checar_prompt.py mi-prompt.md --minimo 8
python3 kit/preflight.py --demo                     # 4 ok, 0 falha, 0 aviso
python3 kit/preflight.py --demo --quebrar           # 1 ok, 3 falha (sale con 1)
```

Modelo para copiar: [`modelos/es/prompt-modelo.md`](modelos/es/prompt-modelo.md) (también en [portugués](modelos/prompt-modelo.md) y [inglés](modelos/en/prompt-modelo.md)).
Skill para Claude Code: `cp -r skill/revisar-prompt ~/.claude/skills/`.

## El proceso, de principio a fin

| # | Paso | Comando | Quién |
|---|---|---|---|
| 1 | Escribir el pedido a partir del modelo | copiar `modelos/es/prompt-modelo.md` | 🧠 tú |
| 2 | Revisar la calificación del pedido | `python3 kit/checar_prompt.py mi-prompt.md --minimo 8` | ⚙️ script |
| 3 | Enviar el pedido a la IA | pegarlo en el chat o en el agente | 🧠 tú |
| 4 | Exigir la prueba (números) y el recibo en la respuesta | ya está en el pedido (`PRUEBA:`, `RECIBO:`) | 🤖 IA |
| 5 | Revisar el sistema en funcionamiento | `python3 kit/preflight.py --alvo URL --pasta DIR --segredo .env` | ⚙️ script |
| 6 | Error real → nueva línea en `LECCIONES:` y nueva verificación en `CHECAGENS_EXTRA` | editar el pedido y `preflight.py` | 🧠 tú |

## Licencia

MIT. Kit gratuito de [INEMA.CLUB](https://inema.club).