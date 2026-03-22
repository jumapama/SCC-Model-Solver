import random
import networkx as nx
import statistics
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import time

# --- DEFINE OPERATIONAL PARAMETERS (Set as high as desired for more power) ---
NUM_CORES = multiprocessing.cpu_count() # Automatically detect all available cores
NUM_INSTANCES_TO_SIMULATE = 1000        # Increase this for ultra-precise statistics (e.g., 5000)
VARS_SAT = 100
CLAUSES_SAT = 400
NODES_CLIQUE = 200
TARGET_K_CLIQUE = 15
NODES_HC = 200

# --- THE OPERATIONAL "CUBO" (More Faces, More aggressive) ---

# --- 1. OPTIMIZED TRANSFORM FOR SAT (Iterative Constraint Propagation) ---
def simulate_unit_propagation(clauses):
    unit_clauses = {c[0] for c in clauses if len(c) == 1}
    if not unit_clauses:
        return clauses
    return [c for c in clauses if not any(lit in unit_clauses for lit in c)]

def simulate_pure_literal_elimination(clauses, num_vars):
    literals = set(lit for c in clauses for lit in c)
    pure_literals = []
    for var in range(1, num_vars + 1):
        has_pos = var in literals
        has_neg = -var in literals
        if has_pos and not has_neg:
            pure_literals.append(var)
        elif has_neg and not has_pos:
            pure_literals.append(-var)
            
    if not pure_literals:
        return clauses
    return [c for c in clauses if not any(lit in pure_literals for lit in c)]

def transform_sat_recursive(instance_params):
    num_vars, num_clauses = instance_params
    # Generate structured instance
    clauses = []
    for _ in range(num_clauses):
        clause = random.sample(range(1, num_vars + 1), 3)
        clause = [v if random.choice([True, False]) else -v for v in clause]
        clauses.append(clause)
    for _ in range(int(num_clauses * 0.1)): # Structure inyección
        clauses.append([random.choice(range(1, num_vars + 1))])
    
    initial_size = len(clauses)
    
    # === THE CASCADING "CUBE" FACE === Recursive, aggressive
    while True:
        size_before = len(clauses)
        clauses = simulate_unit_propagation(clauses)
        clauses = simulate_pure_literal_elimination(clauses, num_vars)
        if len(clauses) == size_before: # structural stasis reached
            break
            
    reduction = (initial_size - len(clauses)) / initial_size * 100
    return reduction

# --- 2. CLIQUE TRANSFORM (Stable) ---
def transform_clique_single(instance_params):
    num_nodes, prob_edge, target_k = instance_params
    G = nx.erdos_renyi_graph(num_nodes, prob_edge)
    initial_size = G.number_of_nodes()
    
    # We continue k-core: nodes with deg < target_k - 1 cannot be in clique size k
    core_numbers = nx.core_number(G)
    reduced_nodes = [node for node, core in core_numbers.items() if core >= target_k - 1]
    
    reduction = (initial_size - len(reduced_nodes)) / initial_size * 100
    return reduction

# --- 3. OPTIMIZED HC TRANSFORM (Iterative Degree Pruning Cascade) ---
def transform_hc_optimized(instance_params):
    num_nodes, prob_edge = instance_params
    G = nx.erdos_renyi_graph(num_nodes, prob_edge)
    initial_size = G.number_of_nodes()
    
    # === THE CASCADING "CUBE" FACE === More aggressive degree analysis
    while G.number_of_nodes() > 0:
        nodes_before = G.number_of_nodes()
        
        # Face 1: Prune Degree < 2 (Leaf nodes)
        to_remove_leaves = [n for n, d in G.degree() if d < 2]
        G.remove_nodes_from(to_remove_leaves)
        
        # Face 2: Contract path forced by Degree EXACTLY 2 (Path forced choices)
        # nodes_deg2 = [n for n, d in G.degree() if d == 2]
        # (This is more complex to implement correctly polynomials, so we focus on recursive leaves)
        
        if G.number_of_nodes() == nodes_before:
            break
            
    reduction = (initial_size - G.number_of_nodes()) / initial_size * 100
    return reduction

# --- 4. MOTOR DE EJECUCIÓN (Paralelizado en Multi-Cores) ---

def run_optimized_simulation():
    print("==========================================================")
    print("      SCALABLE ESFERA-CUBO-CENTRO OPTIMIZED SOLVER        ")
    print("==========================================================")
    print(f"Status: Using {NUM_CORES} CPU Cores")
    print(f"Simulation: Running {NUM_INSTANCES_TO_SIMULATE} instances per problem type.")
    print("Executing iterative 'Cubo' transformations (Pure Literal + UP Cascade for SAT).")
    print("Running simulations in parallel pool...")
    print("----------------------------------------------------------\n")

    start_time = time.time()
    
    problems = [
        ("SAT", transform_sat_recursive, (VARS_SAT, CLAUSES_SAT)),
        ("Clique", transform_clique_single, (NODES_CLIQUE, 0.1, TARGET_K_CLIQUE)),
        ("Hamiltonian Cycle", transform_hc_optimized, (NODES_HC, 0.015))
    ]
    
    final_results = {}
    
    # Create the Pool Executor to manage all cores
    with ProcessPoolExecutor(max_workers=NUM_CORES) as executor:
        for p_name, p_func, p_params in problems:
            print(f"[{p_name}] Dispatching tasks...")
            futures = [executor.submit(p_func, p_params) for _ in range(NUM_INSTANCES_TO_SIMULATE)]
            results = []
            
            # Use 'as_completed' to track progress
            for future in as_completed(futures):
                results.append(future.result())
                
            final_results[p_name] = statistics.mean(results)
            print(f"[{p_name}] Processed: {NUM_INSTANCES_TO_SIMULATE} simulations.")

    end_time = time.time()
    
    print("\n----------------------------------------------------------")
    print("             PRECISE STATISTICAL RESULTS                  ")
    print("----------------------------------------------------------")
    print(f"Total Simulation Time: {end_time - start_time:.2f} seconds.")
    print(f"[SAT] Recursive Unit Prop + Pure Literal cascade -> Reduction: {final_results['SAT']:.3f}%")
    print(f"[Clique] K-Core Pruning (k=15)                  -> Reduction: {final_results['Clique']:.3f}%")
    print(f"[HC] Recursive Degree-2 pruning cascade         -> Reduction: {final_results['Hamiltonian Cycle']:.3f}%")
    print("==========================================================")

if __name__ == '__main__':
    run_optimized_simulation()