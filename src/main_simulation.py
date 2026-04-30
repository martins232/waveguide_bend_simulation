"""
Main Simulation Script
Run BPM simulations for all bend radii and generate comprehensive results
"""

import numpy as np
import matplotlib.pyplot as plt
import time
from config import *
from waveguide_geometry import WaveguideGeometry, InitialField, create_absorbing_boundary
from bpm_engine import BPMEngine, FieldAnalysis
from visualization import BPMVisualizer, create_summary_figure

print("="*70)
print("WAVEGUIDE BEND LOSS SIMULATION")
print("Parametric Sweep: Testing All Bend Radii")
print("="*70)

# =============================================================================
# INITIALIZATION
# =============================================================================

print("\n" + "="*70)
print("INITIALIZATION")
print("="*70)

# Create grids
print("\nCreating spatial grids...")
print(f"  x-range: {X_RANGE*1e6:.1f} μm, {NX} points")
print(f"  z-range: {Z_TOTAL*1e6:.1f} μm, {NZ} steps")

# Initialize BPM engine
bpm = BPMEngine(x, kx)
print(f"\nBPM Engine initialized:")
print(f"  k₀ = {K0:.2e} rad/m")
print(f"  n₀ = {N0:.4f}")
print(f"  Δz = {DZ*1e9:.1f} nm")

# Create initial field
field_gen = InitialField(x)
initial_field = field_gen.gaussian_mode()
initial_power = np.sum(np.abs(initial_field)**2) * DX

print(f"\nInitial field generated:")
print(f"  Type: Gaussian mode approximation")
print(f"  Peak amplitude: {np.max(np.abs(initial_field)):.4f}")
print(f"  Total power: {initial_power:.6e}")
print(f"  Mode width: {MODE_WIDTH*1e6:.3f} μm")

# Bend radii to simulate
bend_radii = BEND_RADII
print(f"\nBend radii to simulate:")
for i, R in enumerate(bend_radii):
    print(f"  {i+1}. R = {R*1e6:5.0f} μm")

# =============================================================================
# RUN SIMULATIONS
# =============================================================================

print("\n" + "="*70)
print("RUNNING SIMULATIONS")
print("="*70)

# Storage for results
all_results = []
simulation_times = []

for i, R in enumerate(bend_radii):
    print(f"\n{'='*70}")
    print(f"SIMULATION {i+1}/{len(bend_radii)}: Bend Radius R = {R*1e6:.0f} μm")
    print(f"{'='*70}")
    
    # Start timer
    t_start = time.time()
    
    # Run simulation
    results = bpm.propagate_bent_waveguide(
        initial_field,
        bend_radius=R,
        z_total=Z_TOTAL,
        nz=NZ,
        bend_start_fraction=BEND_START,
        bend_end_fraction=BEND_END,
        save_interval=50,  # Save every 50 steps for memory efficiency
        verbose=True
    )
    
    # End timer
    t_end = time.time()
    sim_time = t_end - t_start
    simulation_times.append(sim_time)
    
    # Add x_grid to results for visualization
    results['x_grid'] = x
    results['bend_radius'] = R
    
    # Store results
    all_results.append(results)
    
    # Quick analysis
    bend_info = results['bend_info']
    total_loss_dB = FieldAnalysis.calculate_loss_dB(results['power_evolution'])
    loss_90deg = FieldAnalysis.calculate_loss_per_90deg(
        results['power_evolution'],
        results['z_array'],
        R
    )
    
    print(f"\n  Simulation completed in {sim_time:.2f} seconds")
    print(f"  Total loss: {total_loss_dB:.4f} dB")
    print(f"  Loss per 90°: {loss_90deg:.4f} dB/90°")
    print(f"  Bend angle: {bend_info['bend_angle_deg']:.1f}°")

# =============================================================================
# ANALYSIS & SUMMARY
# =============================================================================

print("\n" + "="*70)
print("ANALYSIS SUMMARY")
print("="*70)

# Calculate losses for all radii
loss_data = []

