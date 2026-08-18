# domain/models/registro_models.py
"""Modelos del registro de la dedicación mensual (porcentajes) en Sigrid.

Una línea porcentual en el parte de trabajo (hmores) va SIEMPRE al último
día del mes, con el código de hora MENSUAL (M*) del recurso, can = el
porcentaje sobre 1 (40 % -> 0.4) y pre = el importe mensual del recurso en
reshor. La identidad de la línea en el parte es recurso + mes + código:
no hay día, por lo que un registro M* del mismo recurso y mes en OTRO día
también choca (y pisar lo corrige).
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
    empleado_ide: Optional[int] = None  # con/emp.ide (el transfer resuelve el recurso)
    recurso_ide: Optional[int] = None   # si ya viene resuelto, se respeta
    dni: Optional[str] = None
    nombre: Optional[str] = None
    categoria: Optional[str] = None     # para casar la partida (CI) del recurso
    es_postventa: bool = False
    # Override manual desde el front: si viene, manda sobre el automático.
    paride: Optional[int] = None
    partida_cod: Optional[str] = None

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


# ----------------------------- Sigrid ----------------------------- #

@dataclass
class HoraRecurso:
    """Tipo de hora dado de alta al recurso en reshor."""
    horide: int
    cod: str
    res: Optional[str]
    pre: float

    @property
    def es_mensual(self) -> bool:
        """Códigos M* (MENC, MCAP, MJEFO…): mensual / porcentual."""
        return (self.cod or "").upper().startswith("M")


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
    empleado_ide: Optional[int] = None
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
                                          # auto_categoria | postventa
    aviso: Optional[str] = None           # p.ej. partida no localizada
    hmores_ide: Optional[int] = None    # si ya estaba registrada

    @property
    def clave_conflicto(self) -> str:
        """recurso + MES + código + PARTIDA. Sin día (un registro M* del
        mismo recurso/mes en otro día también choca). La partida forma
        parte de la clave: en el parte de postventa un recurso puede tener
        una línea legítima por cada capítulo/obra."""
        return (f"{self.recurso_ide or 0}|{self.ano}{self.mes:02d}"
                f"|{self.hora_ide or 0}|{self.paride or 0}")


@dataclass
class Conflicto:
    """Ya hay línea(s) M* en Sigrid para ese parte + recurso + mes + código.

    ``lineas``: las que se BORRARÍAN al pisar (mismo código, cualquier día
    del mes — incluye registros mal fechados fuera del último día).
    ``contexto``: otras líneas MENSUALES del mismo recurso con OTRO código,
    solo informativas.
    ``nuevas``: lo que se escribiría en su lugar.
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
