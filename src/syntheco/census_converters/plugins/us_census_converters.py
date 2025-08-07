"""
us_census_converters

This is the code for the US Census Plugins
"""
import pandas as pd
import numpy as np
import requests_cache
import time
import os
import geopandas as gpd

from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from datetime import timedelta

from syntheco.census_converters import hookimpl
from syntheco.census_converters.census_converter import CensusConverter
from syntheco.error import SynthEcoError
from syntheco.logger import log


class APIManager:
    """
    APIManager class

    This singleton class interfaces with the US Census API.

    """

    def __init__(self):
        """
        Constructor

        Sets up the connection to the US Census API.

        Returns:
            An instance of the APIManager
        """
        session = requests_cache.CachedSession(
            "api-response-cache",
            backend="filesystem",
            expire_after=timedelta(days=1),
        )
        retry = Retry(total=5, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry)
        base_url = "https://api.census.gov/data"
        session.mount(base_url, adapter)

        self.session = session
        self.base_url = base_url

    def api_call(self, url="", params=None):
        """
        api_call

        Handles the request to the US Census API.

        Arguments:
            - url (str): the url to request; appended onto the base_url
            - params (dict): the parameters to pass into the request

        Returns:
            The response data in json format
        """
        start = time.time()
        log("DEBUG", f"API call in progress...")

        try:
            response = self.session.get(self.base_url + url, params=params, timeout=10)
            response.raise_for_status()
        # TODO: handle errors separately
        except HTTPError as e:
            log("ERROR", f"Failed API call (HTTPError): {e}")
            raise
        except ConnectionError as e:
            log("ERROR", f"Failed API call (ConnectionError): {e}")
            raise
        except Timeout as e:
            log("ERROR", f"Failed API call (Timeout): {e}")
            raise
        except RequestException as e:
            log("ERROR", f"Failed API call (RequestException): {e}")
            raise
        else:
            elapsed = time.time() - start
            info = "from cache" if response.from_cache else f"took {round(elapsed)}s"
            log("DEBUG", f"Successful API call ({info}): {response.url}")

            return response.json()


api_manager = APIManager()


def _format_df(data, ip=None, api_vars=None, formulate_geo_code=True):
    """
    _format_df

    Helper function that will convert the json data received from the Census API
    to a pandas dataframe with columns set appropriately. This will formulate
    FIPS codes from the present geography columns, setting it as the index, as
    well as set the remaining columns to the API variables.

    Note that FIPS is standardized to GEO_CODE.

    Arguments:
        - data (List[str]): the data to format, in json format
        - ip (InputParams): the input parameters of the census converter instance
        - api_vars (List[str]): the list of API variables retrieved from the Census API
        - formulate_geo_code (bool): if the function should formulate the GEO_CODE as the index

    returns:
        the formatted dataframe
    """
    raw_df = pd.DataFrame(data[1:], columns=data[0])

    if not formulate_geo_code:  # PUMS converter does not require GEO_CODE
        return raw_df

    raw_df["GEO_CODE"] = raw_df["state"] + raw_df["county"]
    if ip["census_high_res_geo_unit"] == "tract":
        raw_df["GEO_CODE"] += raw_df["tract"]

    raw_df = raw_df[["GEO_CODE"] + api_vars]
    raw_df = raw_df.set_index("GEO_CODE")

    return raw_df


