from os.path import join, dirname, abspath

import pandas as pd

import pypsa

from src.data.geographics.manager import _get_country
from src.data.generation.manager import get_gen_from_ppm, find_associated_buses_ehighway
from src.tech_parameters.costs import get_cost

# TODO: this should not depend on e-highway
def add_generators(network: pypsa.Network, use_ex_cap: bool, extendable: bool,
                   ramp_rate: float, ppm_file_name: str = None) -> pypsa.Network:
    """Adds nuclear generators to a PyPsa Network instance.

    Parameters
    ----------
    network: pypsa.Network
        A Network instance with nodes associated to regions.
    use_ex_cap: bool
        Whether to consider existing capacity or not #  TODO: will probably remove that at some point
    extendable: bool
        Whether generators are extendable
    ramp_rate: float
        Percentage of the total capacity for which the generation can be increased or decreased between two time-steps
    ppm_file_name: str
        Name of the file from which to retrieve the data if value is not None

    Returns
    -------
    network: pypsa.Network
        Updated network
    """

    # TODO: add the possibility to remove some plants and allow it to built where it doesn't exist

    # Load existing nuclear plants
    if ppm_file_name is not None:
        ppm_folder = join(dirname(abspath(__file__)), "../../data/ppm/")
        gens = pd.read_csv(ppm_folder + "/" + ppm_file_name, index_col=0, delimiter=";")
        gens["Country"] = gens["Country"].apply(lambda c: _get_country('alpha_2', name=c))
    else:
        gens = get_gen_from_ppm(fuel_type="Nuclear")

    gens = find_associated_buses_ehighway(gens, network)

    if not use_ex_cap:
        gens.Capacity = 0.

    capital_cost, marginal_cost = get_cost('nuclear', len(network.snapshots))

    network.madd("Generator", "Gen nuclear " + gens.Name + " " + gens.bus_id,
                 bus=gens.bus_id.values,
                 p_nom=gens.Capacity.values,
                 p_nom_min=gens.Capacity.values,
                 p_nom_extendable=extendable,
                 type='nuclear',
                 carrier='nuclear',
                 marginal_cost=marginal_cost,
                 capital_cost=capital_cost,
                 ramp_limit_up=ramp_rate,
                 ramp_limit_down=ramp_rate,
                 x=gens.lon.values,
                 y=gens.lat.values)

    return network
