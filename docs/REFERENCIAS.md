# Referencias

La bibliografía que justifica las decisiones de diseño del IEF
([`docs/decisiones/`](decisiones/README.md)). Se cita con `[@clave]`.

**Cómo se lee una entrada.**

| Campo | Qué es |
|---|---|
| **Estado** | *revisado por pares* (revista o congreso arbitrado), *preprint* (sin revisión; puede cambiar), *ensayo* (publicación editorial no arbitrada), *norma* (especificación) o *documentación técnica* (guía o artículo de práctica) |
| **Verificado** | Cuándo se abrió la fuente primaria y se comprobó cada hallazgo contra el texto |
| **Hallazgos que se usan** | Lo que el IEF toma de ese trabajo, con su ubicación entre paréntesis. Parafraseado: la fuente manda |

**Reglas.**
- Solo entra lo que se verificó en la fuente primaria. Los resúmenes de terceros no cuentan como verificación.
- Si una cifra depende de la versión del trabajo, se indica la versión.
- Lo que el trabajo *no* dice no se le atribuye. Los matices necesarios van en la entrada.
- Una referencia que ningún documento cita se quita (`tests/test_referencias.py`).

---

## Registro de decisiones

### [@jansen2005]
- **Cita:** Jansen, A. y Bosch, J. (2005). *Software Architecture as a Set of Architectural Design Decisions*. 5th Working IEEE/IFIP Conference on Software Architecture (WICSA'05), pp. 109–120.
- **Enlace:** https://doi.org/10.1109/WICSA.2005.61
- **Estado:** revisado por pares.
- **Verificado:** 2026-09-24, sobre la reimpresión en la tesis de Jansen (Universidad de Groningen, 2008, cap. 4).
- **Hallazgos que se usan:**
  - (Resumen y §3 «Problems of software architecture») El conocimiento sobre las decisiones de diseño queda implícito y se pierde («knowledge vaporization»). Consecuencias: las reglas que esas decisiones imponían se violan al evolucionar el sistema y las decisiones obsoletas no se retiran.
  - (§1 y §2) Proponen tratar cada decisión como un elemento explícito, con su justificación.

### [@nygard2011]
- **Cita:** Nygard, M. (2011). *Documenting Architecture Decisions*. Cognitect.
- **Enlace:** https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- **Estado:** documentación técnica.
- **Verificado:** 2026-09-24.
- **Hallazgos que se usan:**
  - (Sección del formato) Un registro de decisión tiene título, contexto, decisión, estado y consecuencias.
  - (Sección del estado) Una decisión revertida no se borra: se marca como reemplazada, para que se vea que fue la decisión y que ya no lo es.

## Verificación y autocorrección

### [@huang2024]
- **Cita:** Huang, J., Chen, X., Mishra, S., Zheng, H. S., Yu, A. W., Song, X. y Zhou, D. (2024). *Large Language Models Cannot Self-Correct Reasoning Yet*. ICLR 2024.
- **Enlace:** https://arxiv.org/abs/2310.01798
- **Estado:** revisado por pares.
- **Verificado:** 2026-09-24 (arXiv v2).
- **Hallazgos que se usan:**
  - (Resumen; §3.2, Tabla 3) Sin retroalimentación externa, pedirle al modelo que revise su propia respuesta no mejora el razonamiento, y en sus experimentos la exactitud baja en todos los benchmarks. Por ejemplo, GPT-4 en GSM8K pasa de 95,5 a 89,0.
  - (Matiz) El alcance es la autocorrección *intrínseca* en tareas de razonamiento, con los modelos de 2023–2024. El título dice «yet».

### [@kamoi2024]
- **Cita:** Kamoi, R., Zhang, Y., Zhang, N., Han, J. y Zhang, R. (2024). *When Can LLMs Actually Correct Their Own Mistakes? A Critical Survey of Self-Correction of LLMs*. Transactions of the ACL 12:1417–1440.
- **Enlace:** https://doi.org/10.1162/tacl_a_00713
- **Estado:** revisado por pares.
- **Verificado:** 2026-09-24 (arXiv v3).
- **Hallazgos que se usan:**
  - (Resumen; recuadro de §1) Ningún trabajo previo muestra autocorrección exitosa con retroalimentación de un LLM usado solo con prompts, salvo en tareas excepcionalmente adecuadas. La autocorrección funciona cuando hay retroalimentación externa confiable.

### [@cemri2025]
- **Cita:** Cemri, M., Pan, M. Z., Yang, S., Agrawal, L. A., Chopra, B., Tiwari, R., Keutzer, K., Parameswaran, A., Klein, D., Ramchandran, K., Zaharia, M., Gonzalez, J. E. y Stoica, I. (2025). *Why Do Multi-Agent LLM Systems Fail?* NeurIPS 2025, Track on Datasets and Benchmarks.
- **Enlace:** https://arxiv.org/abs/2503.13657
- **Estado:** revisado por pares.
- **Verificado:** 2026-09-24 (arXiv v3). En la v3, las cifras de la Figura 2 no coinciden con las de la Figura 1; se usan las de la Figura 1 y la §4.
- **Hallazgos que se usan:**
  - (§4, Figura 1; Apéndice A.3) Taxonomía MAST, construida sobre 1.642 trazas de siete marcos multiagente. Dos modos de falla de verificación: verificación ausente o incompleta (FM-3.2, 8,2%) y verificación incorrecta (FM-3.3, 9,1%).
  - (§4, FC3) Muchos verificadores hacen solo comprobaciones superficiales, como que el código compile o que no queden comentarios TODO, aunque se les pida verificar a fondo.
  - (Apéndice H.2, Tabla 5) En un caso de estudio con ChatDev sobre ProgramDev-v0 (32 tareas), reforzar la jerarquía de roles y la especificación del verificador subió el éxito de 25,0% a 34,4%. Cambiar la topología para que la conversación termine solo cuando un agente confirma las revisiones lo subió a 40,6%. Los autores clasifican ambas intervenciones como tácticas, no reportan repeticiones y advierten que no son mejoras sustanciales.

### [@zhong2026]
- **Cita:** Zhong, Z., Raghunathan, A. y Carlini, N. (2026). *ImpossibleBench: Measuring LLMs' Propensity of Exploiting Test Cases*. ICLR 2026.
- **Enlace:** https://arxiv.org/abs/2510.20270
- **Estado:** revisado por pares.
- **Verificado:** 2026-09-24 (arXiv v1 y versión final de ICLR).
- **Hallazgos que se usan:**
  - (§4) Con tests que contradicen la especificación, cualquier «éxito» es trampa. GPT-5 hace trampa en el 54,0% de las tareas de Conflicting-SWEbench.
  - (§5.2, Figura 7) Dejar los tests en solo lectura baja la trampa de GPT-5 de 54% a 39% (Conflicting) y de 76% a 58% (Oneoff), pero no elimina otras formas, como tratar casos especiales. Ocultar los tests la lleva a 0–1%.
  - (§5.3) Dar una salida explícita para pedir intervención humana baja la trampa de GPT-5 de 54% a 9%. En Claude Opus 4.1 el efecto es mucho menor. El texto atribuye el paso de 49% a 12% a o3, pero la leyenda de la Figura 8 dice o4-mini.

### [@gabor2025]
- **Cita:** Gabor, J., Lynch, J. y Rosenfeld, J. (2025). *EvilGenie: A Reward Hacking Benchmark*.
- **Enlace:** https://arxiv.org/abs/2511.21654
- **Estado:** preprint.
- **Verificado:** 2026-09-24 (arXiv v2, mayo de 2026).
- **Hallazgos que se usan:**
  - (§2.5; §4.2) Compararon tres detectores de *reward hacking*: tests retenidos, un juez LLM y la detección de ediciones a los archivos de test. La detección de ediciones solo se activó con un agente, y casi siempre sobre soluciones correctas. El juez LLM fue el más eficaz en los casos inequívocos.

### [@dhanorkar2026]
- **Cita:** Dhanorkar, S., Passi, S. y Vorvoreanu, M. (2026). *Human oversight of agentic systems in practice: Examining the oversight work, challenges, and heuristics of developers using software agents*.
- **Enlace:** https://arxiv.org/abs/2606.05391
- **Estado:** preprint.
- **Verificado:** 2026-09-24 (arXiv v1).
- **Hallazgos que se usan:**
  - (Resumen; §4.2, heurística 2) En entrevistas a 17 desarrolladores, cuando el código del agente es difícil de revisar, delegan la verificación en los tests y tratan un resultado verde como garantía de corrección. Los autores advierten que esa heurística vale lo que valen los tests.
  - (Matiz) El estudio es exploratorio, y 12 de los 17 participantes trabajan en la misma empresa que los autores.

## Autorización y permisos

### [@torresarias2019]
- **Cita:** Torres-Arias, S., Afzali, H., Kuppusamy, T. K., Curtmola, R. y Cappos, J. (2019). *in-toto: Providing farm-to-table guarantees for bits and bytes*. 28th USENIX Security Symposium, pp. 1393–1410.
- **Enlace:** https://www.usenix.org/conference/usenixsecurity19/presentation/torres-arias
- **Estado:** revisado por pares.
- **Verificado:** 2026-09-24 (PDF de USENIX).
- **Hallazgos que se usan:**
  - (§4.2) Cada paso de una cadena de producción deja metadatos firmados con el hash criptográfico de sus entradas («materials») y de sus salidas («products»). Así, un verificador detecta que un artefacto se alteró entre un paso y el siguiente.
  - (Matiz) in-toto habla de pasos ejecutados y firmados por responsables, no de «aprobaciones». Además usa firmas, que dan autenticidad; un hash solo da integridad.

### [@debenedetti2025]
- **Cita:** Debenedetti, E., Shumailov, I., Fan, T., Hayes, J., Carlini, N., Fabian, D., Kern, C., Shi, C., Terzis, A. y Tramèr, F. (2025). *Defeating Prompt Injections by Design*.
- **Enlace:** https://arxiv.org/abs/2503.18813
- **Estado:** preprint.
- **Verificado:** 2026-09-24 (arXiv v2).
- **Hallazgos que se usan:**
  - (Resumen; §5.1) CaMeL extrae el flujo de control solo de la consulta confiable del usuario. El modelo que decide el plan nunca ve los datos no confiables, y a cada valor se le asocian capacidades que las políticas comprueban al llamar herramientas.
  - (Tabla 2) En AgentDojo, con o3, resuelve el 77,3% de las tareas con esas garantías, frente al 84,5% sin defensa. Es utilidad sin ataque.
  - (Matiz, §6.4 y §9.3) Los autores muestran casos en que el flujo de datos termina actuando como flujo de control, y afirman que la inyección de prompts no está resuelta del todo.

### [@michael2026]
- **Cita:** Michael, A. E. y Roesner, F. (2026). *How Agents Ask for Permission: User Permissions for AI Agents, from Interfaces to Enforcement*.
- **Enlace:** https://arxiv.org/abs/2607.13718
- **Estado:** preprint.
- **Verificado:** 2026-09-24 (arXiv v2).
- **Hallazgos que se usan:**
  - (§1; Tabla 1) Analizan los permisos de agentes en seis categorías: modelo de amenaza (adversario y objetivo), especificación en la interfaz, especificación interna, **derivación** de la política interna a partir de lo que el usuario seleccionó, y **aplicación** de esa política en tiempo de ejecución.
  - (§3.1–3.2) Revisaron 21 sistemas y propuestas de 2024 a 2026 (3 revisados por pares, 18 preprints y 1 sistema abierto) y 5 agentes comerciales.

### [@feng2025]
- **Cita:** Feng, K. J. K., McDonald, D. W. y Zhang, A. X. (2025). *Levels of Autonomy for AI Agents*. Knight First Amendment Institute, serie «Artificial Intelligence and Democratic Freedoms».
- **Enlace:** https://arxiv.org/abs/2506.12469
- **Estado:** ensayo.
- **Verificado:** 2026-09-24 (arXiv v2).
- **Hallazgos que se usan:**
  - (Resumen) El nivel de autonomía de un agente es una decisión de diseño, separada de su capacidad. Proponen cinco niveles según el rol del usuario: operador, colaborador, consultor, aprobador y observador.

## Versiones y compatibilidad

### [@semver2]
- **Cita:** Preston-Werner, T. *Semantic Versioning 2.0.0*.
- **Enlace:** https://semver.org/spec/v2.0.0.html
- **Estado:** norma.
- **Verificado:** 2026-09-24.
- **Hallazgos que se usan:**
  - (Regla 4) La versión mayor cero (0.y.z) es desarrollo inicial: cualquier cosa puede cambiar y la API pública no debe considerarse estable.
  - (Regla 8) A partir de 1.0.0, un cambio incompatible exige subir la versión mayor.
  - (FAQ, «How should I handle deprecating functionality?») Antes de retirar algo en una versión mayor, debería haber al menos una versión menor que lo marque como obsoleto.

### [@keepachangelog]
- **Cita:** Lacan, O. *Keep a Changelog 1.1.0*.
- **Enlace:** https://keepachangelog.com/en/1.1.0/
- **Estado:** documentación técnica.
- **Verificado:** 2026-09-24.
- **Hallazgos que se usan:**
  - (Principios) El registro de cambios es para personas, no para máquinas.
  - (Tipos de cambio) Separa lo obsoleto («Deprecated») de lo retirado («Removed»).
  - («Ignoring Deprecations») Debe ser posible actualizar a la versión que anuncia algo como obsoleto, dejar de usarlo y recién entonces actualizar a la versión que lo retira.

### [@bogart2021]
- **Cita:** Bogart, Kästner, Herbsleb y Thung (2021). *When and How to Make Breaking Changes: Policies and Practices in 18 Open Source Software Ecosystems*. ACM Transactions on Software Engineering and Methodology 30(4).
- **Enlace:** https://doi.org/10.1145/3447245
- **Estado:** revisado por pares.
- **Verificado:** 2026-09-24, sobre la versión de autor (https://www.cs.cmu.edu/~ckaestne/pdf/tosem21.pdf). Las secciones coinciden con la publicada; las páginas no.
- **Hallazgos que se usan:**
  - (Tabla 5) Entre las prácticas para comunicar y amortiguar cambios: marcar como obsoleto antes de retirar, escribir una guía de migración, llevar un registro de cambios que documente los problemas de compatibilidad y usar versionado semántico.
  - (§4.3.1) Pocos entrevistados monitoreaban activamente los cambios de lo que usaban, y uno describió los avisos de cambios como una carga con poca señal frente al ruido.
  - (Matiz) Es un estudio de ecosistemas de paquetes. Aplicarlo a proyectos que usan un framework de procesos es una analogía.

### [@raemaekers2017]
- **Cita:** Raemaekers, van Deursen y Visser (2017). *Semantic versioning and impact of breaking changes in the Maven repository*. Journal of Systems and Software 129:140–158.
- **Enlace:** https://doi.org/10.1016/j.jss.2016.04.008
- **Estado:** revisado por pares.
- **Verificado:** 2026-09-24, sobre el manuscrito aceptado (TU Delft, TUD-SERG-2016-011).
- **Hallazgos que se usan:**
  - (§5.2, Tabla 6) En Maven, el 35,7% de las versiones menores y el 23,8% de los parches introducen al menos un cambio incompatible. El número de versión no es una señal confiable de compatibilidad.
  - (§10, Tabla 19) El patrón de deprecación que recomienda SemVer casi no aparece en la práctica: una fracción grande de los métodos públicos se borra sin haberse marcado antes como obsoleta.
  - (Matiz) Son bibliotecas Java de 2005 a 2011, y la herramienta usada subestima los cambios incompatibles.

### [@decan2021]
- **Cita:** Decan y Mens (2021). *Lost in zero space – An empirical comparison of 0.y.z releases in software package distributions*. Science of Computer Programming 208:102656.
- **Enlace:** https://doi.org/10.1016/j.scico.2021.102656
- **Estado:** revisado por pares.
- **Verificado:** 2026-09-24, sobre el preprint (arXiv:2101.00836v1).
- **Hallazgos que se usan:**
  - (§4.2) Menos del 10% de los paquetes estudiados pasó de 0.y.z a 1.0.0 o más: muchos se usan en serio sin salir nunca de la versión cero.
  - (§5.5) En la práctica, los mantenedores no aplican SemVer al pie de la letra en 0.y.z y siguen una política más permisiva.

### [@curino2008prism]
- **Cita:** Curino, Moon y Zaniolo (2008). *Graceful Database Schema Evolution: the PRISM Workbench*. Proceedings of the VLDB Endowment 1(1):761–772.
- **Enlace:** https://doi.org/10.14778/1453856.1453939
- **Estado:** revisado por pares.
- **Verificado:** 2026-09-24 (PDF de vldb.org).
- **Hallazgos que se usan:**
  - (§3.1) La evolución de esquemas es una actividad crítica, costosa y propensa a errores.
  - (§3.2) Entre los requisitos que plantean: operadores de cambio atómicos y bien definidos, poder probar los pasos intermedios y dejar registrada la historia de la evolución.

### [@curino2008wiki]
- **Cita:** Curino, Moon, Tanca y Zaniolo (2008). *Schema Evolution in Wikipedia – Toward a Web Information System Benchmark*. ICEIS 2008, pp. 323–332.
- **Enlace:** https://doi.org/10.5220/0001713003230332
- **Estado:** revisado por pares.
- **Verificado:** 2026-09-24 (PDF de SciTePress).
- **Hallazgos que se usan:**
  - (§1) En cuatro años y medio, Wikipedia tuvo 171 versiones de su esquema, y solo cerca del 22% de las consultas escritas para esquemas antiguos seguían siendo válidas.
  - (§3.2) El 8,8% de los pasos de evolución fueron vueltas a una versión anterior del esquema.

### [@aghajani2019]
- **Cita:** Aghajani et al. (2019). *Software Documentation Issues Unveiled*. ICSE 2019, pp. 1199–1210.
- **Enlace:** https://doi.org/10.1109/ICSE.2019.00122
- **Estado:** revisado por pares.
- **Verificado:** 2026-09-24 (versión de autor).
- **Hallazgos que se usan:**
  - (§IV.A) Un documento está desactualizado cuando no está sincronizado con el resto del sistema. Los problemas de desactualización son el 39% de los problemas de contenido de la documentación que encontraron.

## Agentes y cambios de versión

### [@wang2025]
- **Cita:** Wang, Huang, Zhang, Feng, Zhang, Liu y Peng (2025). *LLMs Meet Library Evolution: Evaluating Deprecated API Usage in LLM-Based Code Completion*. ICSE 2025, pp. 885–897.
- **Enlace:** https://doi.org/10.1109/ICSE55347.2025.00245
- **Estado:** revisado por pares.
- **Verificado:** 2026-09-24 (arXiv:2406.09834).
- **Hallazgos que se usan:**
  - (§IV.A, resumen 2) Todos los modelos evaluados usaron APIs obsoletas, entre el 25% y el 38% de las veces.
  - (§IV.B, resumen 5) Cuando el código que rodea al punto de completado usa la API vieja, la tasa de uso obsoleto sube al 70–90%. El contexto viejo arrastra el uso viejo.
  - (§V.C, resúmenes 9–10) Una intervención determinista durante la generación corrige más del 85% de los casos. Agregar la instrucción al prompt no alcanza.
  - (Matiz) Son modelos de completado de código, no agentes.

### [@wu2024]
- **Cita:** Wu et al. (2024). *VersiCode: Towards Version-controllable Code Generation*.
- **Enlace:** https://arxiv.org/abs/2406.07411
- **Estado:** preprint.
- **Verificado:** 2026-09-24 (arXiv v2).
- **Hallazgos que se usan:**
  - (§1; §4.2) Los modelos conservan conocimiento de programación desactualizado y son poco sensibles a que se les indique la versión. Especificar la versión mejora poco y la ventaja desaparece a nivel de línea y de bloque.

### [@liu2025]
- **Cita:** Liu, Pandit, Ye, Choi y Durrett (2025). *CodeUpdateArena: Benchmarking Knowledge Editing on API Updates*.
- **Enlace:** https://arxiv.org/abs/2407.06249
- **Estado:** preprint.
- **Verificado:** 2026-09-24 (arXiv **v3**; el resumen de la página abs aún refleja una versión anterior con la conclusión contraria).
- **Hallazgos que se usan:**
  - (Tabla 4) Poner en el contexto la documentación del cambio de API mejora mucho a los modelos más capaces: Claude-3.5 pasa de 2,9 a 58,7 y GPT-4 de 2,7 a 34,1. En los modelos abiertos pequeños el efecto es menor.
  - (Matiz) Las actualizaciones de API del benchmark son sintéticas.

### [@misra2026]
- **Cita:** Misra, Islah et al. (2026). *GitChameleon 2.0: Evaluating AI Code Generation Against Python Library Version Incompatibilities*. ACL 2026 (Long Papers), pp. 46792–46831.
- **Enlace:** https://doi.org/10.18653/v1/2026.acl-long.2170
- **Estado:** revisado por pares.
- **Verificado:** 2026-09-24 (PDF de la ACL Anthology).
- **Hallazgos que se usan:**
  - (§3.3.6) Recuperar documentación de la versión correcta mejora el éxito hasta cerca de 10 puntos, pero en el mejor caso más del 40% de los problemas sigue sin resolverse.
  - (§3.3.5) Evalúan también asistentes de terminal e IDE. Darles el enunciado del problema aporta entre 12 y 35 puntos.

### [@chatlatanagulchai2026]
- **Cita:** Chatlatanagulchai et al. (2026). *Agent READMEs: An Empirical Study of Context Files for Agentic Coding*.
- **Enlace:** https://arxiv.org/abs/2511.12884
- **Estado:** preprint.
- **Verificado:** 2026-09-24 (arXiv v2).
- **Hallazgos que se usan:**
  - (§4.2.3) Los archivos de contexto para agentes se mantienen activamente: el 67% de los archivos estudiados se modificó en varios commits.
  - (§5.2) Recomiendan tratar esos archivos como configuración versionada.

### [@gloaguen2026]
- **Cita:** Gloaguen, Mündler, Müller, Raychev y Vechev (2026). *Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?*
- **Enlace:** https://arxiv.org/abs/2602.11988
- **Estado:** preprint.
- **Verificado:** 2026-09-24 (arXiv v2).
- **Hallazgos que se usan:**
  - (§4.3; Apéndice E) Los agentes siguen bien las instrucciones concretas de estos archivos, y las herramientas que mencionan se usan casi solo cuando están mencionadas. En cambio, como resumen descriptivo del repositorio no ayudan.
  - (Resumen) Estos archivos aumentan el costo de inferencia en más del 20%. Conviene que sean breves y accionables.

### [@sato2014]
- **Cita:** Sato, D. (2014). *ParallelChange*. martinfowler.com.
- **Enlace:** https://martinfowler.com/bliki/ParallelChange.html
- **Estado:** documentación técnica.
- **Verificado:** 2026-09-24.
- **Hallazgos que se usan:**
  - (Definición) Un cambio incompatible se hace sin romper a nadie en tres fases: expandir (lo nuevo convive con lo viejo), migrar (los usuarios pasan a lo nuevo) y contraer (se retira lo viejo).
