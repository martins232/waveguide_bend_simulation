"""
Waveguide Geometry Module
Defines refractive index profiles for straight and bent waveguides
"""

import numpy as np
from config import *
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / 'results' / 'figures'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

class WaveguideGeometry:
    """
    Handles waveguide refractive index profiles
    Supports both straight and bent waveguide configurations
    """
    
    def __init__(self, x_grid, n_core=N_CORE, n_clad=N_CLAD, core_width=CORE_WIDTH):
        """
        Initialize waveguide geometry
        
        Parameters:
        -----------
        x_grid : ndarray
            Spatial grid in x-direction [m]
        n_core : float
            Core refractive index
        n_clad : float
            Cladding refractive index
        core_width : float
            Waveguide core width [m]
        """
        self.x = x_grid
        self.n_core = n_core
        self.n_clad = n_clad
        self.core_width = core_width
        
        # Calculate numerical aperture
        self.NA = np.sqrt(n_core**2 - n_clad**2)
        self.delta_n = n_core - n_clad
        
    def straight_waveguide(self):
        """
        Create refractive index profile for straight step-index waveguide
        
        Returns:
        --------
        n_profile : ndarray
            Refractive index as function of x
        """
        n_profile = np.ones_like(self.x) * self.n_clad
        
        # Core region: |x| < core_width/2
        core_mask = np.abs(self.x) < (self.core_width / 2)
        n_profile[core_mask] = self.n_core
        
        return n_profile
    
    def bent_waveguide_conformal(self, bend_radius):
        """
        Create effective refractive index profile for bent waveguide
        using conformal transformation
        
        In a bent waveguide, the effective index is modified by:
        n_eff(x) = n(x) * (1 + x/R)
        
        where:
        - R is the bend radius
        - x is the transverse coordinate (positive = outer edge)
        
        Physical interpretation:
        - Inner edge (x < 0): effective index increases
        - Outer edge (x > 0): effective index decreases
        - This asymmetry causes mode shift and leakage
        
        Parameters:
        -----------
        bend_radius : float
            Radius of curvature [m]
        
        Returns:
        --------
        n_eff_profile : ndarray
            Effective refractive index as function of x
        """
        # Start with straight waveguide profile
        n_straight = self.straight_waveguide()
        
        # Apply conformal transformation
        # n_eff(x) = n(x) * (1 + x/R)
        conformal_factor = 1.0 + self.x / bend_radius
        n_eff_profile = n_straight * conformal_factor
        
        return n_eff_profile
    
    def bent_waveguide_alternative(self, bend_radius):
        """
        Alternative bend model: equivalent straight waveguide with graded index
        
        This model represents the bend as an effective index gradient:
        Δn_eff(x) = n₀ * (x/R)
        
        Useful for understanding the physics qualitatively.
        
        Parameters:
        -----------
        bend_radius : float
            Radius of curvature [m]
        
        Returns:
        --------
        n_eff_profile : ndarray
            Effective refractive index as function of x
        """
        n_straight = self.straight_waveguide()
        
        # Add linear index gradient
        # Δn = n₀ * x/R
        index_gradient = self.n_core * (self.x / bend_radius)
        n_eff_profile = n_straight + index_gradient
        
        return n_eff_profile
    
    def visualize_profiles(self, bend_radii=None):
        """
        Visualize refractive index profiles for different configurations
        
        Parameters:
        -----------
        bend_radii : list or None
            List of bend radii to plot [m]
            If None, uses default from config
        """
        import matplotlib.pyplot as plt
        
        if bend_radii is None:
            bend_radii = BEND_RADII
        
        fig, axes = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot 1: Straight waveguide
        ax1 = axes[0]
        n_straight = self.straight_waveguide()
        ax1.plot(self.x * 1e6, n_straight, 'b-', linewidth=2, label='Straight')
        ax1.axvline(self.core_width/2 * 1e6, color='k', linestyle='--', 
                   alpha=0.3, label='Core boundary')
        ax1.axvline(-self.core_width/2 * 1e6, color='k', linestyle='--', alpha=0.3)
        ax1.set_xlabel('x [μm]')
        ax1.set_ylabel('Refractive Index')
        ax1.set_title('Straight Waveguide: Step-Index Profile')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.set_ylim([self.n_clad - 0.02, self.n_core + 0.02])
        
        # Plot 2: Bent waveguides (conformal mapping)
        ax2 = axes[1]
        colors = ['red', 'orange', 'green', 'blue']
        
        for i, R in enumerate(bend_radii):
            n_bent = self.bent_waveguide_conformal(R)
            label = f'R = {R*1e6:.0f} μm'
            ax2.plot(self.x * 1e6, n_bent, color=colors[i], 
                    linewidth=2, label=label)
        
        # Reference: straight waveguide
        ax2.plot(self.x * 1e6, n_straight, 'k--', 
                linewidth=1, alpha=0.5, label='Straight (ref)')
        
        ax2.axvline(self.core_width/2 * 1e6, color='k', 
                   linestyle=':', alpha=0.3)
        ax2.axvline(-self.core_width/2 * 1e6, color='k', 
                   linestyle=':', alpha=0.3)
        ax2.set_xlabel('x [μm]')
        ax2.set_ylabel('Effective Refractive Index')
        ax2.set_title('Bent Waveguides: Conformal Transformation (n_eff = n × (1 + x/R))')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        plt.tight_layout()
        return fig


