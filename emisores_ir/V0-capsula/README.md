# V0: cápsula LED y horquilla estándar

La cápsula es la parte que lleva la electrónica. Se arma **una sola vez** y se usa con cualquier soporte V1, V2 o V3.

| Pieza | STL | Medidas | Impresión |
|---|---|---|---|
| Cabezal | `capsula_cabezal.stl` | 46 × 18 × 20 mm | Frente para abajo, sin soportes |
| Tapa con pestaña | `capsula_tapa.stl` | 46 × 18 × 14 mm | Plana, con la pestaña hacia arriba |

**Material por cápsula:** 3 LEDs IR de 5 mm, 3 resistencias de 100 Ω (opción A) o 1 de 22 Ω (opción B), 2 heat inserts M3, 2 tornillos M3×10 y un tramo de cable.

## Circuito: elegí según tus LEDs
Primero medí la caída de tensión de un LED con el tester en modo diodo, o fijate el dato "Vf" en la publicación.

**Opción A: una resistencia de 100 Ω por LED.** Es la que conviene con los LEDs genéricos de Emakers (1,7 V, 50 mA máximo).
```
+5V ──┬── 100Ω ──►|── LED1 ──┐
      ├── 100Ω ──►|── LED2 ──┤
      └── 100Ω ──►|── LED3 ──┴── GND
```
- Cada LED recibe unos 35 mA. Anda aunque caigan 1,7 V por LED.
- La cápsula consume unos 105 mA y las 4 cápsulas unos 420 mA, que entrega cualquier cargador USB.

**Opción B: los 3 LEDs en serie con una sola resistencia de 22 Ω.** Solo sirve si cada LED cae **1,35 V o menos**, como los TSAL o SFH 4547 a corriente media. Con el SFH 4547, la comunidad de GUN4IR usa 5,6 Ω.
```
+5V ── 22Ω ──►|──►|──►|── GND        (unos 45-50 mA, las 4 cápsulas suman unos 200 mA)
```
- Si los LEDs caen más tensión, tres en serie no llegan a encender bien con 5 V.

## Cómo se arma
1. Calentá los 2 heat inserts en las torretas del cabezal. Van del lado abierto.
2. Metá los 3 LEDs desde adentro hasta que el reborde haga tope en su alojamiento.
3. Soldalos según el circuito que elegiste. En la **opción A**, cada LED lleva su resistencia de 100 Ω en la pata larga (ánodo, +) y todas las patas cortas (cátodo, −) van juntas a GND. En la **opción B**, van en serie: la pata larga de uno con la corta del siguiente, y la resistencia de 22 Ω al ánodo del primero.
4. Pasá el cable por uno de los dos agujeros de la tapa:
   - El rojo (+5 V) va a las resistencias y el negro (GND) a los cátodos.
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

## Archivos en esta carpeta
| Archivo | Qué es |
|---|---|
| `capsula_cabezal.stl` | Cápsula: cabezal (la misma de [V0](../V0-capsula/README.md), copiada para que tengas todo acá) |
| `capsula_tapa.stl` | Cápsula: tapa con pestaña de bisagra (copia de V0) |

**Se imprimen 4:** 4 × cabezal + 4 × tapa. Los soportes están en las carpetas V1 a V3.
