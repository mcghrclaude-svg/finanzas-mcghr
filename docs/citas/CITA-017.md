# CITA-017 -- Safe area en iOS: sin env(safe-area-inset-*) los toques bajo el notch se pierden

**Frecuencia:** 1 vez detectada (sesion 2026-08-16, pwa-gastos, prueba en iPhone real)
**Nivel:** 3-CONTEXTO

**Error:**
`pwa-gastos/index.html` ya tenia `viewport-fit=cover` y
`apple-mobile-web-app-status-bar-style=black-translucent`, que hacen que el
contenido se dibuje edge-to-edge, por debajo del notch/Dynamic Island y de
la home indicator bar. Sin compensar ese espacio con
`env(safe-area-inset-*)`, dos sintomas distintos en el iPhone real (no
visibles en el simulador de Chrome DevTools):
1. Contenido (titulos, botones) quedaba visualmente tapado por el notch/Dynamic
   Island o la barra de estado.
2. Mas grave: los toques en esa zona superior no llegaban a la app -- el
   sistema operativo los intercepta antes de que el contenido web los reciba,
   asi que no era solo un problema visual sino de interaccion real (botones
   inalcanzables).

**Resolucion:**
Padding compensatorio via `env(safe-area-inset-top)` / `env(safe-area-inset-bottom)`
aplicado una sola vez, a nivel de `#root` en `pwa-gastos/src/index.css` --
no en cada pantalla individualmente, porque las 5 pantallas de la PWA
cuelgan del mismo `#root` y no hay un componente de layout comun entre
ellas. Ver commit `716445d`.

**Prevencion:**
Si una PWA usa `viewport-fit=cover` (necesario para fondo edge-to-edge en
iOS), agregar el padding de `env(safe-area-inset-*)` en el mismo cambio,
no como paso separado -- son dos mitades del mismo mecanismo y sin la
segunda, la primera rompe la interaccion, no solo el aspecto visual.
Probar en un iPhone real (o al menos el simulador de Safari, no el de
Chrome) antes de dar por buena una pantalla full-screen en iOS: el
recorte del notch no se ve igual en DevTools de Chrome.

**Senal de alarma para Hernan:**
Si un boton o campo cerca del borde superior de la pantalla en el iPhone no
responde al tocarlo (pero el mismo elemento en otra posicion si funciona),
sospechar de este problema antes que de un bug de logica.