class USCensusGlobalPlugin:
    """
    USCensusGlobalPlugin

    This is class that houses the implemented hooks for the US Census plugin
    for global tables
    """

    @hookimpl
    def read_raw_data_into_pandas(cens_conv_inst: CensusConverter):
        """
        read_raw_data_into_pandas

        Retrieves relevant data from the Census API

        Returns:
            the raw data table from the US Census data
        """
        ip = cens_conv_inst.input_params
        if ip.input_params["use_census_api"]:
            return USCensusGlobalPlugin._read_raw_data_into_pandas_from_api(ip)
        else:
            return USCensusGlobalPlugin._read_raw_data_into_pandas_from_file(ip)

    @staticmethod
    def _read_raw_data_into_pandas_from_api(ip):
        """
        data variables we will be retrieving from api
        """

        api_vars = [
            "P1_001N",  # total population data
            "H1_001N",  # total housing data
        ]

        url = "/{}/dec/pl".format(ip["census_year"])
        params = {
            "get": ",".join(api_vars),
            "for": "{}:*".format(ip["census_high_res_geo_unit"]),
            "in": "{}".format(ip["census_low_res_geo_unit"]),
            "key": ip["api_key"],
        }

        data = api_manager.api_call(url, params)
        raw_df = _format_df(data, ip, api_vars)
        return raw_df

    @staticmethod
    def _read_raw_data_into_pandas_from_file(ip):
        '''
        _read_raw_data_into_pandas_from_file
        Private function that reads data from downloaded files.
        The python notebook that sets the directory up is in the contrib folder

        The directory structure is {ip.census_data_dir}/{census_year}/Profile/{stateFips}/prof_{stateFips}.csv

        Arguments:
            ip: InputParams from a yaml file

        Returns:
            DataFrame with all of the Profile Variables

        NOTE: ONLY WORKS RIGHT NOW WITH STATE AND TRACTS

        '''
        try:
            low_res_geo_unit = ip.input_params['census_low_res_geo_unit']
            profile_csv = os.path.join(ip.input_params['census_data_dir'],
                                       str(ip.input_params['census_year']),
                                       "Profile",
                                       f"{low_res_geo_unit}",
                                       f"prof_{low_res_geo_unit}.csv")
            profile_iter = pd.read_csv(profile_csv,
                                       iterator=True,
                                       usecols=["state", "county", "tract", "DP05_0001E", "DP04_0001E"],
                                       chunksize=1000)
            raw_df = pd.concat([chunk for chunk in profile_iter])
            raw_df['GEO_CODE'] = raw_df.apply(lambda x: ''.join([str(x['state']).zfill(2),
                                                                 str(x['county']).zfill(3),
                                                                 str(x['tract']).zfill(6)]), axis=1)
            raw_df = raw_df.rename(columns={"DP05_0001E": "total_population", "DP04_0001E": "number_households"})
            raw_df = raw_df.set_index('GEO_CODE')
            return raw_df
        except Exception as e:
            raise SynthEcoError(f"USCensusSummaryPlugin read_raw_data_into_pandas_from_file:\n{e}")

    @hookimpl
    def transform(cens_conv_inst: CensusConverter):
        """
        transform

        Formats the raw data into global tables

        Returns:
            an updated dataframe to be set to processed_data_df
        """
        # total population table
        pop_df = (
            cens_conv_inst.raw_data_df.copy()
            .drop(columns=["number_households"])
            .rename(columns={"total_population": "total"})
        )

        pop_df["total"] = pop_df["total"].astype(np.float64)

        # total number of households table
        nh_df = (
            cens_conv_inst.raw_data_df.copy()
            .drop(columns=["total_population"])
            .rename(columns={"number_households": "total"})
        )

        nh_df["total"] = nh_df["total"].astype(np.float64)

        pop_df.name = "Total Population by High Resolution Geo Unit"
        nh_df.name = "Number of Households by High Resolution Geo Unit"

        geos_hh_interest = list(nh_df[(nh_df["total"] != 0)].index)
        geos_pop_interest = list(pop_df[pop_df["total"] != 0].index)

        geos_of_interest = [x for x in geos_hh_interest if x in geos_pop_interest]

        if cens_conv_inst.input_params.has_keyword("debug_limit_geo_codes"):
            debug_limit = cens_conv_inst.input_params["debug_limit_geo_codes"]

            if debug_limit < len(geos_of_interest):
                geos_of_interest = geos_of_interest[:debug_limit]

        return {
            "total_population_by_geo": pop_df,
            "number_households_by_geo": nh_df,
            "geos_of_interest": geos_of_interest,
            "census_variable_metadata": cens_conv_inst.metadata_json,
        }


