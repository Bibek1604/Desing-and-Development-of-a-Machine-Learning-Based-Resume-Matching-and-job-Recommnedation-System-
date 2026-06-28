"""Lightweight parallel execution for read-heavy endpoints.

Runs independent callables concurrently on a thread pool. Django opens a DB
connection per worker thread, so each task closes its thread-local connections
when it finishes to avoid leaking them. A failing task is logged and yields
``None`` rather than breaking the whole response.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from django.db import connections

log = logging.getLogger("skillmatch.api")


def _wrap(fn: Callable):
    def runner():
        try:
            return fn()
        finally:
            connections.close_all()  # release this worker thread's DB connections
    return runner


def run_parallel(tasks: dict[str, Callable], max_workers: int = 8) -> dict:
    """Execute ``{key: callable}`` concurrently and return ``{key: result}``.

    Order-independent: results are keyed, so a slow task never blocks reading
    the others. Any task that raises is logged and returns ``None``.
    """
    if not tasks:
        return {}
    results: dict = {}
    workers = min(max_workers, len(tasks))
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="sm-parallel") as pool:
        futures = {pool.submit(_wrap(fn)): key for key, fn in tasks.items()}
        for fut, key in futures.items():
            try:
                results[key] = fut.result()
            except Exception as exc:  # noqa: BLE001
                log.warning("parallel task %r failed: %s", key, exc)
                results[key] = None
    return results
