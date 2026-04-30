"""
BPM Engine Module
Core Beam Propagation Method implementation using split-step Fourier algorithm
"""

import numpy as np
from config import *


class BPMEngine:
    """
    Beam Propagation Method (BPM) solver using split-step Fourier method
    
    Solves the paraxial wave equation:
    ∂ψ/∂z = (i/2k₀n₀)∂²ψ/∂x² + ik₀(n(x,z) - n₀)ψ
    
    Using operator splitting:
    ψ(z+Δz) ≈ exp(D̂Δz) · exp(N̂Δz) · ψ(z)
    
    where:
    - D̂ = diffraction operator (applied in Fourier domain)
    - N̂ = refraction operator (applied in spatial domain)
    """
    
    def __init__(self, x_grid, kx_grid, k0=K0, n0=N0, dz=DZ):
        """
        Initialize BPM engine
        
        Parameters:
        -----------
        x_grid : ndarray
            Spatial grid [m]
        kx_grid : ndarray
            Spatial frequency grid [1/m]
        k0 : float
            Free-space wave number [1/m]
        n0 : float
            Reference refractive index
        dz : float
            Propagation step size [m]
        """
        self.x = x_grid
        self.kx = kx_grid
        self.k0 = k0
        self.n0 = n0
        self.dz = dz
        
        # Precompute diffraction operator (frequency domain)
        # exp(-i·kₓ²·Δz/(2k₀n₀))
        self.diffraction_operator = np.exp(-1j * self.kx**2 * self.dz / (2 * self.k0 * self.n0))
        
        # Store field evolution history
        self.field_history = []
        self.power_history = []
        self.z_positions = []
        
    def propagate_step(self, field, n_profile, apply_boundary=True, boundary_window=None):
        """
        Propagate field through one step Δz using split-step method
        
        Algorithm:
        1. Apply diffraction (FFT domain): ψ̃ → exp(D̂Δz) · ψ̃
        2. Apply refraction (spatial domain): ψ → exp(N̂Δz) · ψ
        
        Parameters:
        -----------
        field : ndarray (complex)
            Current field distribution
        n_profile : ndarray (real)
            Refractive index profile n(x)
        apply_boundary : bool
            Whether to apply absorbing boundary
        boundary_window : ndarray or None
            Absorbing boundary window function
        
        Returns:
        --------
        field_new : ndarray (complex)
            Field after propagation step
        """
        # Step 1: Diffraction (Fourier domain)
        # Transform to k-space
        field_fft = np.fft.fft(field)
        
        # Apply diffraction operator
        field_fft *= self.diffraction_operator
        
        # Transform back to spatial domain
        field = np.fft.ifft(field_fft)
        
        # Step 2: Refraction (spatial domain)
        # Calculate phase shift due to index variation
        # Δφ = k₀ · (n(x) - n₀) · Δz
        delta_n = n_profile - self.n0
        phase_shift = np.exp(1j * self.k0 * delta_n * self.dz)
        
        # Apply refraction
        field *= phase_shift
        
        # Step 3: Apply absorbing boundary (if requested)
        if apply_boundary and boundary_window is not None:
            field *= boundary_window
        
        return field
    
    def propagate_waveguide(self, initial_field, n_profile_function, 
                           z_array, save_interval=1, apply_boundary=True,
                           boundary_window=None, verbose=True):
        """
        Propagate field through waveguide with arbitrary index profile
        
        Parameters:
        -----------
        initial_field : ndarray (complex)
            Initial field distribution at z=0
        n_profile_function : callable
            Function that returns n(x) for given z
            Signature: n_profile_function(z) -> ndarray
        z_array : ndarray
            Array of z positions for propagation [m]
        save_interval : int
            Save field every N steps (for memory efficiency)
        apply_boundary : bool
            Apply absorbing boundary condition
        boundary_window : ndarray or None
            Absorbing window (computed if None)
        verbose : bool
            Print progress messages
        
        Returns:
        --------
        results : dict
            Dictionary containing:
            - 'field_evolution': List of saved field snapshots
            - 'power_evolution': Array of total power vs z
            - 'z_positions': Array of z positions where fields were saved
            - 'final_field': Final field distribution
        """
        # Initialize
        field = initial_field.copy()
        Nz = len(z_array)
        dx = self.x[1] - self.x[0]
        
        # Create absorbing boundary if not provided
        if apply_boundary and boundary_window is None:
            from waveguide_geometry import create_absorbing_boundary
            boundary_window = create_absorbing_boundary(self.x)
        
        # Storage
        self.field_history = []
        self.power_history = np.zeros(Nz)
        self.z_positions = []
        
        # Initial conditions
        power_initial = np.sum(np.abs(field)**2) * dx
        self.power_history[0] = power_initial
        self.field_history.append(field.copy())
        self.z_positions.append(z_array[0])
        
        if verbose:
            print(f"Starting BPM propagation...")
            print(f"  Initial power: {power_initial:.6e}")
            print(f"  Total distance: {z_array[-1]*1e6:.1f} μm")
            print(f"  Number of steps: {Nz}")
        
        # Propagation loop
        for i in range(1, Nz):
            z = z_array[i]
            
            # Get refractive index profile at this z
            n_profile = n_profile_function(z)
            
            # Propagate one step
            field = self.propagate_step(field, n_profile, 
                                       apply_boundary=apply_boundary,
                                       boundary_window=boundary_window)
            
            # Calculate power
            power = np.sum(np.abs(field)**2) * dx
            self.power_history[i] = power
            
            # Save field snapshot
            if i % save_interval == 0:
                self.field_history.append(field.copy())
                self.z_positions.append(z)
            
            # Progress reporting
            if verbose and i % (Nz // 10) == 0:
                progress = 100 * i / Nz
                power_loss_percent = 100 * (1 - power / power_initial)
                print(f"  Progress: {progress:.0f}% | z = {z*1e6:.1f} μm | "
                      f"Power loss: {power_loss_percent:.2f}%")
        
        # Save final field
        if len(self.field_history) == 0 or not np.array_equal(field, self.field_history[-1]):
            self.field_history.append(field.copy())
            self.z_positions.append(z_array[-1])
        
        if verbose:
            power_final = self.power_history[-1]
            total_loss_percent = 100 * (1 - power_final / power_initial)
            print(f"  Propagation complete!")
            print(f"  Final power: {power_final:.6e}")
            print(f"  Total loss: {total_loss_percent:.2f}%")
        
        # Return results
        results = {
            'field_evolution': self.field_history,
            'power_evolution': self.power_history,
            'z_positions': np.array(self.z_positions),
            'z_array': z_array,
            'final_field': field
        }
        
        return results
    
    def propagate_straight_waveguide(self, initial_field, n_core=N_CORE, 
                                     n_clad=N_CLAD, core_width=CORE_WIDTH,
                                     z_total=Z_TOTAL, nz=NZ, **kwargs):
        """
        Convenience method: Propagate through straight waveguide
        
        Parameters:
        -----------
        initial_field : ndarray (complex)
            Initial field
        n_core, n_clad : float
            Refractive indices
        core_width : float
            Core width [m]
        z_total : float
            Total propagation distance [m]
        nz : int
            Number of z steps
        **kwargs : additional arguments passed to propagate_waveguide
        
        Returns:
        --------
        results : dict
            Propagation results
        """
        from waveguide_geometry import WaveguideGeometry
        
        # Create geometry
        wg = WaveguideGeometry(self.x, n_core, n_clad, core_width)
        n_straight = wg.straight_waveguide()
        
        # Index profile function (constant in z)
        def n_profile_function(z):
            return n_straight
        
        # Propagate
        z_array = np.linspace(0, z_total, nz)
        results = self.propagate_waveguide(initial_field, n_profile_function, 
                                          z_array, **kwargs)
        
        return results
    
    def propagate_bent_waveguide(self, initial_field, bend_radius,
                                n_core=N_CORE, n_clad=N_CLAD, 
                                core_width=CORE_WIDTH,
                                z_total=Z_TOTAL, nz=NZ,
                                bend_start_fraction=BEND_START,
                                bend_end_fraction=BEND_END,
                                **kwargs):
        """
        Convenience method: Propagate through bent waveguide
        
        Waveguide structure:
        - Straight section: 0 to bend_start_fraction
        - Bend section: bend_start_fraction to bend_end_fraction
        - Straight section: bend_end_fraction to 1.0
        
        Parameters:
        -----------
        initial_field : ndarray (complex)
            Initial field
        bend_radius : float
            Bend radius [m]
        n_core, n_clad : float
            Refractive indices
        core_width : float
            Core width [m]
        z_total : float
            Total propagation distance [m]
        nz : int
            Number of z steps
        bend_start_fraction : float
            Fraction of z_total where bend starts
        bend_end_fraction : float
            Fraction of z_total where bend ends
        **kwargs : additional arguments passed to propagate_waveguide
        
        Returns:
        --------
        results : dict
            Propagation results with added 'bend_info' key
        """
        from waveguide_geometry import WaveguideGeometry
        
        # Create geometry
        wg = WaveguideGeometry(self.x, n_core, n_clad, core_width)
        
        # Get straight and bent profiles
        n_straight = wg.straight_waveguide()
        n_bent = wg.bent_waveguide_conformal(bend_radius)
        
        # Calculate bend positions
        z_bend_start = bend_start_fraction * z_total
        z_bend_end = bend_end_fraction * z_total
        
        # Index profile function (varies with z)
        def n_profile_function(z):
            if z < z_bend_start:
                # Input straight section
                return n_straight
            elif z < z_bend_end:
                # Bend section
                return n_bent
            else:
                # Output straight section
                return n_straight
        
        # Propagate
        z_array = np.linspace(0, z_total, nz)
        results = self.propagate_waveguide(initial_field, n_profile_function, 
                                          z_array, **kwargs)
        
        # Add bend information
        results['bend_info'] = {
            'radius': bend_radius,
            'z_start': z_bend_start,
            'z_end': z_bend_end,
            'bend_length': z_bend_end - z_bend_start,
            'bend_angle_rad': (z_bend_end - z_bend_start) / bend_radius,
            'bend_angle_deg': np.rad2deg((z_bend_end - z_bend_start) / bend_radius)
        }
        
        return results


class FieldAnalysis:
    """
    Analysis tools for BPM simulation results
    """
    
    @staticmethod
    def calculate_loss_dB(power_array, z_start_index=0, z_end_index=-1):
        """
        Calculate propagation loss in dB
        
        Loss [dB] = -10 × log₁₀(P_final / P_initial)
        
        Parameters:
        -----------
        power_array : ndarray
            Array of power vs z
        z_start_index : int
            Start index for loss calculation
        z_end_index : int
            End index for loss calculation
        
        Returns:
        --------
        loss_dB : float
            Loss in decibels
        """
        P_initial = power_array[z_start_index]
        P_final = power_array[z_end_index]
        
        if P_final <= 0 or P_initial <= 0:
            return np.inf
        
        loss_dB = -10 * np.log10(P_final / P_initial)
        return loss_dB
    
    @staticmethod
    def calculate_loss_per_distance(power_array, z_array, distance_unit=1e-6):
        """
        Calculate loss per unit distance (e.g., dB/μm, dB/mm)
        
        Parameters:
        -----------
        power_array : ndarray
            Power vs z
        z_array : ndarray
            z positions [m]
        distance_unit : float
            Unit distance for normalization [m]
            Default: 1e-6 (gives dB/μm)
        
        Returns:
        --------
        loss_per_unit : float
            Loss per unit distance [dB/unit]
        """
        total_distance = z_array[-1] - z_array[0]
        total_loss_dB = FieldAnalysis.calculate_loss_dB(power_array)
        
        loss_per_unit = total_loss_dB / (total_distance / distance_unit)
        return loss_per_unit
    
    @staticmethod
    def calculate_loss_per_90deg(power_array, z_array, bend_radius):
        """
        Calculate loss per 90° bend (standard metric in photonics)
        
        Parameters:
        -----------
        power_array : ndarray
            Power vs z
        z_array : ndarray
            z positions [m]
        bend_radius : float
            Bend radius [m]
        
        Returns:
        --------
        loss_per_90deg : float
            Loss per 90° turn [dB/90°]
        """
        # Arc length for 90° = π/2 × R
        arc_length_90deg = (np.pi / 2) * bend_radius
        
        # Total arc length in simulation
        total_arc_length = z_array[-1] - z_array[0]
        
        # Total loss
        total_loss_dB = FieldAnalysis.calculate_loss_dB(power_array)
        
        # Scale to 90°
        loss_per_90deg = total_loss_dB * (arc_length_90deg / total_arc_length)
        
        return loss_per_90deg
    
    @staticmethod
    def find_mode_center(field, x_grid):
        """
        Find the center of mass of the field intensity
        
        Useful for tracking mode shift in bent waveguides
        
        Parameters:
        -----------
        field : ndarray (complex)
            Field distribution
        x_grid : ndarray
            Spatial grid [m]
        
        Returns:
        --------
        x_center : float
            Center of mass position [m]
        """
        intensity = np.abs(field)**2
        total_intensity = np.sum(intensity)
        
        if total_intensity == 0:
            return 0.0
        
        x_center = np.sum(x_grid * intensity) / total_intensity
        return x_center
    
    @staticmethod
    def find_mode_width(field, x_grid):
        """
        Calculate mode width (1/e² intensity width)
        
        Parameters:
        -----------
        field : ndarray (complex)
            Field distribution
        x_grid : ndarray
            Spatial grid [m]
        
        Returns:
        --------
        width : float
            1/e² width [m]
        """
        intensity = np.abs(field)**2
        x_center = FieldAnalysis.find_mode_center(field, x_grid)
        
        # Calculate second moment
        variance = np.sum((x_grid - x_center)**2 * intensity) / np.sum(intensity)
        width = 2 * np.sqrt(variance)  # 1/e² width
        
        return width
    
    @staticmethod
    def check_energy_conservation(power_array, tolerance=0.01):
        """
        Check if energy is conserved (for straight waveguide validation)
        
        Parameters:
        -----------
        power_array : ndarray
            Power vs z
        tolerance : float
            Acceptable relative power variation
        
        Returns:
        --------
        is_conserved : bool
            True if power variation < tolerance
        max_variation : float
            Maximum relative power variation
        """
        P_initial = power_array[0]
        max_variation = np.max(np.abs(power_array - P_initial) / P_initial)
        
        is_conserved = max_variation < tolerance
        
        return is_conserved, max_variation


# =============================================================================
# TESTING AND VALIDATION
# =============================================================================

if __name__ == "__main__":
    """
    Test BPM engine with straight waveguide (validation)
    """
    import matplotlib.pyplot as plt
    from waveguide_geometry import WaveguideGeometry, InitialField
    from waveguide_geometry import create_absorbing_boundary
    
    print("="*70)
    print("TESTING BPM ENGINE - STRAIGHT WAVEGUIDE VALIDATION")
    print("="*70)
    
    # Create grids from config
    from config import x, kx, z
    
    # Initialize BPM engine
    bpm = BPMEngine(x, kx)
    
    print("\nBPM Engine Parameters:")
    print(f"  k₀:             {bpm.k0:.2e} rad/m")
    print(f"  n₀:             {bpm.n0:.4f}")
    print(f"  Δz:             {bpm.dz*1e9:.1f} nm")
    print(f"  Grid points:    {len(x)}")
    
    # Create initial field
    print("\n" + "="*70)
    print("Creating Initial Field...")
    print("="*70)
    
    field_gen = InitialField(x)
    initial_field = field_gen.gaussian_mode()
    
    print(f"  Peak amplitude: {np.max(np.abs(initial_field)):.4f}")
    print(f"  Initial power:  {np.sum(np.abs(initial_field)**2) * DX:.6e}")
    
    # Test 1: Straight waveguide (should have no loss)
    print("\n" + "="*70)
    print("TEST 1: Straight Waveguide Propagation")
    print("="*70)
    
    results_straight = bpm.propagate_straight_waveguide(
        initial_field,
        z_total=Z_TOTAL,
        nz=NZ,
        save_interval=50,
        verbose=True
    )
    
    # Analyze results
    print("\n" + "="*70)
    print("Analysis:")
    print("="*70)
    
    loss_dB = FieldAnalysis.calculate_loss_dB(results_straight['power_evolution'])
    is_conserved, max_var = FieldAnalysis.check_energy_conservation(
        results_straight['power_evolution']
    )
    
    print(f"\nEnergy Conservation:")
    print(f"  Total loss:        {loss_dB:.6f} dB")
    print(f"  Max variation:     {max_var*100:.4f}%")
    print(f"  Energy conserved:  {'✅ YES' if is_conserved else '❌ NO'}")
    
    # Mode properties
    final_field = results_straight['final_field']
    initial_center = FieldAnalysis.find_mode_center(initial_field, x)
    final_center = FieldAnalysis.find_mode_center(final_field, x)
    initial_width = FieldAnalysis.find_mode_width(initial_field, x)
    final_width = FieldAnalysis.find_mode_width(final_field, x)
    
    print(f"\nMode Properties:")
    print(f"  Initial center:    {initial_center*1e9:.2f} nm")
    print(f"  Final center:      {final_center*1e9:.2f} nm")
    print(f"  Center shift:      {(final_center - initial_center)*1e9:.2f} nm")
    print(f"  Initial width:     {initial_width*1e6:.3f} μm")
    print(f"  Final width:       {final_width*1e6:.3f} μm")
    
    # Visualize
    print("\n" + "="*70)
    print("Generating Validation Plots...")
    print("="*70)
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Plot 1: Power vs z
    ax1 = axes[0, 0]
    ax1.plot(results_straight['z_array']*1e6, 
             results_straight['power_evolution'], 'b-', linewidth=2)
    ax1.set_xlabel('z [μm]')
    ax1.set_ylabel('Total Power')
    ax1.set_title('Power Conservation - Straight Waveguide')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Initial vs final field
    ax2 = axes[0, 1]
    ax2.plot(x*1e6, np.abs(initial_field), 'b-', linewidth=2, label='Initial')
    ax2.plot(x*1e6, np.abs(final_field), 'r--', linewidth=2, label='Final')
    ax2.set_xlabel('x [μm]')
    ax2.set_ylabel('Field Amplitude |E|')
    ax2.set_title('Field Profile: Initial vs Final')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Field evolution (2D map)
    ax3 = axes[1, 0]
    field_array = np.array([np.abs(f) for f in results_straight['field_evolution']])
    z_saved = results_straight['z_positions']
    
    extent = [x[0]*1e6, x[-1]*1e6, z_saved[0]*1e6, z_saved[-1]*1e6]
    im = ax3.imshow(field_array, aspect='auto', origin='lower', 
                    extent=extent, cmap='hot', interpolation='bilinear')
    ax3.set_xlabel('x [μm]')
    ax3.set_ylabel('z [μm]')
    ax3.set_title('Field Evolution |E(x,z)|')
    plt.colorbar(im, ax=ax3, label='Amplitude')
    
    # Plot 4: Power variation (zoom)
    ax4 = axes[1, 1]
    power_variation = (results_straight['power_evolution'] - 
                      results_straight['power_evolution'][0]) / \
                      results_straight['power_evolution'][0] * 100
    ax4.plot(results_straight['z_array']*1e6, power_variation, 'b-', linewidth=2)
    ax4.axhline(0, color='k', linestyle='--', alpha=0.3)
    ax4.set_xlabel('z [μm]')
    ax4.set_ylabel('Power Variation [%]')
    ax4.set_title('Numerical Error Assessment')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../results/figures/bpm_validation_straight.png', dpi=150, bbox_inches='tight')
    print("  Saved: results/figures/bpm_validation_straight.png")
    
    print("\n" + "="*70)
    print("BPM ENGINE VALIDATION COMPLETE ✅")
    print("="*70)
    
    if is_conserved:
        print("\n✅ Validation PASSED - Energy is conserved!")
        print("   BPM engine is working correctly.")
        print("   Ready for bend simulations!")
    else:
        print(f"\n⚠️  Warning: Energy variation is {max_var*100:.4f}%")
        print("   This may indicate numerical issues.")