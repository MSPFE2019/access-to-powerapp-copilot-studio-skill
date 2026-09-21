"""
Azure Function: extract-access-schema

HTTP-triggered function that accepts a base64-encoded .accdb/.mdb file and
returns a JSON schema document (tables, columns, types, relationships,
indexes) — the same shape produced by the local extract_schema.py script.

Deploy on a Linux Function App (Consumption or Premium) with mdbtools
installed via a custom container, OR on a Windows Function App/App Service
with the "Microsoft Access Database Engine" redistributable + pyodbc.
This version tries pyodbc first, falls back to mdbtools CLI.

Request body (POST), JSON:
{
  "fileName": "Database5.accdb",
  "fileContentBase64": "<base64 bytes of the .accdb file>"
}

Response body, JSON:
{
  "tables": [ ... ],
  "warnings": [ ... ]
}
"""
import base64
import json
import logging
import os
import shutil
import subprocess
import tempfile

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="extract-access-schema", methods=["POST"])
def extract_access_schema(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Request body must be JSON."}),
            status_code=400,
            mimetype="application/json",
        )

    file_name = body.get("fileName", "database.accdb")
    b64 = body.get("fileContentBase64")
    if not b64:
        return func.HttpResponse(
            json.dumps({"error": "fileContentBase64 is required."}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        raw = base64.b64decode(b64)
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": f"Invalid base64 content: {e}"}),
            status_code=400,
            mimetype="application/json",
        )

    tmp_dir = tempfile.mkdtemp(prefix="accdb_")
    db_path = os.path.join(tmp_dir, file_name)
    try:
        with open(db_path, "wb") as f:
            f.write(raw)

        schema, warnings = _extract(db_path)
        schema["warnings"] = warnings

        return func.HttpResponse(
            json.dumps(schema, indent=2),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as e:
        logging.exception("Schema extraction failed")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _extract(db_path: str):
    """Try pyodbc (Windows + Access driver) first, then mdbtools (Linux)."""
    warnings = []
    try:
        return _extract_with_pyodbc(db_path), warnings
    except ImportError:
        warnings.append("pyodbc not available; falling back to mdbtools.")
    except Exception as e:
        warnings.append(f"pyodbc extraction failed ({e}); falling back to mdbtools.")

    return _extract_with_mdbtools(db_path), warnings


def _extract_with_pyodbc(db_path: str):
    import pyodbc

    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        rf"DBQ={db_path};"
    )
    cnxn = pyodbc.connect(conn_str, autocommit=True)
    cursor = cnxn.cursor()

    schema = {"tables": []}

    for table_info in cursor.tables(tableType="TABLE"):
        table_name = table_info.table_name
        if table_name.startswith("MSys") or table_name.startswith("~"):
            continue

        table = {
            "name": table_name,
            "columns": [],
            "primary_keys": [],
            "foreign_keys": [],
            "indexes": [],
        }

        for col in cursor.columns(table=table_name):
            table["columns"].append({
                "name": col.column_name,
                "type": col.type_name,
                "size": col.column_size,
                "nullable": bool(col.nullable),
                "default": col.column_def,
            })

        try:
            for pk in cursor.primaryKeys(table=table_name):
                table["primary_keys"].append(pk.column_name)
        except Exception:
            pass

        try:
            for fk in cursor.foreignKeys(foreignTable=table_name):
                table["foreign_keys"].append({
                    "fk_column": fk.fkcolumn_name,
                    "pk_table": fk.pktable_name,
                    "pk_column": fk.pkcolumn_name,
                })
        except Exception:
            pass

        try:
            seen_idx = set()
            for idx in cursor.statistics(table=table_name):
                if idx.index_name and idx.index_name not in seen_idx:
                    seen_idx.add(idx.index_name)
                    table["indexes"].append({
                        "name": idx.index_name,
                        "unique": not bool(idx.non_unique),
                        "column": idx.column_name,
                    })
        except Exception:
            pass

        schema["tables"].append(table)

    cursor.close()
    cnxn.close()
    return schema


def _extract_with_mdbtools(db_path: str):
    """Fallback for Linux hosts: requires mdbtools installed in the container."""
    tables_out = subprocess.run(
        ["mdb-tables", "-1", db_path],
        capture_output=True, text=True, check=True,
    )
    table_names = [t for t in tables_out.stdout.splitlines() if t.strip()]

    schema = {"tables": []}
    for table_name in table_names:
        if table_name.startswith("MSys") or table_name.startswith("~"):
            continue

        schema_sql = subprocess.run(
            ["mdb-schema", db_path, "-T", table_name, "access"],
            capture_output=True, text=True, check=True,
        ).stdout

        columns = []
        for line in schema_sql.splitlines():
            line = line.strip().rstrip(",")
            if line and not line.upper().startswith(("CREATE", ")", "--", "COMMENT")):
                parts = line.split(None, 1)
                if len(parts) == 2:
                    columns.append({"name": parts[0].strip('`"'), "type": parts[1]})

        schema["tables"].append({
            "name": table_name,
            "columns": columns,
            "primary_keys": [],
            "foreign_keys": [],
            "indexes": [],
            "note": "Extracted via mdbtools; relationships/keys require manual review.",
        })

    return schema
