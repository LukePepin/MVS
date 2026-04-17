import asyncio
import contextlib
import math
import struct
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiofiles
import serial
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import insert, select

from .config import (
    CSV_QUEUE_MAXSIZE,
    HYBRID_SCHEMA_VERSION,
    MAX_MTTR_MS,
    SERIAL_BAUD,
    SERIAL_ENABLED,
    SERIAL_NODE_ID,
    SERIAL_PORT,
    SERIAL_READ_TIMEOUT_S,
    SERIAL_RECONNECT_WAIT_S,
    SERIAL_STALE_TIMEOUT_S,
    TRAINING_DATA_FILE,
    UDP_PACKET_BYTES,
    UDP_PACKET_FORMAT,
    UDP_PORT,
    UDP_STALE_TIMEOUT_SEC,
)
from .database import AsyncSessionLocal, engine
from .mock_telemetry import MockTelemetryEngine
from .models import Base, MachineStatus, RawInventory, SensorLogs, WorkOrders


@dataclass(slots=True)
class TelemetryPacket:
    node_id: str
    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float
    mag_x: float
    mag_y: float
    mag_z: float
    timestamp_iso: str


@dataclass(slots=True)
class LiveImuSample:
    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float
    host_time_iso: str
    device_time_iso: str | None
    host_time_monotonic: float


class TelemetryDatagramProtocol(asyncio.DatagramProtocol):
    def __init__(self, queue: asyncio.Queue[TelemetryPacket], stats: dict[str, Any]) -> None:
        self.queue = queue
        self.stats = stats

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        if len(data) != UDP_PACKET_BYTES:
            self.stats["invalid_packets"] += 1
            return

        try:
            accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, mag_x, mag_y, mag_z = struct.unpack(
                UDP_PACKET_FORMAT,
                data,
            )
        except struct.error:
            self.stats["invalid_packets"] += 1
            return

        packet = TelemetryPacket(
            node_id=f"{addr[0]}:{addr[1]}",
            accel_x=accel_x,
            accel_y=accel_y,
            accel_z=accel_z,
            gyro_x=gyro_x,
            gyro_y=gyro_y,
            gyro_z=gyro_z,
            mag_x=mag_x,
            mag_y=mag_y,
            mag_z=mag_z,
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
        )

        try:
            self.queue.put_nowait(packet)
            self.stats["packets_received"] += 1
            self.stats["last_udp_ts"] = asyncio.get_running_loop().time()
        except asyncio.QueueFull:
            self.stats["dropped_packets"] += 1


app = FastAPI(title="MVS (Minimum Viable Spring)", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    app.state.telemetry_queue = asyncio.Queue(maxsize=CSV_QUEUE_MAXSIZE)
    app.state.telemetry_stats = {
        "packets_received": 0,
        "invalid_packets": 0,
        "dropped_packets": 0,
        "last_udp_ts": 0.0,
    }
    app.state.stop_event = asyncio.Event()
    app.state.mock_engine = MockTelemetryEngine()
    app.state.live_imu_sample: LiveImuSample | None = None
    app.state.live_imu_lock = asyncio.Lock()

    csv_path = Path(TRAINING_DATA_FILE)
    app.state.writer_task = asyncio.create_task(
        telemetry_writer_worker(
            queue=app.state.telemetry_queue,
            stop_event=app.state.stop_event,
            csv_path=csv_path,
        )
    )
    app.state.mock_task = asyncio.create_task(app.state.mock_engine.run(app.state.stop_event))

    if SERIAL_ENABLED:
        app.state.serial_task = asyncio.create_task(
            serial_reader_worker(
                stop_event=app.state.stop_event,
                sample_lock=app.state.live_imu_lock,
            )
        )
    else:
        app.state.serial_task = None

    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: TelemetryDatagramProtocol(app.state.telemetry_queue, app.state.telemetry_stats),
        local_addr=("0.0.0.0", UDP_PORT),
    )
    app.state.udp_transport = transport


