"""
canada_census_conveters

This is the code for the Canada Census Plugins
"""


import pandas as pd
import numpy as np
import geopandas as gpd
import json
from syntheco.census_converters import hookimpl
from syntheco.logger import log, data_log
from syntheco.error import SynthEcoError


class CanadaCensusGlobalPlugin:
    """
    CanadaCensusGlobalPlugin

    This is class that houses the implemented hooks for the canada census plugins
    for global tables
    """
    @hookimpl
    def read_raw_data_into_pandas(cens_conv_inst):
        """
        _read_raw_data_into_pandas
        Private member that defines how the raw data is read into pandas
        data frame for the conversion

        Returns:
            returns the raw data table from the canadian census profile data
        """
        try:
            census_year = cens_conv_inst.input_params.input_params['census_year']
            low_res_geo = cens_conv_inst.input_params.input_params['census_low_res_geo_unit']
            high_res_geo = cens_conv_inst.input_params.input_params['census_high_res_geo_unit']
            profile_data_csv = cens_conv_inst.input_params.input_params['census_input_files']['profile_data_csv']

            prof_iter = pd.read_csv(profile_data_csv,
                                    iterator=True,
                                    dtype={'GEO_CODE (POR)': str,
                                           'DIM: Profile of Census Tracts (2247)': str},
                                    chunksize=1000)
            raw_df = pd.concat([chunk[(chunk['GEO_CODE (POR)'].str.find(str(low_res_geo), 0) == 0)
                                      & (chunk['GEO_LEVEL'] == high_res_geo)
                                      & (chunk['CENSUS_YEAR'] == census_year)]
                                for chunk in prof_iter])
            return raw_df
        except Exception as e:
            raise SynthEcoError("CanadaCensusGlobalPlugin: read_raw_data_into_pandas\n{}".format(e))

    @hookimpl
    def transform(cens_conv_inst):
        """
        transform

        This function actually transforms the raw data from the canadian census profile
        and derives the dataframes for the total population and total number_households

        Returns:
            An updated dataframe to be set to processed_data_df
        """
        try:
            # total population table
            raw_df = cens_conv_inst.raw_data_df
            pop_df = raw_df[(raw_df['DIM: Profile of Census Tracts (2247)'] == "Population, 2016")]
            pop_df = pop_df.drop(columns=["DIM: Profile of Census Tracts (2247)",
                                          "Dim: Sex (3): Member ID: [2]: Male",
                                          "Dim: Sex (3): Member ID: [3]: Female",
                                          "GNR", "GNR_LF", "ALT_GEO_CODE",
                                          "Member ID: Profile of Census Tracts (2247)",
                                          "DATA_QUALITY_FLAG"])
            pop_df = pop_df.rename(columns={'Dim: Sex (3): Member ID: [1]: Total - Sex': 'total',
                                            'GEO_CODE (POR)': 'GEO_CODE'})

            # total number of houshold data
            nh_df = raw_df[(raw_df['DIM: Profile of Census Tracts (2247)'] == "Total private dwellings")]
            nh_df = nh_df.drop(columns=["DIM: Profile of Census Tracts (2247)",
                                        "Dim: Sex (3): Member ID: [2]: Male",
                                        "Dim: Sex (3): Member ID: [3]: Female",
                                        "GNR", "GNR_LF", "ALT_GEO_CODE",
                                        "Member ID: Profile of Census Tracts (2247)",
                                        "DATA_QUALITY_FLAG"])
            nh_df = nh_df.rename(columns={'Dim: Sex (3): Member ID: [1]: Total - Sex': 'total',
                                          'GEO_CODE (POR)': 'GEO_CODE'})

            # Fix .. values, for now convert them to zero
            pop_df['total'] = pd.to_numeric(pop_df['total'], downcast='float', errors='coerce').fillna(0.0)
            pop_df = pop_df.set_index('GEO_CODE')
            pop_df.name = "Total Population by High Resolution Geo Unit"

            # Fix .. values, for now convert them to zero
            nh_df['total'] = pd.to_numeric(nh_df['total'], downcast='float', errors='coerce').fillna(0.0)
            nh_df = nh_df.set_index('GEO_CODE')
            nh_df.name = "Number of Households by High Resolution Geo Unit"

            # Finally, the geographic units of interest come from the overlap between pop and hh
            geos_hh_interest = list(nh_df[(nh_df['total'] != 0)].index)
            geos_pop_interest = list(pop_df[pop_df['total'] != 0].index)

            geos_of_interest = [x for x in geos_hh_interest if x in geos_pop_interest]

            if (cens_conv_inst.input_params.has_keyword('debug_limit_geo_codes') and
               cens_conv_inst.input_params['debug_limit_geo_codes'] < len(geos_of_interest)):
                geos_of_interest = geos_of_interest[0:cens_conv_inst.input_params['debug_limit_geo_codes']]

            return {"total_population_by_geo": pop_df,
                    "number_households_by_geo": nh_df,
                    "geos_of_interest": geos_of_interest,
                    "census_variable_metadata": cens_conv_inst.metadata_json}
        except Exception as e:
            raise SynthEco("CanadaCensusGlobalPlugin: transform:\n{}".format(e))


