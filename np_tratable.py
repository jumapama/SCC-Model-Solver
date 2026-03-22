import random
import networkx as nx
import statistics

class ECC_Model_Experiment:
    def __init__(self, num_instances=100):
        self.num_instances = num_instances

    # --- 1. TRANSFORMACIÓN PARA SAT (Propagación Unitaria Simulada) ---
    def generate_3sat(self, num_vars, num_clauses):
        clauses = []
        for _ in range(num_clauses):
            clause = random.sample(range(1, num_vars + 1), 3)
            clause = [v if random.choice([True, False]) else -v for v in clause]
            clauses.append(clause)
        # Inyectamos artificialmente algunas cláusulas unitarias para simular estructura
        for _ in range(int(num_clauses * 0.1)):
            clauses.append([random.choice(range(1, num_vars + 1))])
        return clauses

    def transform_sat(self, clauses):
        initial_size = len(clauses)
        # Simulación básica de propagación unitaria:
        unit_clauses = {c[0] for c in clauses if len(c) == 1}
        reduced_clauses = [c for c in clauses if not any(lit in unit_clauses for lit in c)]
        return initial_size, len(reduced_clauses)

    # --- 2. TRANSFORMACIÓN PARA CLIQUE (Poda de K-Core) ---
    def transform_clique(self, num_nodes, prob_edge, target_k):
        G = nx.erdos_renyi_graph(num_nodes, prob_edge)
        initial_size = G.number_of_nodes()
        
        # Transformación: Eliminar nodos con grado menor a target_k - 1
        core_numbers = nx.core_number(G)
        reduced_nodes = [node for node, core in core_numbers.items() if core >= target_k - 1]
        
        return initial_size, len(reduced_nodes)

    # --- 3. TRANSFORMACIÓN PARA CICLO HAMILTONIANO (Poda de Hojas) ---
    def transform_hc(self, num_nodes, prob_edge):
        G = nx.erdos_renyi_graph(num_nodes, prob_edge)
        initial_size = G.number_of_nodes()
        
        # Transformación: Eliminar nodos con grado < 2 iterativamente
        changed = True
        while changed and G.number_of_nodes() > 0:
            changed = False
            to_remove = [n for n, d in G.degree() if d < 2]
            if to_remove:
                G.remove_nodes_from(to_remove)
                changed = True
                
        return initial_size, G.number_of_nodes()

    # --- MOTOR DE EJECUCIÓN (El Centro) ---
    def run_statistics(self):
        print("=== RESULTADOS DEL MODELO ESFERA-CUBO-CENTRO ===")
        print(f"Instancias evaluadas por problema: {self.num_instances}\n")

        # 1. SAT Stats
        sat_reductions = []
        for _ in range(self.num_instances):
            orig, red = self.transform_sat(self.generate_3sat(num_vars=100, num_clauses=400))
            sat_reductions.append((orig - red) / orig * 100)
        print(f"[SAT] Propagación unitaria -> Reducción promedio del espacio: {statistics.mean(sat_reductions):.2f}%")

        # 2. Clique Stats
        clique_reductions = []
        for _ in range(self.num_instances):
            orig, red = self.transform_clique(num_nodes=200, prob_edge=0.1, target_k=15)
            clique_reductions.append((orig - red) / orig * 100)
        print(f"[Clique] Poda k-core (k=15) -> Reducción promedio del espacio: {statistics.mean(clique_reductions):.2f}%")

        # 3. HC Stats
        hc_reductions = []
        for _ in range(self.num_instances):
            orig, red = self.transform_hc(num_nodes=200, prob_edge=0.015)
            hc_reductions.append((orig - red) / orig * 100)
        print(f"[HC] Poda de grado < 2 -> Reducción promedio del espacio: {statistics.mean(hc_reductions):.2f}%")

# Ejecutar experimento
exp = ECC_Model_Experiment(num_instances=100)
exp.run_statistics()