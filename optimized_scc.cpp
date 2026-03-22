#include <iostream>
#include <vector>
#include <random>
#include <numeric>
#include <algorithm>
#include <set>
#include <boost/dynamic_bitset.hpp> // Optimized for SAT bitsets
#include <boost/graph/adjacency_list.hpp>
#include <boost/graph/core_numbers.hpp> // For Clique (k-core)
#include <omp.h> // Parallelism
#include <chrono>

using namespace std;
using namespace boost;

// === OPERATIONAL CONFIGURATION (Scalable) ===
const int VARS_SAT = 100;
const int CLAUSES_SAT = 400;
const int NODES_HC = 200;
const int NODES_CLIQUE = 200;
const int TARGET_K_CLIQUE = 15;
const int NUM_INSTANCES = 1000; // Increased sample size for precision

// === 1. OPTIMIZED "CUBO" FACE FOR SAT (Iterative Cascades) ===

class SATCube {
public:
    int num_vars;
    vector<vector<int>> clauses;
    SATCube(int vars) : num_vars(vars) {}

    void generate_structured_instance(int num_clauses) {
        clauses.clear();
        mt19937 rng(chrono::steady_clock::now().time_since_epoch().count());
        uniform_int_distribution<int> var_dist(1, num_vars);
        uniform_int_distribution<int> sign_dist(0, 1);

        for (int i = 0; i < num_clauses; ++i) {
            vector<int> clause;
            set<int> unique_literals; // Ensure unique literales in clause
            while (unique_literals.size() < 3) {
                int var = var_dist(rng);
                if (sign_dist(rng) == 0) var = -var;
                unique_literals.insert(var);
            }
            for (int lit : unique_literals) clause.push_back(lit);
            clauses.push_back(clause);
        }

        // Inject structured unit clauses (obvious leverage points)
        for (int i = 0; i < (int)(num_clauses * 0.1); ++i) {
            int var = var_dist(rng);
            clauses.push_back({ var });
        }
    }

    double apply_recursive_cascade_contraction() {
        int initial_clauses_count = clauses.size();

        while (true) {
            int current_clauses_count = clauses.size();

            // Step 1: Unit Propagation Face
            set<int> unit_clauses;
            for (const auto& c : clauses) {
                if (c.size() == 1) unit_clauses.insert(c[0]);
            }
            if (!unit_clauses.empty()) {
                clauses.erase(remove_if(clauses.begin(), clauses.end(),
                    [&](const vector<int>& c) {
                        for (int lit : c) if (unit_clauses.count(lit)) return true;
                        return false;
                    }), clauses.end());
            }

            // Step 2: Pure Literal Elimination Face
            vector<bool> pos_literals(num_vars + 1, false);
            vector<bool> neg_literals(num_vars + 1, false);
            for (const auto& c : clauses) {
                for (int lit : c) {
                    if (lit > 0) pos_literals[lit] = true;
                    else neg_literals[-lit] = true;
                }
            }

            set<int> pure_literals;
            for (int i = 1; i <= num_vars; ++i) {
                if (pos_literals[i] && !neg_literals[i]) pure_literals.insert(i);
                else if (!pos_literals[i] && neg_literals[i]) pure_literals.insert(-i);
            }
            if (!pure_literals.empty()) {
                clauses.erase(remove_if(clauses.begin(), clauses.end(),
                    [&](const vector<int>& c) {
                        for (int lit : c) if (pure_literals.count(lit)) return true;
                        return false;
                    }), clauses.end());
            }

            // Check for stasis
            if (clauses.size() == current_clauses_count) break;
        }

        return (double)(initial_clauses_count - clauses.size()) / initial_clauses_count * 100;
    }
};

// === 2. GRAPH PROBLEM TRANSFORMATIONS (Boost Graph) ===

// Define industrial-strength Boost Graph
typedef adjacency_list<vecS, vecS, undirectedS> Graph;

