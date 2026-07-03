import numpy as np
import scipy.sparse as sp
import logging
import time

logger = logging.getLogger(__name__)

class MobileCrystallineHeart:
    """Crystalline Heart optimized for mobile deployment"""
    
    def __init__(self, n_nodes: int = 256):
        self.n_nodes = n_nodes
        self.E = np.random.randn(n_nodes) * 0.1
        self.W = self._create_sparse_connectivity()
        
        # Mobile optimization parameters
        self.compute_mode = "FULL"  # FULL, REDUCED, CRITICAL
        self.thermal_threshold = 0.8
        self.battery_saver = False
        
        # Stability monitoring
        self.lyapunov_exponents = []
        self.stability_margin = 0.0
        self.convergence_rate = 0.0
        
        # Real-time adaptation
        self.adaptation_rate = 0.05
        self.last_adaptation = time.time()
    
    def _create_sparse_connectivity(self):
        """Create sparse connectivity matrix optimized for mobile"""
        
        # Create a small-world network topology
        # More efficient than random sparse for ODE solving
        n = self.n_nodes
        k = 4  # Average connections per node
        
        # Create ring lattice
        rows = []
        cols = []
        data = []
        
        for i in range(n):
            for j in range(1, k//2 + 1):
                rows.append(i)
                cols.append((i + j) % n)
                data.append(0.1 * np.random.randn())
                
                rows.append((i + j) % n)
                cols.append(i)
                data.append(0.1 * np.random.randn())
        
        # Add random shortcuts (small-world effect)
        n_shortcuts = n // 10
        for _ in range(n_shortcuts):
            i, j = np.random.randint(0, n, 2)
            rows.append(i)
            cols.append(j)
            data.append(0.05 * np.random.randn())
        
        # Create sparse matrix
        W = sp.coo_matrix((data, (rows, cols)), shape=(n, n))
        
        # Ensure symmetry and stability
        W = (W + W.T) / 2
        W.setdiag(-0.8)  # Self-connections for stability
        
        return W.tocsr()  # Compressed Sparse Row format for efficient computation
    
    def update(self, external_input: np.ndarray, 
               dt: float = 0.01,
               thermal_state: float = 0.0) -> dict:
        """
        Update the heart state with mobile optimizations
        
        Args:
            external_input: Sensory input array (audio RMS, etc.)
            dt: Time step (adjusted based on compute load)
            thermal_state: Device temperature (0-1)
        """
        # Adjust compute mode based on thermal state
        if thermal_state > 0.7:
            self.compute_mode = "CRITICAL"
            effective_nodes = self.n_nodes // 4
        elif thermal_state > 0.5:
            self.compute_mode = "REDUCED"
            effective_nodes = self.n_nodes // 2
        else:
            self.compute_mode = "FULL"
            effective_nodes = self.n_nodes
        
        # Mobile-optimized ODE solving
        if self.compute_mode == "FULL":
            result = self._full_update(external_input, dt)
        elif self.compute_mode == "REDUCED":
            result = self._reduced_update(external_input, dt, effective_nodes)
        else:  # CRITICAL
            result = self._critical_update(external_input, dt, effective_nodes)
        
        # Update stability metrics
        self._update_stability_metrics()
        
        return result
    
    def _full_update(self, external_input: np.ndarray, dt: float):
        """Full precision update"""
        # System matrix: A = -βI + γ(W - D)
        beta = 0.8
        gamma = 0.3
        
        # Compute degree matrix (diagonal)
        D = sp.diags(np.asarray(self.W.sum(axis=1)).flatten())
        
        # Efficient sparse matrix multiplication
        W_minus_D = self.W - D
        A = -beta * sp.eye(self.n_nodes) + gamma * W_minus_D
        
        # Solve ODE using exponential integrator (more stable than Euler)
        from scipy.sparse.linalg import expm_multiply
        
        # dt * A * E + external_input
        # expm_multiply takes A, B and computes exp(A) @ B
        # Here we approximate (I + dt*A) @ E + dt * external_input
        # This is a simplified exponential integrator. A full one is more complex.
        # For this setup, we'll revert to a more explicit Euler for now or use full expm_multiply carefully.
        
        # Simplified Euler update for now for direct translation
        dE_dt = -beta * self.E + gamma * self.W @ self.E + external_input
        
        self.E = np.tanh(self.E + dt * dE_dt)
        
        # Compute GCL and other metrics
        gcl = 1.0 - np.mean(np.abs(self.E))
        energy = np.mean(self.E ** 2)
        
        return {"gcl": float(gcl), "energy": float(energy)}
    
    def _reduced_update(self, external_input: np.ndarray, dt: float, n_effective: int):
        """Reduced precision for thermal throttling"""
        # Use principal components for reduced computation
        if not hasattr(self, 'pca_components') or self.pca_components.shape[1] != n_effective:
            # Initialize PCA components (could be precomputed)
            self.pca_components = self._compute_pca_components(n_effective)
        
        # Project to reduced space
        E_reduced = self.pca_components.T @ self.E
        input_reduced = self.pca_components.T @ external_input[:self.n_nodes]
        
        # Update in reduced space
        A_reduced = self.pca_components.T @ self.W @ self.pca_components
        dE_reduced = dt * (-0.8 * E_reduced + 0.3 * A_reduced @ E_reduced + input_reduced)
        E_reduced = np.tanh(E_reduced + dE_reduced)
        
        # Project back
        self.E = self.pca_components @ E_reduced
        
        # Compute metrics
        gcl = 1.0 - np.mean(np.abs(self.E))
        energy = np.mean(self.E ** 2)
        
        return {"gcl": float(gcl), "energy": float(energy)}
    
    def _critical_update(self, external_input: np.ndarray, dt: float, n_effective: int):
        """Minimal computation for critical thermal conditions"""
        # Simple mean-field approximation
        mean_E = np.mean(self.E)
        mean_input = np.mean(external_input[:self.n_nodes])
        
        # Single differential equation
        d_mean = dt * (-0.8 * mean_E + 0.3 * mean_E + mean_input)
        mean_E = np.tanh(mean_E + d_mean)
        
        # Distribute mean to all nodes
        self.E = np.full(self.n_nodes, mean_E) + 0.01 * np.random.randn(self.n_nodes)
        
        # Simplified metrics
        gcl = 1.0 - abs(mean_E)
        energy = mean_E ** 2
        
        return {"gcl": float(gcl), "energy": float(energy)}
    
    def _update_stability_metrics(self):
        """Update Lyapunov stability metrics"""
        # Approximate largest Lyapunov exponent
        # Use a more robust check that handles sparse matrices
        
        # For sparse matrix, direct eigvals can be slow. Using power iteration for largest eigenvalue magnitude.
        # This is a heuristic for stability in a complex non-linear system.
        if len(self.lyapunov_exponents) < 100:
            try:
                # Convert to dense for eigenvalue calculation for simplicity, but in real mobile this is costly
                J = -0.8 * np.eye(self.n_nodes) + 0.3 * self.W.toarray()
                eigenvalues = np.linalg.eigvals(J)
                max_real = np.max(np.real(eigenvalues))
            except Exception as e:
                logger.warning(f"Eigenvalue calculation failed: {e}. Using dummy max_real.")
                max_real = -0.1 # Assume stable if calculation fails

            self.lyapunov_exponents.append(max_real)
            
            # Keep only recent history
            if len(self.lyapunov_exponents) > 100:
                self.lyapunov_exponents.pop(0)
            
            # Update stability margin
            self.stability_margin = -max_real if max_real < 0 else 0.0
            self.convergence_rate = np.exp(max_real * 0.01)  # Per time step

    def _compute_pca_components(self, n_effective: int):
        """Placeholder for PCA component computation"""
        # In a real scenario, this would be trained offline or use a more sophisticated method.
        # For now, return random orthogonal vectors.
        logger.warning("Using random PCA components. In production, precompute these.")
        rand_matrix = np.random.randn(self.n_nodes, n_effective)
        Q, _ = np.linalg.qr(rand_matrix)
        return Q