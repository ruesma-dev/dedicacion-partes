// static/js/app.js
// Dedicación por obra · Ruesma — interfaz de captura rápida.
// Tabla estándar Ruesma (como el front de partes): cabecera burdeos con
// orden por click, fila de filtros por columna, y columnas que se pueden
// mover (arrastrar cabecera) y redimensionar (arrastrar su borde), con
// persistencia en localStorage.

"use strict";

const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

// ------------------------------------------------------------ columnas
const COLUMNAS = {
  nombre: {
    titulo: "Trabajador",
    ancho: 280,
    ordenable: true,
    placeholder: "Filtrar trabajador…",
  },
  categoria: {
    titulo: "Categoría",
    ancho: 210,
    ordenable: true,
    placeholder: "Filtrar categoría…",
  },
  asignaciones: {
    titulo: "Asignaciones",
    ancho: 560,
    ordenable: false,
    placeholder: "Filtrar obra…",
  },
  // F-050 (R23): la partida de cada línea, a la derecha de su obra.
  partida: {
    titulo: "Partida",
    ancho: 320,
    ordenable: false,
    placeholder: "Filtrar partida…",
  },
  total: {
    titulo: "Total",
    ancho: 190,
    ordenable: true,
    num: true,
    placeholder: "ok / falta / sobra…",
  },
};
const ORDEN_COLUMNAS_DEFECTO = ["nombre", "categoria", "asignaciones", "partida", "total"];
// F-050 (R22): columnas con una celda por línea (subfila); las demás son
// del trabajador y ocupan todas sus subfilas (`rowSpan`).
const COLUMNAS_POR_LINEA = ["asignaciones", "partida"];
const CLAVE_TABLA = "dedicacion:tabla:v1";

const state = {
  anio: 0,
  mes: 0,
  periodoEstado: "ABIERTO",
  trabajadores: [],
  obras: [],
  catalogoObras: [],
  resumen: null,
  filtroTexto: "",
  filtroEstado: null,          // OK | FALTA | EXCESO | SIN_CARGA | null
  filtrosCol: {},              // clave de columna -> texto
  soloPendientes: false,
  orden: { campo: "pendientes", dir: 1 },
  columnas: ORDEN_COLUMNAS_DEFECTO.slice(),
  anchos: {},
  seleccionIde: null,          // cursor: la fila de las teclas (↑ ↓ Enter R F7 F8)
  // Selección múltiple (F-029): `ide` marcados con Ctrl/Shift+clic,
  // independiente de los filtros. Solo la escriben `marcarSeleccion` y
  // `fijarSeleccion`.
  seleccion: new Set(),
  ancla: null,                 // fila desde la que Shift+clic hace el rango
  editandoIde: null,
  edicion: [],
  timerGuardado: null,
  guardadoPendiente: false,
  empresa: null,               // empresa elegida en el selector (F-024)
  empresas: [],                // [{empresa, nombre, de_baja}] que sirve la API
};

// Selector de partida (F-050): respuestas de `GET …/partidas` por trabajador,
// obra y modo (se vacía al cargar el cuadrante y su clave tras cada PUT) y
// cómo cerrar el panel abierto.
const selector = { cache: new Map(), cerrar: null };

// ---------------------------------------------------------------- utilidades
const $ = (sel) => document.querySelector(sel);

function normalizar(texto) {
  return (texto || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

// Etiqueta de una obra tal como la pinta la app: «Postv-» delante si es de
// postventa; el código, tal cual, en otro caso (F-041, R1).
function etiquetaObra(cod, esPostventa) {
  return (esPostventa ? "Postv-" : "") + cod;
}

// Texto visible: etiqueta y descripción, lo que enseñan el chip, su `title` y
// el autocompletado. De aquí salen todos los casados de obra (F-041, R2).
function textoObra(cod, descripcion, esPostventa) {
  return etiquetaObra(cod, esPostventa) + " " + (descripcion || "");
}

// ¿La línea del cuadrante casa con el filtro? `q` llega ya normalizado
// (F-041, R4). F-021 la reutilizará para saber qué chip casa.
function lineaCasa(l, q) {
  return normalizar(textoObra(l.cod, l.descripcion, l.es_postventa)).includes(q);
}

// Texto de una partida elegida (F-050, R24): «código · descripción», o
// «partida N» si no trae ninguno de los dos; sin elegida, vacío. `p` lleva
// `partida_ide`, `partida_cod` y `partida_res` (una línea del cuadrante).
function textoPartida(p) {
  if (!p || p.partida_ide == null) return "";
  return [p.partida_cod, p.partida_res].filter(Boolean).join(" · ") ||
    `partida ${p.partida_ide}`;
}

// Partidas del catálogo que casan con el texto (TODAS sus palabras, en
// código y descripción, sin mayúsculas ni tildes) y con el mayor del botón
// (`null` = Todas). El mayor lo manda el transfer; aquí no se clasifica nada.
function filtrarPartidas(partidas, texto, mayor) {
  const palabras = normalizar(texto).split(/\s+/).filter(Boolean);
  return (partidas || []).filter((p) => {
    if (mayor && p.mayor !== mayor) return false;
    const pajar = normalizar(`${p.cod || ""} ${p.res || ""}`);
    return palabras.every((w) => pajar.includes(w));
  });
}

// Lista del selector: las filtradas, en el orden de la API, con la
// propuesta PRIMERA si pasa los filtros y sin repetirla (R26).
// `resp` = {partidas, propuesta}.
function listaSelector(resp, texto, mayor) {
  const lista = filtrarPartidas(resp.partidas, texto, mayor);
  const prop = resp.propuesta;
  const primera = prop ? lista.find((p) => p.ide === prop.paride) : undefined;
  return (primera ? [primera] : [])
    .concat(lista.filter((p) => p !== primera))
    .map((p) => ({ ...p, propuesta: p === primera }));
}

// De dónde sale una partida (`partida_metodo` y `partida_origen` del
// transfer, R6): solo lo rotula.
function rotuloOrigen(metodo, origen) {
  const textos = {
    parte_anterior: "parte anterior",
    ultimo_parte: "último parte",
    auto_nombre: "casada por nombre",
    auto_categoria: "casada por categoría",
    postventa: "obra de postventa",
    var: "partida fija",
    manual: "elegida",
  };
  if (!metodo) return "";
  const texto = textos[metodo] || metodo;
  return origen ? `${texto}: ${origen}` : texto;
}

function fmtPct(valor) {
  const n = Math.round(valor * 100) / 100;
  const texto = Number.isInteger(n) ? String(n) : n.toFixed(2).replace(/0+$/, "");
  return texto.replace(".", ",") + "%";
}

function escapeHtml(texto) {
  const div = document.createElement("div");
  div.textContent = texto == null ? "" : String(texto);
  return div.innerHTML;
}

function toast(mensaje, esError = false) {
  const caja = document.createElement("div");
  caja.className = "toast" + (esError ? " error" : "");
  caja.textContent = mensaje;
  $("#toasts").appendChild(caja);
  setTimeout(() => caja.remove(), esError ? 6000 : 3500);
}

// Añade la empresa elegida a una ruta de la API (F-024, R5). El front no
// decide nada con ella: solo la pasa; filtrar es cosa de la API.
function conEmpresa(ruta) {
  if (state.empresa === null) return ruta;
  const sep = ruta.includes("?") ? "&" : "?";
  return `${ruta}${sep}empresa=${encodeURIComponent(state.empresa)}`;
}

async function api(ruta, opciones = {}) {
  const destino = ruta.startsWith("/periodos/") ? conEmpresa(ruta) : ruta;
  const respuesta = await fetch("/api/v1" + destino, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });
  let cuerpo = null;
  try { cuerpo = await respuesta.json(); } catch (e) { cuerpo = null; }
  if (!respuesta.ok) {
    const mensaje = (cuerpo && cuerpo.error) || `Error HTTP ${respuesta.status}`;
    throw new Error(mensaje);
  }
  return cuerpo;
}

function cargarPrefsTabla() {
  try {
    const datos = JSON.parse(localStorage.getItem(CLAVE_TABLA) || "{}");
    if (Array.isArray(datos.orden)) {
      const validas = datos.orden.filter((c) => COLUMNAS[c]);
      ORDEN_COLUMNAS_DEFECTO.forEach((c) => {
        if (validas.includes(c)) return;
        // F-050 (R23): la columna Partida entra justo a la derecha de la de
        // obras en unas preferencias guardadas sin ella.
        const tras = c === "partida" ? validas.indexOf("asignaciones") : -1;
        if (tras >= 0) validas.splice(tras + 1, 0, c);
        else validas.push(c);
      });
      state.columnas = validas;
    }
    if (datos.anchos && typeof datos.anchos === "object") {
      state.anchos = datos.anchos;
    }
  } catch (e) { /* sin persistencia */ }
}

function guardarPrefsTabla() {
  try {
    localStorage.setItem(
      CLAVE_TABLA,
      JSON.stringify({ orden: state.columnas, anchos: state.anchos })
    );
  } catch (e) { /* sin persistencia */ }
}

// ---------------------------------------------------------------- arranque
async function init() {
  const hoy = new Date();
  state.anio = hoy.getFullYear();
  state.mes = hoy.getMonth() + 1;
  cargarPrefsTabla();
  renderCabeceraTabla();
  enlazarEventos();
  await cargarEmpresas();
  await cargarPeriodo(state.anio, state.mes);
}

// Lista de empresas del selector (F-024, R3 y R4). La de la URL si la API
// la ofrece; si no, la por defecto que dice la API.
async function cargarEmpresas() {
  try {
    const datos = await api("/empresas");
    state.empresas = datos.empresas;
    const pedida = parseInt(
      new URLSearchParams(window.location.search).get("empresa"), 10);
    const ofrecida = state.empresas.some((e) => e.empresa === pedida);
    state.empresa = ofrecida ? pedida : datos.por_defecto;
    pintarSelectorEmpresa();
  } catch (err) {
    toast(err.message, true);
  }
}

function pintarSelectorEmpresa() {
  const sel = $("#selector-empresa");
  sel.innerHTML = "";
  state.empresas.forEach((e) => {
    const opcion = document.createElement("option");
    opcion.value = String(e.empresa);
    // «de baja» lo decide la API (F-032): aquí solo se marca, nunca se oculta.
    opcion.textContent = e.de_baja ? `${e.nombre} (de baja)` : e.nombre;
    sel.appendChild(opcion);
  });
  sel.value = String(state.empresa);
}

// Cambio de empresa: queda en la URL (D2) y se recarga el periodo en curso.
async function cambiarEmpresa(valor) {
  state.empresa = parseInt(valor, 10);
  const url = new URL(window.location.href);
  url.searchParams.set("empresa", String(state.empresa));
  history.replaceState(null, "", url);
  state.seleccionIde = null;
  fijarSeleccion([]);
  await cargarPeriodo(state.anio, state.mes);
}

async function cargarPeriodo(anio, mes) {
  try {
    await api("/periodos", {
      method: "POST",
      body: JSON.stringify({ anio, mes }),
    });
    const datos = await api(`/periodos/${anio}/${mes}/cuadrante`);
    state.anio = anio;
    state.mes = mes;
    aplicarCuadrante(datos);
  } catch (err) {
    toast(err.message, true);
  }
}

function aplicarCuadrante(datos) {
  selector.cache.clear();          // F-050: otro mes, empresa o recarga
  state.periodoEstado = datos.periodo.estado;
  state.trabajadores = datos.trabajadores;
  state.obras = datos.obras;
  state.resumen = datos.resumen;
  state.editandoIde = null;
  state.edicion = [];
  construirCatalogoObras();
  renderCabecera();
  renderTabla();
}

function construirCatalogoObras() {
  // F-025: la API decide qué se ofrece. La entrada normal, si la obra está
  // `activa`; la `Postv-`, si `admite_postventa` (una obra cerrada puede
  // ofrecerse solo como `Postv-`). F-041: la clave es el texto visible de la
  // entrada, sin alias (D1): casa lo mismo que su chip en la columna (R11).
  state.catalogoObras = [];
  state.obras.forEach((o) => {
    if (o.activa) {
      state.catalogoObras.push({
        obra: o, pv: false, cod: etiquetaObra(o.cod, false),
        clave: normalizar(textoObra(o.cod, o.descripcion, false)),
      });
    }
    if (o.admite_postventa) {
      state.catalogoObras.push({
        obra: o, pv: true, cod: etiquetaObra(o.cod, true),
        clave: normalizar(textoObra(o.cod, o.descripcion, true)),
      });
    }
  });
}

// ---------------------------------------------------------------- cabecera
function renderCabecera() {
  $("#periodo-etiqueta").textContent = `${MESES[state.mes - 1]} ${state.anio}`;
  const abierto = state.periodoEstado === "ABIERTO";
  const chipEstado = $("#periodo-estado");
  chipEstado.textContent = abierto ? "ABIERTO" : "CERRADO";
  chipEstado.className = "badge " + (abierto ? "ok" : "danger");
  $("#aviso-cerrado").classList.toggle("oculto", abierto);
  $("#btn-cerrar").classList.toggle("oculto", !abierto);
  ["#btn-copiar-mes", "#btn-sync"].forEach((s) => { $(s).disabled = !abierto; });
  $("#btn-completar").disabled = !abierto;

  const r = state.resumen || { total: 0, ok: 0, falta: 0, exceso: 0, sin_carga: 0 };
  const chips = [
    { clave: null, clase: "normal", texto: `${r.total} trabajadores` },
    { clave: "OK", clase: "ok", texto: `${r.ok} OK` },
    { clave: "SIN_CARGA", clase: "info", texto: `${r.sin_carga} sin carga` },
    { clave: "FALTA", clase: "warn", texto: `${r.falta} falta` },
    { clave: "EXCESO", clase: "danger", texto: `${r.exceso} exceso` },
  ];
  const cont = $("#resumen");
  cont.innerHTML = "";
  chips.forEach((c) => {
    const el = document.createElement("span");
    el.className = `badge ${c.clase}` +
      (state.filtroEstado === c.clave && c.clave ? " filtro-activo" : "");
    el.textContent = c.texto;
    el.title = c.clave ? "Filtrar por estado" : "Quitar filtro";
    el.addEventListener("click", () => {
      state.filtroEstado = state.filtroEstado === c.clave ? null : c.clave;
      renderCabecera();
      renderTabla();
    });
    cont.appendChild(el);
  });
}

// ------------------------------------------------- cabecera de la tabla
function renderCabeceraTabla() {
  const thead = $("#cabecera-tabla");
  thead.innerHTML = "";

  // Fila 1: títulos (burdeos) con orden por click, drag para mover y
  // manija de redimensionado en el borde derecho.
  const filaTitulos = document.createElement("tr");
  state.columnas.forEach((clave) => {
    const col = COLUMNAS[clave];
    const th = document.createElement("th");
    th.dataset.colKey = clave;
    th.className = "ct-th" + (col.num ? " num" : "");
    if (col.ordenable) th.classList.add("th-sort");
    th.appendChild(document.createTextNode(col.titulo));
    const flecha = document.createElement("span");
    flecha.className = "sort-arrow";
    th.appendChild(flecha);
    th.style.width = (state.anchos[clave] || col.ancho) + "px";

    if (col.ordenable) {
      th.addEventListener("click", () => {
        if (state.orden.campo === clave) {
          state.orden.dir = -state.orden.dir;
        } else {
          state.orden = { campo: clave, dir: 1 };
        }
        pintarIndicadoresOrden();
        renderTabla();
      });
    }
    montarManijaAncho(th, clave);
    montarArrastreColumna(th, clave);
    filaTitulos.appendChild(th);
  });
  thead.appendChild(filaTitulos);

  // Fila 2: filtros por columna + Limpiar (estándar Ruesma).
  const filaFiltros = document.createElement("tr");
  filaFiltros.className = "filter-row";
  state.columnas.forEach((clave, idx) => {
    const th = document.createElement("th");
    th.dataset.colKey = clave;
    const caja = document.createElement("div");
    caja.className = "filtro-celda";
    const input = document.createElement("input");
    input.className = "col-filter";
    input.type = "text";
    input.placeholder = COLUMNAS[clave].placeholder || "…";
    input.value = state.filtrosCol[clave] || "";
    input.addEventListener("input", () => {
      state.filtrosCol[clave] = input.value;
      renderTabla();
    });
    input.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") { input.value = ""; input.dispatchEvent(new Event("input")); }
    });
    caja.appendChild(input);
    if (idx === state.columnas.length - 1) {
      const limpiar = document.createElement("button");
      limpiar.type = "button";
      limpiar.className = "filter-clear";
      limpiar.textContent = "Limpiar";
      limpiar.addEventListener("click", () => {
        state.filtrosCol = {};
        state.filtroTexto = "";
        $("#buscador").value = "";
        renderCabeceraTabla();
        renderTabla();
      });
      caja.appendChild(limpiar);
    }
    th.appendChild(caja);
    filaFiltros.appendChild(th);
  });
  thead.appendChild(filaFiltros);

  sincronizarAnchoTabla();
  pintarIndicadoresOrden();
}