@app.on_event("shutdown")
async def shutdown_event() -> None:
    app.state.stop_event.set()

    app.state.udp_transport.close()

    shutdown_marker = TelemetryPacket(
        node_id="shutdown",
        accel_x=0.0,
        accel_y=0.0,
        accel_z=0.0,
        gyro_x=0.0,
        gyro_y=0.0,
        gyro_z=0.0,
        mag_x=0.0,
        mag_y=0.0,
        mag_z=0.0,
        timestamp_iso="shutdown",
    )

    with contextlib.suppress(asyncio.QueueFull):
        app.state.telemetry_queue.put_nowait(shutdown_marker)

    with contextlib.suppress(asyncio.CancelledError):
        await app.state.writer_task

    with contextlib.suppress(asyncio.CancelledError):
        await app.state.mock_task

    if app.state.serial_task:
        with contextlib.suppress(asyncio.CancelledError):
            await app.state.serial_task


async def telemetry_writer_worker(
    queue: asyncio.Queue[TelemetryPacket],
    stop_event: asyncio.Event,
    csv_path: Path,
) -> None:
    header = (
        "NodeID,Accel_X,Accel_Y,Accel_Z,Gyro_X,Gyro_Y,Gyro_Z,Mag_X,Mag_Y,Mag_Z,Timestamp\n"
    )

    try:
        async with aiofiles.open(csv_path, mode="x", encoding="utf-8") as csv_file_create:
            await csv_file_create.write(header)
    except FileExistsError:
        pass

    async with aiofiles.open(csv_path, mode="a", encoding="utf-8") as csv_file:
        while True:
            packet = await queue.get()

            if packet.timestamp_iso == "shutdown" and stop_event.is_set():
                queue.task_done()
                break

            csv_line = (
                f"{packet.node_id},{packet.accel_x:.6f},{packet.accel_y:.6f},{packet.accel_z:.6f},"
                f"{packet.gyro_x:.6f},{packet.gyro_y:.6f},{packet.gyro_z:.6f},"
                f"{packet.mag_x:.6f},{packet.mag_y:.6f},{packet.mag_z:.6f},{packet.timestamp_iso}\n"
            )
            await csv_file.write(csv_line)
            await insert_sensor_log(packet)
            queue.task_done()


async def insert_sensor_log(packet: TelemetryPacket) -> None:
    async with AsyncSessionLocal() as session:
        statement = insert(SensorLogs).values(
            node_id=packet.node_id,
            accel_x=packet.accel_x,
            accel_y=packet.accel_y,
            accel_z=packet.accel_z,
            gyro_x=packet.gyro_x,
            gyro_y=packet.gyro_y,
            gyro_z=packet.gyro_z,
            mag_x=packet.mag_x,
            mag_y=packet.mag_y,
            mag_z=packet.mag_z,
            timestamp=datetime.fromisoformat(packet.timestamp_iso),
        )
        await session.execute(statement)
        await session.commit()


def _parse_serial_imu_line(line: str) -> LiveImuSample | None:
    if not line:
        return None

    if line.startswith("READY:") or line.startswith("ERR:"):
        return None

    if line.startswith("ESTOP:"):
        return None

    parts = [part.strip() for part in line.split(",")]
    if len(parts) < 6:
        return None

    try:
        accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z = (float(part) for part in parts[:6])
    except ValueError:
        return None

    host_time_iso = datetime.now(timezone.utc).isoformat()
    host_time_monotonic = asyncio.get_running_loop().time()
    device_time_iso = None
    return LiveImuSample(
        accel_x=accel_x,
        accel_y=accel_y,
        accel_z=accel_z,
        gyro_x=gyro_x,
        gyro_y=gyro_y,
        gyro_z=gyro_z,
        host_time_iso=host_time_iso,
        device_time_iso=device_time_iso,
        host_time_monotonic=host_time_monotonic,
    )


async def serial_reader_worker(
    stop_event: asyncio.Event,
    sample_lock: asyncio.Lock,
) -> None:
    loop = asyncio.get_running_loop()

    while not stop_event.is_set():
        try:
            with serial.Serial(
                port=SERIAL_PORT,
                baudrate=SERIAL_BAUD,
                timeout=SERIAL_READ_TIMEOUT_S,
            ) as ser:
                while not stop_event.is_set():
                    raw = await loop.run_in_executor(None, ser.readline)
                    if not raw:
                        continue

                    line = raw.decode("utf-8", errors="replace").strip()
                    sample = _parse_serial_imu_line(line)
                    if sample is None:
                        continue

                    async with sample_lock:
                        app.state.live_imu_sample = sample
        except serial.SerialException:
            await asyncio.sleep(SERIAL_RECONNECT_WAIT_S)


