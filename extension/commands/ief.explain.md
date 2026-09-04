---
name: "ief.explain"
description: "El linaje completo de una regla: de dónde viene, qué reemplazó, quién la sostiene"
---

# Explicar una regla (`/speckit.ief.explain`)

## Propósito

Responder la pregunta más cara de un proyecto largo: **¿por qué el sistema hace esto?**

## Por qué existe

La información ya estaba, pero repartida: la procedencia en el id y en `_origen`, el
motivo en `rationale`, la cadena en `supersedes`, el respaldo en `evidence`. Reunirla es
la diferencia entre **tener datos y tener una respuesta**.

El caso que lo justifica es el reencuentro: seis meses después alguien pregunta por qué
se descartan ciertos pedidos, y la respuesta honesta —«ya no se descartan, eso lo cambió
el incremento 002»— exige leer tres archivos y el historial.

## Uso

```bash
python core/scripts/verify_frame.py --mode explain --rule RUL-001-001
```

Busca tanto en las reglas vigentes del proyecto como en las **propuestas** que aún viven
dentro de un incremento sin promover. Si el id no existe, lista los que sí.

## Qué verás

```
  RUL-001-001
  ======================================================================
  Un pedido sin cliente se descarta

  estado    : superseded   (rige todo el proyecto)
  gobierna  : pedidos
  nace en   : 001_ingesta   (promovida el 2026-09-03)

  POR QUE EXISTE
    El 3% del historico no tiene cliente y son pruebas del ERP

  LINAJE
    SUPERADA por RUL-002-001   Un pedido sin cliente NO se descarta...
    -> esta regla ya NO rige. La vigente es RUL-002-001

  QUE LA SOSTIENE
    nada declarado — la regla no cita evidencia
```

## Lo que hay que leer con cuidado

- **`-> esta regla ya NO rige`** es la línea importante. Una regla superada no se borra
  —el rastro es justo lo que hace útil el historial— pero seguir aplicándola es el error
  que este comando existe para evitar.
- **«nada declarado»** no significa que la regla sea falsa; significa que nadie escribió
  qué la sostiene. Es una deuda, y conviene verla.