function pintarIndicadoresOrden() {
  document.querySelectorAll("#cabecera-tabla tr:first-child th").forEach((th) => {
    const flecha = th.querySelector(".sort-arrow");
    if (!flecha) return;
    if (th.dataset.colKey === state.orden.campo) {
      flecha.textContent = state.orden.dir === 1 ? " ▲" : " ▼";
    } else {
      flecha.textContent = "";
    }
  });
}

function sincronizarAnchoTabla() {
  const tabla = $("#tabla");
  tabla.style.tableLayout = "fixed";
  let total = 0;
  document
    .querySelectorAll("#cabecera-tabla tr:first-child th")
    .forEach((th) => { total += parseInt(th.style.width, 10) || 0; });
  tabla.style.minWidth = "100%";
  tabla.style.width = total + "px";
}

function montarManijaAncho(th, clave) {
  const manija = document.createElement("span");
  manija.className = "col-resize";
  manija.setAttribute("draggable", "false");
  th.appendChild(manija);
  manija.addEventListener("click", (ev) => ev.stopPropagation());
  manija.addEventListener("mousedown", (ev) => {
    ev.preventDefault();
    ev.stopPropagation();
    const inicioX = ev.pageX;
    const inicioW = th.offsetWidth;
    document.body.classList.add("col-resizing");
    const mover = (e) => {
      const w = Math.max(70, inicioW + (e.pageX - inicioX));
      th.style.width = w + "px";
      state.anchos[clave] = w;
      sincronizarAnchoTabla();
    };
    const soltar = () => {
      document.removeEventListener("mousemove", mover);
      document.removeEventListener("mouseup", soltar);
      document.body.classList.remove("col-resizing");
      guardarPrefsTabla();
    };
    document.addEventListener("mousemove", mover);
    document.addEventListener("mouseup", soltar);
  });
  manija.addEventListener("dblclick", (ev) => {
    ev.stopPropagation();
    delete state.anchos[clave];
    th.style.width = COLUMNAS[clave].ancho + "px";
    sincronizarAnchoTabla();
    guardarPrefsTabla();
  });
}

function montarArrastreColumna(th, clave) {
  th.setAttribute("draggable", "true");
  th.addEventListener("dragstart", (ev) => {
    th.classList.add("col-dragging");
    if (ev.dataTransfer) {
      ev.dataTransfer.effectAllowed = "move";
      try { ev.dataTransfer.setData("text/plain", clave); } catch (e) { /* IE */ }
    }
  });
  th.addEventListener("dragend", () => {
    th.classList.remove("col-dragging");
    document.querySelectorAll("#cabecera-tabla th").forEach((t) => {
      t.classList.remove("col-drop-target");
    });
  });
  th.addEventListener("dragover", (ev) => {
    ev.preventDefault();
    if (ev.dataTransfer) ev.dataTransfer.dropEffect = "move";
    th.classList.add("col-drop-target");
  });
  th.addEventListener("dragleave", () => th.classList.remove("col-drop-target"));
  th.addEventListener("drop", (ev) => {
    ev.preventDefault();
    th.classList.remove("col-drop-target");
    let origen = "";
    try { origen = ev.dataTransfer.getData("text/plain"); } catch (e) { /* IE */ }
    if (!origen || origen === clave) return;
    const desde = state.columnas.indexOf(origen);
    const hasta = state.columnas.indexOf(clave);
    if (desde < 0 || hasta < 0) return;
    state.columnas.splice(desde, 1);
    state.columnas.splice(hasta, 0, origen);
    guardarPrefsTabla();
    renderCabeceraTabla();
    renderTabla();
  });
}

// ---------------------------------------------------------------- filtrado
const ORDEN_ESTADO = { SIN_CARGA: 0, FALTA: 1, EXCESO: 2, OK: 3 };

function textoColumna(t, clave) {
  if (clave === "nombre") return t.nombre;
  if (clave === "categoria") return t.categoria || "";
  // La columna de obras no pasa por aquí: casa línea a línea (F-041, R4).
  if (clave === "total") {
    const partes = [fmtPct(t.total), String(Math.round(t.total))];
    if (t.estado === "OK") partes.push("ok 100");
    if (t.estado === "FALTA") partes.push("falta x");
    if (t.estado === "EXCESO") partes.push("sobra exceso x");
    if (t.estado === "SIN_CARGA") partes.push("sin carga");
    return partes.join(" ");
  }
  return "";
}

