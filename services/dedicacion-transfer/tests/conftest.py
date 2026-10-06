# tests/conftest.py
"""Fixtures compartidas de la suite offline del transfer (F-002).

Ni red, ni BBDD, ni `.env`: el pipeline solo habla con el cliente que se le
inyecta, así que basta con un doble de ese cliente y un doble de los ajustes.

Lo que aporta sobre el cliente falso de `test_pipeline_offline.py` es que
todo lo que la feature necesita variar está **parametrizado**:

- ``presupuesto_postventa``: el árbol de la obra de postventa. Cuatro
  variantes: ``"hojas"`` (lo que devolvió la lectura real de Sigrid, con sus
  trampas: capítulo de código numérico, duplicados sin cero inicial y
  descripciones que empiezan por el código de otra obra), ``"capitulos"``
  (las obras originales con partidas dentro, así que dejan de ser hoja),
  ``"hojas_inactivas"`` (la partida de la obra original dada de baja) y
  ``"orden_invertido"`` (las mismas filas de ``"hojas"`` al revés).
- ``lineas_parte``: las líneas que ya existen en el parte del mes.
- ``synckeys``: las líneas que ya escribimos nosotros (idempotencia).
- ``obra_postventa_existe``: si la obra de postventa no está en Sigrid.

F-037 le añade, solo como doble y datos: el centro (`cenide`) de las cuatro
obras, la cuenta de plantilla de MENC y MJEFO, una cuenta por subcuenta en
cada centro (ninguna acción anterior gana aviso), partidas sin cuenta y los
partes del periodo derivados de ``parte`` en cada llamada.

Los `ide` son inventados y no coinciden con ningún dato real.
"""
from __future__ import annotations

import sys
from pathlib import Path

# El servicio se ejecuta desde su propia carpeta; los tests importan
# `application`/`domain` como lo hace `main.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from domain.models.registro_models import (
    HoraRecurso, LineaEntrada, LineaSigrid, ObraEntrada, ParteDestino,
    ParteSigrid,
)

#: Código de la obra de pruebas y de la obra de postventa usados por el
#: doble. No son configuración del servicio: son datos del test.
OBRA_PRUEBAS = "0404"
OBRA_ORIGEN = "0678"
OBRA_POSTVENTA = "POSTV2"
#: Obra de origen que existe en Sigrid pero no casa con ninguna partida de
#: la obra de postventa. Desde F-022 el pipeline resuelve la obra de origen
#: también en modo pruebas, así que el doble tiene que conocerla.
OBRA_SIN_PARTIDA_PV = "0001"
#: Empresa de todas las obras y líneas del doble (F-022, R19): la suite
#: anterior a F-022 sigue probando lo mismo, ahora con la empresa explícita.
EMPRESA = 1


class SettingsFalso:
    """Ajustes del transfer, sin pydantic ni `.env`."""

    def __init__(
        self,
        *,
        obra_pruebas_forzar: bool = True,
        postventa_registrar: bool = True,
        postventa_obra_cod: str = OBRA_POSTVENTA,
        marca_pruebas: str = "PRUEBA-PORC",
        paso_pos: int = 64,
    ) -> None:
        self.obra_pruebas_forzar = obra_pruebas_forzar
        self.obra_pruebas_cod = OBRA_PRUEBAS
        self.marca_pruebas = marca_pruebas
        self.postventa_registrar = postventa_registrar
        self.postventa_obra_cod = postventa_obra_cod
        self.paso_pos = paso_pos
        # F-037: estados del parte (`con.est`) como en `config/settings.py`.
        self.est_parte_activo = 1
        self.est_parte_cerrado = 3
        self.est_parte_imputado = 10


def _fila(ide: int, padide: int, pos: int, cod: str, res: str,
          tipdes: int = 0) -> dict:
    """Una fila de `obrparpar` tal y como la devuelve el cliente real.

    ``tipdes = 0`` es activa; cualquier otro valor, dada de baja."""
    return {"ide": ide, "padide": padide, "pos": pos, "tip": 1 if padide else 0,
            "cod": cod, "res": res, "tex": None, "tipdes": tipdes,
            "cosindide": None, "unimed": None}