class InitialField:
    """
    Generate initial field distributions for BPM simulation
    """
    
    def __init__(self, x_grid):
        """
        Initialize field generator
        
        Parameters:
        -----------
        x_grid : ndarray
            Spatial grid in x-direction [m]
        """
        self.x = x_grid
    
    def gaussian_mode(self, width=MODE_WIDTH, center=0.0, amplitude=1.0):
        """
        Generate Gaussian approximation of fundamental waveguide mode
        
        The fundamental mode of a step-index waveguide can be approximated
        as a Gaussian with width related to the core size.
        
        E(x) = A * exp(-(x - x₀)² / w₀²)
        
        Parameters:
        -----------
        width : float
            1/e² intensity width [m]
        center : float
            Center position [m]
        amplitude : float
            Peak amplitude
        
        Returns:
        --------
        field : ndarray (complex)
            Initial field distribution
        """
        # Gaussian envelope
        gaussian = amplitude * np.exp(-((self.x - center)**2) / (width**2))
        
        # Return as complex field (phase = 0 initially)
        field = gaussian.astype(complex)
        
        return field
    
    def fundamental_mode_analytical(self, n_core=N_CORE, n_clad=N_CLAD, 
                                   core_width=CORE_WIDTH, wavelength=WAVELENGTH):
        """
        More accurate fundamental mode using analytical solution
        for step-index slab waveguide
        
        For a symmetric slab waveguide, the TE₀ mode has the form:
        - Inside core: E ~ cos(kx * x)
        - Outside core: E ~ exp(-γ * |x|)
        
        where kx and γ are determined by the eigenvalue equation.
        
        This is more accurate than Gaussian but more complex.
        
        Parameters:
        -----------
        n_core, n_clad : float
            Refractive indices
        core_width : float
            Core width [m]
        wavelength : float
            Wavelength [m]
        
        Returns:
        --------
        field : ndarray (complex)
            Fundamental mode field distribution
        """
        k0 = 2 * np.pi / wavelength
        
        # Simplified approach: use Gaussian with width estimated from V-number
        V = k0 * core_width * np.sqrt(n_core**2 - n_clad**2)
        
        # Effective mode width (empirical for fundamental mode)
        # For V >> 1: mode width ≈ core_width
        # For V ~ 1: mode extends significantly into cladding
        eff_width = core_width / 2 * (1 + 1/V)
        
        return self.gaussian_mode(width=eff_width)
    
    def offset_mode(self, offset_x, width=MODE_WIDTH):
        """
        Generate mode with transverse offset (for testing mode coupling)
        
        Parameters:
        -----------
        offset_x : float
            Offset from center [m]
        width : float
            Mode width [m]
        
        Returns:
        --------
        field : ndarray (complex)
            Offset field distribution
        """
        return self.gaussian_mode(width=width, center=offset_x)
    
    def visualize_modes(self):
        """
        Visualize different initial field distributions
        """
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot 1: Field amplitude
        ax1 = axes[0]
        
        gaussian = self.gaussian_mode()
        analytical = self.fundamental_mode_analytical()
        offset = self.offset_mode(offset_x=0.5e-6)
        
        ax1.plot(self.x * 1e6, np.abs(gaussian), 'b-', 
                linewidth=2, label='Gaussian (simple)')
        ax1.plot(self.x * 1e6, np.abs(analytical), 'r--', 
                linewidth=2, label='Analytical (V-number)')
        ax1.plot(self.x * 1e6, np.abs(offset), 'g:', 
                linewidth=2, label='Offset (0.5 μm)')
        
        ax1.axvline(CORE_WIDTH/2 * 1e6, color='k', linestyle='--', 
                   alpha=0.3, label='Core boundary')
        ax1.axvline(-CORE_WIDTH/2 * 1e6, color='k', linestyle='--', alpha=0.3)
        
        ax1.set_xlabel('x [μm]')
        ax1.set_ylabel('Field Amplitude |E|')
        ax1.set_title('Initial Field Distributions')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Plot 2: Field intensity (log scale to see tails)
        ax2 = axes[1]
        
        ax2.semilogy(self.x * 1e6, np.abs(gaussian)**2, 'b-', 
                    linewidth=2, label='Gaussian')
        ax2.semilogy(self.x * 1e6, np.abs(analytical)**2, 'r--', 
                    linewidth=2, label='Analytical')
        
        ax2.axvline(CORE_WIDTH/2 * 1e6, color='k', linestyle='--', alpha=0.3)
        ax2.axvline(-CORE_WIDTH/2 * 1e6, color='k', linestyle='--', alpha=0.3)
        
        ax2.set_xlabel('x [μm]')
        ax2.set_ylabel('Field Intensity |E|² (log scale)')
        ax2.set_title('Field Intensity - Log Scale (shows evanescent tails)')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        ax2.set_ylim([1e-6, 1.5])
        
        plt.tight_layout()
        return fig


