"""
Script standalone -- importa los gastos que la PWA mobile dejo en OneDrive.

No depende de que el backend FastAPI este corriendo (igual que restore.py
de Backup): solo necesita el paquete backend/ importable en el mismo venv.
Pensado para correr via Tarea Programada de Windows.

Las carpetas a recorrer se resuelven asi (en orden de prioridad):
  1. --carpetas si se paso explicito en la linea de comandos (override manual,
     util para probar una carpeta puntual sin tocar la config).
  2. Si no se paso, se leen de config_pwa_import.raices -- la misma fuente
     que ya usa pwa_export_service.py para exportar catalogos.json. Antes
     este script tenia --carpetas como obligatorio y la Tarea Programada
     lo invocaba con una ruta fija en scripts/_run_import_pwa.bat, sin
     ninguna relacion con lo que el usuario configura en la pantalla PWA
     del escritorio -- agregar una carpeta ahi actualizaba el export pero
     nunca hacia que este script la mirara. Ahora agregar una raiz en esa
     pantalla alimenta ambas direcciones (export de catalogos e import de
     gastos) desde el mismo lugar.

Por cada carpeta padre resuelta, recorre <carpeta>/pendientes/:
  1. Valida el JSON contra el schema esperado y contra los catalogos reales.
  2. Chequea archivos_mobile_procesados (por nombre de archivo) para no
     reprocesar si el script ya corrio sobre ese JSON antes.
  3. Si es valido y no-duplicado: inserta via pwa_import_service, con el
     mismo patron que el alta manual de escritorio (estado='confirmado',
     revisado_humano=1 -- no pasa por el Inbox, decision de diseno).
  4. Si hay foto: la copia a documentos_path.
  5. Mueve JSON (+foto) a <carpeta>/procesados/ si todo salio bien.
  6. Si el JSON es invalido o fallo la insercion: lo deja en pendientes/ y
     registra el error -- no lo mueve.
  7. Registra la corrida completa en log_ejecuciones_mobile.

Ejecucion:
    python -m scripts.import_pwa_gastos --ambiente dev
    python -m scripts.import_pwa_gastos --ambiente prod
    python -m scripts.import_pwa_gastos --ambiente dev --carpetas "C:\\ruta\\puntual"   (override manual)

Nota operativa: si OneDrive tiene "Ahorrar espacio" (Files On-Demand)
activo, la carpeta raiz de gastos debe estar marcada "Mantener siempre en
este dispositivo" -- si no, este script puede ver placeholders vacios en
vez del contenido real.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Importa gastos de la PWA mobile a la DB.")
    parser.add_argument("--ambiente", choices=["dev", "prod"], required=True)
    parser.add_argument("--carpetas", nargs="+", default=None,
                         help="Override manual: una o mas carpetas padre (cada una contiene "
                              "pendientes/ y procesados/). Si se omite, se leen de "
                              "config_pwa_import.raices.")
    return parser.parse_args()


async def resolver_carpetas(db, carpetas_cli: list[str] | None) -> list[str]:
    """Resuelve la lista de carpetas a procesar: el override de --carpetas
    si vino explicito, o config_pwa_import.raices (misma fuente que usa
    pwa_export_service.py para el export de catalogos.json)."""
    if carpetas_cli:
        return carpetas_cli

    from sqlalchemy import text
    raices_json = (await db.execute(
        text("SELECT raices FROM config_pwa_import WHERE id = 1")
    )).scalar_one_or_none()
    return json.loads(raices_json) if raices_json else []


async def procesar_carpeta(db, carpeta: str, documentos_dir: Path, alertas: list[dict], contadores: dict):
    from sqlalchemy import text
    from backend.services.pwa_import_service import importar_gasto

    carpeta_path = Path(carpeta)
    pendientes_dir = carpeta_path / "pendientes"
    procesados_dir = carpeta_path / "procesados"

    if not pendientes_dir.is_dir():
        alertas.append({"archivo": None, "motivo": f"Carpeta pendientes/ no encontrada en {carpeta}"})
        return

    procesados_dir.mkdir(parents=True, exist_ok=True)

    for json_path in sorted(pendientes_dir.glob("*.json")):
        nombre_archivo = json_path.name
        contadores["archivos_leidos"] += 1

        # 1. Idempotencia: si ya se proceso con exito (o quedo como duplicado),
        #    no reprocesar. Si quedo en 'error', reintentar.
        ya_registrado = (await db.execute(
            text("SELECT resultado FROM archivos_mobile_procesados WHERE nombre_archivo = :n"),
            {"n": nombre_archivo},
        )).scalar_one_or_none()
        if ya_registrado is not None and ya_registrado != "error":
            contadores["duplicados"] += 1
            continue

        # 2. Parsear JSON
        try:
            gasto = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            contadores["errores"] += 1
            alertas.append({"archivo": nombre_archivo, "motivo": f"JSON invalido: {e}"})
            await _registrar_archivo_procesado(db, nombre_archivo, gasto=None, resultado="error",
                                                dispositivo="desconocido")
            await db.commit()
            continue

        dispositivo = "iphone_ghr" if gasto.get("quien") == "GHR" else (
            "iphone_mc" if gasto.get("quien") == "MC" else "desconocido")

        # 3. Resolver imagen si el JSON declara una
        ruta_imagen_disco = None
        nombre_imagen_final = None
        tipo_mime_imagen = None
        nombre_imagen_json = gasto.get("imagen")
        if nombre_imagen_json:
            imagen_origen = pendientes_dir / nombre_imagen_json
            if not imagen_origen.is_file():
                contadores["errores"] += 1
                alertas.append({"archivo": nombre_archivo,
                                 "motivo": f"El JSON referencia una imagen que no existe: {nombre_imagen_json}"})
                await _registrar_archivo_procesado(db, nombre_archivo, gasto, resultado="error", dispositivo=dispositivo)
                await db.commit()
                continue
            ext = imagen_origen.suffix or ".jpg"
            doc_id = f"MOB-{gasto.get('id')}"
            destino = documentos_dir / f"{doc_id}{ext}"
            documentos_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(imagen_origen, destino)
            ruta_imagen_disco = str(destino)
            nombre_imagen_final = nombre_imagen_json
            tipo_mime_imagen = "image/jpeg" if ext.lower() in (".jpg", ".jpeg") else "image/png"

        # 4. Insertar
        resultado = await importar_gasto(db, gasto, ruta_imagen_disco, nombre_imagen_final, tipo_mime_imagen)

        if resultado.ok and resultado.motivo == "actualizado":
            contadores["actualizadas"] += 1
            await _registrar_archivo_procesado(
                db, nombre_archivo, gasto, resultado="actualizado", dispositivo=dispositivo,
                id_transaccion_creada=resultado.id_transaccion,
            )
            await db.commit()
            _mover_a_procesados(json_path, nombre_imagen_json, pendientes_dir, procesados_dir)
        elif resultado.ok:
            contadores["transacciones_nuevas"] += 1
            await _registrar_archivo_procesado(
                db, nombre_archivo, gasto, resultado="ok", dispositivo=dispositivo,
                id_transaccion_creada=resultado.id_transaccion,
            )
            await db.commit()
            _mover_a_procesados(json_path, nombre_imagen_json, pendientes_dir, procesados_dir)
        else:
            contadores["errores"] += 1
            await db.rollback()
            alertas.append({"archivo": nombre_archivo, "motivo": resultado.detalle})
            await _registrar_archivo_procesado(db, nombre_archivo, gasto, resultado="error", dispositivo=dispositivo)
            await db.commit()
            # No se mueve -- queda en pendientes/ para reintentar.


def _mover_a_procesados(json_path: Path, nombre_imagen_json: str | None, pendientes_dir: Path, procesados_dir: Path):
    shutil.move(str(json_path), str(procesados_dir / json_path.name))
    if nombre_imagen_json:
        origen_img = pendientes_dir / nombre_imagen_json
        if origen_img.is_file():
            shutil.move(str(origen_img), str(procesados_dir / nombre_imagen_json))


async def _registrar_archivo_procesado(db, nombre_archivo: str, gasto: dict | None, resultado: str,
                                        dispositivo: str, id_transaccion_creada: str | None = None):
    from sqlalchemy import text
    ahora = datetime.now(timezone.utc).isoformat()
    fecha_archivo = (gasto or {}).get("creado_en") or ahora
    await db.execute(
        text("""
            INSERT INTO archivos_mobile_procesados
                (nombre_archivo, dispositivo, fecha_archivo, tipo, fecha_procesado, resultado, id_transaccion_creada)
            VALUES (:nombre_archivo, :dispositivo, :fecha_archivo, 'gasto', :fecha_procesado, :resultado, :id_tx)
            ON CONFLICT(nombre_archivo) DO UPDATE SET
                fecha_procesado = excluded.fecha_procesado,
                resultado = excluded.resultado,
                id_transaccion_creada = excluded.id_transaccion_creada
        """),
        {
            "nombre_archivo": nombre_archivo,
            "dispositivo": dispositivo,
            "fecha_archivo": fecha_archivo,
            "fecha_procesado": ahora,
            "resultado": resultado,
            "id_tx": id_transaccion_creada,
        },
    )


async def run(ambiente: str, carpetas_cli: list[str] | None):
    # CRITICO: fijar ENV_FILE antes de importar backend.core.config -- ese
    # modulo lee la variable al definirse la clase Settings.Config.
    os.environ["ENV_FILE"] = ".env.dev" if ambiente == "dev" else ".env.prod"

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from backend.core.config import get_settings

    settings = get_settings()
    engine = create_async_engine(settings.db_url, echo=False)
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    fecha_inicio = datetime.now(timezone.utc).isoformat()
    contadores = {"archivos_leidos": 0, "transacciones_nuevas": 0, "actualizadas": 0, "duplicados": 0, "errores": 0}
    alertas: list[dict] = []

    async with SessionLocal() as db:
        carpetas = await resolver_carpetas(db, carpetas_cli)
        if not carpetas:
            alertas.append({"archivo": None, "motivo": "config_pwa_import.raices esta vacio -- "
                                                          "configura al menos una carpeta raiz en "
                                                          "Configuracion > PWA (o pasa --carpetas)."})
        for carpeta in carpetas:
            await procesar_carpeta(db, carpeta, Path(settings.documentos_path), alertas, contadores)

        # Regenera resumen_categorias.json (Home de la PWA, Bloque 4) al
        # mismo ritmo que ya corre esta tarea programada -- sin mecanismo de
        # scheduling nuevo. Un fallo aca no debe tumbar el import de gastos,
        # que ya termino e hizo commit por archivo.
        try:
            from backend.services.pwa_export_service import exportar_resumen_categorias_pwa
            await exportar_resumen_categorias_pwa(db)
        except Exception as e:
            alertas.append({"archivo": None, "motivo": f"No se pudo exportar resumen_categorias.json: {e}"})

        fecha_fin = datetime.now(timezone.utc).isoformat()
        notas = (
            f"Import PWA completado. Archivos: {contadores['archivos_leidos']}. "
            f"Nuevas: {contadores['transacciones_nuevas']}. "
            f"Actualizadas: {contadores['actualizadas']}. "
            f"Duplicados: {contadores['duplicados']}. Errores: {contadores['errores']}."
        )
        await db.execute(
            text("""
                INSERT INTO log_ejecuciones_mobile
                    (fecha_inicio, fecha_fin, archivos_leidos, transacciones_nuevas, actualizadas, duplicados, errores, alertas, notas)
                VALUES (:fi, :ff, :al, :tn, :ac, :du, :er, :alertas, :notas)
            """),
            {
                "fi": fecha_inicio, "ff": fecha_fin,
                "al": contadores["archivos_leidos"], "tn": contadores["transacciones_nuevas"],
                "ac": contadores["actualizadas"],
                "du": contadores["duplicados"], "er": contadores["errores"],
                "alertas": json.dumps({"errores": alertas}, ensure_ascii=False),
                "notas": notas,
            },
        )
        await db.commit()

    await engine.dispose()

    print(notas)
    if alertas:
        print("Alertas:")
        for a in alertas:
            print(f"  - {a.get('archivo')}: {a.get('motivo')}")
    return contadores


def main():
    args = parse_args()
    contadores = asyncio.run(run(args.ambiente, args.carpetas))
    sys.exit(1 if contadores["errores"] > 0 else 0)


if __name__ == "__main__":
    main()