print("\n{:<15} {:<20} {:<20} {:<15}".format(
    "Radius [μm]", "Total Loss [dB]", "Loss per 90° [dB]", "Sim Time [s]"
))
print("-"*70)

for i, (R, results, t_sim) in enumerate(zip(bend_radii, all_results, simulation_times)):
    power = results['power_evolution']
    z_array = results['z_array']
    
    total_loss = FieldAnalysis.calculate_loss_dB(power)
    loss_90deg = FieldAnalysis.calculate_loss_per_90deg(power, z_array, R)
    
    loss_data.append({
        'radius': R,
        'radius_um': R * 1e6,
        'total_loss_dB': total_loss,
        'loss_90deg_dB': loss_90deg,
        'simulation_time': t_sim
    })
    
    print("{:<15.1f} {:<20.4f} {:<20.4f} {:<15.2f}".format(
        R*1e6, total_loss, loss_90deg, t_sim
    ))

print("-"*70)
print(f"Total simulation time: {sum(simulation_times):.2f} seconds")

# =============================================================================
# SAVE DATA
# =============================================================================

print("\n" + "="*70)
print("SAVING DATA")
print("="*70)

# Save loss data as NumPy arrays
loss_array = np.array([[ld['radius_um'], ld['loss_90deg_dB']] 
                       for ld in loss_data])
np.save('../results/data/loss_vs_radius.npy', loss_array)
print("  Saved: results/data/loss_vs_radius.npy")

# Save raw results (for later analysis)
np.save('../results/data/all_simulation_results.npy', all_results, allow_pickle=True)
print("  Saved: results/data/all_simulation_results.npy")

# =============================================================================
# GENERATE VISUALIZATIONS
# =============================================================================

print("\n" + "="*70)
print("GENERATING VISUALIZATIONS")
print("="*70)

vis = BPMVisualizer()

# 1. Individual comprehensive plots for each radius
print("\n1. Individual result plots for each radius...")
for results, R in zip(all_results, bend_radii):
    fig = vis.plot_comprehensive_results(results, save_dir='../results/figures')
print("  ✅ Created 4 comprehensive plots")

# 2. Power evolution comparison
print("\n2. Power evolution comparison...")
fig_power, ax_power = plt.subplots(figsize=(12, 7))

colors = ['red', 'orange', 'green', 'blue']
for results, R, color in zip(all_results, bend_radii, colors):
    z_array = results['z_array']
    power = results['power_evolution']
    bend_info = results['bend_info']
    loss_90 = FieldAnalysis.calculate_loss_per_90deg(power, z_array, R)
    
    label = f'R = {R*1e6:.0f} μm ({loss_90:.3f} dB/90°)'
    ax_power.plot(z_array*1e6, power, color=color, linewidth=2, label=label)
    
    # Mark bend region (only for first plot)
    if R == bend_radii[0]:
        ax_power.axvspan(bend_info['z_start']*1e6, bend_info['z_end']*1e6,
                        alpha=0.1, color='gray', label='Bend region')

ax_power.set_xlabel('Propagation Distance z [μm]', fontsize=12)
ax_power.set_ylabel('Total Power [arb. units]', fontsize=12)
ax_power.set_title('Power Evolution - All Bend Radii Comparison', 
                   fontsize=14, fontweight='bold')
ax_power.legend(loc='upper right', fontsize=10)
ax_power.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../results/figures/power_comparison_all_radii.png', dpi=150, bbox_inches='tight')
print("  Saved: results/figures/power_comparison_all_radii.png")
plt.close()

# 3. Loss vs radius (MAIN RESULT)
print("\n3. Loss vs radius (MAIN RESULT)...")
radii_um = [ld['radius_um'] for ld in loss_data]
losses_90 = [ld['loss_90deg_dB'] for ld in loss_data]

fig_loss = vis.plot_loss_comparison(
    bend_radii,
    losses_90,
    title='Waveguide Bend Loss vs Radius (Main Result)',
    save_path='../results/figures/MAIN_RESULT_loss_vs_radius.png'
)
plt.close()

