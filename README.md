# Órdenes de Lentes · Odoo 17

Módulo de **Óptica Zamora** para dar seguimiento a la fabricación y entrega de lentes: reúne paciente, graduación, armazón, tratamientos, laboratorio, fechas y referencia de venta en una orden de trabajo.

**Autor:** Christian Torres PeeWee  
**Versión del módulo:** `17.0.1.0.0`  
**Modelo principal:** `optica.lente.orden`  
**Licencia declarada en el manifiesto:** LGPL-3

## Funciones

- Órdenes con folio automático, por ejemplo `OL/26/0001`.
- Tablero Kanban por estado, listado, formulario y calendario de entregas.
- Carga de la graduación más reciente del paciente como copia editable en la orden.
- Selección de armazón, lentes/tratamientos y laboratorio.
- Registro de medidas del armazón y observaciones.
- Consulta del total y saldo calculados desde la venta y sus facturas.
- Ticket de laboratorio en PDF.
- Pestaña **Pedidos** en contactos para consultar órdenes asignadas a ese contacto como laboratorio.

## Flujo de trabajo

| Estado | Acción habitual | Comportamiento del botón |
| --- | --- | --- |
| En espera | Crear y preparar la orden | Permite cargar la graduación más reciente. |
| En proceso | Enviar a laboratorio | Exige que haya un laboratorio asignado. |
| Por entregar | Recibido de laboratorio | Marca que los lentes están disponibles para entrega. |
| Entregado | Entregado | Rechaza un saldo calculado mayor que cero y registra la fecha real de entrega. |
| Retrabajo | Retrabajo | Disponible desde Por entregar o Entregado. |
| Cancelado | Cancelar | Disponible desde En espera, En proceso o Por entregar. |

**Enviar a laboratorio cambia el estado de la orden.** Este repositorio no implementa el envío de mensajes al laboratorio ni la creación automática de una orden de compra.

Las condiciones anteriores corresponden a los botones. El Kanban permite arrastrar tarjetas y el modelo no incorpora una validación equivalente en `write()`: mover directamente una tarjeta no garantiza ejecutar las comprobaciones ni registrar la fecha de entrega. Para el flujo operativo, utiliza los botones del formulario.

## Requisitos e instalación

Dependencias declaradas:

`base`, `sale`, `purchase`, `mail`, `portal`, `product` y `odoo_graduacion_paciente`.

Se requiere una instalación de **Odoo 17**, generación de PDF operativa y una versión compatible de `odoo_graduacion_paciente` que proporcione el modelo `optica.graduacion` y los campos consumidos por este módulo. Esta dependencia se obtiene por separado y puede requerir autorización del propietario.

### Nombre técnico de la carpeta

Aunque el repositorio se llama `orden_de_lentes`, las referencias actuales al reporte y al CSS usan **`Orden_de_lentes`**, con O mayúscula. Conserva ese nombre al instalar esta versión:

```bash
cd /ruta/a/custom-addons
git clone https://github.com/Bellako85/orden_de_lentes.git Orden_de_lentes
```

1. Incluye el directorio padre en `addons_path`.
2. Instala la dependencia `odoo_graduacion_paciente`.
3. Reinicia Odoo y actualiza la lista de aplicaciones.
4. Instala **Órdenes de Lentes**.
5. Abre **Óptica → Órdenes de Lentes**.

No renombres la carpeta de una instalación existente sin revisar sus identificadores externos. El nombre técnico participa en la resolución de vistas, reportes y recursos.

## Preparación y uso

1. Crea o revisa el contacto del paciente y su graduación.
2. Asigna a los contactos de los laboratorios una etiqueta llamada exactamente **Laboratorio**; el selector utiliza ese nombre para filtrarlos.
3. Crea una orden y selecciona un paciente y una fecha prometida.
4. Vincula la orden de venta correspondiente, si existe.
5. Selecciona laboratorio, armazón y lentes/tratamientos.
6. Revisa la graduación copiada y completa las medidas del armazón.
7. Guarda e imprime el ticket.
8. Avanza mediante los botones de laboratorio, recepción y entrega.

Al abrir el módulo se activa por defecto el filtro **Atrasados**. Retíralo para ver todas las órdenes. El filtro selecciona registros con fecha prometida anterior a hoy y estado distinto de Entregado; también puede incluir órdenes canceladas o en retrabajo.

## Graduación y medidas

La orden conserva una **copia de los valores**, independiente de cambios posteriores en la graduación de referencia.

| Grupo | Datos |
| --- | --- |
| Refracción OD/OI | Esfera, cilindro y eje. |
| Adición | Un valor compartido para ambos ojos. |
| Centrado | DIP, DNP OD, DNP OI y altura de centro óptico. |
| Armazón | Diámetros horizontal y vertical, efectivo, puente y diámetro sugerido. |
| Notas | Observaciones copiadas desde la graduación y editables en la orden. |

La carga se realiza al seleccionar el paciente en el formulario o al pulsar **Cargar Graduación**. Ambos mecanismos buscan la más reciente por `fecha desc`; el botón no carga necesariamente el registro elegido manualmente en “Graduación de referencia”.