#: Presupuesto de la obra de postventa con las obras originales como HOJAS.
#: Reproduce las trampas que documenta `progress/sigrid_F-002.md`:
#:
#: - las obras originales cuelgan de `CD` y no tienen hijos (225 hojas / 23
#:   capítulos en el presupuesto real);
#: - hay **capítulos con código numérico** (`3`, `4`, … `11`), que son los
#:   que podrían colarse como destino si la resolución no filtrara por hoja;
#: - hay partidas duplicadas **sin el cero inicial** colgando de la raíz
#:   (`656`, `664`), que son códigos DISTINTOS de `0656` y `0664`;
#: - hay partidas cuya DESCRIPCIÓN empieza por el código de otra obra, que
#:   es el tercer escalón de la cascada y no debe adelantar al exacto.
PRESUPUESTO_PV_HOJAS: list[dict] = [
    _fila(69000, 0, 0, "CD", "COSTES DIRECTOS"),
    _fila(70001, 69000, 1, "0678", "15 VIVIENDAS Y HOSTEL"),
    _fila(70002, 69000, 2, "0713", "CLUB DEPORTIVO"),
    _fila(70003, 69000, 3, "0656", "33+34 VIVIENDAS TOMARES"),
    _fila(70004, 69000, 4, "0664", "76 VIVIENDAS EN LOS GUINDOS"),
    _fila(70005, 69000, 5, "0999", "0664 VARIOS DE LOS GUINDOS"),
    _fila(70006, 69000, 6, "0998", "0777 OBRA SIN PARTIDA PROPIA"),
    # Capítulo de código numérico: tiene hijos, así que no es hoja.
    _fila(69100, 69000, 7, "11", "OBRAS VARIAS"),
    _fila(69110, 69100, 1, "11.01", "REPARACIONES"),
    # Duplicados sin cero inicial, colgando de la RAÍZ (no de CD).
    _fila(70050, 0, 8, "656", "33+34 VIVIENDAS TOMARES"),
    _fila(70051, 0, 9, "664", "76 VIVIENDAS EN LOS GUINDOS"),
]

#: El mismo, con la partida de la obra original DADA DE BAJA (`tipdes = 1`).
#: Una hoja inactiva no es destino válido: no se escribe contra ella.
PRESUPUESTO_PV_HOJAS_INACTIVAS: list[dict] = [
    _fila(69000, 0, 0, "CD", "COSTES DIRECTOS"),
    _fila(70001, 69000, 1, "0678", "15 VIVIENDAS Y HOSTEL", tipdes=1),
    _fila(70002, 69000, 2, "0713", "CLUB DEPORTIVO"),
]

#: Las MISMAS filas de `PRESUPUESTO_PV_HOJAS`, en orden inverso. Sigrid no
#: garantiza el orden de las filas de una consulta sin `ORDER BY`, así que
#: la partida elegida no puede depender de él.
PRESUPUESTO_PV_ORDEN_INVERTIDO: list[dict] = list(
    reversed(PRESUPUESTO_PV_HOJAS))

#: El mismo presupuesto con las obras originales como CAPÍTULOS: cada una
#: tiene partidas colgando, así que deja de ser hoja. Es el caso que hoy
#: nadie prueba y que decidiría D1.2.
PRESUPUESTO_PV_CAPITULOS: list[dict] = [
    _fila(69000, 0, 0, "CD", "COSTES DIRECTOS"),
    _fila(70001, 69000, 1, "0678", "15 VIVIENDAS Y HOSTEL"),
    _fila(70011, 70001, 1, "0678.MO", "MANO DE OBRA"),
    _fila(70012, 70001, 2, "0678.MAT", "MATERIALES"),
    _fila(70002, 69000, 2, "0713", "CLUB DEPORTIVO"),
    _fila(70021, 70002, 1, "0713.MO", "MANO DE OBRA"),
]

