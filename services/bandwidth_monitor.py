import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict

import redis.asyncio as redis

from config import settings


def _daily_key(date_str: str) -> str:
    return f"bandwidth:daily:{date_str}"


def _last_sample_key() -> str:
    return "bandwidth:last_sample"


def _minute_log_key(date_str: str) -> str:
    return f"bandwidth:minute:{date_str}"


async def _get_redis():
    return await redis.from_url(settings.redis_url, decode_responses=True)


def _read_counter(path: str) -> int:
    with open(path, "r", encoding="utf-8") as handle:
        return int(handle.read().strip())


def _read_interface_bytes(interface: str) -> Dict[str, int]:
    base_path = f"/sys/class/net/{interface}/statistics"
    rx_path = os.path.join(base_path, "rx_bytes")
    tx_path = os.path.join(base_path, "tx_bytes")
    return {
        "rx": _read_counter(rx_path),
        "tx": _read_counter(tx_path)
    }


async def sample_bandwidth():
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    r = await _get_redis()
    try:
        counters = _read_interface_bytes(settings.bandwidth_interface)
        total_bytes = counters["rx"] + counters["tx"]

        last_sample_raw = await r.get(_last_sample_key())
        last_sample = json.loads(last_sample_raw) if last_sample_raw else None
        delta = 0
        if last_sample and "total" in last_sample:
            delta = max(0, total_bytes - int(last_sample["total"]))

        await r.incrby(_daily_key(date_str), delta)
        await r.set(_last_sample_key(), json.dumps({
            "total": total_bytes,
            "rx": counters["rx"],
            "tx": counters["tx"],
            "timestamp": int(time.time())
        }))

        await r.lpush(_minute_log_key(date_str), json.dumps({
            "timestamp": int(time.time()),
            "delta_bytes": delta
        }))
        await r.ltrim(_minute_log_key(date_str), 0, 1440)
    finally:
        await r.close()


async def get_bandwidth_status() -> Dict:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    r = await _get_redis()
    try:
        total_bytes_raw = await r.get(_daily_key(date_str))
        total_bytes = int(total_bytes_raw) if total_bytes_raw else 0
        last_sample_raw = await r.get(_last_sample_key())
        last_sample = json.loads(last_sample_raw) if last_sample_raw else {}
    finally:
        await r.close()

    total_gb = total_bytes / (1024 ** 3)
    remaining_gb = max(0.0, settings.bandwidth_budget_gb - total_gb)
    status = "ok"
    if total_gb >= settings.bandwidth_critical_gb:
        status = "critical"
    elif total_gb >= settings.bandwidth_warn_gb:
        status = "warn"

    return {
        "date": date_str,
        "total_bytes": total_bytes,
        "total_gb": round(total_gb, 2),
        "budget_gb": settings.bandwidth_budget_gb,
        "warn_gb": settings.bandwidth_warn_gb,
        "critical_gb": settings.bandwidth_critical_gb,
        "remaining_gb": round(remaining_gb, 2),
        "status": status,
        "last_sample_ts": last_sample.get("timestamp")
    }


async def run_bandwidth_monitor():
    if not settings.bandwidth_monitor_enabled:
        return

    lock_key = "bandwidth:monitor:lock"
    lock_value = str(os.getpid())
    interval = max(10, settings.bandwidth_sample_interval_seconds)

    while True:
        r = await _get_redis()
        try:
            acquired = await r.set(lock_key, lock_value, nx=True, ex=interval + 30)
        finally:
            await r.close()

        if not acquired:
            await asyncio.sleep(interval)
            continue

        try:
            await sample_bandwidth()
        except Exception:
            pass

        await asyncio.sleep(interval)
