from os.path import join, dirname, abspath
from typing import List, Tuple, Dict, Any
import yaml

import xarray as xr
import numpy as np
import xarray.ufuncs as xu
import dask.array as da
import geopandas as gpd
import scipy.spatial
import geopy.distance

from copy import copy

from src.data.resource.manager import read_resource_database


# TODO:
#  - It's actually probably smarter than using shapes to differentiate between onshore and offshore
#  - I think we should actually change the tech argument to an onshore or offshore argument
#  - Or maybe not because then we have the problem of associating offshore points which are considered onshore
def filter_onshore_offshore_points(onshore: bool, points: List[Tuple[float, float]], spatial_resolution: float):
    """
    Filters coordinates to leave only onshore and offshore coordinates depending on technology

    Parameters
    ----------
    onshore: bool
        If True, keep only points that are offshore, else keep points offshore
    points : List[Tuple[float, float]]
        List of points to filter
    spatial_resolution : float
        Spatial resolution of coordinates

    Returns
    -------
    coordinates : List[tuple(float, float)]
        Coordinates filtered via land/water mask.
    """

    path_land_data = join(dirname(abspath(__file__)),
                          '../../../data/land_data/ERA5_land_sea_mask_20181231_' + str(spatial_resolution) + '.nc')
    dataset = xr.open_dataset(path_land_data)
    dataset = dataset.sortby([dataset.longitude, dataset.latitude])
    dataset = dataset.assign_coords(longitude=(((dataset.longitude + 180) % 360) - 180)).sortby('longitude')
    dataset = dataset.drop('time').squeeze().stack(locations=('longitude', 'latitude'))
    array_watermask = dataset['lsm']

    if onshore:
        mask_watermask = array_watermask.where(array_watermask.data >= 0.3)
    else:
        mask_watermask = array_watermask.where(array_watermask.data < 0.3)

    points_in_mask = mask_watermask[mask_watermask.notnull()].locations.values.tolist()

    return list(set(points).intersection(set(points_in_mask)))


# TODO: merge with other read_database?
def read_filter_database(filename: str, coords: List[Tuple[float, float]] = None) -> xr.Dataset:
    """
    Opens a file containing filtering information

    Parameters
    ----------
    filename: str
        Name of the file containing the filtering information
    coords: List[Tuple[float, float]] (default: None)
        List of points for which we want the filtering information

    Returns
    -------
    dataset: xarray.Dataset
    """

    dataset = xr.open_dataset(filename)
    dataset = dataset.sortby([dataset.longitude, dataset.latitude])

    # Changing longitude from 0-360 to -180-180
    dataset = dataset.assign_coords(longitude=(((dataset.longitude + 180) % 360) - 180)).sortby('longitude')
    dataset = dataset.drop('time').squeeze().stack(locations=('longitude', 'latitude'))
    if coords is not None:
        dataset = dataset.sel(locations=coords)

    return dataset