function trabajadoresVisibles() {
  const q = normalizar(state.filtroTexto);
  let filas = state.trabajadores.filter((t) => {
    // Las bajas solo aparecen si tienen carga en el periodo.
    if (!t.activo && !t.lineas.length) return false;
    if (state.filtroEstado && t.estado !== state.filtroEstado) return false;
    if (state.soloPendientes && t.estado === "OK") return false;
    for (const clave of state.columnas) {
      const filtro = normalizar(state.filtrosCol[clave] || "");
      if (!filtro) continue;
      // Partida (F-050, R28): alguna línea cuyo texto de partida case, el
      // que enseña su celda (en línea: el arnés node de F-041 no lo carga).
      if (clave === "partida") {
        const casaPartida = t.lineas.some((l) => normalizar(
          l.partida_fija ? l.descripcion
            : l.partida_ide != null
              ? `${l.partida_cod || ""} ${l.partida_res || ""}`
              : "automática").includes(filtro));
        if (!casaPartida) return false;
        continue;
      }
      // Obras: alguna línea cuyo texto visible case, no todas juntas (D2).
      const casa = clave === "asignaciones"
        ? t.lineas.some((l) => lineaCasa(l, filtro))
        : normalizar(textoColumna(t, clave)).includes(filtro);
      if (!casa) return false;
    }
    if (!q) return true;
    // Buscador libre de la fila: todos los campos juntos, y de cada línea su
    // texto visible, con su `Postv-` (F-041, R9).
    const pajar = normalizar(
      t.nombre + " " + (t.categoria || "") + " " +
      t.lineas.map((l) => textoObra(l.cod, l.descripcion, l.es_postventa)).join(" ") +
      " " + t.lineas.map((l) => `${l.partida_cod || ""} ${l.partida_res || ""}`).join(" ")
    );
    return pajar.includes(q);
  });

  const { campo, dir } = state.orden;
  filas = filas.slice().sort((a, b) => {
    let d = 0;
    if (campo === "pendientes") {
      d = ORDEN_ESTADO[a.estado] - ORDEN_ESTADO[b.estado];
    } else if (campo === "nombre") {
      d = a.nombre.localeCompare(b.nombre, "es");
    } else if (campo === "categoria") {
      d = (a.categoria || "").localeCompare(b.categoria || "", "es");
    } else if (campo === "total") {
      d = a.total - b.total;
    }
    if (d === 0) d = a.nombre.localeCompare(b.nombre, "es");
    return d * dir;
  });
  return filas;
}

// ---------------------------------------------------------------- tabla
function renderTabla() {
  retirarSugerencias();             // F-042: el campo de obra se va a rehacer
  const cuerpo = $("#cuerpo");
  cuerpo.innerHTML = "";
  const visibles = trabajadoresVisibles();
  const totalBase = state.trabajadores.filter(
    (t) => t.activo || t.lineas.length
  ).length;
  const contador = $("#contador");
  if (contador) {
    contador.textContent = totalBase
      ? `Mostrando ${visibles.length} de ${totalBase}` +
        (state.seleccion.size ? ` · ${state.seleccion.size} seleccionados` : "")
      : "";
  }
  const vacio = $("#vacio");
  vacio.classList.toggle("oculto", state.trabajadores.length > 0 && visibles.length > 0);
  vacio.textContent = state.trabajadores.length === 0
    ? "No hay trabajadores. Pulsa «Sincronizar Sigrid» para cargar los maestros."
    : "Ningún trabajador cumple los filtros activos (buscador, columnas, chips o «Solo pendientes»).";
  $("#tabla").classList.toggle("oculto", state.trabajadores.length === 0);

  if (state.seleccionIde === null && visibles.length) {
    state.seleccionIde = visibles[0].ide;
  }
  visibles.forEach((t) => {
    cuerpo.appendChild(construirFila(t));
    if (t.ide === state.editandoIde) cuerpo.appendChild(construirFilaEditor());
  });
}

// Las filas de un trabajador (F-050, R22): una subfila por línea (al menos
// una, la de «sin carga»), todas con su `data-ide` y su `data-linea`. Las
// columnas del trabajador van en la primera y ocupan todas (`rowSpan`); obra
// y partida, una celda por subfila. Cursor, selección y clic, por trabajador.
function construirFila(t) {
  const frag = document.createDocumentFragment();
  const n = Math.max(1, t.lineas.length);
  for (let idx = 0; idx < n; idx++) {
    const tr = document.createElement("tr");
    tr.className = idx ? "fila subfila" : "fila";
    tr.dataset.ide = t.ide;
    tr.dataset.linea = idx;
    if (!t.activo) tr.classList.add("inactivo");
    if (t.ide === state.seleccionIde) tr.classList.add("seleccionada");
    if (state.seleccion.has(t.ide)) tr.classList.add("multi");
    if (t.ide === state.editandoIde) tr.classList.add("editando");

    state.columnas.forEach((clave) => {
      if (COLUMNAS_POR_LINEA.includes(clave)) {
        tr.appendChild(construirCelda(t, clave, idx));
      } else if (!idx) {
        const td = construirCelda(t, clave, idx);
        td.rowSpan = n;
        tr.appendChild(td);
      }
    });

    // Shift+clic no debe seleccionar el texto de la tabla (F-029, R2).
    tr.addEventListener("mousedown", (ev) => {
      if (ev.shiftKey) ev.preventDefault();
    });
    // Ctrl/Cmd+clic alterna, Shift+clic hace un rango: sin editor (F-029).
    tr.addEventListener("click", (ev) => {
      if (ev.ctrlKey || ev.metaKey || ev.shiftKey) {
        marcarSeleccion(t.ide, ev.shiftKey);
        return;
      }
      state.seleccionIde = t.ide;
      state.ancla = t.ide;
      fijarSeleccion([]);
      if (state.periodoEstado === "ABIERTO") abrirEditor(t.ide);
      else renderTabla();
    });
    frag.appendChild(tr);
  }
  return frag;
}

// ------------------------------------------- selección múltiple (F-029)
// Ctrl/Cmd+clic (`rango` falso): alterna la fila; si la selección estaba
// vacía, el cursor entra antes en ella. Shift+clic (`rango`): la selección
// pasa a ser el rango de filas VISIBLES, en su orden, entre el ancla (o el
// cursor, si no hay ancla visible) y la fila. Con `fijarSeleccion`, la única
// que escribe en `state.seleccion` (R7).
function marcarSeleccion(ide, rango) {
  if (rango) {
    const visibles = trabajadoresVisibles().map((t) => t.ide);
    const a = visibles.indexOf(
      visibles.includes(state.ancla) ? state.ancla : state.seleccionIde);
    const b = visibles.indexOf(ide);
    if (a >= 0 && b >= 0) {
      const [desde, hasta] = a <= b ? [a, b] : [b, a];
      state.seleccion = new Set(visibles.slice(desde, hasta + 1));
      state.seleccionIde = ide;
      renderTabla();
      return;
    }
  }
  const estaba = state.seleccion.has(ide);
  if (state.seleccion.size === 0 && state.seleccionIde !== null)
    state.seleccion.add(state.seleccionIde);
  if (estaba) state.seleccion.delete(ide);
  else state.seleccion.add(ide);
  state.seleccionIde = ide;
  state.ancla = ide;
  renderTabla();
}

// Fija la selección múltiple tal cual (vacía con `[]`). Es la puerta por la
// que F-021 la llenará desde Sesame; no mira los filtros (R7).
function fijarSeleccion(ides) {
  const habia = state.seleccion.size > 0;
  state.seleccion = new Set(ides);
  if (habia || state.seleccion.size > 0) renderTabla();
}

// ------------------------------------------- completar al 100 % (F-029)
// Lo que falta hasta el 100 % lo calcula la API (R12): aquí solo se elige a
// quién y en qué obra, se pregunta y se pinta lo que responde.

// Selección efectiva (D6): la múltiple ∩ visibles; sin múltiple, el cursor.
function seleccionEfectiva() {
  const visibles = trabajadoresVisibles();
  if (state.seleccion.size) {
    return visibles.filter((t) => state.seleccion.has(t.ide));
  }
  return visibles.filter((t) => t.ide === state.seleccionIde);
}

// Entradas del catálogo del cuadrante (normal y `Postv-` por separado, D2)
// que casan con el texto, con la misma comparación que el autocompletado
// del editor (D1); las de código exacto, primero. Sin texto, ninguna.
function candidatasDestino(texto) {
  const q = normalizar(texto);
  if (!q) return [];
  const casan = state.catalogoObras.filter((e) => e.clave.includes(q));
  const exactas = casan.filter((e) => normalizar(e.cod) === q);
  return exactas.concat(casan.filter((e) => !exactas.includes(e)));
}

// Botón «Completar al 100 %» y tecla C (D4): abre el diálogo (R8-R11).
function abrirCompletar() {
  if (state.periodoEstado !== "ABIERTO") return;
  if (state.editandoIde !== null) {
    toast("Cierra el editor (Esc) antes de completar al 100 %", true);
    return;
  }
  if (!$("#modal-registro").classList.contains("oculto")) return;
  const filas = seleccionEfectiva();
  if (!filas.length) {
    toast("No hay trabajadores seleccionados a la vista", true);
    return;
  }
  const ocultos = state.seleccion.size ? state.seleccion.size - filas.length : 0;
  const nombres = filas.map((t) => `<li>${escapeHtml(t.nombre)}</li>`).join("");
  abrirModal(
    `<h2>Completar al 100 % · ${MESES[state.mes - 1]} ${state.anio}</h2>` +
    '<div class="motivo">A cada uno se le pone en la obra elegida lo que le ' +
    "falta hasta el 100 %. Quien ya está al 100 % o por encima no se toca. " +
    "No se registra nada en Sigrid.</div>" +
    '<h3>Obra destino</h3><input id="completar-obra" class="input" ' +
    'autocomplete="off" placeholder="Obra o Postv- (código o nombre)…">' +
    '<div id="completar-candidatas" class="completar-candidatas"></div>' +
    '<div id="completar-elegida" class="completar-elegida"></div>' +
    `<h3>Trabajadores (${filas.length})</h3>` +
    `<ul class="completar-nombres">${nombres}</ul>` +
    (ocultos
      ? `<div class="aviso">${ocultos} seleccionado(s) quedan fuera por ` +
        "estar ocultos por los filtros.</div>"
      : "") +
    '<div class="pie-modal"><button class="btn secondary" ' +
    'id="btn-completar-cancelar">Cancelar (Esc)</button>' +
    '<button class="btn primary" id="btn-completar-confirmar">' +
    "Completar (Enter)</button></div>"
  );
  montarDialogoCompletar(filas);
}

