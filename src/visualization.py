"""
Visualization Module
Publication-quality plotting for BPM simulation results
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import matplotlib.gridspec as gridspec


class BPMVisualizer:
    """
    Visualization tools for BPM simulation results
    """
    
    def __init__(self, figsize=(12, 8), dpi=150):
        """
        Initialize visualizer
        
        Parameters:
        -----------
        figsize : tuple
            Default figure size (width, height) in inches
        dpi : int
            Resolution for saved figures
        """
        self.figsize = figsize
        self.dpi = dpi
        
        # Set publication-quality defaults
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 13
        plt.rcParams['legend.fontsize'] = 10
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
    
    def plot_field_evolution(self, x_grid, z_positions, field_list, 
                            title="Field Evolution", 
                            save_path=None, show_colorbar=True):
        """
        Plot 2D map of field evolution
        
        Parameters:
        -----------
        x_grid : ndarray
            Spatial grid [m]
        z_positions : ndarray
            z positions where fields were saved [m]
        field_list : list of ndarrays
            List of field snapshots
        title : str
            Plot title
        save_path : str or None
            Path to save figure (if None, not saved)
        show_colorbar : bool
            Whether to show colorbar
        
        Returns:
        --------
        fig, ax : matplotlib figure and axes
        """
        # Convert field list to 2D array
        field_array = np.array([np.abs(f) for f in field_list])
        
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Create 2D image
        extent = [x_grid[0]*1e6, x_grid[-1]*1e6, 
                 z_positions[0]*1e6, z_positions[-1]*1e6]
        
        im = ax.imshow(field_array, aspect='auto', origin='lower',
                      extent=extent, cmap='hot', interpolation='bilinear')
        
        ax.set_xlabel('x [μm]')
        ax.set_ylabel('z [μm]')
        ax.set_title(title)
        
        if show_colorbar:
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Field Amplitude |E|')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            print(f"  Saved: {save_path}")
        
        return fig, ax
    
    def plot_power_evolution(self, z_array, power_array, 
                            bend_info=None,
                            title="Power Evolution",
                            save_path=None):
        """
        Plot power vs propagation distance
        
        Parameters:
        -----------
        z_array : ndarray
            z positions [m]
        power_array : ndarray
            Power at each z
        bend_info : dict or None
            Bend information (z_start, z_end)
        title : str
            Plot title
        save_path : str or None
            Path to save figure
        
        Returns:
        --------
        fig, ax : matplotlib figure and axes
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot power
        ax.plot(z_array*1e6, power_array, 'b-', linewidth=2)
        
        # Highlight bend region if provided
        if bend_info is not None:
            z_start = bend_info['z_start']
            z_end = bend_info['z_end']
            ax.axvspan(z_start*1e6, z_end*1e6, alpha=0.2, color='red',
                      label=f'Bend region (R={bend_info["radius"]*1e6:.0f} μm)')
            ax.legend()
        
        ax.set_xlabel('Propagation Distance z [μm]')
        ax.set_ylabel('Total Power [arb. units]')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            print(f"  Saved: {save_path}")
        
        return fig, ax
    
    def plot_field_snapshots(self, x_grid, field_list, z_positions,
                            indices=None, title_prefix="Field at",
                            save_path=None):
        """
        Plot field profiles at specific z positions
        
        Parameters:
        -----------
        x_grid : ndarray
            Spatial grid [m]
        field_list : list
            List of fields
        z_positions : ndarray
            z positions [m]
        indices : list or None
            Indices to plot (if None, plot evenly spaced)
        title_prefix : str
            Prefix for subplot titles
        save_path : str or None
            Path to save
        
        Returns:
        --------
        fig, axes : matplotlib figure and axes
        """
        if indices is None:
            # Plot 4 evenly spaced snapshots
            n_snapshots = min(4, len(field_list))
            indices = np.linspace(0, len(field_list)-1, n_snapshots, dtype=int)
        
        n_plots = len(indices)
        fig, axes = plt.subplots(n_plots, 1, figsize=(10, 2.5*n_plots))
        
        if n_plots == 1:
            axes = [axes]
        
        for i, idx in enumerate(indices):
            ax = axes[i]
            field = field_list[idx]
            z_pos = z_positions[idx]
            
            # Plot amplitude
            ax.plot(x_grid*1e6, np.abs(field), 'b-', linewidth=2)
            ax.set_xlabel('x [μm]')
            ax.set_ylabel('|E|')
            ax.set_title(f'{title_prefix} z = {z_pos*1e6:.1f} μm')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            print(f"  Saved: {save_path}")
        
        return fig, axes
    
    def plot_loss_comparison(self, radii_list, loss_list, 
                            title="Bend Loss vs Radius",
                            save_path=None):
        """
        Plot loss as function of bend radius
        
        This is the KEY RESULT of the simulation!
        
        Parameters:
        -----------
        radii_list : list or ndarray
            Bend radii [m]
        loss_list : list or ndarray
            Loss values [dB]
        title : str
            Plot title
        save_path : str or None
            Path to save
        
        Returns:
        --------
        fig, ax : matplotlib figure and axes
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Convert to μm for plotting
        radii_um = np.array(radii_list) * 1e6
        
        # Plot
        ax.plot(radii_um, loss_list, 'ro-', linewidth=2, markersize=10,
               markerfacecolor='red', markeredgecolor='black', markeredgewidth=1.5)
        
        ax.set_xlabel('Bend Radius [μm]')
        ax.set_ylabel('Loss [dB/90°]')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Add value labels
        for r, loss in zip(radii_um, loss_list):
            ax.text(r, loss + 0.05*max(loss_list), f'{loss:.2f}', 
                   ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            print(f"  Saved: {save_path}")
        
        return fig, ax
    
    def plot_comprehensive_results(self, results_dict, save_dir=None):
        """
        Create comprehensive 4-panel figure for a single simulation
        
        Parameters:
        -----------
        results_dict : dict
            BPM results dictionary with keys:
            - 'field_evolution', 'power_evolution', 'z_positions', etc.
        save_dir : str or None
            Directory to save figure
        
        Returns:
        --------
        fig : matplotlib figure
        """
        fig = plt.figure(figsize=(14, 10))
        gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)
        
        x = results_dict.get('x_grid', None)
        z_pos = results_dict['z_positions']
        fields = results_dict['field_evolution']
        power = results_dict['power_evolution']
        z_array = results_dict['z_array']
        bend_info = results_dict.get('bend_info', None)
        
        # Panel 1: Field evolution (2D map)
        ax1 = fig.add_subplot(gs[0, :])
        field_array = np.array([np.abs(f) for f in fields])
        extent = [x[0]*1e6, x[-1]*1e6, z_pos[0]*1e6, z_pos[-1]*1e6]
        im1 = ax1.imshow(field_array, aspect='auto', origin='lower',
                        extent=extent, cmap='hot', interpolation='bilinear')
        ax1.set_xlabel('x [μm]')
        ax1.set_ylabel('z [μm]')
        ax1.set_title('Field Evolution |E(x,z)|')
        plt.colorbar(im1, ax=ax1, label='Amplitude')
        
        # Panel 2: Power vs z
        ax2 = fig.add_subplot(gs[1, 0])
        ax2.plot(z_array*1e6, power, 'b-', linewidth=2)
        if bend_info:
            ax2.axvspan(bend_info['z_start']*1e6, bend_info['z_end']*1e6,
                       alpha=0.2, color='red', label='Bend')
            ax2.legend()
        ax2.set_xlabel('z [μm]')
        ax2.set_ylabel('Power')
        ax2.set_title('Power Evolution')
        ax2.grid(True, alpha=0.3)
        
        # Panel 3: Field snapshots
        ax3 = fig.add_subplot(gs[1, 1])
        indices = [0, len(fields)//2, -1]
        colors = ['blue', 'green', 'red']
        labels = ['Initial', 'Middle', 'Final']
        for idx, color, label in zip(indices, colors, labels):
            ax3.plot(x*1e6, np.abs(fields[idx]), color=color, 
                    linewidth=2, label=f'{label} (z={z_pos[idx]*1e6:.0f} μm)')
        ax3.set_xlabel('x [μm]')
        ax3.set_ylabel('|E|')
        ax3.set_title('Field Profiles')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        if save_dir:
            if bend_info:
                filename = f"results_R{bend_info['radius']*1e6:.0f}um.png"
            else:
                filename = "results_straight.png"
            save_path = f"{save_dir}/{filename}"
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            print(f"  Saved: {save_path}")
        
        return fig


def create_summary_figure(all_results, radii_list, save_path=None):
    """
    Create publication-quality summary figure comparing all bend radii
    
    Parameters:
    -----------
    all_results : list of dicts
        List of BPM results for different radii
    radii_list : list
        List of bend radii [m]
    save_path : str or None
        Path to save figure
    
    Returns:
    --------
    fig : matplotlib figure
    """
    from bpm_engine import FieldAnalysis
    
    n_radii = len(radii_list)
    
    fig = plt.figure(figsize=(16, 10))
    gs = gridspec.GridSpec(3, n_radii, figure=fig, hspace=0.35, wspace=0.3)
    
    # Row 1: Field evolution for each radius
    for i, (results, R) in enumerate(zip(all_results, radii_list)):
        ax = fig.add_subplot(gs[0, i])
        
        x = results['x_grid']
        z_pos = results['z_positions']
        fields = results['field_evolution']
        
        field_array = np.array([np.abs(f) for f in fields])
        extent = [x[0]*1e6, x[-1]*1e6, z_pos[0]*1e6, z_pos[-1]*1e6]
        
        im = ax.imshow(field_array, aspect='auto', origin='lower',
                      extent=extent, cmap='hot', interpolation='bilinear')
        ax.set_xlabel('x [μm]', fontsize=9)
        ax.set_ylabel('z [μm]', fontsize=9)
        ax.set_title(f'R = {R*1e6:.0f} μm', fontsize=10, fontweight='bold')
        ax.tick_params(labelsize=8)
    
    # Row 2: Power evolution for each radius
    for i, (results, R) in enumerate(zip(all_results, radii_list)):
        ax = fig.add_subplot(gs[1, i])
        
        z_array = results['z_array']
        power = results['power_evolution']
        bend_info = results.get('bend_info')
        
        ax.plot(z_array*1e6, power, 'b-', linewidth=2)
        
        if bend_info:
            ax.axvspan(bend_info['z_start']*1e6, bend_info['z_end']*1e6,
                      alpha=0.2, color='red')
        
        ax.set_xlabel('z [μm]', fontsize=9)
        ax.set_ylabel('Power', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=8)
    
    # Row 3: Loss comparison (spans all columns)
    ax_loss = fig.add_subplot(gs[2, :])
    
    # Calculate loss for each radius
    loss_values = []
    for results, R in zip(all_results, radii_list):
        power = results['power_evolution']
        bend_info = results.get('bend_info')
        
        if bend_info:
            loss_90deg = FieldAnalysis.calculate_loss_per_90deg(
                power, results['z_array'], R
            )
        else:
            loss_90deg = FieldAnalysis.calculate_loss_dB(power)
        
        loss_values.append(loss_90deg)
    
    # Plot loss vs radius
    radii_um = np.array(radii_list) * 1e6
    ax_loss.plot(radii_um, loss_values, 'ro-', linewidth=3, markersize=12,
                markerfacecolor='red', markeredgecolor='black', markeredgewidth=2)
    
    ax_loss.set_xlabel('Bend Radius [μm]', fontsize=12, fontweight='bold')
    ax_loss.set_ylabel('Loss [dB/90°]', fontsize=12, fontweight='bold')
    ax_loss.set_title('KEY RESULT: Bend Loss vs Radius', 
                     fontsize=14, fontweight='bold')
    ax_loss.grid(True, alpha=0.3, linestyle='--')
    
    # Add value labels
    for r, loss in zip(radii_um, loss_values):
        ax_loss.text(r, loss, f'  {loss:.3f} dB', 
                    ha='left', va='center', fontsize=10, fontweight='bold')
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  Saved: {save_path}")
    
    return fig


if __name__ == "__main__":
    print("Visualization module loaded successfully ✅")
    print("Use BPMVisualizer class to create plots")