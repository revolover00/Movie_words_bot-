"""Expose a minimal failure location for the isolated database probe."""
import runpy
import traceback
try:
    runpy.run_path('scripts/probe_database_temp.py', run_name='__main__')
except Exception as exc:
    last = traceback.extract_tb(exc.__traceback__)[-1]
    print(f'::error title=Database probe failure::{type(exc).__name__} at {last.filename}:{last.lineno}', flush=True)
    raise SystemExit(1)