// Destino: el campo se precarga con «Filtrar obra…»; una candidata queda
// elegida, varias se eligen con ↑ ↓ (o clic), ninguna: se escribe (R10).
// Ninguna tecla del diálogo llega a `teclas` (R11).
function montarDialogoCompletar(filas) {
  const modal = $("#modal-registro .modal");
  const input = $("#completar-obra");
  const lista = $("#completar-candidatas");
  let candidatas = [];
  let activa = -1;
  let enviando = false;

  const pintar = () => {
    lista.innerHTML = "";
    candidatas.forEach((e, i) => {
      const fila = document.createElement("div");
      fila.className = "sugerencia" + (i === activa ? " activa" : "") +
        (e.pv ? " es-pv" : "");
      fila.innerHTML =
        `<span class="cod">${escapeHtml(e.cod)}</span>` +
        `<span class="desc">${escapeHtml(e.obra.descripcion)}</span>`;
      fila.addEventListener("mousedown", (ev) => {
        ev.preventDefault();
        activa = i;
        pintar();
      });
      lista.appendChild(fila);
    });
    const elegida = candidatas[activa];
    $("#completar-elegida").innerHTML = elegida
      ? `Destino: <strong>${escapeHtml(elegida.cod)}</strong> · ` +
        `${escapeHtml(elegida.obra.descripcion)}`
      : (input.value
        ? "Ninguna obra del cuadrante casa con ese texto."
        : "Escribe el código o el nombre de la obra.");
    const boton = $("#btn-completar-confirmar");
    if (boton) boton.disabled = !elegida || enviando;
  };
  const refrescar = () => {
    candidatas = candidatasDestino(input.value).slice(0, 14);
    activa = candidatas.length ? 0 : -1;
    pintar();
  };
  const confirmar = () => {
    const elegida = candidatas[activa];
    if (!elegida || enviando) return;
    enviando = true;
    pintar();
    lanzarCompletar(elegida, filas).finally(() => {
      enviando = false;
      if ($("#completar-obra") === input) pintar();
    });
  };

  input.addEventListener("keydown", (ev) => {
    ev.stopPropagation();
    if (ev.key === "ArrowDown" && candidatas.length) {
      ev.preventDefault();
      activa = Math.min(activa + 1, candidatas.length - 1);
      pintar();
    } else if (ev.key === "ArrowUp" && candidatas.length) {
      ev.preventDefault();
      activa = Math.max(activa - 1, 0);
      pintar();
    } else if (ev.key === "Enter") { ev.preventDefault(); confirmar(); }
    else if (ev.key === "Escape") { ev.preventDefault(); cerrarModal(); }
  });
  input.addEventListener("input", refrescar);
  // Fuera del campo (los botones), tampoco llega nada a `teclas`.
  modal.addEventListener("keydown", (ev) => {
    ev.stopPropagation();
    if (ev.key === "Escape") cerrarModal();
  });
  $("#btn-completar-cancelar").addEventListener("click", cerrarModal);
  $("#btn-completar-confirmar").addEventListener("click", confirmar);

  input.value = state.filtrosCol.asignaciones || "";
  refrescar();
  input.focus();
}

// Manda el lote: solo quiénes y el destino, ninguna cifra (R12). Si va
// bien, pinta el resultado, vacía la selección (R6) y recarga el cuadrante;
// si no, enseña el motivo y conserva la selección (R13).
async function lanzarCompletar(entrada, filas) {
  try {
    const datos = await api(
      `/periodos/${state.anio}/${state.mes}/completar`,
      { method: "POST", body: JSON.stringify({
          trabajadores: filas.map((t) => t.ide),
          obra_ide: entrada.obra.ide,
          es_postventa: entrada.pv,
        }) });
    pintarResultadoCompletar(entrada, datos.resultados);
    fijarSeleccion([]);
    await cargarPeriodo(state.anio, state.mes);
  } catch (err) {
    toast(err.message, true);
  }
}

// Resultado por trabajador, con su nombre, tal y como lo da la API (R13).
function pintarResultadoCompletar(entrada, resultados) {
  const TEXTO_RESULTADO = {
    COMPLETADO: "completado",
    YA_AL_100: "sin cambios: ya estaba al 100 %",
    EXCESO: "sin cambios: está por encima del 100 %",
    NO_VIGENTE: "sin cambios: no vigente en el mes",
    NO_VISIBLE: "sin cambios: no visible con la empresa elegida",
  };
  const filas = resultados.map((r) => {
    const t = trabajadorPorIde(r.trabajador_ide);
    const nombre = t ? t.nombre : `Trabajador ${r.trabajador_ide}`;
    const texto = (TEXTO_RESULTADO[r.resultado] || r.resultado) +
      (r.resultado === "COMPLETADO" ? ` (+${fmtPct(r.anadido)})` : "");
    return `<tr><td>${escapeHtml(nombre)}</td><td>${escapeHtml(texto)}</td></tr>`;
  }).join("");
  abrirModal(
    `<h2>Completar al 100 % en ${escapeHtml(entrada.cod)}</h2>` +
    `<div class="motivo">${escapeHtml(entrada.obra.descripcion)}</div>` +
    '<table class="tabla-reg"><thead><tr><th>Trabajador</th>' +
    `<th>Resultado</th></tr></thead><tbody>${filas}</tbody></table>` +
    '<div class="pie-modal"><button class="btn primary" ' +
    'id="btn-completar-cerrar">Cerrar</button></div>'
  );
  $("#modal-registro .modal").addEventListener("keydown", (ev) => {
    ev.stopPropagation();
    if (ev.key === "Escape" || ev.key === "Enter") {
      ev.preventDefault();
      cerrarModal();
    }
  });
  const cerrar = $("#btn-completar-cerrar");
  cerrar.addEventListener("click", cerrarModal);
  cerrar.focus();
}

function construirCelda(t, clave, idx) {
  const td = document.createElement("td");
  if (clave === "nombre") {
    td.className = "celda-nombre";
    td.innerHTML =
      `<span class="nombre">${escapeHtml(t.nombre)}</span>` +
      (t.activo ? "" : '<span class="tag-baja">BAJA</span>') +
      (t.empresa === null
        ? '<span class="tag-sin-empresa" title="Sin empresa en el maestro">' +
          "sin empresa</span>"
        : "");
  } else if (clave === "categoria") {
    td.className = "celda-categoria";
    td.textContent = t.categoria || "—";
  } else if (clave === "asignaciones") {
    // F-050 (R22): solo la línea de esta subfila.
    const chips = document.createElement("div");
    chips.className = "celda-chips";
    const l = t.lineas[idx];
    if (!l) {
      chips.innerHTML = '<span class="sin-carga-texto">sin carga</span>';
    } else {
      const chip = document.createElement("span");
      chip.className = "chip-linea" + (l.es_postventa ? " pv" : "") +
        (l.ofrecible ? "" : " obra-baja") +
        (l.otra_empresa ? " chip-otra-empresa" : "");
      chip.title = l.descripcion +
        (l.ofrecible ? "" : " (la obra ya no se ofrece en este modo)") +
        (l.otra_empresa
          ? " · la obra no es de la empresa de las obras: no se registrará"
          : "");
      chip.innerHTML =
        `<span class="cod">${escapeHtml(etiquetaObra(l.cod, l.es_postventa))}</span>` +
        `<span class="pct">${fmtPct(l.porcentaje)}</span>`;
      chips.appendChild(chip);
    }
    td.appendChild(chips);
  } else if (clave === "partida") {
    // F-050 (R24, R25): la elegida, la fija de una entrada o «automática»;
    // con el periodo abierto, el clic abre el selector (no el editor).
    td.className = "celda-partida";
    const l = t.lineas[idx];
    if (!l) return td;
    if (l.partida_fija) {
      td.classList.add("fija");
      td.innerHTML = `<span class="partida-fija" title="Partida fija de la entrada">${escapeHtml(l.descripcion)}</span>`;
    } else if (l.partida_ide != null) {
      td.innerHTML = `<span class="partida-elegida">${escapeHtml(textoPartida(l))}</span>`;
    } else {
      td.innerHTML = '<span class="partida-auto">automática</span>';
    }
    if (state.periodoEstado === "ABIERTO" && !l.partida_fija) {
      td.classList.add("editable");
      td.addEventListener("click", (ev) => {
        ev.stopPropagation();
        abrirSelectorPartida(t.ide, l.obra_ide, l.es_postventa, td);
      });
    }
  } else if (clave === "total") {
    td.className = "celda-total num";
    td.appendChild(badgeTotal(t.total, t.estado));
    if (t.lineas.length && state.periodoEstado === "ABIERTO") {
      const btnS = document.createElement("button");
      btnS.className = "btn-deshacer-fila btn-sigrid-fila";
      btnS.textContent = "⇪ Sigrid";
      btnS.title = "Registrar en Sigrid solo este trabajador";
      btnS.addEventListener("click", (ev) => {
        ev.stopPropagation();
        registroPreflight(t.ide);
      });
      td.appendChild(btnS);
    }
    if (t.puede_deshacer && state.periodoEstado === "ABIERTO") {
      const btn = document.createElement("button");
      btn.className = "btn-deshacer-fila";
      btn.textContent = "↩";
      btn.title = "Deshacer última modificación (Ctrl+Z)";
      btn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        deshacer(t.ide);
      });
      td.appendChild(btn);
    }
  }
  return td;
}

// Total: ✓ OK · ✗ con lo que falta o sobra hasta el 100 %.
function badgeTotal(total, estado) {
  const span = document.createElement("span");
  span.className = "total-badge";
  const diff = Math.round(Math.abs(100 - total) * 100) / 100;
  if (estado === "OK") {
    span.classList.add("t-ok");
    span.innerHTML =
      `<span class="marca-estado">✓</span><span>${fmtPct(total)}</span>`;
  } else if (estado === "FALTA") {
    span.classList.add("t-falta");
    span.innerHTML =
      `<span class="marca-estado">✗</span><span>${fmtPct(total)}</span>` +
      `<span class="detalle">falta ${fmtPct(diff)}</span>`;
  } else if (estado === "EXCESO") {
    span.classList.add("t-sobra");
    span.innerHTML =
      `<span class="marca-estado">✗</span><span>${fmtPct(total)}</span>` +
      `<span class="detalle">sobra ${fmtPct(diff)}</span>`;
  } else {
    span.classList.add("t-sin");
    span.innerHTML = "<span>— sin carga</span>";
  }
  return span;
}

// ---------------------------------------------------------------- editor
function trabajadorPorIde(ide) {
  return state.trabajadores.find((t) => t.ide === ide) || null;
}

async function abrirEditor(ide) {
  if (state.editandoIde === ide) return;
  if (state.editandoIde !== null) await cerrarEditor();
  const t = trabajadorPorIde(ide);
  if (!t) return;
  state.editandoIde = ide;
  state.edicion = t.lineas.map((l) => ({ ...l }));
  renderTabla();
  const editor = $("#cuerpo tr.fila-editor");
  if (editor) {
    const input = editor.querySelector(".obra-input");
    if (input) input.focus();
    editor.scrollIntoView({ block: "nearest" });
  }
}

async function cerrarEditor() {
  if (state.editandoIde === null) return;
  await guardarAhora();
  state.editandoIde = null;
  state.edicion = [];
  renderTabla();
}

function construirFilaEditor() {
  const tr = document.createElement("tr");
  tr.className = "fila-editor";
  const td = document.createElement("td");
  td.colSpan = state.columnas.length;
  const editor = document.createElement("div");
  editor.className = "editor";
  td.appendChild(editor);
  tr.appendChild(td);
  pintarEditor(editor);
  return tr;
}

