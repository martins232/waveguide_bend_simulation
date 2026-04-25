"""
Simulation Configuration
Parameters for waveguide bend loss simulation
"""

import numpy as np

# =============================================================================
# PHYSICAL PARAMETERS
# =============================================================================

# Material Properties
N_CORE = 1.50           # Core refractive index (glass/polymer)
N_CLAD = 1.45           # Cladding refractive index
WAVELENGTH = 1.55e-6    # Operating wavelength [m] (telecom C-band)

# Derived Parameters
K0 = 2 * np.pi / WAVELENGTH                    # Free-space wave number [1/m]
N0 = N_CORE                                     # Reference index for BPM
DELTA_N = N_CORE - N_CLAD                      # Index contrast
NA = np.sqrt(N_CORE**2 - N_CLAD**2)            # Numerical aperture

# Waveguide Geometry
CORE_WIDTH = 2.0e-6     # Waveguide core width [m] (2 μm - single mode)

# =============================================================================
# SIMULATION GRID PARAMETERS
# =============================================================================

# Spatial Grid (x-direction, transverse to propagation)
X_RANGE = 20e-6         # Total x-window [m] (20 μm - must contain leaking field)
NX = 1024               # Number of spatial points (power of 2 for FFT)
DX = X_RANGE / NX       # Spatial resolution [m]

# Propagation Grid (z-direction)
Z_TOTAL = 150e-6        # Total propagation distance [m] (150 μm)
NZ = 2000               # Number of propagation steps
DZ = Z_TOTAL / NZ       # Propagation step size [m]

# Grid vectors
x = np.linspace(-X_RANGE/2, X_RANGE/2, NX)    # Spatial coordinates [m]
z = np.linspace(0, Z_TOTAL, NZ)                # Propagation coordinates [m]

# k-space grid for FFT
kx = 2 * np.pi * np.fft.fftfreq(NX, DX)       # Spatial frequency [1/m]

# =============================================================================
# BEND PARAMETERS
# =============================================================================

# Bend radii to simulate [m]
BEND_RADII = np.array([5e-6, 10e-6, 20e-6, 50e-6])  # 5, 10, 20, 50 μm

# Bend arc length (fraction of propagation distance where bend occurs)
BEND_START = 0.2        # Start bend at 20% of z_total
BEND_END = 0.8          # End bend at 80% of z_total
BEND_LENGTH = Z_TOTAL * (BEND_END - BEND_START)  # Actual bend section length [m]

# Straight sections
STRAIGHT_IN = int(BEND_START * NZ)   # Input straight section steps
STRAIGHT_OUT = int((1 - BEND_END) * NZ)  # Output straight section steps

# =============================================================================
# INITIAL FIELD PARAMETERS
# =============================================================================

# Gaussian beam (approximate fundamental mode)
MODE_WIDTH = CORE_WIDTH / 2  # Mode width (smaller than core for confinement)
                             # Typical: w0 ≈ core_width / 2 for single mode

# =============================================================================
# ANALYSIS PARAMETERS
# =============================================================================

# Loss calculation
LOSS_REFERENCE_Z = int(0.1 * NZ)   # Reference point for loss (after initial transients)
LOSS_MEASUREMENT_Z = int(0.9 * NZ) # Final measurement point

# dB conversion factor
DB_FACTOR = 10  # 10*log10 for power, 20*log10 for field

# =============================================================================
# VISUALIZATION PARAMETERS
# =============================================================================

# Plot styling
FIGURE_DPI = 150        # Resolution for saved figures
FIGURE_SIZE = (10, 6)   # Default figure size (inches)
CMAP = 'hot'            # Colormap for field intensity plots
LINE_WIDTH = 2          # Line width for plots

# Animation parameters
ANIMATION_FPS = 30      # Frames per second for animations
FIELD_SNAPSHOTS = 100   # Number of z-slices to save for animation

# =============================================================================
# NUMERICAL PARAMETERS
# =============================================================================

# Convergence criteria
MAX_ITERATIONS = 10     # For iterative solvers (if needed)
TOLERANCE = 1e-6        # Convergence tolerance

# Boundary conditions
# Absorbing boundary implemented via window function
BOUNDARY_WIDTH = 0.1    # Fraction of x_range for absorbing boundary
BOUNDARY_POWER = 2      # Power of cosine window (higher = sharper)

# =============================================================================
# VALIDATION FLAGS
# =============================================================================

