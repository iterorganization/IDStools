import logging
import re

from idstools.utils.clihelper import (
    get_database_path,
)
from idstools.utils.idslogger import setup_logger
from idstools.view.magnetics import MagneticsView
from idstools.view.pf_active import PFActiveView
from idstools.view.pf_passive import PFPassiveView
from idstools.view.tf import TFView
from idstools.view.wall import WallView

logger = setup_logger("module", stdout_level=logging.INFO)


def update_labels(ax):
    """Show labels only when zoomed in for all subplots based on zoom width & height."""
    # Iterate over all axes in the figure
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    visible_texts = [
        text
        for text in ax.texts
        if xlim[0] <= text.get_position()[0] <= xlim[1] and ylim[0] <= text.get_position()[1] <= ylim[1]
    ]
    max_visible_texts = 100
    show_labels = len(visible_texts) < max_visible_texts

    for text in ax.texts:
        text.set_visible(False)

        if show_labels and text in visible_texts:
            text.set_visible(True)
    ax.figure.canvas.draw_idle()


def plot_machine_description(ax, ids_data, main_uri=None):
    """
    The `plotMachineDescription` method is responsible for plotting the machine description
    based on the provided pulse list.

    Args:
        main_uri: If provided, machine description entries with the same URI are omitted
                  from the provenance text (to avoid duplication when MD and main data share a URI).
    """

    provenance_groups = {}

    def _add_provenance(ids_name_label, connection_args):
        """Group subsystem labels that originate from the same data-entry URI."""
        uri = get_database_path(connection_args).strip()
        if main_uri is not None and uri == main_uri.strip():
            return
        labels = provenance_groups.setdefault(uri, [])
        if ids_name_label not in labels:
            labels.append(ids_name_label)

    mdlegends = []
    mdlabels = []
    for idsinfo, ids_data_and_config in ids_data.items():
        # if idsDataAndConfig["yamlConfig"] is None:
        #     logger.error(f"Could not retrieve machine description for {idsName}")
        #     databasePath += f"{idsName} = not found"
        #     continue
        ids_name = ids_data_and_config["idsname"]

        idsfield = ids_data_and_config["idsfield"] or ""
        idsocc = ids_data_and_config["idsocc"]

        logger.debug(f"Started to process {ids_name} ids for plotting {idsinfo}")

        matches = re.findall(r"[\[(]([^\])]+)[\])]", idsfield)
        select = ":"
        if len(matches) > 0:
            select = matches[0]
        if ids_name == "pf_active":
            pfcoilsview = PFActiveView(ids_data_and_config["idsData"])
            if "coil" in idsfield or idsfield == "":
                _legend = pfcoilsview.view_active_pf_coils(ax, select=select)
                if _legend:
                    mdlegends.append(_legend)
                    mdlabels.append(f"pf_active:{idsocc}/coil[{select}]")
                    _add_provenance("pf_active", ids_data_and_config["connectionArgs"])
        elif ids_name == "tf":
            select2 = ":"
            if len(matches) == 2:
                select2 = matches[1]
            tfview = TFView(ids_data_and_config["idsData"])
            if "coil" in idsfield or idsfield == "":
                _legend = tfview.view_tf_coils(ax, select_coil=select, select_conductor=select2)
                if _legend:
                    mdlegends.append(_legend)
                    mdlabels.append(f"tf:{idsocc}/coil[{select}]/conductor[{select2}]")
                    _add_provenance("tf", ids_data_and_config["connectionArgs"])
        elif ids_name == "pf_passive":
            pfpassiveview = PFPassiveView(ids_data_and_config["idsData"])
            if "loop" in idsfield or idsfield == "":
                _legend = pfpassiveview.view_pf_passive_loops(ax, select=select)
                if _legend:
                    mdlegends.append(_legend)

                    mdlabels.append(f"pf_passive:{idsocc}/loop[{select}]")
                    _add_provenance("pf_passive", ids_data_and_config["connectionArgs"])
        elif ids_name == "wall":
            wallview = WallView(ids_data_and_config["idsData"])
            select2 = ":"
            if len(matches) == 2:
                select2 = matches[1]
            if "vessel" in idsfield:
                wallview.view_wall_vessel(ax, select_description2d=select, select_unit=select2)
            if "limiter" in idsfield or idsfield == "":
                wallview.view_wall_limiter(ax, select_description2d=select, select_unit=select2)
            _add_provenance("wall", ids_data_and_config["connectionArgs"])
        elif ids_name == "magnetics":
            magnetics_view = MagneticsView(ids_data_and_config["idsData"])
            if "b_field_phi_probe" in idsfield or idsfield == "":
                _legend = magnetics_view.view_b_field_probes(ax, probe_type="b_field_phi_probe", select=select)
                if _legend:
                    mdlegends.append(_legend)
                    mdlabels.append(f"magnetics:{idsocc}/b_field_phi_probe[{select}]")
            if "b_field_pol_probe" in idsfield or idsfield == "":
                _legend = magnetics_view.view_b_field_probes(ax, probe_type="b_field_pol_probe", select=select)
                if _legend:
                    mdlegends.append(_legend)
                    mdlabels.append(f"magnetics:{idsocc}/b_field_pol_probe[{select}]")
            if "flux_loop" in idsfield or idsfield == "":
                _legend = magnetics_view.view_flux_loop(ax, select=select)
                if _legend:
                    mdlegends.append(_legend)
                    mdlabels.append(f"magnetics:{idsocc}/flux_loop[{select}]")
            if "rogowski_coil" in idsfield or idsfield == "":
                _legend = magnetics_view.view_rogowski_coil(ax, select=select)
                if _legend:
                    mdlegends.append(_legend)
                    mdlabels.append(f"magnetics:{idsocc}/rogowski_coil[{select}]")
            if "shunt" in idsfield or idsfield == "":
                _legend = magnetics_view.view_shunt(ax, select=select)
                if _legend:
                    mdlegends.append(_legend)
                    mdlabels.append(f"magnetics:{idsocc}/shunt[{select}]")
            _add_provenance("magnetics", ids_data_and_config["connectionArgs"])
        else:
            _add_provenance(f"{ids_name} (No visualization yet)", ids_data_and_config["connectionArgs"])
            logger.info(f"Visualization is not implemented yet for machine description {ids_name}")

    handles, labels = ax.get_legend_handles_labels()
    handles.extend(mdlegends)
    labels.extend(mdlabels)
    if labels:
        legend = ax.legend(handles=handles, labels=labels, loc="upper left", bbox_to_anchor=(1.15, 1), fancybox=True)
        for legline in legend.get_lines():
            legline.set_picker(8 * 0.5)
        for text in legend.get_texts():
            text.set_picker(True)
        for patch in legend.get_patches():
            patch.set_picker(True)
    ax.set_aspect("equal", adjustable="box")
    # ax.callbacks.connect("xlim_changed", update_labels)
    # ax.callbacks.connect("ylim_changed", update_labels)
    ax.plot()

    return " | ".join(f"{', '.join(labels)} = {uri}" for uri, labels in provenance_groups.items())
