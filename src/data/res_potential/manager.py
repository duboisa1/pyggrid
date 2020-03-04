from os.path import join, dirname, abspath
from typing import *

import numpy as np
import pandas as pd
import xarray as xr

from shapely.ops import cascaded_union

from src.data.geographics.manager import nuts3_to_nuts2, get_nuts_area, get_onshore_shapes, get_offshore_shapes, \
    match_points_to_region, get_subregions
from src.data.topologies.ehighway import get_ehighway_clusters


missing_region_dict = {
    "NO": ["SE"],
    "CH": ["AT"],
    "BA": ["HR"],
    "ME": ["HR"],
    "RS": ["BG"],
    "AL": ["BG"],
    "MK": ["BG"]
}

# TODO: ask david
#  - need to change this - use what I have done in my code or try at least
def update_potential_files(input_ds: pd.DataFrame, tech: str) -> pd.DataFrame:
    """
    Updates NUTS2 potentials with i) non-EU data and ii) re-indexed (2013 vs 2016) NUTS2 regions.

    Parameters
    ----------
    input_ds: pd.DataFrame
    tech : str

    Returns
    -------
    input_ds : pd.DataFrame
    """

    if tech in ['wind_onshore', 'pv_residential', 'pv_utility']:

        dict_regions_update = {'FR21': 'FRF2', 'FR22': 'FRE2', 'FR23': 'FRD1', 'FR24': 'FRB0', 'FR25': 'FRD2',
                               'FR26': 'FRC1', 'FR30': 'FRE1', 'FR41': 'FRF3', 'FR42': 'FRF1', 'FR43': 'FRC2',
                               'FR51': 'FRG0', 'FR52': 'FRH0', 'FR53': 'FRI3', 'FR61': 'FRI1', 'FR62': 'FRJ2',
                               'FR63': 'FRI2', 'FR71': 'FRK2', 'FR72': 'FRK1', 'FR81': 'FRJ1', 'FR82': 'FRL0',
                               'FR83': 'FRM0', 'PL11': 'PL71', 'PL12': 'PL9', 'PL31': 'PL81', 'PL32': 'PL82',
                               'PL33': 'PL72', 'PL34': 'PL84', 'UKM2': 'UKM7'}

        new_index = [dict_regions_update[x] if x in dict_regions_update else x for x in input_ds.index]
        input_ds.index = new_index

    if tech == 'wind_onshore':

        input_ds.loc['AL01'] = 2.
        input_ds.loc['AL02'] = 2.
        input_ds.loc['AL03'] = 2.
        input_ds.loc['BA'] = 3.
        input_ds.loc['ME00'] = 3.
        input_ds.loc['MK00'] = 5.
        input_ds.loc['RS11'] = 0.
        input_ds.loc['RS12'] = 10.
        input_ds.loc['RS21'] = 10.
        input_ds.loc['RS22'] = 10.
        input_ds.loc['CH01'] = 1.
        input_ds.loc['CH02'] = 1.
        input_ds.loc['CH03'] = 1.
        input_ds.loc['CH04'] = 1.
        input_ds.loc['CH05'] = 1.
        input_ds.loc['CH06'] = 1.
        input_ds.loc['CH07'] = 1.
        input_ds.loc['NO01'] = 3.
        input_ds.loc['NO02'] = 3.
        input_ds.loc['NO03'] = 3.
        input_ds.loc['NO04'] = 3.
        input_ds.loc['NO05'] = 3.
        input_ds.loc['NO06'] = 3.
        input_ds.loc['NO07'] = 3.
        input_ds.loc['IE04'] = input_ds.loc['IE01']
        input_ds.loc['IE05'] = input_ds.loc['IE02']
        input_ds.loc['IE06'] = input_ds.loc['IE02']
        input_ds.loc['LT01'] = input_ds.loc['LT00']
        input_ds.loc['LT02'] = input_ds.loc['LT00']
        input_ds.loc['UKM8'] = input_ds.loc['UKM3']
        input_ds.loc['UKM9'] = input_ds.loc['UKM3']
        input_ds.loc['PL92'] = input_ds.loc['PL9']
        input_ds.loc['PL91'] = 0.
        input_ds.loc['HU11'] = 0.
        input_ds.loc['HU12'] = input_ds.loc['HU10']
        input_ds.loc['UKI5'] = 0.
        input_ds.loc['UKI6'] = 0.
        input_ds.loc['UKI7'] = 0.

    elif tech == 'wind_offshore':

        input_ds.loc['EZAL'] = 2.
        input_ds.loc['EZBA'] = 0.
        input_ds.loc['EZME'] = 0.
        input_ds.loc['EZMK'] = 0.
        input_ds.loc['EZRS'] = 0.
        input_ds.loc['EZCH'] = 0.
        input_ds.loc['EZNO'] = 20.
        input_ds.loc['EZIE'] = 20.
        input_ds.loc['EZEL'] = input_ds.loc['EZGR']

    elif tech == 'wind_floating':

        input_ds.loc['EZAL'] = 2.
        input_ds.loc['EZBA'] = 0.
        input_ds.loc['EZME'] = 0.
        input_ds.loc['EZMK'] = 0.
        input_ds.loc['EZRS'] = 0.
        input_ds.loc['EZCH'] = 0.
        input_ds.loc['EZNO'] = 100.
        input_ds.loc['EZIE'] = 120.
        input_ds.loc['EZEL'] = input_ds.loc['EZGR']

    elif tech == 'pv_residential':

        input_ds.loc['AL01'] = 1.
        input_ds.loc['AL02'] = 1.
        input_ds.loc['AL03'] = 1.
        input_ds.loc['BA'] = 3.
        input_ds.loc['ME00'] = 1.
        input_ds.loc['MK00'] = 1.
        input_ds.loc['RS11'] = 5.
        input_ds.loc['RS12'] = 2.
        input_ds.loc['RS21'] = 2.
        input_ds.loc['RS22'] = 2.
        input_ds.loc['CH01'] = 6.
        input_ds.loc['CH02'] = 6.
        input_ds.loc['CH03'] = 6.
        input_ds.loc['CH04'] = 6.
        input_ds.loc['CH05'] = 6.
        input_ds.loc['CH06'] = 6.
        input_ds.loc['CH07'] = 6.
        input_ds.loc['NO01'] = 3.
        input_ds.loc['NO02'] = 0.
        input_ds.loc['NO03'] = 3.
        input_ds.loc['NO04'] = 3.
        input_ds.loc['NO05'] = 0.
        input_ds.loc['NO06'] = 0.
        input_ds.loc['NO07'] = 0.
        input_ds.loc['IE04'] = input_ds.loc['IE01']
        input_ds.loc['IE05'] = input_ds.loc['IE02']
        input_ds.loc['IE06'] = input_ds.loc['IE02']
        input_ds.loc['LT01'] = input_ds.loc['LT00']
        input_ds.loc['LT02'] = input_ds.loc['LT00']
        input_ds.loc['UKM8'] = input_ds.loc['UKM3']
        input_ds.loc['UKM9'] = input_ds.loc['UKM3']
        input_ds.loc['PL92'] = input_ds.loc['PL9']
        input_ds.loc['PL91'] = 5.
        input_ds.loc['HU11'] = input_ds.loc['HU10']
        input_ds.loc['HU12'] = input_ds.loc['HU10']
        input_ds.loc['UKI5'] = 1.
        input_ds.loc['UKI6'] = 1.
        input_ds.loc['UKI7'] = 1.

    elif tech == 'pv_utility':

        input_ds.loc['AL01'] = 1.
        input_ds.loc['AL02'] = 1.
        input_ds.loc['AL03'] = 1.
        input_ds.loc['BA'] = 3.
        input_ds.loc['ME00'] = 1.
        input_ds.loc['MK00'] = 1.
        input_ds.loc['RS11'] = 0.
        input_ds.loc['RS12'] = 2.
        input_ds.loc['RS21'] = 2.
        input_ds.loc['RS22'] = 1.
        input_ds.loc['CH01'] = 6.
        input_ds.loc['CH02'] = 6.
        input_ds.loc['CH03'] = 6.
        input_ds.loc['CH04'] = 6.
        input_ds.loc['CH05'] = 6.
        input_ds.loc['CH06'] = 6.
        input_ds.loc['CH07'] = 6.
        input_ds.loc['NO01'] = 3.
        input_ds.loc['NO02'] = 0.
        input_ds.loc['NO03'] = 3.
        input_ds.loc['NO04'] = 3.
        input_ds.loc['NO05'] = 0.
        input_ds.loc['NO06'] = 0.
        input_ds.loc['NO07'] = 0.
        input_ds.loc['IE04'] = input_ds.loc['IE01']
        input_ds.loc['IE05'] = input_ds.loc['IE02']
        input_ds.loc['IE06'] = input_ds.loc['IE02']
        input_ds.loc['LT01'] = input_ds.loc['LT00']
        input_ds.loc['LT02'] = input_ds.loc['LT00']
        input_ds.loc['UKM8'] = input_ds.loc['UKM3']
        input_ds.loc['UKM9'] = input_ds.loc['UKM3']
        input_ds.loc['PL92'] = input_ds.loc['PL9']
        input_ds.loc['PL91'] = 2.
        input_ds.loc['HU11'] = 0.
        input_ds.loc['HU12'] = 2.
        input_ds.loc['UKI5'] = 0.
        input_ds.loc['UKI6'] = 0.
        input_ds.loc['UKI7'] = 0.

    regions_to_remove = ['AD00', 'SM00', 'CY00', 'LI00', 'FRY1', 'FRY2', 'FRY3', 'FRY4', 'FRY5', 'ES63', 'ES64', 'ES70',
                         'HU10', 'IE01', 'IE02', 'LT00', 'UKM3']

    input_ds = input_ds.drop(regions_to_remove, errors='ignore')

    return input_ds