CHECK_ENERGY_CONSERVATION = True    # Monitor total power
CHECK_STRAIGHT_WAVEGUIDE = True     # Validate with straight guide first
VERBOSE = True                       # Print progress messages

# =============================================================================
# OUTPUT PARAMETERS
# =============================================================================

# Save options
SAVE_FIGURES = True
SAVE_DATA = True
SAVE_ANIMATIONS = False  # Set to True to generate animations (time-consuming)

# File formats
FIGURE_FORMAT = 'png'    # or 'pdf', 'svg'
DATA_FORMAT = 'npy'      # NumPy binary format

# =============================================================================
# DERIVED/CALCULATED PARAMETERS
# =============================================================================

def print_simulation_info():
    """Print key simulation parameters for verification"""
    print("="*70)
    print("WAVEGUIDE BEND SIMULATION - CONFIGURATION")
    print("="*70)
    print(f"\nPhysical Parameters:")
    print(f"  Wavelength:        {WAVELENGTH*1e6:.3f} μm")
    print(f"  Core index:        {N_CORE:.3f}")
    print(f"  Cladding index:    {N_CLAD:.3f}")
    print(f"  Index contrast:    {DELTA_N:.4f} ({100*DELTA_N/N_CORE:.2f}%)")
    print(f"  Core width:        {CORE_WIDTH*1e6:.2f} μm")
    
    print(f"\nGrid Parameters:")
    print(f"  x-range:           {X_RANGE*1e6:.1f} μm")
    print(f"  Nx points:         {NX}")
    print(f"  dx resolution:     {DX*1e9:.2f} nm ({DX/WAVELENGTH:.3f} λ)")
    print(f"  z-range:           {Z_TOTAL*1e6:.1f} μm")
    print(f"  Nz steps:          {NZ}")
    print(f"  dz step:           {DZ*1e9:.1f} nm ({DZ/WAVELENGTH:.4f} λ)")
    
    print(f"\nBend Parameters:")
    print(f"  Bend radii:        {[f'{r*1e6:.0f}' for r in BEND_RADII]} μm")
    print(f"  Bend length:       {BEND_LENGTH*1e6:.1f} μm")
    print(f"  Bend angle:        {np.rad2deg(BEND_LENGTH/BEND_RADII.min()):.1f}° (tightest)")
    
    print(f"\nNumerical Quality:")
    critical_radius = 10 * WAVELENGTH / DELTA_N
    print(f"  Critical radius:   ~{critical_radius*1e6:.1f} μm (theoretical)")
    print(f"  Points per λ:      {WAVELENGTH/DX:.1f}")
    print(f"  Steps per λ:       {WAVELENGTH/DZ:.1f}")
    
    print(f"\nMemory Estimate:")
    memory_mb = (NX * NZ * 16) / 1e6  # Complex128 = 16 bytes
    print(f"  Field storage:     ~{memory_mb:.1f} MB per simulation")
    print("="*70 + "\n")

# =============================================================================
# THEORETICAL ESTIMATES
# =============================================================================

def estimate_critical_radius():
    """
    Estimate critical bend radius using simple theory
    
    Rule of thumb: R_critical ≈ 10λ / Δn
    """
    R_crit = 10 * WAVELENGTH / DELTA_N
    return R_crit

def estimate_loss_coefficient(radius):
    """
    Rough estimate of loss coefficient [1/m] for a given bend radius
    
    Based on: α ≈ exp(-C * R / R_critical)
    where C is a geometry-dependent constant (~2-3)
    """
    R_crit = estimate_critical_radius()
    if radius < R_crit:
        # High loss regime
        alpha = 1e4 * np.exp(-2 * radius / R_crit)  # Empirical
    else:
        # Low loss regime
        alpha = 1e2 * (R_crit / radius)**3  # Power law scaling
    return alpha

if __name__ == "__main__":
    # Print configuration when run directly
    print_simulation_info()
    
    print("\nTheoretical Predictions:")
    R_crit = estimate_critical_radius()
    print(f"  Critical radius: {R_crit*1e6:.1f} μm")
    print(f"\n  Expected losses:")
    for R in BEND_RADII:
        alpha = estimate_loss_coefficient(R)
        loss_per_90deg = alpha * (np.pi/2 * R)
        loss_dB = 10 * np.log10(np.e) * loss_per_90deg
        print(f"    R = {R*1e6:4.0f} μm: ~{loss_dB:.2f} dB/90° (very rough estimate)")