import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.models.mesa_schema import Base, Resource, Worker, Product, WorkOrder
from backend.app.database import DATABASE_URL
import datetime

async def seed_database():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as session:
        # Check if already seeded
        from sqlalchemy import select
        res = await session.execute(select(Resource).limit(1))
        if res.scalars().first():
            print("Database already seeded with MESA schema.")
            return

        print("Seeding MESA DB with initial nodes and products...")
        
        # Resources (Tri-Branch topology)
        resources = [
            Resource(resource_id="R0", resource_type="Infeed Robot", capacity_limit=5, current_status="Idle"),
            Resource(resource_id="M1", resource_type="CNC Mill", capacity_limit=1, current_status="Idle"),
            Resource(resource_id="M2", resource_type="Dual Laser Cutter", capacity_limit=2, current_status="Idle"),
            Resource(resource_id="M3", resource_type="CNC Lathe", capacity_limit=1, current_status="Idle"),
            Resource(resource_id="R1", resource_type="Outfeed Merge Robot", capacity_limit=1, current_status="Idle")
        ]
        session.add_all(resources)

        # Products
        products = [
            Product(product_id="Gasket_A", routing_path="R0,M2,R1", cycle_time=15.0, approval_status="Approved"),
            Product(product_id="Shaft_B", routing_path="R0,M3,R1", cycle_time=45.0, approval_status="Approved"),
            Product(product_id="Housing_C", routing_path="R0,M1,R1", cycle_time=60.0, approval_status="Approved")
        ]
        session.add_all(products)
        
        # Initial Work Orders
        orders = [
            WorkOrder(product_id="Gasket_A", requesting_unit="Unit_Alpha", due_date=datetime.datetime.utcnow() + datetime.timedelta(days=1), status="Pending"),
            WorkOrder(product_id="Shaft_B", requesting_unit="Unit_Bravo", due_date=datetime.datetime.utcnow() + datetime.timedelta(hours=4), status="Pending"),
            WorkOrder(product_id="Housing_C", requesting_unit="Unit_Charlie", due_date=datetime.datetime.utcnow() + datetime.timedelta(hours=12), status="Pending")
        ]
        session.add_all(orders)

        await session.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_database())
