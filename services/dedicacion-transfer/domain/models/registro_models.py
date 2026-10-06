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

    @property
    def fecha_int(self) -> int:
        """Último día del mes: fec de las líneas porcentuales."""
        ultimo = calendar.monthrange(int(self.ano), int(self.mes))[1]
        return int(f"{int(self.ano)}{int(self.mes):02d}{ultimo:02d}")


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
                                          # var (F-039, fija)
    # Aviso informativo que acompaña a la acción en la tabla del preflight.
    # Que haya aviso NO implica que la línea se vaya a escribir: si es el de
    # «sin partida», además viaja un Conflicto que la retiene hasta que
    # alguien confirme (ARCHITECTURE.md#regla-sin-partida).
    aviso: Optional[str] = None
    hmores_ide: Optional[int] = None    # si ya estaba registrada
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
class Conflicto:
    """Algo que el humano tiene que confirmar antes de que se escriba.

    Hay TRES tipos, y los distingue ``motivo``:

    - ``"pisado"``: ya hay en el parte una línea que es LA MISMA que la
      nuestra (ARCHITECTURE.md#regla-conflicto). ``lineas`` son las que se
      BORRARÍAN al confirmar (cualquier día del mes: incluye registros mal
      fechados fuera del último día).
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
    borradas: int = 0
    pendientes_confirmacion: list[Conflicto] = field(default_factory=list)
    error: Optional[str] = None