// Optimized transform for HC (Iterative degree pruning cascade)
double transform_hc_boost(int num_nodes, double prob) {
    Graph G;
    mt19937 rng(chrono::steady_clock::now().time_since_epoch().count());
    uniform_real_distribution<double> dist(0.0, 1.0);
    int initial_nodes = num_nodes;

    // Generate random Erdos-Renyi G(n, p) graph
    for (int u = 0; u < num_nodes; ++u) {
        for (int v = u + 1; v < num_nodes; ++v) {
            if (dist(rng) < prob) add_edge(u, v, G);
        }
    }

// === RECURSIVE "CUBO" FACE FOR HC ===
    while (num_vertices(G) > 0) {
        int nodes_before = num_vertices(G);
        vector<int> to_remove;
        
        // Iteratively find nodes with degree < 2 (cannot form a cycle)
        for (auto [v, end] = vertices(G); v != end; ++v) {
            if (degree(*v, G) < 2) to_remove.push_back(*v);
        }

        if (to_remove.empty()) break; // Stasis reached

        // LA CURA DEL SEGFAULT: Ordenar de mayor a menor para no corromper la memoria
        sort(to_remove.rbegin(), to_remove.rend());

        for (int v : to_remove) {
            clear_vertex(v, G);
            remove_vertex(v, G);
        }
    }

    return (double)(initial_nodes - num_vertices(G)) / initial_nodes * 100;
}

// Transform for Clique (Boost k-core optimal polynomial contraction)
double transform_clique_boost(int num_nodes, double prob, int target_k) {
    Graph G;
    mt19937 rng(chrono::steady_clock::now().time_since_epoch().count());
    uniform_real_distribution<double> dist(0.0, 1.0);
    int initial_nodes = num_nodes;

    for (int u = 0; u < num_nodes; ++u) {
        for (int v = u + 1; v < num_nodes; ++v) {
            if (dist(rng) < prob) add_edge(u, v, G);
        }
    }

    // === RECURSIVE "CUBO" FACE FOR CLIQUE === (Optimal K-Core)
    if (num_vertices(G) == 0) return 0;

    // Core number calculation is O(m+n)
    map<int, int> core_num;
    core_numbers(G, make_assoc_property_map(core_num));

    int reduced_count = 0;
    for (auto const& [v, core] : core_num) {
        if (core < target_k - 1) reduced_count++;
    }

    return (double)reduced_count / initial_nodes * 100;
}

// === 3. MOTOR DE EJECUCI N PARALELO (Multi-Core Dispatcher) ===

int main() {
    cout << "==========================================================" << endl;
    cout << "      SCALABLE ESFERA-CUBO-CENTRO OMP SOLVER (C++)       " << endl;
    cout << "==========================================================" << endl;
    cout << "Status: " << omp_get_max_threads() << " CPU Cores Detected" << endl;
    cout << "Simulation: Processing " << NUM_INSTANCES << " instances per problem type." << endl;
    cout << "Running simulations in parallel pool..." << endl;
    cout << "----------------------------------------------------------\n" << endl;

    auto start_time = chrono::high_resolution_clock::now();

    double sat_reduction_sum = 0;
    double hc_reduction_sum = 0;
    double clique_reduction_sum = 0;

    // Dispatch instances to all available cores
#pragma omp parallel reduction(+:sat_reduction_sum, hc_reduction_sum, clique_reduction_sum)
    {
        // 1. SAT recursive cascade instances
#pragma omp for
        for (int i = 0; i < NUM_INSTANCES; ++i) {
            SATCube cube(VARS_SAT);
            cube.generate_structured_instance(CLAUSES_SAT);
            sat_reduction_sum += cube.apply_recursive_cascade_contraction();
        }

        // 2. HC recursive degree pruning instances
#pragma omp for
        for (int i = 0; i < NUM_INSTANCES; ++i) {
            hc_reduction_sum += transform_hc_boost(NODES_HC, 0.015);
        }

        // 3. Clique optimal k-core instances
#pragma omp for
        for (int i = 0; i < NUM_INSTANCES; ++i) {
            clique_reduction_sum += transform_clique_boost(NODES_CLIQUE, 0.1, TARGET_K_CLIQUE);
        }
    }

    auto end_time = chrono::high_resolution_clock::now();
    chrono::duration<double> duration = end_time - start_time;

    cout << "\n----------------------------------------------------------" << endl;
    cout << "             PRECISE STATISTICAL RESULTS                  " << endl;
    cout << "----------------------------------------------------------" << endl;
    cout << "Total Simulation Time: " << duration.count() << " seconds." << endl;
    cout << "[SAT] Recursive Unit Prop + Pure Literal cascade -> Reduction: " << sat_reduction_sum / NUM_INSTANCES << "%" << endl;
    cout << "[Clique] Boost K-Core Pruning (k=" << TARGET_K_CLIQUE << ")          -> Reduction: " << clique_reduction_sum / NUM_INSTANCES << "%" << endl;
    cout << "[HC] Recursive Degree-2 pruning cascade         -> Reduction: " << hc_reduction_sum / NUM_INSTANCES << "%" << endl;
    cout << "==========================================================" << endl;

    return 0;
}