# TODO:
#  - merge with my code
#  - Need at least to add as argument a list of codes for which we want the capacity
def capacity_potential_from_enspresso(tech: str) -> pd.DataFrame:
    """
    Returning capacity potential per NUTS2 region for a given tech, based on the ENSPRESSO dataset.

    Parameters
    ----------
    tech : str
        Technology name among 'wind_onshore', 'wind_offshore', 'wind_floating', 'pv_utility' and 'pv_residential'

    Returns
    -------
    nuts2_capacity_potentials: pd.DataFrame
        Dict storing technical potential per NUTS2 region.
    """
    accepted_techs = ['wind_onshore', 'wind_offshore', 'wind_floating', 'pv_utility', 'pv_residential']
    assert tech in accepted_techs, "Error: tech {} is not in {}".format(tech, accepted_techs)

    path_potential_data = join(dirname(abspath(__file__)), '../../../data/res_potential/source/ENSPRESO')
    if tech == 'wind_onshore':

        cap_potential_file = pd.read_excel(join(path_potential_data, 'ENSPRESO_WIND_ONSHORE_OFFSHORE.XLSX'),
                                           sheet_name='Wind Potential EU28 Full', index_col=1)

        onshore_wind = cap_potential_file[
            (cap_potential_file['Unit'] == 'GWe') &
            (cap_potential_file['Onshore Offshore'] == 'Onshore') &
            (cap_potential_file['Scenario'] == 'EU-Wide high restrictions')]

        nuts2_capacity_potentials_ds = onshore_wind.groupby(onshore_wind.index)['Value'].sum()

    elif tech == 'wind_offshore':

        offshore_categories = ['12nm zone, water depth 0-30m', '12nm zone, water depth 30-60m',
                               '12nm zone, water depth 60-100m Floating', 'Water depth 0-30m',
                               'Water depth 30-60m', 'Water depth 60-100m Floating']

        cap_potential_file = pd.read_excel(join(path_potential_data, 'ENSPRESO_WIND_ONSHORE_OFFSHORE.XLSX'),
                                           sheet_name='Wind Potential EU28 Full', index_col=1)

        offshore_wind = cap_potential_file[
            (cap_potential_file['Unit'] == 'GWe') &
            (cap_potential_file['Onshore Offshore'] == 'Offshore') &
            (cap_potential_file['Scenario'] == 'EU-Wide low restrictions') &
            (cap_potential_file['Offshore categories'].isin(offshore_categories))]
        nuts2_capacity_potentials_ds = offshore_wind.groupby(offshore_wind.index)['Value'].sum()

    elif tech == 'wind_floating':

        cap_potential_file = pd.read_excel(join(path_potential_data, 'ENSPRESO_WIND_ONSHORE_OFFSHORE.XLSX'),
                                           sheet_name='Wind Potential EU28 Full', index_col=1)

        offshore_wind = cap_potential_file[
            (cap_potential_file['Unit'] == 'GWe') &
            (cap_potential_file['Onshore Offshore'] == 'Offshore') &
            (cap_potential_file['Scenario'] == 'EU-Wide low restrictions') &
            (cap_potential_file['Wind condition'] == 'CF > 25%') &
            (cap_potential_file['Offshore categories'] == 'Water depth 100-1000m Floating')]
        nuts2_capacity_potentials_ds = offshore_wind.groupby(offshore_wind.index)['Value'].sum()

    elif tech == 'pv_utility':

        cap_potential_file = pd.read_excel(join(path_potential_data, 'ENSPRESO_SOLAR_PV_CSP.XLSX'),
                                           sheet_name='NUTS2 170 W per m2 and 3%', skiprows=2, index_col=2)
        nuts2_capacity_potentials_ds = cap_potential_file['PV - ground']

    elif tech == 'pv_residential':

        cap_potential_file = pd.read_excel(join(path_potential_data, 'ENSPRESO_SOLAR_PV_CSP.XLSX'),
                                           sheet_name='NUTS2 170 W per m2 and 3%', skiprows=2, index_col=2)
        nuts2_capacity_potentials_ds = cap_potential_file['PV - roof/facades']

    # TODO: need to update this function
    return update_potential_files(nuts2_capacity_potentials_ds, tech)


