from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class WorkOrders(Base):
    __tablename__ = "work_orders"

    order_id: Mapped[str] = mapped_column("OrderID", String(64), primary_key=True)
    requesting_unit: Mapped[str] = mapped_column("Requesting_Unit", String(128), nullable=False)
    due_date: Mapped[datetime] = mapped_column("DueDate", DateTime, nullable=False)
    status: Mapped[str] = mapped_column("Status", String(32), nullable=False)


class MachineStatus(Base):
    __tablename__ = "machine_status"
    __table_args__ = (
        CheckConstraint("Current_State IN ('Idle','Busy','Error')", name="ck_machine_current_state"),
    )

    machine_id: Mapped[str] = mapped_column("MachineID", String(64), primary_key=True)
    current_state: Mapped[str] = mapped_column("Current_State", String(16), nullable=False)
    job_in_progress: Mapped[Optional[str]] = mapped_column("Job_In_Progress", String(128), nullable=True)
    est_completion: Mapped[Optional[datetime]] = mapped_column("Est_Completion", DateTime, nullable=True)


class RawInventory(Base):
    __tablename__ = "raw_inventory"

    material_id: Mapped[str] = mapped_column("MaterialID", String(64), primary_key=True)
    current_weight_kg: Mapped[float] = mapped_column("Current_Weight_KG", Float, nullable=False)
    last_updated: Mapped[datetime] = mapped_column("Last_Updated", DateTime, nullable=False)


class SensorLogs(Base):
    __tablename__ = "sensor_logs"

    log_id: Mapped[int] = mapped_column("LogID", Integer, primary_key=True, autoincrement=True)
    node_id: Mapped[str] = mapped_column("NodeID", String(64), nullable=False)
    accel_x: Mapped[float] = mapped_column("Accel_X", Float, nullable=False)
    accel_y: Mapped[float] = mapped_column("Accel_Y", Float, nullable=False)
    accel_z: Mapped[float] = mapped_column("Accel_Z", Float, nullable=False)
    gyro_x: Mapped[float] = mapped_column("Gyro_X", Float, nullable=False)
    gyro_y: Mapped[float] = mapped_column("Gyro_Y", Float, nullable=False)
    gyro_z: Mapped[float] = mapped_column("Gyro_Z", Float, nullable=False)
    mag_x: Mapped[float] = mapped_column("Mag_X", Float, nullable=False)
    mag_y: Mapped[float] = mapped_column("Mag_Y", Float, nullable=False)
    mag_z: Mapped[float] = mapped_column("Mag_Z", Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column("Timestamp", DateTime, nullable=False)


class Genealogy(Base):
    __tablename__ = "genealogy"

    serial_id: Mapped[str] = mapped_column("SerialID", String(128), primary_key=True)
    work_order_id: Mapped[str] = mapped_column("WorkOrderID", String(64), ForeignKey("work_orders.OrderID"), nullable=False)
    gcode_hash: Mapped[str] = mapped_column("GCode_Hash", String(128), nullable=False)
    inspection_result: Mapped[str] = mapped_column("Inspection_Result", String(64), nullable=False)


class LotEvents(Base):
    __tablename__ = "lot_events"

    event_id: Mapped[int] = mapped_column("EventID", Integer, primary_key=True, autoincrement=True)
    serial_id: Mapped[str] = mapped_column("SerialID", String(128), ForeignKey("genealogy.SerialID"), nullable=False)
    station_point: Mapped[str] = mapped_column("StationPoint", String(64), nullable=False)
    status: Mapped[str] = mapped_column("Status", String(32), nullable=False) # e.g. 'Entered', 'Left', 'Blocked'
    timestamp: Mapped[datetime] = mapped_column("Timestamp", DateTime, nullable=False)


class OEELog(Base):
    __tablename__ = "oee_log"

    oee_id: Mapped[int] = mapped_column("OEEID", Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column("Timestamp", DateTime, nullable=False)
    interval_minutes: Mapped[int] = mapped_column("Interval_Minutes", Integer, nullable=False) # 5 for 5-min, 0 for full session
    availability: Mapped[float] = mapped_column("Availability", Float, nullable=False)
    performance: Mapped[float] = mapped_column("Performance", Float, nullable=False)
    quality: Mapped[float] = mapped_column("Quality", Float, nullable=False)
    final_oee: Mapped[float] = mapped_column("FinalOEE", Float, nullable=False)