function pintarEditor(editor) {
  editor.innerHTML = "";

  state.edicion.forEach((linea, idx) => {
    editor.appendChild(chipEditable(linea, idx, editor));
  });

  // --- añadir obra (normal o Postv-) ---
  const anadir = document.createElement("div");
  anadir.className = "anadir";
  const inputObra = document.createElement("input");
  inputObra.className = "obra-input";
  inputObra.placeholder = "Añadir obra o Postv- (código o nombre)…";
  inputObra.autocomplete = "off";
  anadir.appendChild(inputObra);
  // El panel de sugerencias NO va dentro de la fila: lo cuelga de <body>
  // montarAutocompletado (F-042).
  const sugerencias = document.createElement("div");
  sugerencias.className = "sugerencias oculto";
  editor.appendChild(anadir);
  montarAutocompletado(inputObra, sugerencias, editor);

  // --- total en vivo + indicador de guardado ---
  const total = totalEdicion();
  const badge = badgeTotal(total.suma, total.estado);
  badge.classList.add("total-vivo");
  editor.appendChild(badge);
  const guardando = document.createElement("span");
  guardando.className = "guardando";
  guardando.textContent = state.guardadoPendiente ? "●" : "✓";
  editor.appendChild(guardando);

  // --- acciones ---
  const acciones = document.createElement("div");
  acciones.className = "acciones-fila";
  const btnArriba = document.createElement("button");
  btnArriba.className = "btn secondary small";
  btnArriba.textContent = "⤒ Copiar fila superior (F7)";
  btnArriba.addEventListener("click", () => copiarDeArriba(state.editandoIde));
  const btnRepetir = document.createElement("button");
  btnRepetir.className = "btn secondary small";
  btnRepetir.textContent = "↺ Mes anterior (F8)";
  btnRepetir.addEventListener("click", () => copiarTrabajador(state.editandoIde));
  const btnSigrid = document.createElement("button");
  btnSigrid.className = "btn secondary small btn-sigrid-editor";
  btnSigrid.textContent = "⇪ Registrar en Sigrid";
  btnSigrid.title = "Registrar en Sigrid solo este trabajador";
  btnSigrid.addEventListener("click", async () => {
    const ide = state.editandoIde;
    await guardarAhora();              // no registrar sin guardar
    registroPreflight(ide);
  });
  const btnHecho = document.createElement("button");
  btnHecho.className = "btn primary small";
  btnHecho.textContent = "Hecho (Esc)";
  btnHecho.addEventListener("click", () => cerrarEditor());
  acciones.appendChild(btnArriba);
  acciones.appendChild(btnRepetir);
  acciones.appendChild(btnSigrid);
  acciones.appendChild(btnHecho);
  editor.appendChild(acciones);
}

function chipEditable(linea, idx, editor) {
  const chip = document.createElement("span");
  chip.className = "chip-edit" + (linea.es_postventa ? " pv" : "");

  const cod = document.createElement("span");
  cod.className = "cod";
  cod.textContent = etiquetaObra(linea.cod, linea.es_postventa);
  cod.title = linea.descripcion;
  chip.appendChild(cod);

  const pct = document.createElement("input");
  pct.className = "pct-input";
  pct.inputMode = "decimal";
  pct.value = linea.porcentaje ? String(linea.porcentaje).replace(".", ",") : "";
  pct.addEventListener("input", () => {
    linea.porcentaje = parsearPct(pct.value);
    refrescarTotalVivo(editor);
    programarGuardado();
  });
  // Si se deja en blanco, se rellena con lo que falta hasta el 100 %.
  pct.addEventListener("blur", () => {
    if (pct.value.trim() !== "") return;
    const restante = restanteSin(linea);
    if (restante > 0) {
      linea.porcentaje = restante;
      pct.value = String(restante).replace(".", ",");
      refrescarTotalVivo(editor);
      programarGuardado();
    }
  });
  pct.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") {
      ev.preventDefault();
      pct.blur();
      const inputObra = editor.querySelector(".obra-input");
      if (inputObra) inputObra.focus();
    }
  });
  chip.appendChild(pct);

  const btnPv = document.createElement("button");
  btnPv.className = "btn-pv" + (linea.es_postventa ? " activo" : "");
  btnPv.textContent = "PV";
  btnPv.title = "Alternar postventa";
  btnPv.addEventListener("click", () => {
    // F-025 (R23): solo a un modo que la API ofrece para esa obra.
    const ofrecido = linea.es_postventa ? linea.obra_activa : linea.obra_admite_postventa;
    if (!ofrecido) {
      toast(linea.es_postventa
        ? "Esa obra no se ofrece como obra normal"
        : "Esa obra no admite postventa", true);
      return;
    }
    const nuevaClave = `${linea.obra_ide}|${!linea.es_postventa}`;
    const duplicada = state.edicion.some(
      (l, i) => i !== idx && `${l.obra_ide}|${l.es_postventa}` === nuevaClave
    );
    if (duplicada) {
      toast("Ya existe esa obra en ese modo (normal/postventa)", true);
      return;
    }
    linea.es_postventa = !linea.es_postventa;
    pintarEditor(editor);
    programarGuardado();
  });
  chip.appendChild(btnPv);

  const btnX = document.createElement("button");
  btnX.className = "btn-x";
  btnX.textContent = "✕";
  btnX.title = "Quitar";
  btnX.addEventListener("click", () => {
    state.edicion.splice(idx, 1);
    pintarEditor(editor);
    programarGuardado();
  });
  chip.appendChild(btnX);

  return chip;
}

// ------------------------------------------- panel de sugerencias (F-042)
// El panel cuelga de <body> y es `position: fixed` (styles.css): ni
// `.panel { overflow: hidden }` ni `.panel-tabla { overflow-x: auto }` lo
// recortan, también en la última fila. Hay uno solo a la vez; esta variable
// guarda cómo quitar el vivo (su nodo y sus escuchas de scroll y resize).
let desmontarSugerencias = null;

// Dónde va el panel, en coordenadas de la ventana. `campo` es el
// getBoundingClientRect() del campo de obra, `alto` el alto natural del
// panel (con el tope de 280 px del CSS) y `ventana` {alto, ancho}. Debajo
// del campo; si ahí no cabe y encima hay más sitio, encima. Nunca se sale de
// la ventana: el ancho y el alto se limitan al sitio que hay.
function posicionSugerencias(campo, alto, ventana) {
  const HUECO = 4;     // entre el campo y el panel
  const MARGEN = 8;    // con el borde de la ventana
  const ancho = Math.min(430, ventana.ancho - 2 * MARGEN);
  const left = Math.max(MARGEN, Math.min(campo.left, ventana.ancho - MARGEN - ancho));
  const abajo = ventana.alto - campo.bottom - HUECO - MARGEN;
  const arriba = campo.top - HUECO - MARGEN;
  const haciaArriba = alto > abajo && arriba > abajo;
  const altoMax = Math.max(0, Math.min(alto, haciaArriba ? arriba : abajo));
  const top = haciaArriba ? campo.top - HUECO - altoMax : campo.bottom + HUECO;
  return { top, left, ancho, altoMax, haciaArriba };
}

// Coloca el panel junto al campo (si está abierto).
function colocarSugerencias(input, panel) {
  if (panel.classList.contains("oculto")) return;
  panel.style.maxHeight = "";       // alto natural, con el tope del CSS
  const pos = posicionSugerencias(input.getBoundingClientRect(), panel.offsetHeight, {
    alto: document.documentElement.clientHeight,
    ancho: document.documentElement.clientWidth,
  });
  panel.style.top = `${pos.top}px`;
  panel.style.left = `${pos.left}px`;
  panel.style.width = `${pos.ancho}px`;
  panel.style.maxHeight = `${pos.altoMax}px`;
}

// Quita el panel vivo y sus escuchas. La llaman renderTabla (cerrar el
// editor, cambiar de fila o repintar destruyen el campo) y
// montarAutocompletado antes de montar uno nuevo.
function retirarSugerencias() {
  if (desmontarSugerencias) desmontarSugerencias();
  desmontarSugerencias = null;
}

function montarAutocompletado(input, panel, editor) {
  let candidatas = [];
  let activa = -1;

  retirarSugerencias();
  document.body.appendChild(panel);
  const recolocar = () => colocarSugerencias(input, panel);
  // En captura: el scroll de `.panel-tabla` no burbujea hasta window.
  window.addEventListener("scroll", recolocar, true);
  window.addEventListener("resize", recolocar);
  desmontarSugerencias = () => {
    window.removeEventListener("scroll", recolocar, true);
    window.removeEventListener("resize", recolocar);
    panel.remove();
  };

  const refrescar = () => {
    const q = normalizar(input.value);
    candidatas = state.catalogoObras
      .filter((e) => !q || e.clave.includes(q))
      .slice(0, 14);
    activa = candidatas.length ? 0 : -1;
    panel.innerHTML = "";
    candidatas.forEach((e, i) => {
      const fila = document.createElement("div");
      fila.className = "sugerencia" + (i === activa ? " activa" : "") +
        (e.pv ? " es-pv" : "");
      fila.innerHTML =
        `<span class="cod">${escapeHtml(e.cod)}</span>` +
        `<span class="desc">${escapeHtml(e.obra.descripcion)}</span>`;
      fila.addEventListener("mousedown", (ev) => {
        ev.preventDefault();
        elegir(e);
      });
      panel.appendChild(fila);
    });
    panel.classList.toggle("oculto", !q || candidatas.length === 0);
    colocarSugerencias(input, panel);
  };

  const marcarActiva = () => {
    panel.querySelectorAll(".sugerencia").forEach((el, i) => {
      el.classList.toggle("activa", i === activa);
    });
  };

  const elegir = (entrada) => {
    input.value = "";
    panel.classList.add("oculto");
    const existente = state.edicion.find(
      (l) => l.obra_ide === entrada.obra.ide && l.es_postventa === entrada.pv
    );
    if (existente) {
      pintarEditor(editor);
      enfocarPct(editor, state.edicion.indexOf(existente));
      return;
    }
    const restante = 100 - totalEdicion().suma;
    state.edicion.push({
      obra_ide: entrada.obra.ide,
      cod: entrada.obra.cod,
      descripcion: entrada.obra.descripcion,
      es_postventa: entrada.pv,
      porcentaje: restante > 0 ? Math.round(restante * 100) / 100 : 100,
      // Las marcas de la obra, tal y como las da la API (las mira el botón
      // PV); el catálogo solo ofrece entradas ofrecibles.
      obra_activa: entrada.obra.activa,
      obra_admite_postventa: entrada.obra.admite_postventa,
      ofrecible: true,
    });
    pintarEditor(editor);
    enfocarPct(editor, state.edicion.length - 1);
    programarGuardado();
  };

  input.addEventListener("input", refrescar);
  input.addEventListener("focus", refrescar);
  input.addEventListener("keydown", (ev) => {
    const abierto = !panel.classList.contains("oculto");
    if (ev.key === "ArrowDown" && abierto) {
      ev.preventDefault();
      activa = Math.min(activa + 1, candidatas.length - 1);
      marcarActiva();
    } else if (ev.key === "ArrowUp" && abierto) {
      ev.preventDefault();
      activa = Math.max(activa - 1, 0);
      marcarActiva();
    } else if (ev.key === "Enter") {
      ev.preventDefault();
      if (abierto && activa >= 0) elegir(candidatas[activa]);
    } else if (ev.key === "Escape") {
      if (abierto) {
        panel.classList.add("oculto");
        ev.stopPropagation();
      } else {
        cerrarEditor();
      }
    }
  });
  input.addEventListener("blur", () => {
    setTimeout(() => panel.classList.add("oculto"), 150);
  });
}