class CanadaCensusSummaryPlugin:
    """
    CanadaCensusSummaryPlugin

    This class houses the implemented hooks for the canada census plugins
    for processed Summary Count tables
    """
    @hookimpl
    def read_raw_data_into_pandas(cens_conv_inst):
        """
        _read_raw_data_into_pandas
        Private member that reads defines how the raw data is read into pandas
        data frame for the conversion

        Returns:
            returns the raw data table from the canadian census profile data

        NOTE: This is duplicating the globals as it has the same data, would
        be good to implement some sort of caching that would not need to do this
        """
        try:
            census_year = cens_conv_inst.input_params.input_params['census_year']
            low_res_geo = cens_conv_inst.input_params.input_params['census_low_res_geo_unit']
            high_res_geo = cens_conv_inst.input_params.input_params['census_high_res_geo_unit']
            profile_data_csv = cens_conv_inst.input_params.input_params['census_input_files']['profile_data_csv']
            pums_ds = cens_conv_inst.metadata_json

            # this class it is necessary to have the Global Tables initilized
            if cens_conv_inst.global_tables is None:
                raise TypeError("CanadaCensusSummaryPlugin requires global_tables to be defined in order to work")

            prof_iter = pd.read_csv(profile_data_csv,
                                    iterator=True,
                                    dtype={'GEO_CODE (POR)': str,
                                           'DIM: Profile of Census Tracts (2247)': str},
                                    chunksize=1000)
            raw_df = pd.concat([chunk[(chunk['GEO_CODE (POR)'].str.find(str(low_res_geo), 0) == 0)
                                      & (chunk['GEO_LEVEL'] == high_res_geo)
                                      & (chunk['CENSUS_YEAR'] == census_year)]
                                for chunk in prof_iter])
            return raw_df
        except Exception as e:
            raise SynthEcoError("CanadaCensusSummaryPlugin: read_raw_data_into_pandas\n{}".format(e))

    @hookimpl
    def transform(cens_conv_inst):
        try:
            fitting_vars = cens_conv_inst.input_params.input_params['census_fitting_vars']
            sum_tables = {}
            profile_df = cens_conv_inst.raw_data_df
            for var in fitting_vars:
                pums_ds = cens_conv_inst.metadata_json[var]

                # extract variables from profiles
                prof_var_df = profile_df[profile_df['Member ID: Profile of Census Tracts (2247)'].
                                         isin([int(x) for x in pums_ds['profile_hh_inds']])]
                prof_var_df = prof_var_df.reset_index()
                log("DEBUG", "prof_var_df {}|{}:".format(var, prof_var_df))

                # Create the table that aligns with the pums
                sum_df = prof_var_df[['GEO_CODE (POR)',
                                      'Member ID: Profile of Census Tracts (2247)',
                                      "DATA_QUALITY_FLAG",
                                      'Dim: Sex (3): Member ID: [1]: Total - Sex']].copy()

                sum_df = sum_df.rename(columns={'GEO_CODE (POR)': 'GEO_CODE',
                                                'Member ID: Profile of Census Tracts (2247)': "{}_ind".format(var),
                                                'Dim: Sex (3): Member ID: [1]: Total - Sex': 'total'})

                sum_df['total'] = pd.to_numeric(sum_df['total'],
                                                downcast='float',
                                                errors='coerce')
                log("DEBUG", "sum_df {}:\n{}".format(var, sum_df))
                # Replace categories of text with the index number from pums_data_structures
                profile_cats = pums_ds['profile_hh_cats']
                profile_inds = [int(x) for x in pums_ds['profile_hh_inds']]
                sum_df[var] = sum_df.apply(lambda row:
                                           profile_cats[profile_inds.index(row['{}_ind'.format(var)])][0],
                                           axis=1)

                sum_df = sum_df.drop(columns={'{}_ind'.format(var)})
                # scale the NaNs in left by the average value of the CMA and scaled down to the population in that area
                averages = sum_df.groupby(var)['total'].mean()

                # Capture case where all variables are 0, right now make them all even cause
                # I don't know what else to do with them
                sum_by_geo = sum_df.groupby('GEO_CODE').sum()
                sum_df['total'] = sum_df.apply(lambda x: 1.0 if sum_by_geo.loc[x['GEO_CODE']]['total'] == 0
                                               else x['total'], axis=1)
                log("DEBUG", "sum_df_2 {}:\n{}".format(var, sum_df))

                # Handle bad or obfuscated data values
                population_df = cens_conv_inst.global_tables.data['total_population_by_geo']
                for index, row in sum_df.iterrows():
                    pop = population_df.loc[row['GEO_CODE']]['total']
                    if pd.isnull(row['total']) or (row['total'] == 0.0
                                                   and str(row['DATA_QUALITY_FLAG']).find("9") == 0):
                        ave = averages.loc[row[var]]['total']
                        sum_df.loc[index, 'total'] = 0 if pop == 0 else ave/pop

                log("DEBUG", "sum_df_3 {}:\n{}".format(var, sum_df))
                log("DEBUG", "pums_ds {}:\n{} ".format(var, pums_ds))

                # Finally, we need align the summary table into the common categorical variables if needed
                if pums_ds['profile_type'] == "categorical" \
                    and "common_var_map" in pums_ds \
                        and pums_ds['common_var_map'] != {}:
                    log("DEBUG", "Aligning {} categories with PUMS".format(var))
                    common_var_map = pums_ds['common_var_map']
                    com_keys = common_var_map.keys()
                    sum_df = sum_df.reset_index()
                    sum_df = sum_df.rename(columns={'total': 'total_org'})
                    sum_df['total'] = [np.NaN for x in range(0, sum_df.shape[0])]
                    sum_df['total'] = sum_df.apply(lambda x:
                                                   sum_df[(sum_df['GEO_CODE'] == x['GEO_CODE']) &
                                                          (sum_df[var].
                                                           isin(common_var_map[str(x[var])]['profile_inds']))]
                                                         ['total_org'].sum()
                                                   if str(x[var]) in com_keys else np.NaN, axis=1)
                    sum_df = sum_df.dropna(axis=0) \
                                   .drop(columns=['total_org'])
                sum_df = sum_df.set_index('GEO_CODE')
                sum_df.name = "{} Summary Table".format(var)
                log("DEBUG", "sum_df_4 {}:\n{}".format(var, sum_df))
                sum_tables[var] = sum_df

            '''
            summary_geo_tables = {}
            nhouses_by_geo_df = cens_conv_inst.global_tables.data['number_households_by_geo']
            geos_of_interest = cens_conv_inst.global_tables.data['geos_of_interest']
            # Now we need to reorient the summary tables by geocode so that it prepared for fitting
            for geo_code in geos_of_interest:
                ### Extract area of interest from summary_tables
                summary_geo_tables[geo_code] = []
                ### Scale by the numer of households in this area
                n_houses = nhouses_by_geo_df.loc[geo_code,'total']

                for var in fitting_vars:
                    sum_t_df = sum_tables[var]
                    sum_t_df = sum_t_df.set_index('GEO_CODE')

                    sum_g_df = sum_t_df.loc[geo_code,].reset_index()\
                                                      .set_index([var])

                    sum_g_ser = sum_g_df['total']
                    sum_g_total = sum_g_ser.sum()
                    sum_g_ser = sum_g_ser.astype("float64")
                    sum_g_ser = sum_g_ser.apply(lambda x: 0 if sum_g_total == 0 else (x/sum_g_total)*n_houses)
                    sum_g_ser.name = "Summary Table for geo: {}".format(geo_code)
                    summary_geo_tables[geo_code].append(sum_g_ser)

            return summary_geo_tables
            '''
            return sum_tables
        except Exception as e:
            raise SynthEcoError("CanadaCensusSummaryPlugin: transform\n{}".format(e))


