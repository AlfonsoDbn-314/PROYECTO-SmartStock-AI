# Bodegas y lotes

El inventario se organiza por **bodegas** (almacenes físicos) y **lotes**.

- Cada **medicamento** del catálogo puede tener varios **lotes**.
- Cada **lote** está almacenado en una **bodega**, tiene su propio número de
  lote, fecha de caducidad y stock.
- El stock total de un medicamento es la suma del stock de todos sus lotes.

Bodegas habituales:
- BOD-CENTRAL: Bodega Central.
- BOD-FRIO: Cámara de Frío (refrigerados 2-8°C), p. ej. insulina.
- BOD-SUR / BOD-NORTE: sucursales.

Rotación **FEFO** (First Expired, First Out): siempre se despacha primero el
lote con la fecha de caducidad más próxima.
