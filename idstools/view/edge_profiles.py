import logging

import numpy as np
from matplotlib.collections import PolyCollection

from idstools.compute.edge_profiles import EdgeProfilesCompute

logger = logging.getLogger("module")


class EdgeProfilesView:
    def __init__(self, edge_profile_ids=None):
        self.edge_profiles_compute = EdgeProfilesCompute(edge_profile_ids)

    @staticmethod
    def view_plasma_composition_with_species_concentration(ids_object, slice_index=0, print_data=False):
        """
        Nice display of plasma composition with species concentrations
        """
        composition_data = EdgeProfilesCompute.get_plasma_composition_with_species_concentration(
            ids_object, slice_index
        )
        if composition_data != 0 and composition_data != -1:
            edge_profiles_view = EdgeProfilesView()
            edge_profiles_view._print_plasma_composition(composition_data)
            edge_profiles_view._print_specis_concentration(composition_data)

            if print_data is True:
                import json

                print(json.dumps(composition_data, sort_keys=True, indent=4))
        return composition_data

    def _print_plasma_composition(self, composition_data):
        disp_species = f"{'species:': <15}"
        disp_a = f"{'a:': <15}"
        disp_z = f"{'z:': <15}"
        disp_nspec_over_ntot = f"{'n_over_ntot:': <15}"
        disp_nspec_over_ne = f"{'n_over_ne:': <15}"
        disp_nspec_over_nmaj = f"{'n_over_n_maj:': <15}"
        main_species = ""

        for species_key, species_data in composition_data.items():
            if species_data["nspec_over_ntot"] > 0.45:
                if len(main_species) == 0:
                    main_species = main_species + species_data["species"]
                else:
                    main_species = main_species + "-" + species_data["species"]
            if species_data["nspec_over_ne"] > 0.0:
                species_name = f"{species_data['species']}({species_data['label']})"
                species_name = species_name[:11]
                disp_species = f"{disp_species} {species_name : >12}"
                a = f"{species_data['a'].value :.1f}"
                disp_a = f"{disp_a} {a : >12}"
                z = f"{species_data['z'] :.1f}"
                disp_z = f"{disp_z} {z : >12}"
                if species_data["nspec_over_ntot"] < 1.0e-2:
                    nspec_over_ntot = f"{species_data['nspec_over_ntot'] :.2e}"
                    disp_nspec_over_ntot = f"{disp_nspec_over_ntot} {nspec_over_ntot : >12}"
                else:
                    nspec_over_ntot = f"{species_data['nspec_over_ntot'] :.3f}"
                    disp_nspec_over_ntot = f"{disp_nspec_over_ntot} {nspec_over_ntot : >12}"
                if species_data["nspec_over_ne"] < 1.0e-2:
                    nspec_over_ne = f"{species_data['nspec_over_ne'] :.2e}"
                    disp_nspec_over_ne = f"{disp_nspec_over_ne} {nspec_over_ne : >12}"
                else:
                    nspec_over_ne = f"{species_data['nspec_over_ne'] :.3f}"
                    disp_nspec_over_ne = f"{disp_nspec_over_ne} {nspec_over_ne : >12}"
                if species_data["nspec_over_nmaj"] < 1.0e-2:
                    nspec_over_nmaj = f"{species_data['nspec_over_nmaj'] :.2e}"
                    disp_nspec_over_nmaj = f"{disp_nspec_over_nmaj} {nspec_over_nmaj : >12}"
                else:
                    nspec_over_nmaj = f"{species_data['nspec_over_nmaj'] :.3f}"
                    disp_nspec_over_nmaj = f"{disp_nspec_over_nmaj} {nspec_over_nmaj : >12}"

        print(disp_species)
        print(disp_a)
        print(disp_z)
        print(disp_nspec_over_ntot)
        print(disp_nspec_over_ne)
        print(disp_nspec_over_nmaj)
        print("   ------------")

    def _print_specis_concentration(self, composition_data):
        for species_key, species_data in composition_data.items():
            states = species_data["states"]
            nstates = len(states)
            if nstates > 1:
                comm = "s"
            else:
                comm = ""
            if nstates != 0:
                print(
                    species_data["species"],
                    " has ",
                    nstates,
                    " state" + comm,
                )
            istate = 0
            for state_key, state_data in states.items():
                n_ni = f"{state_data['n_ni']:.6f}"
                label_space = 0
                if state_data["label"].strip() != "":
                    label_space = 7
                print(
                    f"\t {'state' + str(istate + 1) : <8}{state_data['label'].value: <{label_space}} z : "
                    f"{state_data['z_average']:.6f} n/ni, % :{n_ni : >12}"
                )
                istate += 1

    def view_electrons_density(self, ax, time_slice, show_separatrix=False):
        """
        The function `view_electrons_density` plots the electron density on the original GGD mesh
        using tripcolor (Gouraud shading) and adds a separatrix line.

        Args:
            ax: The parameter "ax" is an instance of the matplotlib Axes class. It represents the axes on
                which the electron density plot will be drawn.
            time_slice: The `time_slice` parameter represents the time slice at which the neutral density will be
                plotted. It is an optional parameter with a default value of 0. Defaults to 0

        Returns:
            the tripcolor object 'c'.
        """
        ne_values = self.edge_profiles_compute.get_electron_density_on_cells(time_slice)

        if ne_values is not None:
            polygons, cell_values = self.edge_profiles_compute.get_cell_polygons_and_values(time_slice, ne_values)
            if polygons is None or len(polygons) == 0:
                logger.warning("edge_profiles: no cell polygons available, cannot plot electron density")
                return None
            all_r = np.concatenate([v[:, 0] for v in polygons])
            all_z = np.concatenate([v[:, 1] for v in polygons])
            ax.grid(False)
            pc = PolyCollection(polygons, array=cell_values, cmap="coolwarm", linewidths=0)
            pc.set_clim(float(cell_values.min()), float(cell_values.max()))
            ax.add_collection(pc)
            ax.set_xlim(all_r.min(), all_r.max())
            ax.set_ylim(all_z.min(), all_z.max())
            core_boundry = self.edge_profiles_compute.get_core_boundry(time_slice)
            ax.fill(core_boundry[:, 0], core_boundry[:, 1], facecolor="w", edgecolor="none")
            if show_separatrix:
                separatrix = self.edge_profiles_compute.get_separatrix(time_slice)
                if separatrix is not None:
                    ax.scatter(separatrix[:, 0], separatrix[:, 1], color="#FF1493", marker="x", s=10)
            ax.set_aspect("equal", adjustable="box")
            ax.set_xlabel("R,m")
            ax.set_ylabel("Z,m")
            ax.set_title("Electron density")
            return pc
        else:
            xmin, xmax = ax.get_xlim()
            ymin, ymax = ax.get_ylim()
            ax.text(
                (xmax + xmin) / 2,
                (ymax + ymin) / 2,
                "No data",
                horizontalalignment="left",
                verticalalignment="center",
            )
            return None

    def view_ion_density(self, ax, time_slice, show_separatrix=False):
        """
        The function `view_ion_density` plots the ion density on the original GGD mesh
        using tripcolor (Gouraud shading) and adds a separatrix line.

        Args:
            ax: The parameter "ax" is an instance of the matplotlib Axes class. It represents the axes on
                which the ion density plot will be drawn.
            time_slice: The `time_slice` parameter represents the time slice at which the neutral density will
                be plotted. It is an optional parameter with a default value of 0. Defaults to 0

        Returns:
            the tripcolor object 'c'.
        """
        ni_values = self.edge_profiles_compute.get_ion_density_on_cells(time_slice)

        if ni_values is not None:
            polygons, cell_values = self.edge_profiles_compute.get_cell_polygons_and_values(time_slice, ni_values)
            all_r = np.concatenate([v[:, 0] for v in polygons])
            all_z = np.concatenate([v[:, 1] for v in polygons])
            ax.grid(False)
            pc = PolyCollection(polygons, array=cell_values, cmap="coolwarm", linewidths=0)
            pc.set_clim(float(cell_values.min()), float(cell_values.max()))
            ax.add_collection(pc)
            ax.set_xlim(all_r.min(), all_r.max())
            ax.set_ylim(all_z.min(), all_z.max())
            core_boundry = self.edge_profiles_compute.get_core_boundry(time_slice)
            ax.fill(core_boundry[:, 0], core_boundry[:, 1], facecolor="w", edgecolor="none")
            if show_separatrix:
                separatrix = self.edge_profiles_compute.get_separatrix(time_slice)
                if separatrix is not None:
                    ax.scatter(separatrix[:, 0], separatrix[:, 1], color="#FF1493", marker="x", s=10)
            ax.set_aspect("equal", adjustable="box")
            ax.set_xlabel("R,m")
            ax.set_ylabel("Z,m")
            ax.set_title("Ion density")
            return pc
        else:
            xmin, xmax = ax.get_xlim()
            ymin, ymax = ax.get_ylim()
            ax.text(
                (xmax + xmin) / 2,
                (ymax + ymin) / 2,
                "No data",
                horizontalalignment="left",
                verticalalignment="center",
            )
            return None

    def view_neutral_density(self, ax, time_slice, show_separatrix=False):
        """
        The function `view_neutral_density` plots the neutral density on the original GGD mesh
        using tripcolor (Gouraud shading) and adds a separatrix line.

        Args:
            ax: The parameter "ax" is an instance of the matplotlib Axes class. It represents the axes
                on  which the plot will be drawn.
            time_slice: The `time_slice` parameter represents the time slice at which the neutral density
                will be plotted. It is an optional parameter with a default value of 0. Defaults to 0

        Returns:
            the tripcolor object 'c'.
        """
        n_neutral_values = self.edge_profiles_compute.get_neutral_density_on_cells(time_slice)

        if n_neutral_values is not None:
            polygons, cell_values = self.edge_profiles_compute.get_cell_polygons_and_values(
                time_slice, n_neutral_values
            )
            all_r = np.concatenate([v[:, 0] for v in polygons])
            all_z = np.concatenate([v[:, 1] for v in polygons])
            ax.grid(False)
            pc = PolyCollection(polygons, array=cell_values, cmap="coolwarm", linewidths=0)
            pc.set_clim(float(cell_values.min()), float(cell_values.max()))
            ax.add_collection(pc)
            ax.set_xlim(all_r.min(), all_r.max())
            ax.set_ylim(all_z.min(), all_z.max())
            core_boundry = self.edge_profiles_compute.get_core_boundry(time_slice)
            ax.fill(core_boundry[:, 0], core_boundry[:, 1], facecolor="w", edgecolor="none")
            if show_separatrix:
                separatrix = self.edge_profiles_compute.get_separatrix(time_slice)
                if separatrix is not None:
                    ax.scatter(separatrix[:, 0], separatrix[:, 1], color="#FF1493", marker="x", s=10)
            ax.set_aspect("equal", adjustable="box")
            ax.set_xlabel("R,m")
            ax.set_ylabel("Z,m")
            ax.set_title("Neutral density")
            return pc
        else:
            xmin, xmax = ax.get_xlim()
            ymin, ymax = ax.get_ylim()
            ax.text(
                (xmax + xmin) / 2,
                (ymax + ymin) / 2,
                "No data",
                horizontalalignment="left",
                verticalalignment="center",
            )
            return None

    def view_equatorial_plane_and_diverter_density(self, ax, time_slice, logscale=True):
        OUTER_MIDPLANE_INDEX = 11
        OUTER_TARGET_INDEX = 13
        INNER_TARGET_INDEX = 14

        any_data = False

        for subset_idx, label in (
            (OUTER_MIDPLANE_INDEX, "Outer midplane"),
            (OUTER_TARGET_INDEX, "Outer divertor target"),
            (INNER_TARGET_INDEX, "Inner divertor target"),
        ):
            r_t, z_t, ne_t = self.edge_profiles_compute.get_rz_and_ne_on_subset(time_slice, subset_idx)
            if r_t is None or len(r_t) == 0:
                continue
            # Arc-length as x-axis
            coords = np.column_stack([r_t, z_t])
            seg_len = np.sqrt(np.sum(np.diff(coords, axis=0) ** 2, axis=1))
            arc = np.concatenate([[0.0], np.cumsum(seg_len)])
            ax.plot(arc, ne_t, label=label)
            any_data = True

        if any_data:
            if logscale:
                ax.set_yscale("log")
            ax.set_title("Electron density")
            ax.set_xlabel("Distance along profile (m)")
            ax.set_ylabel("n$_e$ (m$^{-3}$)")
            ax.legend()
        else:
            xmin, xmax = ax.get_xlim()
            ymin, ymax = ax.get_ylim()
            ax.text(
                (xmax + xmin) / 2,
                (ymax + ymin) / 2,
                "No data",
                horizontalalignment="left",
                verticalalignment="center",
            )
            return None

    def show_info_on_plot(self, ax, info: str = ""):
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        left, width = xmin, xmax - xmin
        bottom, height = ymin, ymax - ymin
        right = left + width
        top = bottom + height
        ax.text(
            right,
            top,
            info,
            horizontalalignment="right",
            verticalalignment="bottom",
            fontsize=5,
        )