class CanadaCensusPUMSPlugin:
    """
    CanadaCensusPUMSPlugin

    This class houses the implemented hooks for the canada census plugins
    for processed PUMS Tables
    """
    @hookimpl
    def read_raw_data_into_pandas(cens_conv_inst):
        """
        read_raw_data_into_pandas
        Actually reads in raw data in csv format and saves as pandas df
        Input: A csv file holding all PUMS data called pums_h_csv
        Output: a pandas data frame with raw PUMS data matched to user-specified low res geo units (CMA)
                called raw_data_df
        """
        try:
            pums_h_csv = cens_conv_inst.input_params.input_params['census_input_files']['pums_h_csv']
            low_res_geo = cens_conv_inst.input_params.input_params['census_low_res_geo_unit']
            pums_iter = pd.read_csv(pums_h_csv,
                                    iterator=True,
                                    dtype={'CMA': str},
                                    chunksize=1000)

            raw_df = pd.concat([chunk[(chunk['CMA'].str.find(str(low_res_geo), 0) == 0)] for chunk in pums_iter])
            return raw_df
        except Exception as e:
            raise SynthEcoError("CanadaCensusPUMSPlugin: read_raw_data_into_pandas\n{}".format(e))

    @hookimpl
    def transform(cens_conv_inst):
        """
        transform
        Data transformations
        Input: Cleaned and pre-processed pandas df called processed_data_df
        Output: processed pums_freq_df as pandas df which is now in the correct format as a frequency table
        """
        try:
            fitting_variables = cens_conv_inst.input_params['census_fitting_vars']

            # draws from pums structure file for chosen variables and excludes pums type 'special'
            # (will be handled separately)
            processed_data_df = cens_conv_inst.raw_data_df[['HH_ID', 'EF_ID', 'CF_ID', 'PP_ID', 'CF_RP', 'WEIGHT'] +
                                                           [x for x in fitting_variables
                                                           if cens_conv_inst.metadata_json[x]['pums_type']
                                                           != "special"]]

            # selecting Census Family Rep 1 or 3 to represent household
            processed_data_df = processed_data_df[(processed_data_df['CF_RP'] != 2)]

            # removing NA
            processed_data_df = processed_data_df.dropna()
            # This is for pums continous and profile categorical
            for v in [x for x in fitting_variables if cens_conv_inst.metadata_json[x]['pums_type'] == "continuous"]:
                new_col_name = "{}_m".format(v)
                processed_data_df[new_col_name] = [np.NaN for x in range(0, processed_data_df.shape[0])]
                lookup = [(int(i), x['pums_inds'])
                          for i, x in cens_conv_inst.metadata_json[v]["common_var_map"].items()]
                for i, c in lookup:
                    upper = float(c[1])
                    lower = float(c[0])
                    processed_data_df.loc[(processed_data_df[v] >= lower) &
                                          (processed_data_df[v] <= upper), new_col_name] = i
            # This for pums categorical to profile categorical
            for v in [x for x in fitting_variables if cens_conv_inst.metadata_json[x]['pums_type'] == "categorical"]:
                # Since these are categories, we need to make sure that the names are strings
                processed_data_df = processed_data_df.astype({v: "str"})
                new_col_name = "{}_m".format(v)
                processed_data_df[new_col_name] = [np.NaN for x in range(0, processed_data_df.shape[0])]
                lookup = cens_conv_inst.metadata_json[v]["common_var_map"]
                for i, c in lookup.items():
                    processed_data_df.loc[(processed_data_df[v]).isin(c["pums_inds"]), new_col_name] = i
            # Handle Special Variables that have functions associated with them
            special_vars = [x for x in fitting_variables if cens_conv_inst.metadata_json[x]['pums_type'] == "special"]
            for v in special_vars:
                processed_data_df = CanadaCensusPUMSPlugin._special(processed_data_df, v)

            # Renaming columns
            processed_data_df = processed_data_df.rename(columns={x: "{}_V".format(x) for x in fitting_variables})
            processed_data_df = processed_data_df.rename(columns={"{}_m".format(x): x for x in fitting_variables})

            # another round of removing NA
            processed_data_df = processed_data_df.dropna()
            # create freq table by grouping by fitting var and calculating totals
            processed_data_df = processed_data_df.reset_index()
            pums_freq_df = processed_data_df.groupby(fitting_variables).size()
            pums_freq_df = pums_freq_df.reset_index() \
                                       .rename(columns={0: "total"})
            pums_freq_df['total'] = pums_freq_df['total'].astype(np.float64)

            pums_freq_df = pums_freq_df.astype({x: "int64" for x in fitting_variables})
            pums_freq_df = pums_freq_df.astype({x: "str" for x in fitting_variables})

            processed_data_df.name = "PUMS Data Categorical Representation"
            pums_freq_df.name = "PUMS Data Frequency Representation"
            cens_conv_inst.raw_data_df.name = "PUMS Data Raw Data"

            return {"raw_data": cens_conv_inst.raw_data_df,
                    "categorical_table": processed_data_df,
                    "frequency_table": pums_freq_df,
                    "separate": False}
        except Exception as e:
            SynthEcoError("CanadaCensusPUMSPlugin:transform\n{}".format(str(e)))

    # Special function for dealing with HHSIZE variables
    @staticmethod
    def _special(pums_df, var):
        """
        static private function that will hold the special function that need
        to be used for certain census variables that require additional processing
        """
        if var == "HHSIZE":
            new_col_name = "{}_m".format(var)
            hhsize = pums_df.groupby('HH_ID').size()
            pums_df['HHSIZE_m'] = pums_df.apply(lambda row: hhsize[row['HH_ID']]
                                                if hhsize[row['HH_ID']] <= 5
                                                else 5, axis=1)
        else:
            print("Variable {} is not a special variable")
            raise

        return pums_df


