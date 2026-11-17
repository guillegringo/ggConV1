# ggCon V1: lightgun GUN4IR casera

Una pistola de luz para GUN4IR con Pro Micro USB-C, cámara IR DFRobot SEN0158, gatillo con microswitch y 4 botones, más los 4 emisores IR que van en la tele. Todo se imprime en una Bambu Lab A1 mini.
Esta versión es la básica: no tiene solenoide ni vibración.

![pistola](pistola/renders/02_tres_cuartos.png)

| | |
|---|---|
| ![interior](pistola/renders/05_interior_34.png) | ![emisor](emisores_ir/V2-gancho/v2_tele_finita.png) |

Video del ensamblado: [`pistola/renders/ensamblado.mp4`](pistola/renders/ensamblado.mp4)

## Estructura
```
pistola/        modelo CAD (FreeCAD), renders y video (Blender), STL listos para imprimir
emisores_ir/    emisores IR modulares: cápsula + 5 soportes, circuito, guía por escenario
firmware/       sketch de prueba de cámara y botones (antes de cargar GUN4IR)
```
Los modelos son paramétricos. Si cambiás una medida arriba del script, regenerás con:
```
"D:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe" pistola\pistola_fc.py
"D:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe" emisores_ir\emisor_fc.py
"D:\Program Files\Blender Foundation\Blender 5.0\blender.exe" -b -P pistola\render_blender.py -- stills
```

---

## Lista de compras
Hay dos tiendas de Buenos Aires. **Emakers** tiene casi todo, incluidos los LEDs IR, así que con un solo viaje alcanza. **Candy-HO** sirve de alternativa para lo que falte.
Precios y stock verificados el 17/11/2026. Pueden cambiar.

