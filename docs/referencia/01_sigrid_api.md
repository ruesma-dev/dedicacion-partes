<!-- docs/referencia/01_sigrid_api.md -->
# sigrid-api — vive en `azure-apps`, no aquí

> Puntero creado el 2026-08-19 al instalar el arnés. Documento real:
> `C:\Users\pgris\PycharmProjects\azure-apps\sigrid_api.md`.

Contrato de `POST /api/sql/read` y de la escritura, las dos bases
(`ruesma` / `ruesma_rep`), el tope de 1.000 filas por petición, el corte del
balanceador a los 230 s y el patrón de paginación obligatorio.

No se copia aquí: la única copia es la de `azure-apps`, y dos copias
divergen siempre. Si al trabajar descubres que ese documento está
desactualizado, corrígelo allí en el mismo trabajo.