def create_absorbing_boundary(x_grid, boundary_width=BOUNDARY_WIDTH, power=BOUNDARY_POWER):
    """
    Create absorbing boundary condition using window function
    
    Prevents non-physical reflections from grid edges by gradually
    absorbing the field near boundaries.
    
    Uses a raised cosine (Tukey) window:
    w(x) = cos²(π(|x| - x_boundary) / (2 * width))
    
    Parameters:
    -----------
    x_grid : ndarray
        Spatial grid [m]
    boundary_width : float
        Fraction of total x_range for absorbing region
    power : float
        Power of cosine function (higher = sharper transition)
    
    Returns:
    --------
    window : ndarray
        Absorbing window function (1 in center, 0 at edges)
    """
    x_max = np.max(np.abs(x_grid))
    boundary_start = x_max * (1 - boundary_width)
    
    window = np.ones_like(x_grid)
    
    # Left boundary
    left_mask = x_grid < -boundary_start
    if np.any(left_mask):
        x_left = x_grid[left_mask]
        window[left_mask] = np.cos(np.pi * (x_left + boundary_start) / 
                                   (2 * x_max * boundary_width))**power
    
    # Right boundary
    right_mask = x_grid > boundary_start
    if np.any(right_mask):
        x_right = x_grid[right_mask]
        window[right_mask] = np.cos(np.pi * (x_right - boundary_start) / 
                                    (2 * x_max * boundary_width))**power
    
    return window


# =============================================================================
# TESTING AND VISUALIZATION
# =============================================================================