function enfocarPct(editor, idx) {
  const inputs = editor.querySelectorAll(".pct-input");
  const input = inputs[idx];
  if (input) {
    input.focus();
    input.select();
  }
}

function parsearPct(texto) {
  const n = parseFloat(String(texto).replace(",", "."));
  if (!isFinite(n) || n <= 0) return 0;
  return Math.min(Math.round(n * 100) / 100, 100);
}

function totalEdicion() {
  const suma = state.edicion.reduce(
    (acc, l) => acc + (l.porcentaje > 0 ? l.porcentaje : 0), 0
  );
  const redondeada = Math.round(suma * 100) / 100;
  let estado = "SIN_CARGA";
  if (state.edicion.length) {
    if (Math.abs(redondeada - 100) <= 0.005) estado = "OK";
    else estado = redondeada < 100 ? "FALTA" : "EXCESO";
  }
  return { suma: redondeada, estado };
}

function restanteSin(lineaExcluida) {
  const suma = state.edicion.reduce((acc, l) => {
    if (l === lineaExcluida) return acc;
    return acc + (l.porcentaje > 0 ? l.porcentaje : 0);
  }, 0);
  return Math.max(Math.round((100 - suma) * 100) / 100, 0);
}

function refrescarTotalVivo(editor) {
  const badge = editor.querySelector(".total-vivo");
  if (!badge) return;
  const { suma, estado } = totalEdicion();
  const nuevo = badgeTotal(suma, estado);
  nuevo.classList.add("total-vivo");
  badge.replaceWith(nuevo);
}

// ------------------------------------------- selector de partida (F-050)
// Desplegable con buscador y botones Todas · CD · CI · CP (R25-R27). Lo usan
// la columna Partida y el modal de registro (R29). El front no decide nada:
// pinta lo que sirve la API (catálogo, mayor, propuesta, botón inicial) y
// guarda lo que se elige con `PUT …/partida`.
function clavePartidas(trabajadorIde, obraIde, esPostventa) {
  return [state.anio, state.mes, state.empresa, trabajadorIde, obraIde,
    esPostventa].join("|");
}

function cerrarSelectorPartida() {
  if (selector.cerrar) selector.cerrar();
  selector.cerrar = null;
}

// `ancla`: el elemento junto al que sale el panel; `despues`: lo que se hace
// tras guardar (el modal repite su análisis).
async function abrirSelectorPartida(trabajadorIde, obraIde, esPostventa, ancla, despues) {
  const rect = ancla.getBoundingClientRect();
  if (state.editandoIde === trabajadorIde) await guardarAhora();
  cerrarSelectorPartida();
  const clave = clavePartidas(trabajadorIde, obraIde, esPostventa);
  let resp = selector.cache.get(clave);
  if (!resp) {
    try {
      resp = await api(`/periodos/${state.anio}/${state.mes}/trabajadores/${trabajadorIde}/partidas?obra_ide=${obraIde}&es_postventa=${esPostventa}`);
    } catch (err) {
      toast(err.message, true);
      return;
    }
    selector.cache.set(clave, resp);
  }
  montarSelectorPartida(resp, {
    trabajadorIde, obraIde, esPostventa, ancla, rect, despues, clave,
  });
}

function montarSelectorPartida(resp, ctx) {
  cerrarSelectorPartida();
  const panel = document.createElement("div");
  panel.className = "panel-partida";
  panel.innerHTML =
    '<input class="buscar-partida" autocomplete="off" ' +
    'placeholder="Buscar partida (código o descripción)…">' +
    `<div class="mayores">${["", "CD", "CI", "CP"].map((m) =>
      `<button type="button" data-mayor="${m}">${m || "Todas"}</button>`).join("")}</div>` +
    '<div class="lista-partidas"></div>';
  document.body.appendChild(panel);
  const input = panel.querySelector(".buscar-partida");
  const lista = panel.querySelector(".lista-partidas");
  const base = {
    partidas: ctx.esPostventa ? resp.partidas_postventa : resp.partidas,
    propuesta: resp.propuesta,
  };
  let mayor = resp.ambito || null;
  let opciones = [];
  let activa = 0;

  // Junto a su ancla, como el panel de F-042; si el ancla se ha rehecho
  // (guardado del editor), donde estaba al abrir.
  const recolocar = () => {
    const pos = posicionSugerencias(
      ctx.ancla.isConnected ? ctx.ancla.getBoundingClientRect() : ctx.rect,
      panel.offsetHeight, {
        alto: document.documentElement.clientHeight,
        ancho: document.documentElement.clientWidth,
      });
    panel.style.top = `${pos.top}px`;
    panel.style.left = `${pos.left}px`;
    panel.style.width = `${pos.ancho}px`;
    panel.style.maxHeight = `${pos.altoMax}px`;
  };
  const elegir = async (op) => {
    if (!op) return;
    const partida = op.automatica ? null : { ide: op.ide, cod: op.cod, res: op.res };
    cerrarSelectorPartida();
    try {
      const datos = await api(
        `/periodos/${state.anio}/${state.mes}/trabajadores/${ctx.trabajadorIde}/partida`,
        { method: "PUT", body: JSON.stringify({ obra_ide: ctx.obraIde,
          es_postventa: ctx.esPostventa, partida }) });
      selector.cache.delete(ctx.clave);
      aplicarFila(datos);
      if (ctx.despues) ctx.despues();
    } catch (err) {
      toast(err.message, true);
    }
  };
  const pintar = () => {
    panel.querySelectorAll(".mayores button").forEach((b) =>
      b.classList.toggle("on", (b.dataset.mayor || null) === mayor));
    opciones = listaSelector(base, input.value, mayor).concat([{ automatica: true }]);
    activa = Math.min(activa, opciones.length - 1);
    lista.innerHTML = opciones.length === 1
      ? '<div class="vacio">Sin partidas con ese filtro</div>' : "";
    opciones.forEach((op, i) => {
      const fila = document.createElement("div");
      fila.className = "opcion" + (i === activa ? " activa" : "") +
        (op.propuesta ? " propuesta" : "") + (op.automatica ? " automatica" : "");
      fila.innerHTML = op.automatica
        ? '<span class="desc">automática (la propone el registro)</span>'
        : `<span class="cod">${escapeHtml(op.cod || "")}</span>` +
          `<span class="desc">${escapeHtml(op.res || "")}</span>` +
          (op.propuesta
            ? `<span class="origen">propuesta · ${escapeHtml(rotuloOrigen(resp.propuesta.metodo, resp.propuesta.origen))}</span>`
            : "");
      fila.addEventListener("mousedown", (ev) => {
        ev.preventDefault();
        elegir(op);
      });
      lista.appendChild(fila);
    });
    const viva = lista.querySelector(".opcion.activa");
    if (viva) viva.scrollIntoView({ block: "nearest" });
    recolocar();
  };

  const fuera = (ev) => {
    if (!panel.contains(ev.target)) cerrarSelectorPartida();
  };
  document.addEventListener("mousedown", fuera, true);
  window.addEventListener("scroll", recolocar, true);
  window.addEventListener("resize", recolocar);
  selector.cerrar = () => {
    document.removeEventListener("mousedown", fuera, true);
    window.removeEventListener("scroll", recolocar, true);
    window.removeEventListener("resize", recolocar);
    panel.remove();
  };

  panel.querySelectorAll(".mayores button").forEach((b) => {
    b.addEventListener("mousedown", (ev) => {
      ev.preventDefault();
      mayor = b.dataset.mayor || null;
      activa = 0;
      pintar();
    });
  });
  input.addEventListener("input", () => { activa = 0; pintar(); });
  // Sus teclas no llegan a `teclas` ni al modal: Esc cierra solo el panel.
  input.addEventListener("keydown", (ev) => {
    ev.stopPropagation();
    if (ev.key === "ArrowDown") {
      ev.preventDefault();
      activa = Math.min(activa + 1, opciones.length - 1);
      pintar();
    } else if (ev.key === "ArrowUp") {
      ev.preventDefault();
      activa = Math.max(activa - 1, 0);
      pintar();
    } else if (ev.key === "Enter") {
      ev.preventDefault();
      elegir(opciones[activa]);
    } else if (ev.key === "Escape") {
      ev.preventDefault();
      cerrarSelectorPartida();
    }
  });
  pintar();
  input.focus();
}

// ---------------------------------------------------------------- guardado
function programarGuardado() {
  state.guardadoPendiente = true;
  marcarGuardando("●");
  clearTimeout(state.timerGuardado);
  state.timerGuardado = setTimeout(guardarAhora, 700);
}

function marcarGuardando(simbolo) {
  const el = document.querySelector(".editor .guardando");
  if (el) el.textContent = simbolo;
}

async function guardarAhora() {
  clearTimeout(state.timerGuardado);
  if (!state.guardadoPendiente || state.editandoIde === null) return;
  const ide = state.editandoIde;
  const lineas = state.edicion
    .filter((l) => l.porcentaje > 0)
    .map((l) => ({
      obra_ide: l.obra_ide,
      es_postventa: l.es_postventa,
      porcentaje: l.porcentaje,
    }));
  try {
    const datos = await api(
      `/periodos/${state.anio}/${state.mes}/trabajadores/${ide}/asignaciones`,
      { method: "PUT", body: JSON.stringify({ lineas }) }
    );
    state.guardadoPendiente = false;
    aplicarFila(datos);
    marcarGuardando("✓");
  } catch (err) {
    marcarGuardando("!");
    toast("No se pudo guardar: " + err.message, true);
  }
}

function aplicarFila(datos) {
  const idx = state.trabajadores.findIndex(
    (t) => t.ide === datos.trabajador.ide
  );
  if (idx >= 0) state.trabajadores[idx] = datos.trabajador;
  state.resumen = datos.resumen;
  renderCabecera();
  if (state.editandoIde !== datos.trabajador.ide) {
    renderTabla();
  } else {
    refrescarCeldasFila(datos.trabajador);
  }
}

// Repinta las celdas de una fila SIN tocar el editor abierto (así los
// chips, el total y el botón de Sigrid reflejan lo ya guardado).
// F-050 (R22): rehace TODAS las subfilas del trabajador (pueden ser más o
// menos que antes); el editor, que va detrás, no se toca.
function refrescarCeldasFila(t) {
  const viejas = document.querySelectorAll(
    `#cuerpo tr.fila[data-ide="${t.ide}"]`);
  if (!viejas.length) return;
  viejas[0].before(construirFila(t));
  viejas.forEach((tr) => tr.remove());
}