Cambiar únicamente la referencia no copia sus valores. Las creaciones mediante API tampoco ejecutan automáticamente el `onchange` del formulario.

Si cambias a un paciente sin graduación, el código actual no limpia los valores previos. Comprueba siempre paciente, referencia y datos antes de emitir el ticket. Las conversiones de datos no numéricos utilizan cero como respaldo.

Las medidas del armazón se introducen manualmente: este módulo no calcula automáticamente el diámetro sugerido ni realiza transposición de la receta.

## Total, saldo y entrega

El cálculo es informativo y depende de la venta vinculada:

| Situación | Total mostrado | Saldo mostrado |
| --- | --- | --- |
| Sin venta | Cero | Cero |
| Venta sin facturas | Total de la venta | Total de la venta |
| Venta con facturas | Suma de totales de facturas que no estén en borrador ni canceladas; si la suma es cero, total de la venta | Suma de sus saldos pendientes |

El botón **Entregado** bloquea únicamente cuando `saldo_pendiente > 0`.

Por tanto, un saldo cero no siempre demuestra pago: una orden sin venta, o una venta que solo tenga facturas en borrador/canceladas, puede mostrar cero pendiente. Revisa la documentación contable antes de entregar.

El módulo no registra pagos, no concilia facturas y no implementa conversión de divisas. La moneda de la orden de lentes toma por defecto la moneda de la compañía.

## Ticket de laboratorio

El botón **Imprimir Ticket** genera un reporte QWeb PDF con:

- Folio, paciente, laboratorio, armazón y fecha prometida.
- Estado y productos de lentes/tratamientos.
- Graduación OD/OI y adición.
- Datos de centrado cuando tienen valor.
- Medidas del armazón y observaciones.
- Fecha y hora de generación.

Los valores ópticos positivos se muestran con signo `+` y dos decimales; los ejes se muestran sin decimales. El formateador actual representa el cero como `-`, tanto en potencias como en ejes: verifica esa convención al interpretar el ticket.

El reporte incluye textos fijos de **Óptica Zamora**. Revisa la presentación, tipografías e iconos en el motor PDF de tu instalación.

## Vistas y permisos

- **Kanban:** agrupación por estado y tarjetas con paciente, laboratorio, productos, saldo y fecha.
- **Lista:** consulta de órdenes y búsqueda por folio, paciente o laboratorio.
- **Calendario:** organización por fecha prometida; no implica sincronización con Google Calendar.
- **Contactos → Pedidos:** relación mediante `lab_partner_id`; muestra las órdenes del laboratorio, no el historial del paciente.

| Grupo | Leer | Crear | Modificar | Eliminar |
| --- | --- | --- | --- | --- |
| Usuario interno (`base.group_user`) | Sí | Sí | Sí | No |
| Administración (`base.group_system`) | Sí | Sí | Sí | Sí |

El repositorio no incluye reglas de registro para separar órdenes por compañía. Aunque el modelo hereda `portal.mixin`, no hay controladores ni páginas de portal propias en este módulo.

## Estructura del código

| Ruta | Contenido |
| --- | --- |
| `__manifest__.py` | Dependencias, vistas, reporte y recursos. |
| `models/lente_orden.py` | Orden, estados, graduación, importes y acciones. |
| `models/res_partner.py` | Relación de pedidos por laboratorio. |
| `data/sequence.xml` | Folios `OL/AA/0001`; secuencia compartida sin compañía asignada. |
| `views/lente_orden_views.xml` | Formulario, Kanban, lista, calendario, filtros y menús. |
| `views/res_partner_views.xml` | Pestaña Pedidos. |
| `report/` | Acción y plantilla del ticket PDF. |
| `security/ir.model.access.csv` | Permisos por grupo. |
| `static/src/css/lente_orden_flow.css` | Estilo del tablero. |

Los archivos `*.save` no están declarados como datos del módulo y no se cargan durante la instalación.

## Comprobación básica

En una base de pruebas:

1. Crea una orden y comprueba el folio.
2. Selecciona un paciente con graduación y compara los datos copiados.
3. Prueba un paciente sin graduación para detectar valores heredados de la selección anterior.
4. Comprueba que Enviar a laboratorio exige un laboratorio.
5. Vincula una venta con saldo real y verifica que el botón Entregado la bloquea.
6. Completa el pago y comprueba la entrega y su fecha.
7. Genera un PDF y revisa signos, ceros, medidas, observaciones y saltos de página.
8. Retira el filtro Atrasados y confirma que se ven las órdenes nuevas.

Esta documentación describe el código revisado; no constituye una certificación de instalación o ejecución en otra base de Odoo.

## Licencia

El [manifiesto](__manifest__.py) declara **LGPL-3**. El árbol revisado no incluye un archivo `LICENSE` con el texto completo. Las dependencias conservan sus propias licencias y condiciones de acceso.

## Apoya el proyecto ⭐

¿Te sirvió este módulo? Déjale una estrella al repositorio. Detrás hay muchas noches de desarrollo y pruebas en una óptica real.

**El `git clone` es gratis; la estrellita también.** 😄