@app.get("/dashboard_data")
async def get_dashboard_data() -> dict[str, Any]:
    start_ts = asyncio.get_running_loop().time()

    async with AsyncSessionLocal() as session:
        machine_status_result = await session.execute(select(MachineStatus))
        raw_inventory_result = await session.execute(select(RawInventory))
        work_orders_result = await session.execute(select(WorkOrders))

        machine_status_rows = machine_status_result.scalars().all()
        raw_inventory_rows = raw_inventory_result.scalars().all()
        work_order_rows = work_orders_result.scalars().all()

    elapsed_ms = (asyncio.get_running_loop().time() - start_ts) * 1000.0

    now_monotonic = asyncio.get_running_loop().time()
    last_udp_ts = app.state.telemetry_stats["last_udp_ts"]
    local_mesh_status = (now_monotonic - last_udp_ts) <= UDP_STALE_TIMEOUT_SEC if last_udp_ts else False

    cloud_status = elapsed_ms <= MAX_MTTR_MS

    return {
        "mode": "live",
        "schema_version": HYBRID_SCHEMA_VERSION,
        "latency_ms": round(elapsed_ms, 3),
        "cloud_status": cloud_status,
        "local_mesh_status": local_mesh_status,
        "telemetry_stats": app.state.telemetry_stats,
        "machine_status": [
            {
                "machine_id": row.machine_id,
                "current_state": row.current_state,
                "job_in_progress": row.job_in_progress,
                "est_completion": row.est_completion.isoformat() if row.est_completion else None,
            }
            for row in machine_status_rows
        ],
        "raw_inventory": [
            {
                "material_id": row.material_id,
                "current_weight_kg": row.current_weight_kg,
                "last_updated": row.last_updated.isoformat(),
            }
            for row in raw_inventory_rows
        ],
        "work_orders": [
            {
                "order_id": row.order_id,
                "requesting_unit": row.requesting_unit,
                "due_date": row.due_date.isoformat(),
                "status": row.status,
            }
            for row in work_order_rows
        ],
    }


@app.get("/hybrid/dashboard_data")
async def get_hybrid_dashboard_data() -> dict[str, Any]:
    start_ts = asyncio.get_running_loop().time()
    payload = await app.state.mock_engine.snapshot()
    elapsed_ms = (asyncio.get_running_loop().time() - start_ts) * 1000.0

    payload["mode"] = "hybrid"
    payload["latency_ms"] = round(elapsed_ms, 3)

    nodes = payload.get("schematic", {}).get("nodes", [])
    target_node = None
    for node in nodes:
        if node.get("id") == SERIAL_NODE_ID:
            target_node = node
            break

    if target_node is not None:
        target_node["source"] = "live"
        async with app.state.live_imu_lock:
            sample = app.state.live_imu_sample

        now_monotonic = asyncio.get_running_loop().time()
        is_stale = True
        if sample is not None:
            is_stale = (now_monotonic - sample.host_time_monotonic) > SERIAL_STALE_TIMEOUT_S

        if sample is None or is_stale:
            target_node["raw_imu"] = None
            target_node["host_time"] = None
            target_node["device_time"] = None
            target_node["status"] = "Disconnected"
        else:
            target_node["raw_imu"] = {
                "ax": sample.accel_x,
                "ay": sample.accel_y,
                "az": sample.accel_z,
                "gx": sample.gyro_x,
                "gy": sample.gyro_y,
                "gz": sample.gyro_z,
            }
            target_node["host_time"] = sample.host_time_iso
            target_node["device_time"] = sample.device_time_iso

            accel_mag = math.sqrt(
                sample.accel_x**2 + sample.accel_y**2 + sample.accel_z**2
            )
            gyro_mag = math.sqrt(
                sample.gyro_x**2 + sample.gyro_y**2 + sample.gyro_z**2
            )
            target_node["status"] = "Busy" if accel_mag > 0.3 or gyro_mag > 15.0 else "Idle"

    return payload


@app.get("/mock/dashboard_data")
async def get_mock_dashboard_data() -> dict[str, Any]:
    start_ts = asyncio.get_running_loop().time()
    payload = await app.state.mock_engine.snapshot()
    elapsed_ms = (asyncio.get_running_loop().time() - start_ts) * 1000.0
    payload["latency_ms"] = round(elapsed_ms, 3)
    return payload


@app.post("/mock/reset")
async def reset_mock_engine() -> dict[str, Any]:
    app.state.mock_engine.reset()
    return {"status": "ok", "message": "mock engine reset"}