class USCensusSummaryPlugin:
    """
    USCensusSummaryPlugin

    This class houses the implemented hooks for the US Census plugins
    for processed summary count tables
    """

    @hookimpl
    def read_raw_data_into_pandas(cens_conv_inst: CensusConverter):
        """
        _read_raw_data_into_pandas

        Retrieves relevant data from the Census API

        Returns:
            the raw data table from the US Census data
        """
        # retrieve api vars from metadata_json
        metadata_json = cens_conv_inst.metadata_json
        ip = cens_conv_inst.input_params
        if ip.input_params["use_census_api"]:
            print("!!!!!! using API")
            return USCensusSummaryPlugin._read_raw_data_into_pandas_from_api(ip, metadata_json)
        else:
            print("!!!!!!!Using Files Summary")
            return USCensusSummaryPlugin._read_raw_data_into_pandas_from_file(ip)

    @staticmethod
    def _read_raw_data_into_pandas_from_api(ip, metadata_json):
        '''
        saving this function for later, currently doesn't get all of the data needed for the process
        '''
        pums_vars = ip["census_fitting_vars"]
        api_vars = [metadata_json[v]["profile_vars"] for v in pums_vars]
        api_vars = [
            pv for v in api_vars for pv in v
        ]  # flatten nested list of profile_vars

        assert len(api_vars) <= 50  # TODO: split this case into multiple api calls

        url = "/{}/acs/acs5/profile".format(ip["census_year"])
        params = {
            "get": ",".join(api_vars),
            "for": "{}:*".format(ip["census_high_res_geo_unit"]),
            "in": "{}".format(ip["census_low_res_geo_unit"]),
            "key": ip["api_key"],
        }

        data = api_manager.api_call(url, params)
        raw_df = _format_df(data, ip, api_vars)
        return raw_df

    @staticmethod
    def _read_raw_data_into_pandas_from_file(ip):
        '''
        _read_raw_data_into_pandas_from_file
        Private function that reads data from downloaded files.
        The python notebook that sets the directory up is in the contrib folder

        The directory structure is {ip.census_data_dir}/{census_year}/Profile/{stateFips}/prof_{stateFips}.csv

        Arguments:
            ip: InputParams from a yaml file

        Returns:
            DataFrame with all of the Profile Variables

        NOTE: ONLY WORKS RIGHT NOW WITH STATE AND TRACTS

        '''
        try:
            low_res_geo_unit = ip.input_params['census_low_res_geo_unit']
            profile_csv = os.path.join(ip.input_params['census_data_dir'],
                                       str(ip.input_params['census_year']),
                                       "Profile",
                                       f"{low_res_geo_unit}",
                                       f"prof_{low_res_geo_unit}.csv")
            profile_iter = pd.read_csv(profile_csv,
                                       iterator=True,
                                       chunksize=1000)
            raw_df = pd.concat([chunk for chunk in profile_iter])
            print("zfilling")
            raw_df['GEO_CODE'] = raw_df.apply(lambda x: ''.join([str(x['state']).zfill(2),
                                                                 str(x['county']).zfill(3),
                                                                 str(x['tract']).zfill(6)]), axis=1)
            raw_df = raw_df.set_index('GEO_CODE')
            return raw_df

        except Exception as e:
            return SynthEcoError(f"USCensusSummaryPlugin read_raw_data_into_pandas_from_file:\n{e}")

    @hookimpl
    def transform(cens_conv_inst: CensusConverter):
        """
        transform

        Formats the raw data into processed summary count tables

        TODO: This only works with the full profile data frame

        Returns:
            an updated dataframe to be set to processed_data_df
        """
        pums_vars = cens_conv_inst.input_params["census_fitting_vars"]
        proc_df = cens_conv_inst.raw_data_df.copy()

        sum_tables = {}
        for var in pums_vars:
            print(f"var = {var}")
            var_ds = cens_conv_inst.metadata_json[var]
            var_df = proc_df[var_ds["profile_vars"]].astype(np.int64)
            print(f"var_df = {var_df}")

            # sum profile vars for each index i in common_var_map to get summary totals
            lookup = [
                (int(i), c["profile_vars"]) for i, c in var_ds["common_var_map"].items()
            ]
            for i, prof_vars in lookup:
                var_df[i] = var_df[prof_vars].sum(axis=1)

            var_df = var_df.drop(columns=var_ds["profile_vars"]).stack().reset_index()
            var_df.columns = ["GEO_CODE", var, "total"]

            # handle cases where total is 0 for all indices in common_var_map
            # TODO maybe eliminate them, but that messes with the pums

            sum_by_geo = var_df.groupby("GEO_CODE").sum()
            var_df["total"] = var_df.apply(
                lambda x: 1.0  # right now just converts them to 1.0
                if sum_by_geo.loc[x["GEO_CODE"]]["total"] == 0
                else x["total"],
                axis=1,
            )

            var_df = var_df.set_index("GEO_CODE")
            var_df["total"] = var_df["total"].astype(np.float64)
            var_df.name = f"{var} Summary Table"
            sum_tables[var] = var_df
        return sum_tables


