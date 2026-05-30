# Movimientos de inventario

Existen dos tipos de movimiento:
- **Entrada**: suma unidades al stock (compras, devoluciones de clientes).
- **Salida**: resta unidades del stock (ventas, mermas).

Reglas:
- Una salida nunca puede dejar el stock en negativo; si no hay suficiente stock,
  el movimiento se rechaza.
- Tras cada movimiento se recalcula el `stock_actual` y se evalúa si el medicamento
  quedó en bajo stock.