#: Presupuesto de la obra ORIGEN: capítulo CI con las partidas de mando.
PRESUPUESTO_ORIGEN: list[dict] = [
    _fila(80000, 0, 0, "CI", "COSTES INDIRECTOS"),
    _fila(80001, 80000, 1, "CI.1.10", "ENCARGADO (ACUNA)"),
    _fila(80002, 80000, 2, "CI.1.20", "JEFE DE OBRA"),
]

PRESUPUESTOS_PV = {
    "hojas": PRESUPUESTO_PV_HOJAS,
    "capitulos": PRESUPUESTO_PV_CAPITULOS,
    "hojas_inactivas": PRESUPUESTO_PV_HOJAS_INACTIVAS,
    "orden_invertido": PRESUPUESTO_PV_ORDEN_INVERTIDO,
}


class ClienteFalso:
    """Doble del cliente de escritura de Sigrid. No abre ningún socket.

    Registra en ``escritos`` las sentencias que el pipeline le habría
    mandado, que es lo único que se puede comprobar sin escribir de verdad.
    """

    def __init__(
        self,
        *,
        presupuesto_postventa: str = "hojas",
        lineas_parte: list[LineaSigrid] | None = None,
        synckeys: dict[str, LineaSigrid] | None = None,
        parte_existe: bool = True,
        obra_postventa_existe: bool = True,
    ) -> None:
        if presupuesto_postventa not in PRESUPUESTOS_PV:
            raise ValueError(
                f"presupuesto_postventa debe ser uno de "
                f"{sorted(PRESUPUESTOS_PV)}, no {presupuesto_postventa!r}")
        self.obra = ObraEntrada(ide=828942, codigo=OBRA_PRUEBAS,
                                nombre="PRUEBAS", empresa=EMPRESA)
        self.obra_pv = ObraEntrada(ide=999001, codigo=OBRA_POSTVENTA,
                                   nombre="POSTVENTA 2", empresa=EMPRESA)
        self.obra_origen = ObraEntrada(ide=555001, codigo=OBRA_ORIGEN,
                                       nombre="15 VIVIENDAS", empresa=EMPRESA)
        self.obra_sin_partida_pv = ObraEntrada(
            ide=555002, codigo=OBRA_SIN_PARTIDA_PV, nombre="SIN PARTIDA PV",
            empresa=EMPRESA)
        # F-037: centro de coste (`obr.cenide`) de cada obra.
        for o, cenide in ((self.obra, 828943), (self.obra_pv, 999002),
                          (self.obra_origen, 555101),
                          (self.obra_sin_partida_pv, 555102)):
            o.cenide = cenide
        self.capitulos = PRESUPUESTOS_PV[presupuesto_postventa]
        self.partidas_origen = PRESUPUESTO_ORIGEN
        self._obra_pv_existe = bool(obra_postventa_existe)
        # Recursos (F-026: los manda la API, el transfer no los elige):
        # 100 (viejo, sin M*) y 200 (MENC); 300 (solo horas de convenio, sin
        # M*); 400 (MJEFO). El 400 es el SEGUNDO trabajador con M*, y hace
        # falta para los casos en los que un recurso queda bloqueado y tiene
        # que quedar otro que sí se escriba.
        self.horas = {
            100: [HoraRecurso(1, "HLPE", None, 20.0)],
            200: [HoraRecurso(5, "MENC", None, 9000.0,
                              caa_cod="00000.CIMO03"),
                  HoraRecurso(9, "HEGR", None, 30.0)],
            300: [HoraRecurso(1, "HLPE", None, 20.0),
                  HoraRecurso(9, "HEGR", None, 30.0)],
            400: [HoraRecurso(6, "MJEFO", None, 11000.0,
                              caa_cod="00000.CIMO02")],
        }
        self.parte = ParteDestino(ano=2026, mes=7, existe=parte_existe,
                                  ide=777 if parte_existe else None,
                                  cod="PT26/00251" if parte_existe else None)
        self.lineas_parte = list(lineas_parte or [])
        self.synckeys = dict(synckeys or {})
        self.escritos: list[dict] = []
        # Lecturas de la obra de postventa y de presupuestos (F-025 R7): el
        # universo las hace UNA vez por petición, no una por obra.
        self.n_obra_por_codigo = 0
        self.n_capitulos_de_obra = 0

    # --- lecturas --- #
    def obra_por_codigo(self, cod, empresa):
        """Todas las obras del doble son de `EMPRESA` (F-022)."""
        self.n_obra_por_codigo += 1
        if empresa != EMPRESA:
            return None
        if cod == OBRA_PRUEBAS:
            return self.obra
        if cod == OBRA_POSTVENTA:
            return self.obra_pv if self._obra_pv_existe else None
        if cod == OBRA_ORIGEN:
            return self.obra_origen
        if cod == OBRA_SIN_PARTIDA_PV:
            return self.obra_sin_partida_pv
        return None

    def obra_por_ide(self, ide):
        return self.obra

    def capitulos_de_obra(self, obride):
        self.n_capitulos_de_obra += 1
        if obride == self.obra_pv.ide:
            return self.capitulos
        if obride == self.obra_origen.ide:
            return self.partidas_origen
        return []

    def horas_de_recursos(self, resides):
        return {r: self.horas.get(r, []) for r in resides}

    def partes_existentes(self, obra_ide, periodos):
        return {(p[0], p[1]): self.parte for p in periodos}

    def partes_del_periodo(self, obra_ide, ano, mes):
        """F-037: se deriva de ``parte`` EN CADA LLAMADA (En registro si
        existe), así la relectura tras crear ve el parte nuevo."""
        if not (self.parte.existe and self.parte.ide):
            return []
        return [ParteSigrid(int(self.parte.ide), self.parte.cod, 1)]

    def cuentas_de_centro(self, cenide, empresa, subcuentas):
        """F-037: UNA cuenta `<obra>.<subcuenta>` por subcuenta pedida."""
        obras = (self.obra, self.obra_pv, self.obra_origen,
                 self.obra_sin_partida_pv)
        cod = {getattr(o, "cenide", 0): o.codigo for o in obras}.get(cenide)
        return {s: [(90000 + i, f"{cod}.{s}")]
                for i, s in enumerate(sorted(subcuentas), start=1)}

    def partidas_de_lineas(self, parides):
        """F-037: las partidas del doble no tienen cuenta."""
        return {}

    def siguiente_cod_pt(self, ano, empresa=None):
        return "PT26/09999"

    def max_pos(self, hmoide):
        return 64

    def lineas_del_parte(self, hmoide, resides):
        return [l for l in self.lineas_parte if l.reside in set(resides)]

    def lineas_por_synckey(self, claves):
        return {k: v for k, v in self.synckeys.items() if k in set(claves)}

    # --- escrituras (solo se acumulan) --- #
    def stmts_crear_parte(self, **kw):
        return [{"sql": "crear", "parameters": kw}]

    def stmt_insert_linea(self, **kw):
        return {"sql": "insert", "parameters": kw}

    @staticmethod
    def stmt_borrar_linea(ide):
        return {"sql": "delete", "parameters": [ide]}

    def escribir(self, statements):
        self.escritos.extend(statements)
        return len(statements)

    # --- ayudas de aserción --- #
    def inserts(self) -> list[dict]:
        return [s["parameters"] for s in self.escritos if s["sql"] == "insert"]

    def borrados(self) -> list[int]:
        return [s["parameters"][0] for s in self.escritos
                if s["sql"] == "delete"]


def linea_previa(**kw) -> LineaSigrid:
    """Línea `M*` que ya está en el parte (la que provoca el conflicto)."""
    datos = dict(ide=5001, reside=200, fecha_int=20260715, horide=5,
                 hora_codigo="MENC", can=1.0, tot=9000.0, synckey=None,
                 paride=0)
    datos.update(kw)
    return LineaSigrid(**datos)


def linea(**kw) -> LineaEntrada:
    """Línea de entrada del cuadrante con valores por defecto sensatos."""
    datos = dict(registro_id=1, ano=2026, mes=7, porcentaje=0.4,
                 recurso_ide=200, nombre="Acuna Mera, Antonio",
                 categoria="Encargado", empresa=EMPRESA)
    datos.update(kw)
    return LineaEntrada(**datos)