// ---------------------------------------------------------------- acciones
async function deshacer(ide) {
  try {
    const datos = await api(
      `/periodos/${state.anio}/${state.mes}/trabajadores/${ide}/deshacer`,
      { method: "POST" }
    );
    if (state.editandoIde === ide) {
      state.edicion = datos.trabajador.lineas.map((l) => ({ ...l }));
      state.guardadoPendiente = false;
    }
    aplicarFila(datos);
    renderTabla();
    toast("Deshecho: " + datos.trabajador.nombre);
  } catch (err) {
    toast(err.message, true);
  }
}

// F8: repetir mes anterior del trabajador.
async function copiarTrabajador(ide) {
  if (ide === null) return;
  try {
    const datos = await api(
      `/periodos/${state.anio}/${state.mes}/trabajadores/${ide}/copiar-anterior`,
      { method: "POST" }
    );
    if (!datos.periodo_origen) {
      toast("No hay periodo anterior con datos", true);
      return;
    }
    if (state.editandoIde === ide) {
      state.edicion = datos.trabajador.lineas.map((l) => ({ ...l }));
      state.guardadoPendiente = false;
    }
    aplicarFila(datos);
    renderTabla();
    const extra = datos.lineas_omitidas_obra_inactiva
      ? ` (${datos.lineas_omitidas_obra_inactiva} líneas omitidas por obra inactiva)`
      : "";
    toast(
      `Copiado de ${MESES[datos.periodo_origen.mes - 1]} ` +
      `${datos.periodo_origen.anio}${extra}`
    );
  } catch (err) {
    toast(err.message, true);
  }
}

// F7: copiar las asignaciones de la fila inmediatamente superior.
async function copiarDeArriba(ide) {
  if (ide === null) return;
  const visibles = trabajadoresVisibles();
  const idx = visibles.findIndex((t) => t.ide === ide);
  if (idx <= 0) {
    toast("No hay fila superior de la que copiar", true);
    return;
  }
  const origen = visibles[idx - 1];
  const lineas = origen.lineas
    .filter((l) => l.ofrecible)
    .map((l) => ({
      obra_ide: l.obra_ide,
      es_postventa: l.es_postventa,
      porcentaje: l.porcentaje,
    }));
  if (!lineas.length) {
    toast(`${origen.nombre} no tiene asignaciones que copiar`, true);
    return;
  }
  try {
    const datos = await api(
      `/periodos/${state.anio}/${state.mes}/trabajadores/${ide}/asignaciones`,
      { method: "PUT", body: JSON.stringify({ lineas }) }
    );
    if (state.editandoIde === ide) {
      state.edicion = datos.trabajador.lineas.map((l) => ({ ...l }));
      state.guardadoPendiente = false;
    }
    aplicarFila(datos);
    renderTabla();
    toast(`Copiado de ${origen.nombre}`);
  } catch (err) {
    toast(err.message, true);
  }
}

async function copiarMesAnterior() {
  if (!confirm(
    "Copiar las asignaciones del último periodo con datos a los " +
    "trabajadores sin carga. No se pisa nada ya introducido. ¿Continuar?"
  )) return;
  try {
    const datos = await api(
      `/periodos/${state.anio}/${state.mes}/copiar-anterior`,
      { method: "POST" }
    );
    if (!datos.periodo_origen) {
      toast("No hay periodo anterior con datos", true);
      return;
    }
    toast(
      `Copiados ${datos.trabajadores_copiados} trabajadores desde ` +
      `${MESES[datos.periodo_origen.mes - 1]} ${datos.periodo_origen.anio} · ` +
      `${datos.con_carga_previa} ya tenían carga · ` +
      `${datos.sin_datos_origen} sin datos de origen`
    );
    await cargarPeriodo(state.anio, state.mes);
  } catch (err) {
    toast(err.message, true);
  }
}

async function sincronizar() {
  const boton = $("#btn-sync");
  boton.disabled = true;
  boton.textContent = "Sincronizando…";
  try {
    const datos = await api("/sync", { method: "POST" });
    toast(
      `Sigrid OK (${datos.duracion_s}s): ${datos.empleados.recibidos} empleados ` +
      `(+${datos.empleados.altas}/-${datos.empleados.desactivados}), ` +
      `${datos.obras.recibidos} obras ` +
      `(+${datos.obras.altas}/-${datos.obras.desactivados})`
    );
    await cargarPeriodo(state.anio, state.mes);
  } catch (err) {
    toast(err.message, true);
  } finally {
    boton.disabled = false;
    boton.textContent = "Sincronizar Sigrid";
  }
}

async function cambiarEstadoPeriodo(accion) {
  try {
    await api(`/periodos/${state.anio}/${state.mes}/${accion}`, {
      method: "POST",
    });
    await cargarPeriodo(state.anio, state.mes);
    toast(accion === "cerrar" ? "Periodo cerrado" : "Periodo reabierto");
  } catch (err) {
    toast(err.message, true);
  }
}

// ---------------------------------------------------------------- eventos
function enlazarEventos() {
  $("#btn-mes-prev").addEventListener("click", () => moverMes(-1));
  $("#btn-mes-next").addEventListener("click", () => moverMes(1));
  $("#btn-sync").addEventListener("click", sincronizar);
  $("#btn-copiar-mes").addEventListener("click", copiarMesAnterior);
  $("#btn-completar").addEventListener("click", abrirCompletar);
  $("#btn-export").addEventListener("click", () => {
    window.location.href =
      "/api/v1" + conEmpresa(`/periodos/${state.anio}/${state.mes}/export.xlsx`);
  });
  $("#selector-empresa").addEventListener("change", (ev) =>
    cambiarEmpresa(ev.target.value));
  $("#btn-cerrar").addEventListener("click", () => {
    if (confirm("¿Cerrar el periodo? Quedará en solo lectura.")) {
      cambiarEstadoPeriodo("cerrar");
    }
  });
  $("#btn-reabrir").addEventListener("click", () =>
    cambiarEstadoPeriodo("reabrir")
  );

  $("#buscador").addEventListener("input", (ev) => {
    state.filtroTexto = ev.target.value;
    renderTabla();
  });
  $("#buscador").addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") ev.target.blur();
    if (ev.key === "ArrowDown") {
      ev.preventDefault();
      ev.target.blur();
      moverSeleccion(0);
    }
  });
  const chkPendientes = $("#solo-pendientes");
  // Los navegadores restauran el estado del checkbox al recargar sin
  // disparar "change": se sincroniza con el estado real de la app.
  chkPendientes.checked = state.soloPendientes;
  chkPendientes.addEventListener("change", () => {
    state.soloPendientes = chkPendientes.checked;
    renderTabla();
  });

  document.addEventListener("keydown", teclas);
  window.addEventListener("beforeunload", () => {
    if (state.guardadoPendiente) guardarAhora();
  });
}

async function moverMes(delta) {
  await cerrarEditor();
  let mes = state.mes + delta;
  let anio = state.anio;
  if (mes < 1) { mes = 12; anio -= 1; }
  if (mes > 12) { mes = 1; anio += 1; }
  state.seleccionIde = null;
  state.filtroEstado = null;
  fijarSeleccion([]);
  await cargarPeriodo(anio, mes);
}

function teclas(ev) {
  const abierto = state.periodoEstado === "ABIERTO";
  const objetivo = state.editandoIde !== null
    ? state.editandoIde
    : state.seleccionIde;

  // F7 / F8 funcionan siempre (también dentro de inputs del editor).
  if (ev.key === "F7" && abierto && objetivo !== null) {
    ev.preventDefault();
    copiarDeArriba(objetivo);
    return;
  }
  if (ev.key === "F8" && abierto && objetivo !== null) {
    ev.preventDefault();
    copiarTrabajador(objetivo);
    return;
  }

  const enInput = ["INPUT", "TEXTAREA", "SELECT"].includes(
    document.activeElement.tagName
  );

  if (state.editandoIde !== null) {
    if (ev.key === "Escape" && !enInput) cerrarEditor();
    if (ev.key === "z" && (ev.ctrlKey || ev.metaKey)) {
      ev.preventDefault();
      deshacer(state.editandoIde);
    }
    return;
  }
  if (enInput) return;

  if (ev.key === "/") {
    ev.preventDefault();
    $("#buscador").focus();
  } else if (ev.key === "ArrowDown") {
    ev.preventDefault();
    moverSeleccion(1);
  } else if (ev.key === "ArrowUp") {
    ev.preventDefault();
    moverSeleccion(-1);
  } else if (ev.key === "Enter" && state.seleccionIde !== null) {
    if (abierto) abrirEditor(state.seleccionIde);
  } else if ((ev.key === "r" || ev.key === "R") && state.seleccionIde !== null) {
    if (abierto) copiarTrabajador(state.seleccionIde);
  } else if (ev.key === "z" && (ev.ctrlKey || ev.metaKey)) {
    if (state.seleccionIde !== null && abierto) {
      ev.preventDefault();
      deshacer(state.seleccionIde);
    }
  } else if (ev.key === "Escape" && state.seleccion.size) {
    fijarSeleccion([]);
  } else if ((ev.key === "c" || ev.key === "C") &&
             !ev.ctrlKey && !ev.metaKey && !ev.altKey) {
    if (abierto) abrirCompletar();
  }
}

function moverSeleccion(delta) {
  const visibles = trabajadoresVisibles();
  if (!visibles.length) return;
  let idx = visibles.findIndex((t) => t.ide === state.seleccionIde);
  if (idx === -1) idx = 0;
  else idx = Math.min(Math.max(idx + delta, 0), visibles.length - 1);
  state.seleccionIde = visibles[idx].ide;
  renderTabla();
  const tr = $(`#cuerpo tr.fila[data-ide="${state.seleccionIde}"]`);
  if (tr) tr.scrollIntoView({ block: "nearest" });
}

// ---------------------------------------------------------------- go
document.addEventListener("DOMContentLoaded", init);

// ------------------------------------------- Registro en Sigrid
// `pisar`: las claves de las casillas que se vuelven a marcar al repintar el
// modal (F-049); `seq`: la última petición de preflight (solo esa pinta);
// `lineas`: por `registro_id`, el trabajador, la obra y el modo de cada
// acción con selector de partida (F-050, R29). La partida elegida en el
// modal se GUARDA en el cuadrante: no viaja en el cuerpo del registro.
const registro = { pisar: new Set(), trabajadorIde: null, seq: 0, lineas: {} };

function abrirModal(html) {
  const ov = $("#modal-registro");
  ov.innerHTML = `<div class="modal">${html}</div>`;
  ov.classList.remove("oculto");
  ov.addEventListener("click", (e) => { if (e.target === ov) cerrarModal(); },
    { once: true });
}
function cerrarModal() { $("#modal-registro").classList.add("oculto"); }