def filter_points_by_layer(filter_name: str, points: List[Tuple[float, float]], spatial_resolution: float,
                           tech_dict: Dict[str, Any]) -> List[Tuple[float, float]]:
    """
    Compute locations to remove from the initial set following various
    land-, resource-, populatio-based criteria.

    Parameters
    ----------
    filter_name: str
        Name of the filter to be applied
    points : List[Tuple[float, float]]
        List of points.
    spatial_resolution : float
        Spatial resolution of the points.
    tech_dict : Dict[str, Any]
        Dict object containing technical tech_parameters and constraints of a given technology.

    Returns
    -------
    points : List[Tuple[float, float]]
        List of filtered points.

    """
    if filter_name == 'protected_areas':

        protected_areas_selection = tech_dict['protected_areas_selection']
        threshold_distance = tech_dict['protected_areas_distance_threshold']

        path_land_data = join(dirname(abspath(__file__)), '../../../data/land_data/WDPA_Feb2019-shapefile-points.shp')
        dataset = gpd.read_file(path_land_data)

        # Retrieve the geopandas Point objects and their coordinates
        dataset = dataset[dataset['IUCN_CAT'].isin(protected_areas_selection)]
        protected_points = dataset.geometry.apply(lambda p: (round(p[0].x, 2), round(p[0].y, 2))).values

        # Compute closest protected point for each coordinae
        protected_points = np.array([[p[0], p[1]] for p in protected_points])
        points = np.array([[p[0], p[1]] for p in points])
        closest_points = \
            protected_points[np.argmin(scipy.spatial.distance.cdist(protected_points, points, 'euclidean'), axis=0)]

        # Remove coordinates that are too close to protected areas
        points_to_remove = []
        for coord1, coord2 in zip(points, closest_points):
            if geopy.distance.geodesic((coord1[1], coord1[0]), (coord2[1], coord2[0])).km < threshold_distance:
                points_to_remove.append(tuple(coord1))

        points = list(set(points) - set(points_to_remove))

    elif filter_name == 'resource_quality':

        # TODO: still fucking slow, make no sense to be so slow
        # TODO: does it make sense to reload this dataset?
        path_resource_data = join(dirname(abspath(__file__)), '../../../data/resource/' + str(spatial_resolution))
        database = read_resource_database(path_resource_data)
        database = database.sel(locations=sorted(points))
        # TODO: slice on time?

        if tech_dict['resource'] == 'wind':
            array_resource = xu.sqrt(database.u100 ** 2 + database.v100 ** 2)
        elif tech_dict['resource'] == 'pv':
            array_resource = database.ssrd / 3600.
        else:
            raise ValueError("Error: Resource must be wind or pv")

        array_resource_mean = array_resource.mean(dim='time')
        mask_resource = array_resource_mean.where(array_resource_mean.data < tech_dict['resource_threshold'], 0)
        coords_mask_resource = mask_resource[da.nonzero(mask_resource)].locations.values.tolist()
        points = list(set(points).difference(set(coords_mask_resource)))

    elif filter_name == 'orography':

        dataset_name = join(dirname(abspath(__file__)),
                            '../../../data/land_data/ERA5_orography_characteristics_20181231_' + str(spatial_resolution) + '.nc')
        dataset = read_filter_database(dataset_name, points)

        altitude_threshold = tech_dict['altitude_threshold']
        slope_threshold = tech_dict['terrain_slope_threshold']

        array_altitude = dataset['z'] / 9.80665
        array_slope = dataset['slor']

        mask_altitude = array_altitude.where(array_altitude.data > altitude_threshold)
        points_mask_altitude = mask_altitude[mask_altitude.notnull()].locations.values.tolist()

        mask_slope = array_slope.where(array_slope.data > slope_threshold)
        points_mask_slope = mask_slope[mask_slope.notnull()].locations.values.tolist()

        points_mask_orography = set(points_mask_altitude).union(set(points_mask_slope))
        points = list(set(points).difference(points_mask_orography))

    elif filter_name == 'forestry':

        dataset_name = join(dirname(abspath(__file__)),
                            '../../../data/land_data/ERA5_surface_characteristics_20181231_'+str(spatial_resolution)+'.nc')
        dataset = read_filter_database(dataset_name, points)

        forestry_threshold = tech_dict['forestry_ratio_threshold']

        array_forestry = dataset['cvh']

        mask_forestry = array_forestry.where(array_forestry.data >= forestry_threshold)
        points_mask_forestry = mask_forestry[mask_forestry.notnull()].locations.values.tolist()

        points = list(set(points).difference(set(points_mask_forestry)))

    elif filter_name == 'water_mask':

        dataset_name = join(dirname(abspath(__file__)),
                            '../../../data/land_data/ERA5_land_sea_mask_20181231_' + str(spatial_resolution) + '.nc')
        dataset = read_filter_database(dataset_name, points)

        array_watermask = dataset['lsm']

        mask_watermask = array_watermask.where(array_watermask.data < 0.9)
        points_mask_watermask = mask_watermask[mask_watermask.notnull()].locations.values.tolist()

        points = list(set(points).difference(set(points_mask_watermask)))

    elif filter_name == 'bathymetry':

        dataset_name = join(dirname(abspath(__file__)),
                            '../../../data/land_data/ERA5_land_sea_mask_20181231_' + str(spatial_resolution) + '.nc')
        dataset = read_filter_database(dataset_name, points)

        depth_threshold_low = tech_dict['depth_threshold_low']
        depth_threshold_high = tech_dict['depth_threshold_high']

        array_watermask = dataset['lsm']
        # Careful with this one because max depth is 999.
        array_bathymetry = dataset['wmb'].fillna(0.)

        mask_offshore = array_bathymetry.where((
            (array_bathymetry.data < depth_threshold_low) | (array_bathymetry.data > depth_threshold_high)) | \
            (array_watermask.data > 0.1))
        points_mask_offshore = mask_offshore[mask_offshore.notnull()].locations.values.tolist()

        points = list(set(points).difference(set(points_mask_offshore)))

    # TODO: check how we organize this file within the structure
    elif filter_name == 'population_density':

        path_population_data = \
            join(dirname(abspath(__file__)),
                 '../../../data/population_density/gpw_v4_population_density_rev11_' + str(spatial_resolution) + '.nc')
        dataset = xr.open_dataset(path_population_data)

        varname = [item for item in dataset.data_vars][0]
        dataset = dataset.rename({varname: 'data'})
        # The value of 5 for "raster" fetches data for the latest estimate available in the dataset, that is, 2020.
        data_pop = dataset.sel(raster=5)

        array_pop_density = data_pop['data'].interp(longitude=np.arange(-180, 180, float(spatial_resolution)),
                                                    latitude=np.arange(-89, 91, float(spatial_resolution))[::-1],
                                                    method='nearest').fillna(0.)
        array_pop_density = array_pop_density.stack(locations=('longitude', 'latitude'))

        population_density_threshold_low = tech_dict['population_density_threshold_low']
        population_density_threshold_high = tech_dict['population_density_threshold_high']

        mask_population = array_pop_density.where((array_pop_density.data < population_density_threshold_low) |
                                                  (array_pop_density.data > population_density_threshold_high))
        points_mask_population = mask_population[mask_population.notnull()].locations.values.tolist()

        points = list(set(points).difference(set(points_mask_population)))

    else:

        raise ValueError(' Layer {} is not available.'.format(str(filter_name)))

    return points


