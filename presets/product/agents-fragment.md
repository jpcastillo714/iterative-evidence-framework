* **Estructura:** configuracion en `config` (ningun parametro vive en el codigo), etapas en `pipelines`, runbooks y app en `despliegue`, y material de entrada en `onboarding`.
* **El onboarding no es opcional.** El equipo rota; el proyecto no puede vivir en una cabeza. Si alguien nuevo no puede arrancar leyendo esa carpeta, el incremento no esta terminado.
* **El contrato de datos es una frontera.** El paso 3 declara lo que otros equipos pueden esperar de ti y lo que tu esperas de ellos. Romperlo en silencio es como se cae un pipeline aguas abajo.
* **Los datos de origen son de solo lectura.** Todo derivado se reconstruye desde el pipeline; nada se edita en el sitio.
* **Idempotencia:** una etapa que se ejecuta dos veces debe dejar el mismo estado. Si no, no es reproducible aunque lo parezca.