class CanadaCensusBorderPlugin:
    """

    """

    @hookimpl
    def read_raw_data_into_pandas(cens_conv_inst):
        """
        read_raw_data_into_pandas

        Retrieves relevant data from the Census API

        Returns:
        the raw data table from the Canadian Census data
        """
        try:
            ip = cens_conv_inst.input_params
            border_file = ip['census_input_files']['border_gml']

            return gpd.read_file(border_file).to_crs("WGS 84")

        except Exception as e:
            raise SynthEcoError(f"CanadaCensusBorder.read raw data error: \n{e}")

    @hookimpl
    def transform(cens_conv_inst):
        """
        transform

        Formats the raw data into processed Border tables

        Returns:
            an updated dataframe to be set to processed_data_df
        """

        try:
            processed_df = cens_conv_inst.raw_data_df.rename(columns={'CTUID': 'GEO_UNIT'}).astype({'GEO_UNIT': 'str'})
            processed_df['GEO_UNIT_P'] = processed_df.apply(lambda row: f"{row['GEO_UNIT']}0"
                                                            if "." in row['GEO_UNIT'][-2]
                                                            else row['GEO_UNIT'], axis=1)
            processed_df = processed_df.drop(columns=['GEO_UNIT']).rename(columns={'GEO_UNIT_P': 'GEO_UNIT'})
            return processed_df
        except Exception as e:
            raise SynthEcoError(f"CanadaCensusBorder.transform error: \n{e}")
