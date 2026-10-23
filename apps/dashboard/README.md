# Dengue Signal Atlas

Construye un prototipo navegable del dashboard SAT-Dengue V2, tomando como fuente funcional principal el documento adjunto PROD-04-dashboard-master-user-story.md y las especificaciones de Construye_un_prototipo_navegable_del_dashboard_pasted.md.

Debe seguir el diseño de esta página como referencia visual: https://dengue-watch-pro.lovable.app (tema oscuro profesional, paleta de colores oklch, tarjetas refinadas, tipografía y distribución visual limpia), sin copiar datos ni reglas científicas de esa versión.

Requisitos clave:

1. MVP de solo lectura con banner permanente: "DATOS DEMOSTRATIVOS — NO USAR PARA DECISIONES OPERATIVAS".
2. Navegación con pestañas independientes para Tolima y Meta, selector de municipios (Ibagué, Espinal, Melgar, Chaparral, Mariquita para Tolima; Villavicencio, Acacías, Granada, Puerto López para Meta), periodo de referencia T, fecha actual en Bogotá, fecha de generación y versión del procedimiento.
3. Vista principal en este orden:
   - Estado de gobernanza: MODELO NO APROBADO, G5: NOT_APPROVED, Champion: no seleccionado, con texto explicativo institucional.
   - Situación observada actual (Mes T): Casos observados y zona del canal endémico (Éxito, Seguridad, Alerta, Exceso).
   - Tarjetas independientes para pronósticos T+1 y T+2 con mes objetivo, probabilidad estimada, umbral aplicado, estado de alerta y aclaración de que estima probabilidad de superar P75 histórico.
   - Gráfico interactivo de Canal Endémico con zonas P25, mediana, P75 y mes T resaltado.
   - Mapa/representación territorial departamental con toggle T+1/T+2 y tabla accesible equivalente.
   - Gráfico compacto de comparación de horizontes T+1 vs T+2 con umbrales.
   - Contexto histórico del modelo (falsas alertas, sensibilidad de detección) y sección desplegable de detalles técnicos (AUROC, AP, Brier).
4. Sin sección de recomendaciones ni insights automáticos. Coherencia total entre datos simulados.

This project was built with [Lovable](https://lovable.dev).

**Live app**: https://dengue-signal-atlas.lovable.app

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/e6e0fff0-3a0f-49c5-9ae7-0861d41b8dd3).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

The dashboard now reads all dynamic content from the Stage 7 read-only API. Copy
`.env.example` to `.env.local`. Leave `VITE_API_BASE_URL` empty to use the same
origin; during local development, set `VITE_API_PROXY_TARGET` to the API origin
and Vite will proxy `/api`. An absolute `VITE_API_BASE_URL` is also supported
when an explicitly allowed cross-origin deployment is configured by the API.

Start the Stage 7 API from the monorepo root, then run the dashboard independently:

```sh
uvicorn --factory scripts.read_only_api.api:create_app
cd apps/dashboard
bun install --frozen-lockfile
bun run dev
```

The browser requests `GET /api/dashboard?department_code={code}&period={YYYY-MM}`.
The response is validated with Zod before a single adapter creates the visual
view model. Failed or incompatible requests clear the visible result and require
an explicit retry; no local demonstration-data fallback exists.
