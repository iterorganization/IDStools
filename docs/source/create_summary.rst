################
 create_summary
################

*create_summary* creates a ``summary`` IDS from the other IDSs stored in an
IMAS data entry (Data Dictionary 3 or 4) and writes it back into the same
entry. The summary is written in the DD version of the entry, without
conversion.

Each filled summary quantity records in its ``source`` node the IDS path it
was taken or computed from. Quantities that cannot be obtained from the IDSs
of the entry are left empty.

- If the entry already contains a summary IDS, the command stops with an
  error before building the summary, unless ``--force`` is given (the
  existing summary is then overwritten). A summary cannot be overwritten in a
  netCDF file.
- ``--time-base IDS`` selects the IDS defining the summary time base
  (default: the first of core_profiles, plasma_profiles, edge_profiles,
  equilibrium, core_sources, magnetics). Signals not covering the whole time
  base are left out.
- ``--dry-run`` builds and prints the summary without writing it.
- ``-v`` also prints the summary on a normal run, with informative messages;
  ``-vv`` adds debug messages.

From Python, the summary is built in memory and only written on request:

.. code-block:: python

   from idstools.domain.summary import build_summary, write_summary

   summary = build_summary("imas:hdf5?path=/path/to/entry", verbose=True)  # reads the entry only
   write_summary(summary, "imas:hdf5?path=/path/to/entry")

- ``build_summary(uri, time_base=None, comment=None, verbose=False)`` returns
  the summary IDS, in the DD version of the entry. With ``verbose``, it
  prints the filled quantities. An existing summary in the entry is ignored.
- ``write_summary(summary, uri, force=False)`` writes a summary IDS into an
  existing data entry. It refuses to overwrite an existing summary without
  ``force`` (and always in a netCDF file), and to write into an entry of
  another DD major version.
- ``has_summary(uri)`` and ``check_writable(uri, force)`` check the entry
  beforehand.
- The summary ``ids_properties/provenance`` references the IDSs of the
  entry it was built from (those appearing as paths in the ``source``
  nodes), also when it is written into another entry.

All of them raise ``SummaryError`` on failure.

***********************
 Syntax create_summary
***********************

   .. program-output:: create_summary -h

************************
 Example create_summary
************************

   .. code-block:: bash

      $ create_summary -u "imas:hdf5?user=public;pulse=134174;run=117;database=ITER;version=3" --dry-run
      Summary on 106 time(s) [10.5992, 75.0001] s, 73 quantities:
        code/name                                               'JINTRAC_JETTO'                <- core_profiles
        global_quantities/ip                                    [-3228381.9854 -3228382.226  -3228382.4666] <- equilibrium/time_slice/global_quantities/ip
        ...
        global_quantities/h_98                                  [0.1246 0.1246 0.1246]         <- summary/global_quantities/tau_energy / global_quantities/tau_energy_98
      Dry run: summary not written.

*********
 Sources
*********

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - IDS
     - Summary quantities
   * - equilibrium
     - ip, q_95, \*_mhd betas, li_3_mhd, energy_mhd, volume, magnetic axis,
       boundary shape, r0/b0
   * - core_profiles
     - global quantities, ohmic current, values on axis and at the
       separatrix, volume averages (per species), thermal and total energy
       contents, effective hydrogenic mass and hydrogen fraction
   * - core_profiles + equilibrium
     - line averages on the horizontal chord through the magnetic axis
   * - core_sources
     - absorbed NBI/EC/IC/LH power, ohmic, fusion (alpha) and radiated powers
   * - nbi, ec_launchers, ic_antennas, lh_antennas
     - launched powers, frequencies, NBI energy and species
   * - waves
     - power coupled by each EC/IC/LH launcher (coherent waves matched by
       antenna name)
   * - edge_profiles, plasma_profiles (GGD)
     - outer midplane separatrix and target separatrix values, strike
       points, configuration
   * - radiation (GGD)
     - radiated power outside the LCFS and in the SOL
   * - gas_injection
     - gas injection rates
   * - magnetics
     - ip, when no other IDS provides it
   * - dataset_description
     - machine, pulse, simulation (DD >= 4.1 summary)

Quantities renamed between DD 3 and DD 4 are mapped when the DD documents the
same definition (e.g. ``li`` / ``li_3``, ``beta_normal`` /
``beta_tor_norm``, NBI species ``label`` / ``name``). The DD 3 summary
``local/magnetic_axis/b_field``, whose component is not specified, is not
filled.

***************************************
 Computed and derived summary signals
***************************************

Most summary quantities are copied from another IDS of the data entry. The
quantities below are instead computed from the profiles of the entry, or
derived from other summary quantities. Each one records its formula in its
``source`` node.