def filter_points(technologies: List[str], tech_config: Dict[str, Any], init_points: List[Tuple[float, float]],
                  spatial_resolution: float, filtering_layers: Dict[str, bool]) -> Dict[str, List[Tuple[float, float]]]:
    """
    Returns the set of potential deployment locations for each region and available technology.

    Parameters
    ----------
    init_points : List[Tuple(float, float)]
        List of points to filter
    tech_config: Dict[str, Any]
        Gives for every technology, a set of configuration parameters and their associated values
    spatial_resolution : float
        Spatial resolution at which the points are defined.
    technologies : List[str]
        List of technologies for which we want to filter points.
    filtering_layers: Dict[str, bool]
        Dictionary indicating if a given filtering layers needs to be applied. If the layer name is present as key and
        associated to a True boolean, then the corresponding is applied.

        List of possible filter names:

        resource_quality:
            If taken into account, discard points whose average resource quality over
            the available time horizon are below a threshold defined in the config_tech.yaml file.
        population_density:
            If taken into account, discard points whose population density is below a
            threshold defined in the config_tech.yaml file for each available technology.
        protected_areas:
            If taken into account, discard points who are closer to protected areas (defined in config_tech.yaml)
            in their vicinity than a distance threshold defined in the config_tech.yaml file.
        orography:
            If taken into account, discard points whose altitude and terrain slope
            are above thresholds defined in the config_tech.yaml file for each individual technology.
        forestry:
            If taken into account, discard points whose forest cover share
            is above a threshold defined in the config_tech.yaml file.
        water_mask:
            If taken into account, discard points whose water coverage share
            is above a threshold defined in the config_tech.yaml file.
        bathymetry (valid for offshore technologies):
            If taken into account, discard points whose water depth is above a threshold defined
            in the config_tech.yaml file for offshore and floating wind, respectively.

    Returns
    -------
    tech_points_dict : Dict[str, List[Tuple(float, float)]]
        Dict object giving for each technology the list of filtered points.

    """
    tech_points_dict = dict.fromkeys(technologies)

    for tech in technologies:

        tech_dict = tech_config[tech]

        points = copy(init_points)
        for key in filtering_layers:

            if len(points) == 0:
                break

            # Apply the filter if it is set to true
            if filtering_layers[key]:

                # Some filter should not apply to some technologies
                if key == 'bathymetry' and tech_dict['deployment'] in ['onshore', 'utility', 'residential']:
                    continue
                if key in ['orography', 'population_density', 'protected_areas', 'forestry', 'water_mask'] \
                        and tech_dict['deployment'] in ['offshore', 'floating']:
                    continue
                points = filter_points_by_layer(key, points, spatial_resolution, tech_dict)

        tech_points_dict[tech] = points

    return tech_points_dict