### Opción recomendada: todo en Emakers
**Emakers**: Alsina 1761, Congreso, CABA. Abre de lunes a viernes de 9 a 18. Tel. 4372-9492. [emakers.com.ar](https://www.emakers.com.ar)

| Qué | Cant. | Producto | Precio | Stock |
|---|---|---|---|---|
| LEDs IR de 940 nm y 5 mm | **2 packs** (20 LEDs) | [Led Infrarrojo Emisor 5mm x10](https://www.emakers.com.ar/tienda/diodos-modulos-y-matrices-led/diodos-led-unitarios/led-infrarrojo-emisor-5mm-de-diametro-x10-unidades) | $872 c/pack | ✅ |
| Resistencias de 100 Ω (una por LED) | 1 kit x50 | [Kit 50 resistencias 100 Ω 1/4 W 1%](https://www.emakers.com.ar/tienda/componentes-electronicos/resistencias/kit-50-resistencias-100-ohm-14w-metal-film-con-1-tolerancia) | $1.453 | ✅ |
| Pulsadores 12×12 (A, B, Start, Select + 1 de repuesto) | 5 | [Tact Switch 4 patas 12x12x7.5](https://www.emakers.com.ar/tienda/componentes-electronicos/pulsadores-interruptores/tact-switch-4-patas-12x12x75-em5-5720) | $203 c/u | ✅ |
| Termocontraíble | 1 kit | [Kit termocontraíble 127 piezas](https://www.emakers.com.ar/tienda/componentes-electronicos/kits-de-componentes/kit-termocontraible-127pcs-negro-varias-medidas) | $3.872 | ✅ |
| Cable para alimentar y unir los emisores | 4 | [Cable de carga micro USB de 1 m](https://www.emakers.com.ar/tienda/modulos-alimentacion-y-pilas/cargadores/cable-de-carga-microusb-de-1m-em1109). Se corta y se usan los hilos rojo y negro. Uno conserva la ficha USB-A para enchufar | $2.904 c/u | ✅ |
| Microswitch del gatillo | ver ⚠️ | [Micro Switch final de carrera 5 A, 20×10×6 mm](https://www.emakers.com.ar/tienda/componentes-electronicos/pulsadores-interruptores/micro-switch-final-de-carrera-5a-250v-cnc-leva-corta) | $812 | ✅ |

**Total en Emakers:** unos **$19.700**, más el microswitch.

⚠️ **Microswitch:** el de Emakers mide **20 × 10 × 6 mm**, y la pistola está diseñada para uno **subminiatura de 12,8 × 6,5 × 5,8 mm**. Hay dos caminos:
- Adaptar el alojamiento de la pistola al de 20 × 10 mm, que es el tamaño más fácil de conseguir. Es un cambio de parámetros en `pistola/pistola_fc.py`.
- Comprar el subminiatura en Candy-HO (ver abajo).

⚠️ **Pulsadores:** los de Emakers miden 7,5 mm de alto y los del diseño 7,3 mm. Antes de imprimir, medí cuánto sobresale el vástago del cuerpo y ajustá `TACT_BODY` y `TACT_STEM` en `pistola/pistola_fc.py`.

**No hay en Emakers:** cinta doble faz. Sirve cualquiera de espuma de librería o ferretería, o la de Candy-HO.

### Alternativa o complemento: Candy-HO
| Qué | Producto | Precio |
|---|---|---|
| Microswitch subminiatura del gatillo | [Microswitch SPDT con palanca 1A 125V, SKU 8184](https://candy-ho.com/producto/microswitch-final-de-carrera-spdt-palanca-roller-1a-125v-arduino/). Antes de comprar, confirmá en el local que mida unos 12,8 × 6,5 × 5,8 mm | $590 |
| Pulsadores 12×12×7,3 | [Tact Switch B3F-4055, SKU 2506](https://candy-ho.com/producto/boton-switch-tact-b3f-4055-push-button-generico-12x12x7-3/) | $190 c/u |
| Resistencias de 100 Ω x10 | [Buscar "resistencia 100 ohm"](https://candy-ho.com/?s=resistencia+100+ohm&post_type=product) (SKU 1403 o 1429) | $410 |
| Cinta doble faz | [Bifaz de 12 mm × 10 m, SKU 4920](https://candy-ho.com/producto/cinta-adhesiva-bifaz-doble-faz-12-mm-x-10-mts/) | $2.990 |
| Termocontraíble | [Kit de 127 piezas, SKU 6164](https://candy-ho.com/producto/kit-termocontraible-tubos-7-tamanos-combo-127-piezas/) | $4.770 |
| Cable USB tipo C de 1 m | [SKU 6601](https://candy-ho.com/producto/cable-usb-tipo-c-1-metro-generico/) | $2.732 |
| *Opcional:* conector para desenchufar cada emisor | [JST RCY de 2 pines, SKU 4025](https://candy-ho.com/producto/conector-jst-rcy-2-pines-pitch-2-5mm-siliconado-10cm/) | $490 c/u |
| *Opcional:* estaño | [Estaño 60/40 de 1 mm, 100 g, SKU 6179](https://candy-ho.com/producto/estano-en-rollo-1mm-60-40-0-1kg-soldadura-rollo-100gr/) | $15.561 |

Candy-HO **no tiene LEDs IR**. Esos van sí o sí en Emakers.

### Sobre los LEDs IR
- La comunidad de GUN4IR recomienda el **Osram SFH 4547**, pero en Argentina no se consigue sin traerlo de afuera.
- Los genéricos de 940 nm de Emakers alcanzan para jugar a 2 o 3 m. Antes de armar las 4 cápsulas, **probá una sola** con GUN4IR utils.
- Con estos LEDs (1,7 V, 50 mA) cada LED va con **su propia resistencia de 100 Ω**, unos 35 mA cada uno. Está explicado en [V0-capsula](emisores_ir/V0-capsula/README.md).

### Lo que ya tenés
- Cámara DFRobot SEN0158
- Pro Micro USB-C
- Heat inserts M3: **22** en total (10 para la pistola y 12 para los emisores)
- Tornillos M3:
  - **18 × M3×10**: 9 para la pistola, 1 para el ajuste del gatillo y 8 para las tapas de los emisores
  - **1 × M3×25**: eje del gatillo
  - **4 × M3×16**: bisagra de cada emisor
- Licencia DIY de GUN4IR ([gun4ir.com](https://gun4ir.com))

---

## Pistola
Está modelada en FreeCAD, con lofts anatómicos en el mango: palm swell, 3 apoyos de dedos y la base ensanchada. Tiene cola de castor, corredera con el lomo redondeado, estrías, miras y riel. Mide 174 × 125 × 30 mm.

| Pieza | Medidas | Encastre |
|---|---|---|
| DFRobot SEN0158 | Plano oficial: Ø16,45 × 34,1 mm + cola de Ø7,69 × 7 mm | Va en un caño de Ø16,7, con labio adelante y escalón atrás |
| Pro Micro USB-C | Placa de 35,0 × 18,0 × 1,6 mm, USB-C de 9,0 × 3,3 mm que asoma 1,0 mm | Va sobre rieles con tope. El USB-C sale por la base del mango |
| Microswitch | 12,8 × 6,5 × 5,8 mm | Queda encerrado entre las dos mitades. El gatillo tiene un tornillo M3 de ajuste |
| Tact 12×12 | B3F-4055 | Entra a presión con clic, con un botón impreso encima |

Antes de imprimir, **medí con calibre** la cámara y el microswitch. Si no coinciden, ajustá `CAM_D` y `SW_*` en `pistola/pistola_fc.py`.

**Cableado**

| Función | Pin del Pro Micro |
|---|---|
| Cámara: rojo VCC / negro GND / amarillo SDA / verde SCL | VCC / GND / **2** / **3** |
| Gatillo (COM + NO del microswitch) | 4 → GND |
| A / B / Start / Select | 5 / 6 / 7 / 8 → GND |

**Impresión**
- Las mitades van con la cara exterior sobre la cama, que es como vienen los STL.
- Usá soportes **tree** solo desde la cama, para el guardamonte, la cola de castor y la curva del mango.
- PLA o PETG, 4 perímetros y 15 % de relleno gyroid.

**Armado**
1. Probá cámara y botones con `firmware/test_hardware`.
2. Poné los heat inserts en la mitad izquierda.
3. Meté la cámara, el Pro Micro, el gatillo con su tornillo de ajuste, el microswitch y los botones.
4. Cableá todo.
5. Cerrá con 9 × M3×10 y el eje M3×25, todos desde la derecha.

---

## Emisores IR: sistema modular
Son 4 **cápsulas** iguales, cada una con **3 LEDs IR de 5 mm**. Con los LEDs de Emakers, cada LED lleva su propia resistencia de 100 Ω. Cada cápsula se monta sobre el **soporte** que corresponda a tu setup: tele finita, tele gruesa, tele colgada, proyector o arcade. Si cambiás de setup, cambiás solo el soporte y no volvés a soldar.

| | | |
|---|---|---|
| ![](emisores_ir/V2-gancho/v2_tele_finita.png) | ![](emisores_ir/V3-pared/v3_proyector.png) | ![](emisores_ir/V4-arcade/v4_arcade_frente.png) |

- **[Índice de los emisores IR](emisores_ir/README.md)**: las 5 versiones (base, gancho, pared, arcade y hub) y el circuito.
- **[Guía por escenario](emisores_ir/escenarios.md)**: qué soporte usar en cada setup y cuánto inclinar las cápsulas.
- **[Ideas futuras](emisores_ir/ideas-futuras.md)**

**Antes de cerrar las cápsulas, probá los LEDs.** La luz IR no se ve a simple vista, pero la cámara del celular sí la muestra (en muchos celulares solo la cámara frontal). Si conseguís LEDs con otra tensión de trabajo (Vf), recalculá la resistencia: R = (5 − 3·Vf) / I, con I entre 40 y 70 mA.