Many of these quantities are read by other IDStools tools, e.g.
*plotscenario* (``h_98``, ``tau_energy``, ``energy_thermal``,
``energy_total``, ``current_ohm``, ``power_steady``, ``fusion/power``,
per-launcher ``heating_current_drive/*/power``).

Quantities computed from the IDSs
=================================

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Summary path
     - Obtained from
   * - ``global_quantities/current_ohm``
     - core_profiles ``global_quantities/ip`` − ``current_non_inductive``
   * - ``global_quantities/energy_thermal``, ``energy_electrons_thermal``,
       ``energy_ion_total_thermal``
     - 3/2 × volume integral of the electron and ion thermal pressures of
       core_profiles (``electrons/pressure_thermal``,
       ``pressure_ion_total``; without them, e·n·T per species).
       ``energy_thermal`` is the sum of the electron and ion energies, so
       that the summary is consistent. ``pressure_thermal`` is only used when
       one of them is missing; otherwise a warning is logged when its energy
       differs from the sum by more than 1%.
   * - ``global_quantities/energy_total``
     - Volume integral of (``pressure_parallel``/2 +
       ``pressure_perpendicular``), which includes the fast particles. Only
       filled when the entry has these pressures.
   * - ``volume_average/meff_hydrogenic``
     - (Σ a·n) / (Σ n) over the hydrogenic ions (H, D, T, DT), with
       volume-averaged densities
   * - ``volume_average/isotope_fraction_hydrogen``
     - n_H / (n_H + n_D + n_T + n_DT), with volume-averaged densities
   * - ``line_average/*`` (``n_e``, ``t_e``, ``t_i_average``, ``zeff``,
       ``n_i/*``, ``n_i_total``)
     - Average along the horizontal chord through the magnetic axis. The
       chord width at each flux surface, ``r_outboard`` − ``r_inboard``,
       comes from equilibrium ``time_slice/profiles_1d``, interpolated
       linearly in time. The profile grid and the equilibrium must both
       cover the plasma from the axis to the separatrix.
   * - ``fusion/power``
     - core_sources fusion source (identifier index 6)
   * - ``heating_current_drive/{ec,ic,lh}[i]/power``
     - waves ``coherent_wave[:]/global_quantities/power``. Each wave is
       matched to a launcher of ec_launchers, ic_antennas or lh_antennas by
       ``identifier/antenna_name``, and the waves of the same launcher are
       summed.

The core_sources powers (``heating_current_drive/power_*``, ``power_ohm``,
``fusion/power``, radiated powers) are taken, in this order of preference,
from:

#. ``source/global_quantities/power``.
#. ``profiles_1d/electrons/power_inside`` + ``total_ion_power_inside`` at
   the last radial point.
#. The volume integral of ``profiles_1d/electrons/energy`` +
   ``total_ion_energy``. The grid must reach the separatrix.

Quantities derived from the summary
===================================

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Summary path
     - Definition
   * - ``heating_current_drive/power_additional``
     - Sum of the coupled NBI, EC, IC and LH powers
   * - ``heating_current_drive/<system>[0]/power``
     - The system total (``power_ec``, ...), when the system has a single
       launcher
   * - ``global_quantities/denergy_thermal_dt``
     - Time derivative of ``energy_thermal`` on the summary time base
   * - ``global_quantities/power_steady``
     - ``power_ohm`` + ``power_additional`` + ``fusion/power`` −
       ``denergy_thermal_dt``
   * - ``global_quantities/power_loss``
     - ``power_steady`` minus the radiation inside the LCFS. This is
       ``power_radiated_inside_lcfs`` if available, else core_sources
       ``power_radiated``, else the sum of ``power_bremsstrahlung``,
       ``power_synchrotron`` and ``power_line``.
   * - ``global_quantities/tau_energy``
     - ``energy_thermal`` / ``power_steady``
   * - ``global_quantities/tau_energy_98``
     - IPB98(y,2) scaling (see below)
   * - ``global_quantities/h_98``
     - ``tau_energy`` / ``tau_energy_98``
   * - ``global_quantities/greenwald_fraction``
     - ``line_average/n_e`` [10²⁰ m⁻³] / (\|``ip``\| [MA] / (π
       ``boundary/minor_radius``\ ²))

IPB98(y,2) scaling
------------------

.. math::

   \tau_{98} = 0.0562 \, I^{0.93} B^{0.15} n^{0.41} P^{-0.69} R^{1.97}
   \kappa_a^{0.78} \varepsilon^{0.58} M^{0.19}

The inputs are:

- **I** = \|``global_quantities/ip``\| [MA].
- **B** = \|``global_quantities/b0``\| · ``r0`` / R [T], the vacuum field at
  the geometric axis.
- **n** = ``line_average/n_e`` [10¹⁹ m⁻³].
- **P** = ``global_quantities/power_steady`` [MW], the loss power of the
  scaling. The radiation is not subtracted.
- **R** = ``boundary/geometric_axis_r`` [m].
- **ε** = a / R, with a = ``boundary/minor_radius`` [m].
- **κ_a** = ``global_quantities/volume`` / (2π² R a²), the area elongation.
- **M** = ``volume_average/meff_hydrogenic`` [u].

Conventions and limitations
===========================

- **Missing heating terms:** all heating powers come from core_sources, so a
  heating term absent from it counts as zero in ``power_steady``.
- **Single time slice:** time derivatives need at least two summary times.
  With a single time slice, ``denergy_thermal_dt``, ``power_steady``,
  ``power_loss``, ``tau_energy``, ``tau_energy_98`` and ``h_98`` are not
  filled.
- **Empty inputs:** a derived quantity is left empty when any of its inputs
  is missing, or invalid at some time. For example, a negative or zero
  ``power_steady`` at one time leaves ``tau_energy``, ``tau_energy_98`` and
  ``h_98`` empty.
- **Not computed:** ``global_quantities/h_mode`` and
  ``stationary_phase_flag`` cannot be derived reliably from the IDSs, so they
  are not computed. ``fusion/neutron_power_total`` and the fast-particle
  energies (``energy_fast_parallel``, ``energy_fast_perpendicular``) are not
  computed yet.
