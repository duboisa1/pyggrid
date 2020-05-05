from os.path import join, dirname, abspath
from typing import Tuple

import pandas as pd

NHoursPerYear = 8760.0


# TODO: This function allows to do the conversion to David's file until we homogenize techs
def get_plant_type(tech: str) -> Tuple[str, str]:

    if tech == "ccgt":
        return "NGPP", "CCGT"
    elif tech == "ocgt":
        return "NGPP", "OCGT"
    elif tech == "nuclear":
        return "Nuclear", "Uranium"
    elif tech == "sto":
        return "Hydro", "Reservoir"
    elif tech == "ror":
        return "Hydro", "Run-of-river"
    elif tech == "phs":
        return "Storage", "Pumped-hydro"
    elif tech == "Li-ion":
        return "Storage", "Li-ion"
    elif tech == "wind_onshore":
        return "Wind", "Onshore"
    elif tech == "wind_offshore":
        return "Wind", "Offshore"
    elif tech == "wind_floating":
        return "Wind", "Floating"
    elif tech == "pv_utility":
        return "PV", "Utility"
    elif tech == "pv_residential":
        return "PV", "Residential"
    # TODO: For now consider overhead lines for HVAC and undersea cables for HVDC
    #  Would need to do sht much more clever
    elif tech == "AC":
        return "Transmission", "HVAC_OHL"
    elif tech == "DC":
        return "Transmission", "HVDC_SC"


def get_cost(tech: str, nb_hours: float) -> Tuple[float, float]:
    """
    Return capital and marginal cost for a given generation technology.

    Parameters
    ----------
    tech: str
        Name of a technology
    nb_hours: float
        Number of hours over which the investment costs will be used

    Returns
    -------
    Capital cost (M€/GWel or M€/GWel/km) and marginal cost (M€/GWhel)

    """
    tech_info_fn = join(dirname(abspath(__file__)), "../../../data/technologies/tech_info.xlsx")
    tech_info = pd.read_excel(tech_info_fn, sheet_name='values', index_col=[0, 1])

    plant, plant_type = get_plant_type(tech)
    # assert tech in tech_info.index, f"Error: Cost for {tech} is not computable yet."
    tech_info = tech_info.loc[plant, plant_type]

    # Capital cost is the sum of investment and FOM
    capital_cost = (tech_info["FOM"] + tech_info["CAPEX"]/tech_info["lifetime"]) * nb_hours/NHoursPerYear

    fuel_info_fn = join(dirname(abspath(__file__)), "../../../data/technologies/fuel_info.xlsx")
    fuel_info = pd.read_excel(fuel_info_fn, sheet_name='values', index_col=0)

    # Marginal cost is the sum of VOM, fuel cost and CO2 cost
    if tech in ['AC', 'DC']:
        marginal_cost = 0
    else:
        marginal_cost = tech_info['VOM']
        fuel = tech_info['fuel']
        if not pd.isna(fuel):
            # Add fuel cost
            marginal_cost += fuel_info.loc[fuel, 'cost'] / tech_info['efficiency_ds']
            # Add CO2 cost
            marginal_cost += fuel_info.loc['CO2', 'cost'] * fuel_info.loc[fuel, 'CO2'] / tech_info["efficiency_ds"]

    return round(capital_cost, 6), round(marginal_cost, 6)


if __name__ == "__main__":
    techs = ["ccgt", "ocgt", "nuclear", "sto", "ror", "phs", "wind_onshore", "wind_offshore", "wind_floating",
             "pv_utility", "pv_residential", "Li-ion", "AC", "DC"]
    for tech_ in techs:
        print(tech_)
        print(get_cost(tech_, 24))