def get_capacity_potential(tech_points_dict: Dict[str, List[Tuple[float, float]]], spatial_resolution: float,
                           regions: List[str], existing_capacity_ds: pd.Series = None) -> pd.Series:
    """
    Computes the capacity that can potentially be deployed at

    Parameters
    ----------
    tech_points_dict : Dict[str, Dict[str, List[Tuple[float, float]]]
        Dictionary associating to each tech a list of points.
    spatial_resolution : float
        Spatial resolution of the points.
    regions: List[str]
        Codes of geographical regions in which the points are situated
    existing_capacity_ds: pd.Series (default: None)
        Data series given for each tuple of (tech, point) the existing capacity.

    Returns
    -------
    capacity_potential_df : pd.Series
        TODO comment
    """

    accepted_techs = ['wind_onshore', 'wind_offshore', 'wind_floating', 'pv_utility', 'pv_residential']
    for tech in tech_points_dict.keys():
        assert tech in accepted_techs, "Error: tech {} is not in {}".format(tech, accepted_techs)

    # Load population density dataset
    path_pop_data = join(dirname(abspath(__file__)), '../../../data/population_density')
    dataset_population = \
        xr.open_dataset(join(path_pop_data, 'gpw_v4_population_density_rev11_' + str(spatial_resolution) + '.nc'))
    # Rename the only variable to data # TODO: is there not a cleaner way to do this?
    varname = [item for item in dataset_population.data_vars][0]
    dataset_population = dataset_population.rename({varname: 'data'})
    # The value of 5 for "raster" fetches data for the latest estimate available in the dataset, that is, 2020.
    data_pop = dataset_population.sel(raster=5)

    # Compute population density at intermediate points
    array_pop_density = data_pop['data'].interp(longitude=np.arange(-180, 180, float(spatial_resolution)),
                                                latitude=np.arange(-89, 91, float(spatial_resolution))[::-1],
                                                method='linear').fillna(0.)
    array_pop_density = array_pop_density.stack(locations=('longitude', 'latitude'))

    # TOD0: should maybe be passed as argument directly
    subregions = []
    for region in regions:
        subregions += get_subregions(region)

    tech_coords_tuples = [(tech, point) for tech, points in tech_points_dict.items() for point in points]
    capacity_potential_ds = pd.Series(0., index=pd.MultiIndex.from_tuples(tech_coords_tuples))

    for tech in tech_points_dict.keys():

        # Get coordinates for which we want capacity
        coords = tech_points_dict[tech]

        # Compute potential for each NUTS2 or EEZ
        potential_per_subregion_df = capacity_potential_from_enspresso(tech)

        # Get NUTS2 and EEZ shapes
        # TODO: this is shit -> not generic enough, expl: would probably not work for us states
        #  would need to get this out of the loop
        if tech in ['wind_offshore', 'wind_floating']:
            onshore_shapes_union = \
                cascaded_union(get_onshore_shapes(subregions, filterremote=True,
                                                  save_file_name=''.join(sorted(subregions))
                                                                 + "_subregions_on.geojson")["geometry"].values)
            filter_shape_data = get_offshore_shapes(subregions, onshore_shape=onshore_shapes_union,
                                                    filterremote=True,
                                                    save_file_name=''.join(sorted(subregions))
                                                                   + "_subregions_off.geojson")
            filter_shape_data.index = ["EZ" + code if code != 'GB' else 'EZUK' for code in filter_shape_data.index]
        else:
            codes = [code for code in potential_per_subregion_df.index if code[:2] in subregions]
            filter_shape_data = get_onshore_shapes(codes, filterremote=True,
                                                   save_file_name=''.join(sorted(subregions)) + "_nuts2_on.geojson")

        # Find the geographical region code associated to each coordinate
        coords_to_subregions_ds = match_points_to_region(coords, filter_shape_data["geometry"])
        # TODO: might be cleaner to use a pd.series
        coords_to_subregions_df = pd.DataFrame(coords_to_subregions_ds.values, coords_to_subregions_ds.index,
                                               columns=["subregion"])

        if tech in ['wind_offshore', 'wind_floating']:

            # For offshore sites, divide the total potential of the region by the number of coordinates
            # associated to that region
            # TODO: change variable names
            region_freq_ds = coords_to_subregions_df.groupby(['subregion'])['subregion'].count()
            region_freq_df = pd.DataFrame(region_freq_ds.values, index=region_freq_ds.index, columns=['freq'])
            region_freq_df["cap_pot"] = potential_per_subregion_df[region_freq_df.index]
            coords_to_subregions_df = \
                coords_to_subregions_df.merge(region_freq_df,
                                              left_on='subregion', right_on='subregion', right_index=True)
            capacity_potential = coords_to_subregions_df["cap_pot"]/coords_to_subregions_df["freq"]
            capacity_potential_ds.loc[tech, capacity_potential.index] = capacity_potential.values

        elif tech in ['wind_onshore', 'pv_utility', 'pv_residential']:

            # TODO: change variable names
            coords_to_subregions_df['pop_dens'] = \
                 np.clip(array_pop_density.sel(locations=coords).values, a_min=1., a_max=None)
            if tech in ['wind_onshore', 'pv_utility']:
                coords_to_subregions_df['pop_dens'] = 1./coords_to_subregions_df['pop_dens']
            coords_to_subregions_df_sum = coords_to_subregions_df.groupby(['subregion']).sum()
            coords_to_subregions_df_sum["cap_pot"] = potential_per_subregion_df[coords_to_subregions_df_sum.index]
            coords_to_subregions_df_sum.columns = ['sum_per_subregion', 'cap_pot']
            coords_to_subregions_df_merge = \
                coords_to_subregions_df.merge(coords_to_subregions_df_sum,
                                              left_on='subregion', right_on='subregion', right_index=True)

            capacity_potential_per_coord = coords_to_subregions_df_merge['pop_dens'] * \
                coords_to_subregions_df_merge['cap_pot']/coords_to_subregions_df_merge['sum_per_subregion']
            capacity_potential_ds.loc[tech, capacity_potential_per_coord.index] = capacity_potential_per_coord.values

    # Update capacity potential with existing potential if present
    if existing_capacity_ds is not None:
        underestimated_capacity = existing_capacity_ds > capacity_potential_ds
        capacity_potential_ds[underestimated_capacity] = existing_capacity_ds[underestimated_capacity]

    return capacity_potential_ds