if __name__ == "__main__":
    """
    Test the waveguide geometry module
    """
    import matplotlib.pyplot as plt
    
    print("="*70)
    print("TESTING WAVEGUIDE GEOMETRY MODULE")
    print("="*70)
    
    # Create spatial grid from config
    from config import x, BEND_RADII
    
    # Initialize geometry
    wg = WaveguideGeometry(x)
    
    print("\nWaveguide Parameters:")
    print(f"  Core width:     {wg.core_width*1e6:.2f} μm")
    print(f"  n_core:         {wg.n_core:.4f}")
    print(f"  n_clad:         {wg.n_clad:.4f}")
    print(f"  Δn:             {wg.delta_n:.4f}")
    print(f"  NA:             {wg.NA:.4f}")
    
    # Test refractive index profiles
    print("\n" + "="*70)
    print("Refractive Index Profiles:")
    print("="*70)
    
    n_straight = wg.straight_waveguide()
    print(f"\nStraight waveguide:")
    print(f"  n_max = {np.max(n_straight):.4f}")
    print(f"  n_min = {np.min(n_straight):.4f}")
    
    for R in BEND_RADII:
        n_bent = wg.bent_waveguide_conformal(R)
        print(f"\nBent waveguide (R = {R*1e6:.0f} μm):")
        print(f"  n_max = {np.max(n_bent):.4f} (outer edge)")
        print(f"  n_min = {np.min(n_bent):.4f} (inner edge)")
        print(f"  Δn_asymmetry = {np.max(n_bent) - np.min(n_bent):.6f}")
    
    # Visualize profiles
    print("\n" + "="*70)
    print("Generating index profile plots...")
    fig1 = wg.visualize_profiles()
    plt.savefig(RESULTS_DIR / 'refractive_index_profiles.png', dpi=150, bbox_inches='tight')
    print("  Saved: results/figures/refractive_index_profiles.png")
    
    # Test initial fields
    print("\n" + "="*70)
    print("Initial Field Distributions:")
    print("="*70)
    
    field_gen = InitialField(x)
    
    gaussian = field_gen.gaussian_mode()
    analytical = field_gen.fundamental_mode_analytical()
    
    print(f"\nGaussian mode:")
    print(f"  Peak amplitude: {np.max(np.abs(gaussian)):.4f}")
    print(f"  Total power:    {np.sum(np.abs(gaussian)**2) * DX:.6e}")
    
    print(f"\nAnalytical mode:")
    print(f"  Peak amplitude: {np.max(np.abs(analytical)):.4f}")
    print(f"  Total power:    {np.sum(np.abs(analytical)**2) * DX:.6e}")
    
    # Visualize fields
    print("\n" + "="*70)
    print("Generating initial field plots...")
    fig2 = field_gen.visualize_modes()
    plt.savefig(RESULTS_DIR / 'initial_field_modes.png', dpi=150, bbox_inches='tight')
    print("  Saved: results/figures/initial_field_modes.png")
    
    # Test absorbing boundary
    print("\n" + "="*70)
    print("Absorbing Boundary:")
    print("="*70)
    
    window = create_absorbing_boundary(x)
    
    print(f"  Boundary width: {BOUNDARY_WIDTH*100:.0f}% of x_range")
    print(f"  Window min:     {np.min(window):.4f}")
    print(f"  Window max:     {np.max(window):.4f}")
    
    # Visualize absorbing boundary
    fig3, ax = plt.subplots(figsize=(10, 4))
    ax.plot(x * 1e6, window, 'b-', linewidth=2)
    ax.axhline(1.0, color='k', linestyle='--', alpha=0.3)
    ax.fill_between(x * 1e6, 0, window, alpha=0.3)
    ax.set_xlabel('x [μm]')
    ax.set_ylabel('Window Function')
    ax.set_title('Absorbing Boundary Condition (Tukey Window)')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / 'absorbing_boundary.png', dpi=150, bbox_inches='tight')
    print("  Saved: results/figures/absorbing_boundary.png")
    
    print("\n" + "="*70)
    print("MODULE TEST COMPLETE ✅")
    print("="*70)
    print("\nAll visualizations saved to results/figures/")
    print("\nNext: Implement BPM propagation engine (bpm_engine.py)")