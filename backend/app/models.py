from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class WorkOrders(Base):
    __tablename__ = "work_orders"

    order_id: Mapped[int] = mapped_column("OrderID", Integer, primary_key=True, autoincrement=True)
    requesting_unit: Mapped[str] = mapped_column("Requesting_Unit", String(128), nullable=False)
    due_date: Mapped[datetime] = mapped_column("DueDate", DateTime, nullable=False)
    status: Mapped[str] = mapped_column("Status", String(32), nullable=False)


class MachineStatus(Base):
    __tablename__ = "machine_status"
    __table_args__ = (
        CheckConstraint("Current_State IN ('Idle','Busy','Error')", name="ck_machine_current_state"),
    )

    machine_id: Mapped[int] = mapped_column("MachineID", Integer, primary_key=True, autoincrement=True)
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
    work_order_id: Mapped[int] = mapped_column("WorkOrderID", ForeignKey("work_orders.OrderID"), nullable=False)
    gcode_hash: Mapped[str] = mapped_column("GCode_Hash", String(128), nullable=False)
    inspection_result: Mapped[str] = mapped_column("Inspection_Result", String(64), nullable=False)
