# scripts/mutantes_manuales_f034.py
"""Mutantes manuales de F-034 (design §10): los cambios de atributo
(`empresa_obras` <-> `empresa` / `por_defecto`) que el operador automático de
`harness.mutacion` no genera. Aplica cada mutante sobre el árbol, lanza la
suite de dedicacion-api (`pytest -x`) y RESTAURA el fichero, pase lo que pase.

Uso, desde la raíz del repositorio y con el árbol limpio:
    python scripts/mutantes_manuales_f034.py

Solo toca ficheros locales y la suite offline: ni red, ni BBDD, ni Sigrid.
Resultado y análisis: `progress/impl_F-034.md`, sección «Evidencias».
"""
import subprocess
import sys
from pathlib import Path

API = Path(__file__).resolve().parents[1] / "services" / "dedicacion-api"
PY = str(API / ".venv" / ("Scripts/python.exe" if sys.platform == "win32"
                          else "bin/python"))
M = [
 ("M1", "application/use_cases.py", "if o.empresa == filtro.empresa_obras", "if o.empresa == filtro.empresa"),
 ("M2", "application/use_cases.py", "if o.empresa == filtro.empresa_obras", "if o.empresa == filtro.por_defecto"),
 ("M3", "application/registro_sigrid.py", '"empresa": filtro.empresa_obras,', '"empresa": filtro.empresa,'),
 ("M4", "application/registro_sigrid.py", '"empresa": filtro.empresa_obras,', '"empresa": filtro.por_defecto,'),
 ("M5", "application/registro_sigrid.py", "empresa_obras=self._por_defecto)", "empresa_obras=empresa or self._por_defecto)"),
 ("M6", "interface_adapters/api/routes.py", "a_trabajador_out(f, filtro.empresa_obras) for f", "a_trabajador_out(f, filtro.empresa) for f"),
 ("M7", "interface_adapters/api/routes.py", "empresa_obras=empresa_imputacion)", "empresa_obras=empresa or empresa_imputacion)"),
 ("M8", "interface_adapters/api/routes.py", "por_defecto=empresa_imputacion,", "por_defecto=empresa or empresa_imputacion,"),
 ("M9", "domain/empresas.py", "    return filtro.empresa == filtro.por_defecto", "    return filtro.empresa == filtro.empresa_obras"),
 ("M10", "domain/empresas.py", "    return filtro.empresa == filtro.por_defecto", "    return filtro.empresa != filtro.por_defecto"),
 ("M11", "domain/empresas.py", "return empresa_trabajador == filtro.empresa", "return empresa_trabajador == filtro.empresa_obras"),
 ("M12", "interface_adapters/api/schemas.py", "linea_de_otra_empresa(ln.obra_empresa,\n                                                   empresa_obras)", "linea_de_otra_empresa(ln.obra_empresa,\n                                                   1)"),
]
# Las tres rutas por fila: una por una.
for i in range(3):
    M.append((f"M13.{i+1}", "interface_adapters/api/routes.py", ("trabajador=a_trabajador_out(fila, filtro.empresa_obras),", i), "trabajador=a_trabajador_out(fila, filtro.empresa),"))
for nombre, rel, viejo, nuevo in M:
    p = API / rel
    original = p.read_bytes()
    s = original.decode("utf-8")
    if isinstance(viejo, tuple):
        viejo, n = viejo
        partes = s.split(viejo)
        assert len(partes) == 4, nombre
        s = viejo.join(partes[:n+1]) + nuevo + viejo.join(partes[n+1:])
    else:
        assert s.count(viejo) == 1, nombre
        s = s.replace(viejo, nuevo)
    p.write_bytes(s.encode("utf-8"))
    try:
        r = subprocess.run([PY, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "tests"], cwd=API, capture_output=True, text=True)
        ult = [l for l in r.stdout.splitlines() if l.startswith("FAILED")]
        print(nombre, "MUERTO" if r.returncode else "SOBREVIVE", rel, "|", ult[0][7:] if ult else r.stdout.splitlines()[-1])
    finally:
        p.write_bytes(original)