# 4. Summary figure with everything
print("\n4. Comprehensive summary figure...")
fig_summary = create_summary_figure(
    all_results,
    bend_radii,
    save_path='../results/figures/comprehensive_summary.png'
)
plt.close()
print("  Saved: results/figures/comprehensive_summary.png")

# 5. Field evolution side-by-side
print("\n5. Field evolution comparison (side-by-side)...")
fig_fields, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

for i, (results, R) in enumerate(zip(all_results, bend_radii)):
    ax = axes[i]
    
    field_array = np.array([np.abs(f) for f in results['field_evolution']])
    z_pos = results['z_positions']
    extent = [x[0]*1e6, x[-1]*1e6, z_pos[0]*1e6, z_pos[-1]*1e6]
    
    im = ax.imshow(field_array, aspect='auto', origin='lower',
                  extent=extent, cmap='hot', interpolation='bilinear')
    
    ax.set_xlabel('x [μm]')
    ax.set_ylabel('z [μm]')
    ax.set_title(f'R = {R*1e6:.0f} μm', fontweight='bold')
    
    # Mark bend region
    bend_info = results['bend_info']
    ax.axhline(bend_info['z_start']*1e6, color='white', linestyle='--', 
              alpha=0.5, linewidth=1)
    ax.axhline(bend_info['z_end']*1e6, color='white', linestyle='--', 
              alpha=0.5, linewidth=1)

plt.suptitle('Field Evolution Comparison - All Bend Radii', 
            fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('../results/figures/field_evolution_comparison.png', dpi=150, bbox_inches='tight')
print("  Saved: results/figures/field_evolution_comparison.png")
plt.close()

# =============================================================================
# FINAL SUMMARY
# =============================================================================

print("\n" + "="*70)
print("SIMULATION COMPLETE! ✅")
print("="*70)

print("\n📊 KEY FINDINGS:")
print("-"*70)

# Find critical radius (where loss exceeds 1 dB/90°)
critical_threshold = 1.0  # dB/90°
critical_radii = [ld for ld in loss_data if ld['loss_90deg_dB'] < critical_threshold]

if critical_radii:
    R_critical = critical_radii[-1]['radius_um']  # Largest radius below threshold
    print(f"  Critical Radius (< {critical_threshold} dB/90°): ~{R_critical:.0f} μm")
else:
    print(f"  All tested radii exceed {critical_threshold} dB/90° loss")

# Highest and lowest loss
min_loss_data = min(loss_data, key=lambda x: x['loss_90deg_dB'])
max_loss_data = max(loss_data, key=lambda x: x['loss_90deg_dB'])

print(f"\n  Lowest Loss:  R = {min_loss_data['radius_um']:.0f} μm → "
      f"{min_loss_data['loss_90deg_dB']:.4f} dB/90°")
print(f"  Highest Loss: R = {max_loss_data['radius_um']:.0f} μm → "
      f"{max_loss_data['loss_90deg_dB']:.4f} dB/90°")

# Loss ratio
loss_ratio = max_loss_data['loss_90deg_dB'] / min_loss_data['loss_90deg_dB']
print(f"\n  Loss Ratio (tightest/gentlest): {loss_ratio:.1f}×")

print("\n📁 RESULTS SAVED:")
print("-"*70)
print("  Data files:")
print("    - results/data/loss_vs_radius.npy")
print("    - results/data/all_simulation_results.npy")
print("\n  Figures:")
print("    - results/figures/results_R5um.png")
print("    - results/figures/results_R10um.png")
print("    - results/figures/results_R20um.png")
print("    - results/figures/results_R50um.png")
print("    - results/figures/power_comparison_all_radii.png")
print("    - results/figures/MAIN_RESULT_loss_vs_radius.png ⭐")
print("    - results/figures/comprehensive_summary.png")
print("    - results/figures/field_evolution_comparison.png")

print("\n" + "="*70)
print("All simulations and visualizations complete!")
print("Ready for report writing (Step 5)")
print("="*70)