// La partida que se escribiría en una acción (F-050, R29): su código aunque
// no esté en ningún catálogo, «partida N» sin código, «sin partida» sin
// ella (F-049 c). Texto plano: quien lo pinta lo escapa.
function textoPartidaAccion(a) {
  if (!a.paride) return "sin partida";
  return a.partida_cod || `partida ${a.paride}`;
}

// El preflight del periodo para el trabajador de la petición (todos o uno).
// Las partidas son las guardadas en el cuadrante (F-050, R29).
function pedirPreflight() {
  return api(
    `/periodos/${state.anio}/${state.mes}/registro/preflight`,
    { method: "POST", body: JSON.stringify({ trabajador_ide: registro.trabajadorIde }) });
}

async function registroPreflight(trabajadorIde = null) {
  registro.trabajadorIde = trabajadorIde;
  const seq = ++registro.seq;
  const btn = $("#btn-registro");
  btn.disabled = true; btn.textContent = "Analizando…";
  try {
    const pf = await pedirPreflight();
    if (seq !== registro.seq) return;
    registro.pisar = new Set();
    pintarModalPreflight(pf);
  } catch (err) { toast(err.message, true); }
  finally { btn.disabled = false; btn.textContent = "Registrar en Sigrid"; }
}

// F-049 (ampliación a): al cambiar una partida (F-050: ya guardada con el
// selector) se repite el preflight y se repinta, para que los avisos digan
// lo que se va a escribir. Las casillas marcadas se conservan por su clave. Mientras se
// analiza no se puede pulsar «Registrar»; solo pinta la última petición y
// nunca reabre un modal ya cerrado.
async function repreflightPartida() {
  const seq = ++registro.seq;
  const btn = $("#btn-ejecutar-registro");
  if (btn) { btn.disabled = true; btn.textContent = "Analizando…"; }
  try {
    const pf = await pedirPreflight();
    if (seq !== registro.seq) return;
    if ($("#modal-registro").classList.contains("oculto")) return;
    registro.pisar = new Set([...document.querySelectorAll(".chk-pisar:checked")]
      .map((c) => c.value));
    pintarModalPreflight(pf);
  } catch (err) {
    if (seq !== registro.seq) return;
    toast(err.message, true);
    if (btn) { btn.disabled = false; btn.textContent = "Registrar"; }
  }
}

// F-049: los avisos del preflight se rotulan según su `motivo`. Funciones
// puras (sin DOM): devuelven texto plano y quien lo pinta lo escapa. Solo
// formatean lo que manda el transfer (`Conflicto` serializado con `asdict`):
// no deciden qué se confirma ni qué se escribe. `can`, `suma_*` y `exceso`
// llegan en la escala 0-1 de Sigrid.

// % de lo que se escribiría: la suma de `nuevas`, como la propiedad
// `nueva_can` del `Conflicto` del transfer (que `asdict` no publica).
function pctNuevas(c) {
  const suma = (c.nuevas || []).reduce((s, n) => s + (Number(n.can) || 0), 0);
  return fmtPct(suma * 100);
}

function rotuloConflicto(c) {
  const quien = c.nombre || String(c.recurso_ide);
  const hora = c.hora_codigo || "";
  const enParte = c.parte_cod ? ` en el parte ${c.parte_cod}` : "";
  const nuevo = pctNuevas(c);
  const motivo = c.motivo || "pisado";
  if (motivo === "sin_partida") {
    return { tipo: motivo, titulo: "Sin partida",
      detalle: `${quien}, ${hora} ${nuevo}${enParte}: se escribiría sin ` +
        `partida de imputación. Elige una partida en la tabla o marca la ` +
        `casilla para escribirlo sin partida` };
  }
  if (motivo === "sobrecarga") {
    const ya = (c.contexto || []).map((l) =>
      `${l.hora_codigo || ""} ${fmtPct((Number(l.can) || 0) * 100)}`).join(", ");
    return { tipo: motivo, titulo: "Sobrecarga",
      detalle: `${quien}${enParte}: ya tiene ` +
        `${fmtPct(c.suma_existente * 100)}${ya ? ` (${ya})` : ""}, ` +
        `se añade ${nuevo} y sumaría ${fmtPct(c.suma_total * 100)}, un ` +
        `${fmtPct(c.exceso * 100)} por encima de la jornada. Marca la ` +
        `casilla para escribirlo igualmente` };
  }
  if (motivo === "pisado") {
    const viejas = (c.lineas || []).map((l) =>
      `línea ${l.ide} (${l.hora_codigo || ""} ` +
      `${fmtPct((Number(l.can) || 0) * 100)}, fec ${l.fecha_int})`).join(", ");
    return { tipo: motivo, titulo: "Pisar",
      detalle: `${hora} de ${quien}${enParte}: se borran ${viejas} y se ` +
        `escribe ${nuevo}` };
  }
  // Un motivo que este front aún no conoce no se disfraza de «Pisar»: se
  // enseña tal cual, con lo que se escribiría.
  return { tipo: motivo, titulo: "Confirmar",
    detalle: `${quien}, ${hora} ${nuevo}${enParte}: ${motivo}` };
}

function pintarModalPreflight(pf) {
  registro.lineas = {};
  let html = `<h2>Registrar en Sigrid · ${MESES[state.mes - 1]} ${state.anio}</h2>`;
  (pf.obras || []).forEach((o) => {
    html += `<h3>Obra ${escapeHtml(o.obra.codigo || "")} · ` +
      `${escapeHtml(o.obra.nombre || "")}</h3>`;
    if (!o.ok) { html += `<div class="conflicto">${escapeHtml(o.error || "error")}</div>`; return; }
    if (o.forzada_pruebas) {
      html += `<div class="aviso-pruebas">MODO PRUEBAS: se escribirá en la obra ` +
        `${escapeHtml(o.obra_destino.codigo || "")}</div>`;
    }
    (o.partes || []).forEach((p) => {
      html += `<div class="motivo">Parte ${p.ano}/${String(p.mes).padStart(2, "0")} ` +
        `(${escapeHtml(p.obra_cod || "")}): ${p.existe ? "existe" : "se creará"} ` +
        `${escapeHtml(p.cod || "")}</div>`;
    });
    const filas = (o.acciones || []).map((a) => {
      const aviso = a.aviso ? `<div class="aviso">${escapeHtml(a.aviso)}</div>` : "";
      // F-050 (R29): el botón con la partida de la línea; su clic abre el
      // MISMO selector que la columna Partida para esa línea.
      const botonPartida = (texto) => {
        registro.lineas[a.registro_id] = {
          trabajador: a.recurso_ide, obra_ide: o.obra.ide,
          es_postventa: a.es_postventa,
        };
        return `<button type="button" class="sel-partida" data-reg="${a.registro_id}">` +
          `${escapeHtml(texto)}</button>`;
      };
      let sel;
      if (a.accion === "escribir" && a.partida_metodo === "var") {
        // Partida VAR fija: la decide el transfer, no se edita (F-039).
        sel = `<span class="partida-fija">${escapeHtml(a.partida_cod || "")}</span>` + aviso;
      } else if (a.accion === "escribir") {
        // La partida a escribir y de dónde sale.
        const origen = rotuloOrigen(a.partida_metodo, a.partida_origen);
        sel = botonPartida(textoPartidaAccion(a)) +
          (origen ? `<div class="origen-partida">${escapeHtml(origen)}</div>` : "") +
          aviso;
      } else {
        // R29 (ampliación del 2026-10-10): la omitida por R20 (su elegida ya
        // no es hoja activa) también lleva el botón, con la partida que
        // nombra el motivo del transfer (MOTIVO_PARTIDA_NO_HOJA de
        // propuesta_partida.py). Solo se lee ese texto: el front no decide
        // qué partida vale. Sin motivo, exec(undefined) no casa.
        const r20 = /^la partida (.+) elegida no es una partida hoja activa del presupuesto de la obra /
          .exec(a.motivo);
        sel = (r20 ? botonPartida(r20[1]) : "") +
          `<span class="motivo">${escapeHtml(a.motivo || "")}</span>`;
      }
      return `<tr><td>${escapeHtml(a.nombre || "")}</td>` +
        `<td>${a.destino === "postventa" ? "Postventa" : "Obra"}</td>` +
        `<td>${a.accion}</td>` +
        `<td class="num">${a.can != null ? fmtPct(a.can * 100) : ""}</td>` +
        `<td>${escapeHtml(a.hora_codigo || "")}</td><td>${sel}</td></tr>`;
    }).join("");
    html += `<table class="tabla-reg"><thead><tr><th>Trabajador</th>` +
      `<th>Destino</th><th>Acción</th><th>%</th><th>Cód. hora</th>` +
      `<th>Partida de imputación (clic para cambiarla)</th></tr></thead>` +
      `<tbody>${filas}</tbody></table>`;
    (o.conflictos || []).forEach((c) => {
      // F-049: rótulo por tipo; la casilla sigue llevando la misma `clave`.
      const r = rotuloConflicto(c);
      html += `<div class="conflicto"><label class="check">` +
        `<input type="checkbox" class="chk-pisar" value="${escapeHtml(c.clave)}"` +
        `${registro.pisar.has(c.clave) ? " checked" : ""}> ` +
        `<strong>${escapeHtml(r.titulo)}</strong> · ${escapeHtml(r.detalle)}` +
        `</label></div>`;
    });
  });
  html += `<div class="pie-modal">` +
    `<button class="btn secondary" onclick="cerrarModal()">Cancelar</button>` +
    `<button class="btn primary" id="btn-ejecutar-registro">Registrar</button></div>`;
  abrirModal(html);
  document.querySelectorAll(".sel-partida").forEach((boton) => {
    boton.addEventListener("click", () => {
      const l = registro.lineas[boton.dataset.reg];
      abrirSelectorPartida(l.trabajador, l.obra_ide, l.es_postventa, boton, repreflightPartida);
    });
  });
  $("#btn-ejecutar-registro").addEventListener("click", registroEjecutar);
}

async function registroEjecutar() {
  const pisar = [...document.querySelectorAll(".chk-pisar:checked")]
    .map((c) => c.value);
  const btn = $("#btn-ejecutar-registro");
  btn.disabled = true; btn.textContent = "Registrando…";
  try {
    const r = await api(
      `/periodos/${state.anio}/${state.mes}/registro/ejecutar`,
      { method: "POST", body: JSON.stringify({
          pisar_claves: pisar, trabajador_ide: registro.trabajadorIde,
          usuario: document.body.dataset.usuario || "local" }) });
    let esc = 0, omi = 0, pend = 0;
    (r.obras || []).forEach((o) => {
      esc += (o.escritas || []).length; omi += (o.omitidas || []).length;
      pend += (o.pendientes_confirmacion || []).length;
    });
    cerrarModal();
    toast(`Sigrid: ${esc} escritas · ${omi} omitidas · ` +
      `${pend} pendientes de confirmar${pend ? " (repite y marca pisar)" : ""}`,
      !r.ok);
  } catch (err) { toast(err.message, true); }
}

document.addEventListener("DOMContentLoaded", () => {
  const b = $("#btn-registro");
  if (b) b.addEventListener("click", () => registroPreflight(null));
});
