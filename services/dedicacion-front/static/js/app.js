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
  total: {
    titulo: "Total",
    ancho: 190,
    ordenable: true,
    num: true,
    placeholder: "ok / falta / sobra…",
  },
};
const ORDEN_COLUMNAS_DEFECTO = ["nombre", "categoria", "asignaciones", "total"];
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
  seleccionIde: null,
  editandoIde: null,
  edicion: [],
  timerGuardado: null,
  guardadoPendiente: false,
};

// ---------------------------------------------------------------- utilidades
const $ = (sel) => document.querySelector(sel);

function normalizar(texto) {
  return (texto || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
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

async function api(ruta, opciones = {}) {
  const respuesta = await fetch("/api/v1" + ruta, {
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
        if (!validas.includes(c)) validas.push(c);
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
  // Cada obra activa se ofrece dos veces: normal y versión postventa.
  state.catalogoObras = [];
  state.obras
    .filter((o) => o.activa)
    .forEach((o) => {
      state.catalogoObras.push({
        obra: o, pv: false, cod: o.cod,
        clave: normalizar(o.cod + " " + o.descripcion),
      });
      state.catalogoObras.push({
        obra: o, pv: true, cod: "Postv-" + o.cod,
        clave: normalizar("postv postventa postv-" + o.cod + " " +
                          o.cod + " " + o.descripcion),
      });
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
  if (clave === "asignaciones") {
    return t.lineas
      .map((l) =>
        (l.es_postventa ? "postv postv-" : "") + l.cod + " " + l.descripcion
      )
      .join(" ");
  }
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
      if (filtro && !normalizar(textoColumna(t, clave)).includes(filtro)) {
        return false;
      }
    }
    if (!q) return true;
    const pajar = normalizar(
      t.nombre + " " + (t.categoria || "") + " " +
      t.lineas.map((l) => l.cod + " " + l.descripcion).join(" ")
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
  const cuerpo = $("#cuerpo");
  cuerpo.innerHTML = "";
  const visibles = trabajadoresVisibles();
  const totalBase = state.trabajadores.filter(
    (t) => t.activo || t.lineas.length
  ).length;
  const contador = $("#contador");
  if (contador) {
    contador.textContent = totalBase
      ? `Mostrando ${visibles.length} de ${totalBase}`
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

function construirFila(t) {
  const tr = document.createElement("tr");
  tr.className = "fila";
  tr.dataset.ide = t.ide;
  if (!t.activo) tr.classList.add("inactivo");
  if (t.ide === state.seleccionIde) tr.classList.add("seleccionada");
  if (t.ide === state.editandoIde) tr.classList.add("editando");

  state.columnas.forEach((clave) => {
    tr.appendChild(construirCelda(t, clave));
  });

  tr.addEventListener("click", () => {
    state.seleccionIde = t.ide;
    if (state.periodoEstado === "ABIERTO") abrirEditor(t.ide);
    else renderTabla();
  });
  return tr;
}

function construirCelda(t, clave) {
  const td = document.createElement("td");
  if (clave === "nombre") {
    td.className = "celda-nombre";
    td.innerHTML =
      `<span class="nombre">${escapeHtml(t.nombre)}</span>` +
      (t.activo ? "" : '<span class="tag-baja">BAJA</span>');
  } else if (clave === "categoria") {
    td.className = "celda-categoria";
    td.textContent = t.categoria || "—";
  } else if (clave === "asignaciones") {
    const chips = document.createElement("div");
    chips.className = "celda-chips";
    if (!t.lineas.length) {
      chips.innerHTML = '<span class="sin-carga-texto">sin carga</span>';
    } else {
      t.lineas.forEach((l) => {
        const chip = document.createElement("span");
        chip.className = "chip-linea" + (l.es_postventa ? " pv" : "") +
          (l.obra_activa ? "" : " obra-baja");
        chip.title = l.descripcion + (l.obra_activa ? "" : " (obra desactivada)");
        chip.innerHTML =
          `<span class="cod">${l.es_postventa ? "Postv-" : ""}` +
          `${escapeHtml(l.cod)}</span>` +
          `<span class="pct">${fmtPct(l.porcentaje)}</span>`;
        chips.appendChild(chip);
      });
    }
    td.appendChild(chips);
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
  const sugerencias = document.createElement("div");
  sugerencias.className = "sugerencias oculto";
  anadir.appendChild(sugerencias);
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
  cod.textContent = (linea.es_postventa ? "Postv-" : "") + linea.cod;
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

function montarAutocompletado(input, panel, editor) {
  let candidatas = [];
  let activa = -1;

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
      obra_activa: true,
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
function refrescarCeldasFila(t) {
  const tr = $(`#cuerpo tr.fila[data-ide="${t.ide}"]`);
  if (!tr) return;
  tr.innerHTML = "";
  state.columnas.forEach((clave) => tr.appendChild(construirCelda(t, clave)));
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
    .filter((l) => l.obra_activa)
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
  $("#btn-export").addEventListener("click", () => {
    window.location.href =
      `/api/v1/periodos/${state.anio}/${state.mes}/export.xlsx`;
  });
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
const registro = { overrides: {}, pisar: new Set(), trabajadorIde: null };

function abrirModal(html) {
  const ov = $("#modal-registro");
  ov.innerHTML = `<div class="modal">${html}</div>`;
  ov.classList.remove("oculto");
  ov.addEventListener("click", (e) => { if (e.target === ov) cerrarModal(); },
    { once: true });
}
function cerrarModal() { $("#modal-registro").classList.add("oculto"); }

function opcionesPartida(partidas, sel) {
  const ops = ['<option value="0">— sin partida —</option>'];
  (partidas || []).forEach((p) => {
    ops.push(`<option value="${p.ide}" ${p.ide === sel ? "selected" : ""}>` +
      `${escapeHtml(p.cod || "")} · ${escapeHtml(p.res || "")}</option>`);
  });
  return ops.join("");
}

async function registroPreflight(trabajadorIde = null) {
  registro.trabajadorIde = trabajadorIde;
  const btn = $("#btn-registro");
  btn.disabled = true; btn.textContent = "Analizando…";
  try {
    const pf = await api(
      `/periodos/${state.anio}/${state.mes}/registro/preflight`,
      { method: "POST", body: JSON.stringify({ overrides: registro.overrides,
          trabajador_ide: registro.trabajadorIde }) });
    registro.pisar = new Set();
    pintarModalPreflight(pf);
  } catch (err) { toast(err.message, true); }
  finally { btn.disabled = false; btn.textContent = "Registrar en Sigrid"; }
}

function pintarModalPreflight(pf) {
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
      const partidas = a.destino === "postventa" ? o.partidas_postventa
        : o.partidas_obra;
      const sel = a.accion === "escribir"
        ? `<select class="sel-partida" data-reg="${a.registro_id}">` +
          `${opcionesPartida(partidas, a.paride)}</select>` +
          (a.aviso ? `<div class="aviso">${escapeHtml(a.aviso)}</div>` : "")
        : `<span class="motivo">${escapeHtml(a.motivo || "")}</span>`;
      return `<tr><td>${escapeHtml(a.nombre || "")}</td>` +
        `<td>${a.destino === "postventa" ? "Postventa" : "Obra"}</td>` +
        `<td>${a.accion}</td>` +
        `<td class="num">${a.can != null ? fmtPct(a.can * 100) : ""}</td>` +
        `<td>${escapeHtml(a.hora_codigo || "")}</td><td>${sel}</td></tr>`;
    }).join("");
    html += `<table class="tabla-reg"><thead><tr><th>Trabajador</th>` +
      `<th>Destino</th><th>Acción</th><th>%</th><th>Cód. hora</th>` +
      `<th>Partida de imputación (editable)</th></tr></thead>` +
      `<tbody>${filas}</tbody></table>`;
    (o.conflictos || []).forEach((c) => {
      const viejas = (c.lineas || []).map((l) =>
        `línea ${l.ide} (fec ${l.fecha_int}, can ${l.can})`).join(", ");
      html += `<div class="conflicto"><label class="check">` +
        `<input type="checkbox" class="chk-pisar" value="${escapeHtml(c.clave)}"> ` +
        `Pisar ${escapeHtml(c.hora_codigo || "")} de ` +
        `${escapeHtml(c.nombre || String(c.recurso_ide))}: se borran ${viejas} ` +
        `y se escribe ${fmtPct(c.nueva_can != null ? c.nueva_can * 100 : 0)}` +
        `</label></div>`;
    });
  });
  html += `<div class="pie-modal">` +
    `<button class="btn secondary" onclick="cerrarModal()">Cancelar</button>` +
    `<button class="btn primary" id="btn-ejecutar-registro">Registrar</button></div>`;
  abrirModal(html);
  document.querySelectorAll(".sel-partida").forEach((sel) => {
    sel.addEventListener("change", () => {
      registro.overrides[sel.dataset.reg] = parseInt(sel.value, 10) || 0;
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
          pisar_claves: pisar, overrides: registro.overrides,
          trabajador_ide: registro.trabajadorIde,
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
