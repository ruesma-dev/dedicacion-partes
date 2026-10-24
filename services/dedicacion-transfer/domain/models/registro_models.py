# domain/models/registro_models.py
"""Modelos del registro de la dedicación mensual (porcentajes) en Sigrid.

Estructuras de datos del proceso: qué entra, qué hay ya en el parte y qué
se propone hacer. No deciden nada; las reglas que las gobiernan viven en
`docs/ARCHITECTURE.md` § Semántica de dominio imprescindible:

  - la forma de la línea que se escribe: ARCHITECTURE.md#regla-p2 y
    ARCHITECTURE.md#regla-p3;
  - cuándo dos líneas del parte son la MISMA:
    ARCHITECTURE.md#regla-conflicto;
  - cuánta jornada admite un parte: ARCHITECTURE.md#regla-capacidad;
  - qué pasa con una línea que no casa partida:
    ARCHITECTURE.md#regla-sin-partida;
  - a qué empresa pertenece la obra: ARCHITECTURE.md#regla-empresa;
  - la cuenta analítica de la línea y el parte del periodo que la recibe:
    ARCHITECTURE.md#regla-analitica (F-037, copia de la F-031 de `partes`).
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from typing import Optional


# ----------------------------- entrada ----------------------------- #

@dataclass
class LineaEntrada:
    """Una asignación de dedicación (trabajador/obra/mes) a registrar."""
    registro_id: int                    # id de la asignación en PostgreSQL
    ano: int
    mes: int
    porcentaje: float                   # sobre 1: 40 % -> 0.4
    # Recurso del trabajador (`res.ide`), el que manda la API: se usa tal
    # cual, el transfer no lo elige (ARCHITECTURE.md#regla-recurso, F-026).
    recurso_ide: Optional[int] = None
    dni: Optional[str] = None
    nombre: Optional[str] = None
    categoria: Optional[str] = None     # para casar la partida (CI) del recurso
    es_postventa: bool = False
    # Override manual desde el front: si viene, manda sobre el automático.
    paride: Optional[int] = None
    partida_cod: Optional[str] = None
    # Empresa (`con.emp`) a la que se imputa la línea. Sin ella no se adivina
    # nada: ver ARCHITECTURE.md#regla-empresa.
    empresa: Optional[int] = None
    # F-039: partida VAR de una entrada `VAR-NN` del cuadrante. Si viene, la
    # partida es esa y solo esa, o la línea se omite: ver
    # ARCHITECTURE.md#regla-var.
    var_paride: Optional[int] = None
    # F-055 (R8, R16): la propuesta guardada en el cuadrante de una línea
    # automática (sin elegida). Si vale (hoja activa del presupuesto de la
    # obra de origen), se escribe con ella; si no, la línea es pendiente y
    # se propone como hoy (R6). Ver ARCHITECTURE.md#regla-partida.
    propuesta_paride: Optional[int] = None
    propuesta_cod: Optional[str] = None
    propuesta_res: Optional[str] = None
    propuesta_metodo: Optional[str] = None
    propuesta_origen: Optional[str] = None
    # F-051 (R14): `hmores.ide` de la línea que ya escribimos para esta
    # asignación (`asignacion.sigrid_hmores_ide`); None si la api no lo
    # tiene. Localiza lo nuestro aunque su `synckey` sea de otro sistema.
    hmores_ide: Optional[int] = None

    @property
    def fecha_int(self) -> int:
        """Último día del mes: fec de las líneas porcentuales."""
        ultimo = calendar.monthrange(int(self.ano), int(self.mes))[1]
        return int(f"{int(self.ano)}{int(self.mes):02d}{ultimo:02d}")


@dataclass
class IncidenciaEntrada:
    """F-030 (R23): una incidencia del cuadrante (vacaciones, baja…) a
    registrar en el parte de su obra: dos líneas, ver
    ARCHITECTURE.md#regla-incidencia. `id` es el de la incidencia en
    PostgreSQL; `desde` y `hasta`, días del mes ya completados por la API;
    `paride`, la partida de la línea de % del trabajador en esa obra o 0.

    Anexo R30 (R39): la traza de la api de una ya registrada, por rol, el
    `hmores.ide` y el día de su línea en Sigrid (None si no consta)."""
    id: int
    recurso_ide: int | None
    empresa: int | None
    codigo: str
    ano: int
    mes: int
    desde: int | None
    hasta: int | None
    paride: int | None = 0
    hmores_ide_ini: int | None = None
    hmores_ide_fin: int | None = None
    dia_ini: int | None = None
    dia_fin: int | None = None
    # F-062 (R15, R24): la obra de la incidencia (para la cadena entre obras,
    # D11) y, si su `fin` es un `CIZ` ajeno que movimos, su día original.
    obra_ide: int | None = None
    dia_fin_antes: int | None = None


@dataclass
class ObraEntrada:
    ide: Optional[int] = None
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    # `con.emp` de la ficha resuelta en Sigrid (ARCHITECTURE.md#regla-empresa).
    empresa: Optional[int] = None


# ----------------------------- Sigrid ----------------------------- #

@dataclass
class HoraRecurso:
    """Tipo de hora dado de alta al recurso en reshor."""
    horide: int
    cod: str
    res: Optional[str]
    pre: float
    # F-037 (R2): código de la cuenta analítica de `reshor.caaide` (la
    # plantilla del recurso para este tipo de hora) y si este tipo es el
    # tipo por defecto del recurso (`reshor.horide = res.horide`). Con valor
    # por defecto: los `HoraRecurso(...)` posicionales siguen valiendo.
    caa_cod: Optional[str] = None
    defecto: bool = False

    @property
    def es_mensual(self) -> bool:
        """Códigos M* (MENC, MCAP, MJEFO…): mensual / porcentual."""
        return (self.cod or "").upper().startswith("M")


@dataclass(frozen=True)
class ParteSigrid:
    """F-037 (R9): un parte (`hmo`) del periodo tal como está en Sigrid, con
    su estado `con.est` (1 En registro, 3 Cerrado, 10 Imputado...)."""
    ide: int
    cod: Optional[str]
    est: Optional[int]


@dataclass(frozen=True)
class PartidaCuenta:
    """F-037 (R3): partida (`obrparpar`) y el código de su cuenta analítica
    (`con.cod` de `obrparpar.caaide`; None si no tiene)."""
    ide: int
    cod: Optional[str]
    caa_cod: Optional[str]


@dataclass(frozen=True)
class PartidaValida:
    """F-055 (R3, R4): una partida (`obrparpar`) leída por `ide`, con su
    obra, si es hoja (sin hijas de su misma obra, como
    `build_arbol_partidas`) y si está de alta (`tipdes = 0`)."""
    ide: int
    obride: int
    cod: Optional[str]
    res: Optional[str]
    es_hoja: bool
    activa: bool

    def vale_en(self, obra_ide: int) -> bool:
        """¿Es hoja activa del presupuesto de `obra_ide`? El mismo veredicto
        que `construir_catalogo` sobre el presupuesto entero (R4)."""
        return self.obride == int(obra_ide) and self.es_hoja and self.activa


@dataclass
class ParteDestino:
    """Parte de trabajo (hmo) de una obra y mes."""
    ano: int
    mes: int
    obra_cod: Optional[str] = None      # obra del parte (normal o postventa)
    existe: bool = False
    ide: Optional[int] = None
    cod: Optional[str] = None           # existente o propuesto
    creado: bool = False
    # F-037 (R15, contrato de `partes`): estado del elegido (None si es
    # nuevo), si es un complementario (el periodo tiene partes cerrados),
    # los códigos de los cerrados, todos los partes del periodo y el aviso.
    estado: Optional[int] = None
    complementario: bool = False
    cerrados: list[str] = field(default_factory=list)
    del_periodo: list[ParteSigrid] = field(default_factory=list)
    aviso: Optional[str] = None


@dataclass
class LineaSigrid:
    """Línea ya existente en Sigrid (para avisar de pisado)."""
    ide: int
    reside: int
    fecha_int: int
    horide: Optional[int]
    hora_codigo: Optional[str]
    can: Optional[float]
    tot: Optional[float]
    synckey: Optional[str]
    nuestra: bool = False               # la escribimos nosotros (synckey)
    paride: int = 0                     # partida/capítulo (postventa)
    # F-051 (R12, R18): lo que solo rellena `lineas_para_editar`, la lectura
    # previa a editar una línea: su parte (`hmoide`, código y `con.est`),
    # `pre`, cuenta analítica, `tex` y si tiene enlaces de Sigrid.
    hmoide: Optional[int] = None
    parte_cod: Optional[str] = None
    parte_est: Optional[int] = None
    pre: Optional[float] = None
    caaide: Optional[int] = None
    tex: Optional[str] = None
    enlazada: bool = False


# ----------------------------- salida ----------------------------- #

@dataclass
class AccionLinea:
    """Qué se hará con una línea de entrada."""
    registro_id: int
    accion: str                         # escribir | omitir | ya_registrado
    ano: int
    mes: int
    fecha_int: int
    nombre: Optional[str] = None
    motivo: Optional[str] = None
    recurso_ide: Optional[int] = None
    hora_ide: Optional[int] = None
    hora_codigo: Optional[str] = None
    can: Optional[float] = None         # porcentaje sobre 1
    pre: Optional[float] = None         # importe mensual del recurso
    tot: Optional[float] = None
    es_postventa: bool = False
    destino: str = "obra"               # obra | postventa
    paride: int = 0                     # partida de imputación
    partida_cod: Optional[str] = None
    partida_metodo: Optional[str] = None  # manual | auto_nombre |
                                          # auto_categoria | postventa |
                                          # var (F-039, fija) |
                                          # parte_anterior | ultimo_parte
    # F-050 (R6, R21): de dónde sale la partida propuesta («parte P · MM/AAAA
    # · obra O»); None si es elegida, casada, de postventa o VAR.
    partida_origen: str | None = None
    # F-055 (R9): descripción de la partida de imputación; None sin partida.
    partida_res: str | None = None
    # Aviso informativo que acompaña a la acción en la tabla del preflight.
    # Que haya aviso NO implica que la línea se vaya a escribir: si es el de
    # «sin partida», además viaja un Conflicto que la retiene hasta que
    # alguien confirme (ARCHITECTURE.md#regla-sin-partida).
    aviso: Optional[str] = None
    hmores_ide: Optional[int] = None    # si ya estaba registrada
    # F-051 (R3): la línea al 0 % que esta acción EDITA en vez de insertar
    # (lo leído: ide, hmoide, parte_cod, horide, hora_codigo, paride, can,
    # fecha_int, synckey); None si inserta.
    linea_cero: Optional[dict] = None
    # F-037 (R6, contrato de `partes`): cuenta analítica que se escribirá en
    # `hmores.caaide`. `caa_ide = 0` = sin cuenta (la línea se escribe
    # igual); `caa_motivo` None = cuenta resuelta; `caa_aviso` solo si la
    # obra podría arreglarse; `caa_origen` "recurso" | "partida" | None y
    # `caa_nota` si la subcuenta sale de la partida.
    caa_ide: int = 0
    caa_cod: Optional[str] = None
    caa_motivo: Optional[str] = None
    caa_aviso: Optional[str] = None
    caa_origen: Optional[str] = None
    caa_nota: Optional[str] = None
    # La CLAVE de conflicto de esta acción no se calcula aquí: sale de
    # `application.services.reglas_porcentajes.clave_conflicto`, junto al
    # criterio de choque que la tiene que respetar. Tenerla en dos capas es
    # lo que dejó que la clave y el criterio se desalinearan.


@dataclass
class AccionIncidencia:
    """F-030 (R24, R31): qué se hará con UNA de las dos líneas de una
    incidencia (`rol` `ini`: su `CI*` el día `desde`; `fin`: `CIZ` el día
    `hasta`). Lleva los campos que el paso de la cuenta analítica comparte
    con `AccionLinea` (`recurso_ide`, `hora_ide`, `paride`, `destino`,
    `aviso` y `caa_*`). Siempre `can = 0` y `tot = 0`: no son jornada.

    Anexo R30 (R41, R46): `editar` cambia SOLO la `fec` de la línea
    `hmores_ide` (en el parte `hmoide`) de `fec_antes` a `fecha_int`."""
    id: int
    rol: str                            # ini | fin
    accion: str                         # escribir | editar | omitir | ya_registrado
    fecha_int: int
    recurso_ide: int | None = None
    ano: int = 0
    mes: int = 0
    hora_ide: int | None = None
    hora_codigo: str | None = None
    pre: float = 0.0
    paride: int = 0
    motivo: str | None = None
    parte_cod: str | None = None
    hmores_ide: int | None = None
    destino: str = "obra"               # una incidencia no va a postventa
    aviso: str | None = None
    caa_ide: int = 0
    caa_cod: str | None = None
    caa_motivo: str | None = None
    caa_aviso: str | None = None
    caa_origen: str | None = None
    caa_nota: str | None = None
    fec_antes: int | None = None
    hmoide: int | None = None


@dataclass
class LineaIncidenciaSigrid:
    """F-030 (R27): una línea de incidencia (`CI*`/`CIZ`) del recurso ya
    escrita en algún parte del mes, con el código del parte. Anexo R30
    (R40-R43): su `can`, su parte (`hmoide`) y el estado del parte."""
    ide: int
    reside: int
    fecha_int: int
    hora_codigo: str | None
    synckey: str | None
    parte_cod: str | None
    can: float | None = None
    hmoide: int | None = None
    parte_est: int | None = None
    # F-062 (R5, R10, R12, design §6): la obra del parte, el centro, la
    # partida y la cuenta de la línea y la empresa del parte (`con.emp`).
    obride: int | None = None
    cenide: int | None = None
    paride: int | None = None
    caaide: int | None = None
    parte_emp: int | None = None


@dataclass
class Conflicto:
    """Algo que el humano tiene que confirmar antes de que se escriba.

    Hay TRES tipos, y los distingue ``motivo``:

    - ``"pisado"``: ya hay en el parte una línea que es LA MISMA que la
      nuestra (ARCHITECTURE.md#regla-conflicto). ``lineas`` son las que se
      EDITAN al confirmar (cualquier día del mes: incluye registros mal
      fechados fuera del último día): ``edita_ide`` la que pasa a ser la
      nuestra y ``a_cero_ides`` las que se ponen a 0 (F-051, R4-R5). Nunca
      se borra ninguna.
    - ``"sobrecarga"``: el trabajador se pasaría de la jornada del parte
      (ARCHITECTURE.md#regla-capacidad). **Nunca lleva ``lineas``**, porque
      una sobrecarga no borra nada: eso hace que sea cierto *por
      construcción* y no por una comprobación que alguien pueda quitar. Las
      líneas que ha contado viajan en ``contexto``, que es informativo.
    - ``"sin_partida"``: la línea se escribiría sin imputar a ninguna
      partida de la obra (ARCHITECTURE.md#regla-sin-partida). Tampoco lleva
      ``lineas``, y por el mismo motivo: no sustituye a nada. Es el único
      de los tres que es propiedad de UNA línea y no del parte, y por eso
      su ``clave`` va por ``registro_id``.

    ``contexto``: otras líneas mensuales del mismo recurso, solo
    informativas. ``nuevas``: lo que se escribiría. Los cuatro campos
    numéricos solo tienen contenido en la sobrecarga; el tercer motivo, que
    añadió F-013, no necesitó ni un campo más. Todos los campos añadidos por
    F-002 tienen valor por defecto para que un cliente que los ignore siga
    funcionando igual que antes.
    """
    clave: str
    recurso_ide: int
    nombre: Optional[str]
    ano: int
    mes: int
    parte_cod: Optional[str]
    horide: Optional[int] = None
    hora_codigo: Optional[str] = None
    lineas: list[LineaSigrid] = field(default_factory=list)
    contexto: list[LineaSigrid] = field(default_factory=list)
    nuevas: list[dict] = field(default_factory=list)
    registros: list[int] = field(default_factory=list)
    motivo: str = "pisado"              # pisado | sobrecarga | sin_partida
    suma_existente: float = 0.0         # jornada ya ocupada que se ha contado
    suma_total: float = 0.0             # suma_existente + nueva_can
    exceso: float = 0.0                 # suma_total - 1
    # F-051 (R4, R5): solo en el pisado.
    edita_ide: Optional[int] = None
    a_cero_ides: list[int] = field(default_factory=list)

    @property
    def nueva_can(self) -> float:
        return round(sum(float(n.get("can") or 0.0) for n in self.nuevas), 4)


@dataclass
class Preflight:
    """Resultado del análisis previo: qué se hará y qué hay que confirmar."""
    obra_destino: ObraEntrada
    obra_origen: ObraEntrada
    forzada_pruebas: bool
    partes: list[ParteDestino] = field(default_factory=list)
    acciones: list[AccionLinea] = field(default_factory=list)
    conflictos: list[Conflicto] = field(default_factory=list)
    # F-030 (R31): las dos líneas de cada incidencia; vacía sin incidencias.
    incidencias: list[AccionIncidencia] = field(default_factory=list)

    @property
    def n_escribir(self) -> int:
        return sum(1 for a in self.acciones if a.accion == "escribir")

    @property
    def n_omitir(self) -> int:
        return sum(1 for a in self.acciones if a.accion == "omitir")

    @property
    def n_ya(self) -> int:
        return sum(1 for a in self.acciones if a.accion == "ya_registrado")


@dataclass
class ResultadoRegistro:
    """Resultado de la escritura efectiva."""
    ok: bool
    obra_destino: ObraEntrada
    forzada_pruebas: bool
    partes: list[ParteDestino] = field(default_factory=list)
    escritas: list[dict] = field(default_factory=list)   # {registro_id, hmoide…}
    omitidas: list[dict] = field(default_factory=list)   # {registro_id, motivo}
    ya_registradas: list[int] = field(default_factory=list)
    pisadas: list[str] = field(default_factory=list)     # claves pisadas
    borradas: int = 0                   # F-051 (R19): siempre 0
    # F-051 (R16, R18): las líneas editadas y las puestas a 0, con lo que
    # tenían y lo que queda; `hmores.ide` de cada ya registrada.
    editadas: list[dict] = field(default_factory=list)
    a_cero: list[dict] = field(default_factory=list)
    ya_registradas_ide: dict[int, int] = field(default_factory=dict)
    pendientes_confirmacion: list[Conflicto] = field(default_factory=list)
    error: Optional[str] = None
    # F-030 (R31): las líneas de las incidencias, con su `hmores_ide` si se
    # escribieron; vacía sin incidencias.
    incidencias: list[AccionIncidencia] = field(default_factory=list)