class USCensusPUMSPlugin:
    """
    USCensusPUMSPlugin

    This class houses the implemented hooks for the US Census plugins
    for processed PUMS tables
    """

    @hookimpl
    def read_raw_data_into_pandas(cens_conv_inst: CensusConverter):
        """
        _read_raw_data_into_pandas

        Retrieves relevant data from the Census API

        Returns:
            the raw data table from the US Census data
        """
        ip = cens_conv_inst.input_params
        if ip.input_params["use_census_api"]:
            print("!!!!!! using API")
            return USCensusPUMSPlugin._read_raw_data_into_pandas_from_api(ip)
        else:
            print("!!!!!!!Using Files")
            return USCensusPUMSPlugin._read_raw_data_into_pandas_from_files(ip)

    @staticmethod
    def _read_raw_data_into_pandas_from_api(ip):

        try:
            api_vars = ["SERIALNO"] + ip["census_fitting_vars"]

            url = "/{}/acs/acs5/pums".format(ip["census_year"])
            params = {
                "get": ",".join(api_vars),
                "for": "{}".format(ip["census_low_res_geo_unit"]),
                "key": ip["api_key"],
            }

            data = api_manager.api_call(url, params)
            raw_df = _format_df(data, formulate_geo_code=False)
            return raw_df
        except Exception as e:
            raise SynthEcoError("USCensusPUMSPlugin read_raw_data_into_pandas_api\n{}".format(e))

    @staticmethod
    def _read_raw_data_into_pandas_from_files(ip):
        """
        _read_raw_data_into_pandas_from_files

        This private function reads the data from downloaded files.
        The files can be found at https://www2.census.gov/programs-surveys/acs/data/pums/
        There are two zip files that need to be downloaded, one for the households and one for the
        people file.

        There is a utility script in contrib (TODO) that will download one or all states.

        The directory structure that is needed is
        {ip.census_data_dir}/census_year/PUMS/[stateFips]/[p,h]/psam_[p,h][stateFips].csv

        Arguments:
            ip: InputParams from a yaml file

        Returns:
            raw_df: Dictionary with "Household" and "People" DataFrames
        """

        try:
            raw_df = {}
            low_res_geo = ip.input_params['census_low_res_geo_unit']

            pums_h_csv = os.path.join(ip.input_params['census_data_dir'],
                                      str(ip.input_params['census_year']),
                                      "PUMS",
                                      low_res_geo,
                                      "h/psam_h{}.csv".format(low_res_geo))
            pums_h_iter = pd.read_csv(pums_h_csv,
                                      iterator=True,
                                      dtype={'SERIALNO': str},
                                      chunksize=1000)

            raw_df["Household"] = pd.concat([chunk for chunk in pums_h_iter])

            raw_df["Household"] = raw_df["Household"].rename(columns={'SERIALNO': 'HH_ID'})
            raw_df["Household"].name = "PUMS Raw Houshold Data"

            pums_p_csv = os.path.join(ip.input_params['census_data_dir'],
                                      str(ip.input_params['census_year']),
                                      "PUMS",
                                      low_res_geo,
                                      "p/psam_p{}.csv".format(low_res_geo))
            pums_p_iter = pd.read_csv(pums_p_csv,
                                      iterator=True,
                                      dtype={'SERIALNO': str},
                                      chunksize=1000)

            # doing this here, cause I have all of the information, need a better place for this

            raw_df["Person"] = pd.concat([chunk for chunk in pums_p_iter])
            raw_df["Person"] = raw_df["Person"].rename(columns={'SERIALNO': 'HH_ID'})
            raw_df["Person"].name = "PUMS Raw Household Data"

            # Lastly, there is no point in keeping households that don't have people entries
            raw_df["Household"] = raw_df["Household"][raw_df["Household"]['HH_ID'].isin(set(raw_df['Person']['HH_ID']))]

            return raw_df

        except Exception as e:
            raise SynthEcoError("USCensusPUMSPlugin read_raw_data_into_pandas_file\n{}".format(e))

    @hookimpl
    def transform(cens_conv_inst: CensusConverter):
        """
        transform

        Formats the raw data into processed PUMS tables

        Returns:
            an updated dataframe to be set to processed_data_df
        """
        pums_vars = cens_conv_inst.input_params["census_fitting_vars"]
        proc_df = cens_conv_inst.raw_data_df['Household'].copy()
        proc_df = proc_df.fillna(-999999)
        proc_df[pums_vars] = proc_df[pums_vars].astype(np.int64)

        for var in pums_vars:
            new_col_name = f"{var}_m"
            proc_df[new_col_name] = [np.NaN for _ in range(proc_df.shape[0])]

            lookup = [
                (int(i), c["pums_inds"])
                for i, c in cens_conv_inst.metadata_json[var]["common_var_map"].items()
            ]
            for i, constraints in lookup:
                if len(constraints) == 1:  # for single index constraints
                    proc_df.loc[proc_df[var] == int(constraints[0]), new_col_name] = i
                elif len(constraints) == 2:  # for index range constraints
                    lower = int(constraints[0])
                    upper = int(constraints[1])
                    proc_df.loc[
                        (proc_df[var] >= lower) & (proc_df[var] <= upper), new_col_name
                    ] = i

        proc_df = proc_df.rename(columns={x: f"{x}_V" for x in pums_vars}).rename(
            columns={f"{x}_m": x for x in pums_vars}
        )

        freq_df = (
            proc_df.groupby(pums_vars).size().reset_index().rename(columns={0: "total"})
        )

        freq_df["total"] = freq_df["total"].astype(np.float64)
        freq_df = freq_df.astype({v: np.int64 for v in pums_vars})

        proc_df.name = "PUMS Data Categorical Representation"
        freq_df.name = "PUMS Data Frequency Representation"

        return {
            "categorical_table": proc_df,
            "frequency_table": freq_df,
            "raw_data": cens_conv_inst.raw_data_df,
            "separate": True
        }

    @staticmethod
    def get_all_raw_pums_from_api(census_year, stateFips, api_manager, api_key):
        '''
        get_all_raw_pums_from_api

        function that uses the US Census API and then creates a csv that can be cached
        to read by in as this is very time consuming.

        Arguments:
            census_year: integer year of the census you want to get
            stateFips: integer of the state fips code you want (pums only available by state)
            api_manager: an instance of the APIManger class

        '''

        pums_URL = f"/{census_year}/acs/acs5/pums"

        # Get all variables
        vars_URL = f"{pums_URL}/variables.json"
        variable_dirty_list = api_manager.api_call(vars_URL)
        var_list = [x for x, v in variable_dirty_list['variables'].items()
                    if x not in ['for', 'in', 'ucgid']]

        n = 15  # chunk size, wouldn't change
        var_list_chunks = [var_list[i*n:(i+1)*n] for i in range((len(var_list) + n-1) // n)]
        data = pd.DataFrame()
        # Now run through and get all of the pums from the variables
        for ic in var_list_chunks:
            ic_str = ",".join(ic)
            params = {
                "get": f"SERIALNO,{ic_str}",
                "for": f"state:{stateFips}",
                "key": api_key
            }
            datax = pd.DataFrame(api_manager.api_call(pums_URL, params))
            datax.columns = datax.iloc[0]
            datax = datax.drop(datax.index[0])
            datax = datax.set_index(["SERIALNO", "state"])

            data = pd.concat([data, datax], axis=1)
        return data


class USCensusBorderPlugin:
    """
    Class to hold the border data for geographic sampling
    """

    @hookimpl
    def read_raw_data_into_pandas(cens_conv_inst: CensusConverter):
        """
        _read_raw_data_into_pandas

        Retrieves relevant data from the Census API

        Returns:
            the raw data table from the US Census data
        """
        try:
            ip = cens_conv_inst.input_params
            low_res_geo = ip.input_params['census_low_res_geo_unit']
            border_file = os.path.join(ip.input_params['census_data_dir'],
                                       str(ip.input_params['census_year']),
                                       "Borders",
                                       low_res_geo,
                                       f"tl_{ip.input_params['census_year']}_{low_res_geo}_tract.shp")
            return gpd.read_file(border_file).to_crs("WGS 84")
        except Exception as e:
            raise SynthEcoError(f"USCensusBorder._read_raw_data error: \n{e}")

    @hookimpl
    def transform(cens_conv_inst: CensusConverter):
        """
        transform

        Formats the raw data into processed Border tables

        Returns:
            an updated dataframe to be set to processed_data_df
        """

        try:
            return cens_conv_inst.raw_data_df.rename(columns={"GEOID": "GEO_UNIT"})
        except Exception as e:
            raise SynthEcoError("USCensusBorder._transform error: \n{e}")
