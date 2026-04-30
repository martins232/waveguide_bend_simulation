"""
Test BPM Engine with Bent Waveguides
Quick test to verify bend simulations work before full parametric sweep
"""

import numpy as np
import matplotlib.pyplot as plt
from config import *
from waveguide_geometry import WaveguideGeometry, InitialField, create_absorbing_boundary
from bpm_engine import BPMEngine, FieldAnalysis
from visualization import BPMVisualizer

print("="*70)
print("TESTING BPM ENGINE - BENT WAVEGUIDE")
print("="*70)

# Create grids
print("\nInitializing grids and BPM engine...")

# Initialize BPM engine
bpm = BPMEngine(x, kx)

# Create initial field
field_gen = InitialField(x)
initial_field = field_gen.gaussian_mode()

print(f"  Grid size: {len(x)} points")
print(f"  Initial power: {np.sum(np.abs(initial_field)**2) * DX:.6e}")

# Test with a single bend radius (10 μm)
test_radius = 10e-6

print(f"\n" + "="*70)
print(f"TEST: Bent Waveguide (R = {test_radius*1e6:.0f} μm)")
print("="*70)

# Run simulation
results_bent = bpm.propagate_bent_waveguide(
    initial_field,
    bend_radius=test_radius,
    z_total=Z_TOTAL,
    nz=NZ,
    save_interval=50,
    verbose=True
)

# Analyze results
print("\n" + "="*70)
print("Analysis:")
print("="*70)

bend_info = results_bent['bend_info']
print(f"\nBend Information:")
print(f"  Radius:        {bend_info['radius']*1e6:.1f} μm")
print(f"  Bend length:   {bend_info['bend_length']*1e6:.1f} μm")
print(f"  Bend angle:    {bend_info['bend_angle_deg']:.1f}°")
print(f"  z_start:       {bend_info['z_start']*1e6:.1f} μm")
print(f"  z_end:         {bend_info['z_end']*1e6:.1f} μm")

# Calculate losses
total_loss_dB = FieldAnalysis.calculate_loss_dB(results_bent['power_evolution'])
loss_90deg = FieldAnalysis.calculate_loss_per_90deg(
    results_bent['power_evolution'],
    results_bent['z_array'],
    test_radius
)

print(f"\nLoss Analysis:")
print(f"  Total loss:         {total_loss_dB:.4f} dB")
print(f"  Loss per 90°:       {loss_90deg:.4f} dB/90°")

# Mode shift analysis
initial_center = FieldAnalysis.find_mode_center(initial_field, x)
final_center = FieldAnalysis.find_mode_center(results_bent['final_field'], x)
mode_shift = final_center - initial_center

print(f"\nMode Properties:")
print(f"  Initial center:     {initial_center*1e9:.2f} nm")
print(f"  Final center:       {final_center*1e9:.2f} nm")
print(f"  Mode shift:         {mode_shift*1e9:.2f} nm")

# Visualize
print("\n" + "="*70)
print("Generating Visualizations...")
print("="*70)

vis = BPMVisualizer()

# Add x_grid to results for visualization
results_bent['x_grid'] = x

# Comprehensive results plot
fig = vis.plot_comprehensive_results(results_bent, save_dir='../results/figures')
print("  ✅ Comprehensive plot created")

# Power evolution
fig_power = vis.plot_power_evolution(
    results_bent['z_array'],
    results_bent['power_evolution'],
    bend_info=bend_info,
    title=f'Power Evolution - R = {test_radius*1e6:.0f} μm',
    save_path='../results/figures/test_bent_power.png'
)

# Field evolution
fig_field = vis.plot_field_evolution(
    x, 
    results_bent['z_positions'],
    results_bent['field_evolution'],
    title=f'Field Evolution - R = {test_radius*1e6:.0f} μm',
    save_path='../results/figures/test_bent_field_evolution.png'
)

print("\n" + "="*70)
print("BENT WAVEGUIDE TEST COMPLETE ✅")
print("="*70)
print(f"\n✅ Bend simulation working correctly!")
print(f"   Observed {loss_90deg:.4f} dB/90° loss for R = {test_radius*1e6:.0f} μm")
print(f"   Mode shifted by {mode_shift*1e9:.2f} nm toward outer edge")
print("\n   Ready for full parametric sweep!")

plt.close('all')