# TODO: need to add offshore potential computation
# TODO: improve based on similar function in generation.manager
def get_potential_ehighway(bus_ids: List[str], carrier: str) -> pd.DataFrame:
    """
    Returns the RES potential in GW/km2 for e-highway clusters

    Parameters
    ----------
    bus_ids: List[str]
        E-highway clusters identifier (used as bus_ids in the network)
    carrier: str
        wind or pv

    Returns
    -------
    total_capacities: pd.DataFrame indexed by bus_ids

    """
    # Get capacities
    data_dir = join(dirname(abspath(__file__)), "../../../data/res_potential/source/ENSPRESO/")
    capacities = []
    if carrier == "pv":
        unit = "GWe"
        capacities = pd.read_excel(join(data_dir, "ENSPRESO_SOLAR_PV_CSP.XLSX"),
                                   sheet_name="NUTS2 170 W per m2 and 3%",
                                   usecols="C,H", header=2)
        capacities.columns = ["code", "capacity"]
        capacities["unit"] = pd.Series([unit]*len(capacities.index))

    elif carrier == "wind":
        unit = "GWe"
        # TODO: Need to pay attention to this scenario thing
        scenario = "Reference - Large turbines"
        # cap_factor = "20%  < CF < 25%"  # TODO: not to sure what to do with this
        capacities = pd.read_excel(join(data_dir, "ENSPRESO_WIND_ONSHORE_OFFSHORE.XLSX"),
                                   sheet_name="Wind Potential EU28 Full",
                                   usecols="B,F,G,I,J")
        capacities.columns = ["code", "scenario", "cap_factor", "unit", "capacity"]
        capacities = capacities[capacities.scenario == scenario]
        capacities = capacities[capacities.unit == unit]
        # capacity = capacity[capacity.cap_factor == cap_factor]
        capacities = capacities.groupby(["code", "unit"], as_index=False).agg('sum')
    else:
        # TODO: this is shitty
        print("This carrier is not supported")

    # Transforming capacities to capacities per km2
    area = get_nuts_area()
    area.index.name = 'code'

    nuts2_conversion_fn = join(dirname(abspath(__file__)),
                               "../../../data/geographics/source/eurostat/NUTS2-conversion.csv")
    nuts2_conversion = pd.read_csv(nuts2_conversion_fn, index_col=0)

    # Convert index to new nuts2
    for old_code in nuts2_conversion.index:
        old_capacity = capacities[capacities.code == old_code]
        old_area = area.loc[old_code]["2013"]
        for new_code in nuts2_conversion.loc[old_code]["Code 2016"].split(";"):
            new_area = area.loc[new_code]["2016"]
            new_capacity = old_capacity.copy()
            new_capacity.code = new_code
            new_capacity.capacity = old_capacity.capacity*new_area/old_area
            capacities = capacities.append(new_capacity, ignore_index=True)
        capacities = capacities.drop(capacities[capacities.code == old_code].index)

    # The areas are in square kilometre so we obtain GW/km2
    def to_cap_per_area(x):
        return x["capacity"]/area.loc[x["code"]]["2016"] if x["code"] in area.index else None
    capacities["capacity"] = capacities[["code", "capacity"]].apply(lambda x: to_cap_per_area(x), axis=1)
    capacities = capacities.set_index("code")

    # Get codes of NUTS3 regions and countries composing the cluster
    eh_clusters = get_ehighway_clusters()

    total_capacities = np.zeros(len(bus_ids))
    for i, bus_id in enumerate(bus_ids):

        # TODO: would probably need to do sth more clever
        #  --> just setting capacitities at seas as 10MW/km2
        if bus_id not in eh_clusters.index:
            total_capacities[i] = 0.01 if carrier == 'wind' else 0
            continue

        codes = eh_clusters.loc[bus_id].codes.split(",")

        # TODO: this is a shitty hack
        if codes[0][0:2] in missing_region_dict:
            codes = missing_region_dict[codes[0][0:2]]

        if len(codes[0]) != 2:
            nuts2_codes = nuts3_to_nuts2(codes)
            total_capacities[i] = np.average([capacities.loc[code]["capacity"] for code in nuts2_codes],
                                             weights=[area.loc[code]["2016"] for code in codes])
        else:
            # If the code corresponds to a countries, get the correspond list of NUTS2
            nuts2_codes = [code for code in capacities.index.values if code[0:2] == codes[0]]
            total_capacities[i] = np.average([capacities.loc[code]["capacity"] for code in nuts2_codes],
                                             weights=[area.loc[code]["2016"] for code in nuts2_codes])

    return pd.DataFrame(total_capacities, index=bus_ids, columns=["capacity"]).capacity