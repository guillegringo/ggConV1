# V0: cápsula LED y horquilla estándar

La cápsula es la parte que lleva la electrónica. Se arma **una sola vez** y se usa con cualquier soporte V1, V2 o V3.

| Pieza | STL | Medidas | Impresión |
|---|---|---|---|
| Cabezal | `stl/capsula_cabezal.stl` | 46 × 18 × 20 mm | Frente para abajo, sin soportes |
| Tapa con pestaña | `stl/capsula_tapa.stl` | 46 × 18 × 14 mm | Plana, con la pestaña hacia arriba |

**Material por cápsula:** 3 LEDs IR de 5 mm, 1 resistencia de 22 Ω, 2 heat inserts M3, 2 tornillos M3×10 y un tramo de cable.

## Cómo se arma
1. Calentá los 2 heat inserts en las torretas del cabezal. Van del lado abierto.
2. Metá los 3 LEDs desde adentro hasta que el reborde haga tope en su alojamiento.
3. Soldalos **en serie**: la pata larga (ánodo, +) de uno va a la corta (cátodo, −) del siguiente. La resistencia va al ánodo del primero.
4. Pasá el cable por uno de los dos agujeros de la tapa:
   - El rojo (+5 V) va a la resistencia y el negro (GND) al cátodo del último LED.
   - Si la cápsula **no** es la última de la cadena, el cable que sigue sale por el otro agujero, empalmado en paralelo.
5. **Probá antes de cerrar.** Mirá los LEDs con la cámara del celular: tienen que verse violeta o blanco. En muchos celulares solo los muestra la cámara frontal.
6. Cerrá la tapa con 2 × M3×10.

## Horquilla estándar
Es la interfaz que comparten todos los soportes:
- La pestaña de la tapa mide 6,6 mm y entra entre dos orejas de 7 mm, con 0,2 mm de juego por lado.
- El eje está 28 mm detrás del frente de la cápsula.
- El tornillo es un **M3×16**: entra por la oreja con la cabeza embutida (3 mm) y rosca en un heat insert de la otra oreja.
- La inclinación útil es de ±25°. Apretá lo justo para que mantenga el ángulo: funciona como bisagra a fricción.

Si diseñás un soporte nuevo, usá `fork_solid()` y `fork_cut()` de `emisor_fc.py` y la cápsula va a encajar sola.

## Parámetros (en `emisor_fc.py`)
| Parámetro | Valor | Qué controla |
|---|---|---|
| `LED_HOLE` | 5,15 | Agujero para el LED de 5 mm. Subilo a 5,25 si entra muy duro |
| `LED_FLANGE_D` | 6,1 | Alojamiento del reborde del LED |
| `LED_X` | −9, 0, 9 | Separación entre LEDs |
| `CABLE_D` | 4,6 | Paso del cable. Medí el tuyo |
| `INSERT_D` | 4,2 | Agujero para el heat insert M3 |
