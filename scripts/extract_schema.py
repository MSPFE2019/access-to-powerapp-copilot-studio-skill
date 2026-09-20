#!/usr/bin/env python3
"""
Extract schema (tables, columns, types, relationships, indexes) from a
Microsoft Access database (.accdb/.mdb) into a JSON document that can be
used to plan a migration to SharePoint Lists or Dataverse.

Requires: pyodbc + "Microsoft Access Database Engine" driver (Windows),
or run via mdbtools on Linux/macOS as a fallback (see --mdbtools).

Usage:
    python extract_schema.py "C:\\path\\to\\database.accdb" --out schema.json
"""
import argparse
import json
import sys


def extract_with_pyodbc(db_path):
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
            continue  # skip system/temp tables

        table = {"name": table_name, "columns": [], "primary_keys": [],
                 "foreign_keys": [], "indexes": []}

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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("db_path", help="Path to .accdb or .mdb file")
    parser.add_argument("--out", default="schema.json", help="Output JSON path")
    args = parser.parse_args()

    try:
        schema = extract_with_pyodbc(args.db_path)
    except ImportError:
        print("pyodbc is not installed. Install it with: pip install pyodbc\n"
              "Also ensure the 'Microsoft Access Database Engine' driver is installed.\n"
              "On non-Windows systems, use mdbtools instead:\n"
              "  mdb-schema database.accdb access > schema.sql\n"
              "  mdb-tables database.accdb\n"
              "  mdb-export database.accdb TableName > table.csv",
              file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to extract schema: {e}", file=sys.stderr)
        sys.exit(1)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)

    print(f"Schema written to {args.out} "
          f"({len(schema['tables'])} tables extracted).")


if __name__ == "__main__":
    main()
