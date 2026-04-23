import simpy
import pulp
import random
import asyncio

class EARC_Simulator:
    def __init__(self, env):
        self.env = env
        self.r0 = simpy.Resource(env, capacity=5)
        self.m1 = simpy.Resource(env, capacity=1) # CNC Mill
        self.m2 = simpy.Resource(env, capacity=2) # Dual Laser Cutter
        self.m3 = simpy.Resource(env, capacity=1) # CNC Lathe
        self.r1 = simpy.Resource(env, capacity=1) # Outfeed Merge Robot
        
        self.completed_jobs = 0
        self.total_flow_time = 0.0
        
    def process_job(self, name, route, cycle_times):
        start_time = self.env.now
        
        # Route parsing
        for step in route:
            res = getattr(self, step.lower())
            with res.request() as req:
                yield req
                # Simulate processing time
                proc_time = cycle_times.get(step, 10.0)
                # Introduce some variation (M/M/1 queue style)
                actual_time = random.expovariate(1.0 / proc_time)
                yield self.env.timeout(actual_time)
                
        self.completed_jobs += 1
        self.total_flow_time += (self.env.now - start_time)

def optimize_schedule(work_orders):
    """
    Uses PuLP to optimize routing (EDD - Earliest Due Date heuristic mapping).
    For now, a simple placeholder LP to demonstrate integration.
    """
    prob = pulp.LpProblem("EARC_Scheduling", pulp.LpMinimize)
    
    # Decision variables for sequence
    # Minimizing total tardiness
    job_vars = pulp.LpVariable.dicts("JobStartTime", [wo['id'] for wo in work_orders], lowBound=0, cat='Continuous')
    
    # Objective function: minimize sum of start times (SPT heuristic proxy)
    prob += pulp.lpSum([job_vars[wo['id']] for wo in work_orders])
    
    # Just a basic constraint that start time >= 0
    for wo in work_orders:
        prob += job_vars[wo['id']] >= 0
        
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    # Return sorted by assigned start time
    scheduled = sorted(work_orders, key=lambda wo: job_vars[wo['id']].varValue)
    return scheduled

async def run_headless_simulation(num_jobs=50):
    env = simpy.Environment()
    sim = EARC_Simulator(env)
    
    # Mock data
    products = ['Gasket_A', 'Shaft_B', 'Housing_C']
    routes = {
        'Gasket_A': ['R0', 'M2', 'R1'],
        'Shaft_B': ['R0', 'M3', 'R1'],
        'Housing_C': ['R0', 'M1', 'R1']
    }
    times = {
        'R0': 2.0, 'M1': 60.0, 'M2': 15.0, 'M3': 45.0, 'R1': 5.0
    }
    
    work_orders = []
    for i in range(num_jobs):
        prod = random.choice(products)
        work_orders.append({'id': i, 'prod': prod, 'due': random.randint(100, 1000)})
        
    # Optimize
    scheduled_orders = optimize_schedule(work_orders)
    
    def job_generator():
        for wo in scheduled_orders:
            route = routes[wo['prod']]
            env.process(sim.process_job(f"Job_{wo['id']}", route, times))
            # Arrivals
            yield env.timeout(random.expovariate(1.0 / 10.0))
            
    env.process(job_generator())
    env.run(until=5000)
    
    oee = 0.0
    if sim.completed_jobs > 0:
        oee = (sim.completed_jobs * 15.0) / env.now # rough performance estimate
        
    return {
        "completed_jobs": sim.completed_jobs,
        "average_flow_time": sim.total_flow_time / max(1, sim.completed_jobs),
        "simulated_oee": min(1.0, oee)
    }

if __name__ == "__main__":
    res = asyncio.run(run_headless_simulation(50))
    print("Simulation Results:", res)
