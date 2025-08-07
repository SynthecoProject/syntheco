"""
ipf_census_fitting

This is the implementation of IPF for fitting census data
"""

import pandas as pd
import numpy as np
from ipfn import ipfn
from syntheco.census_fitting_procedures import hookimpl
from syntheco.logger import log, data_log
from syntheco.error import SynthEcoError
from syntheco.util import random_round_to_integer
import random as rn
import multiprocessing as mp
import time
import pickle as pkl


class IPFCensusHouseholdFittingProcedure:
    """
    IPFCensusFittingProcedure

    This class houses the implemented hooks for the iterative proportional
    fitting procedure for census fitting
    """

    @hookimpl
    def perform_fitting(fit_proc_inst):
        """
        perform_fitting

        Function that performs the IPF fitting, the data must be prepared before
        calling this function

        Arguments:
            fit_proc_inst: instance of the plugin class

        geo_code: the code fo the geographic unit that you want to fit
        summary_tables: marginal tables for the geographic area corresponding to geo_code
                        There will be one marginal series per the fitting variables
        pums_freq: This is the pums table modified to represent the frequency of each
                   combination of the values for the fitting variables

        fitting_vars: the variable that are being used for marginal tables
                      (TODO: Make this nomenclature consistent)

        n_houses: the number of houses in the geographic area corresponding to geo_code

        returns a pandas dataFrame that provides the results of the IPF procedure
        """
        log("INFO", "--IPF--: Beginning Iterative Proportional Fitting Procedure")
        log("INFO", f"--IPF--: Running in Parallel with {fit_proc_inst.input_params['parallel_num_cores']}")
        try:
            # IPF Specific input parameters
            max_iterations = fit_proc_inst.input_params["ipf_max_iterations"]
            fail_on_nonconvergence = fit_proc_inst.input_params["ipf_fail_on_nonconvergence"]
            convergence_rate = fit_proc_inst.input_params["ipf_convergence_rate"]
            rate_tolerance = fit_proc_inst.input_params["ipf_rate_tolerance"]

            # SynthEco Params
            fitting_vars = fit_proc_inst.input_params["census_fitting_vars"]
            geo_codes_of_interest = fit_proc_inst.global_tables.data['geos_of_interest']
            num_houses = fit_proc_inst.global_tables.data['number_households_by_geo']
            summary_tables = fit_proc_inst.summary_tables.data
            pums_freq_org = fit_proc_inst.pums_tables.data['frequency_table']
            pums_hier = fit_proc_inst.pums_tables.data['categorical_table']
            metadata_json = fit_proc_inst.global_tables.data['census_variable_metadata']
            alpha = fit_proc_inst.input_params['ipf_alpha']
            K = fit_proc_inst.input_params['ipf_k']

            fit_res = {}
            unconverged_geos = []
            fitting_arg_list = []

            for geo_code in geo_codes_of_interest:
                log("DEBUG", f"--IPF--: Beginning processing for geo_code {geo_code}")
                n_houses = num_houses.loc[geo_code, 'total']
                summary_geo_tables = []
                pums_freq = pums_freq_org.copy(deep=True)
                # Extract the geo_code information from summary Tables
                for var in fitting_vars:
                    log("DEBUG", f"--IPF--: Transforming {geo_code} {var}")
                    sum_t_df = summary_tables[var]
                    # sum_t_df = sum_t_df.set_index('GEO_CODE')

                    sum_g_df = sum_t_df.loc[geo_code, ].reset_index().set_index([var])

                    sum_g_ser = sum_g_df['total']
                    sum_g_total = sum_g_ser.sum()
                    sum_g_ser = sum_g_ser.astype("float64")
                    sum_g_ser = sum_g_ser.apply(lambda x: 0 if sum_g_total == 0 else round((x/sum_g_total)*n_houses, 0))
                    summary_geo_tables.append(sum_g_ser)

                # set up a list with all of the function calls that need to be made to the fitting procedure
                fitting_arg_list.append([geo_code, summary_geo_tables, pums_freq, fitting_vars, n_houses,
                                         max_iterations, convergence_rate, rate_tolerance])
            # Parallel execution
            arg_list = [tuple(x) for x in fitting_arg_list]
            with mp.Pool(fit_proc_inst.input_params["parallel_num_cores"]) as pool:
                results_p = pool.map(IPFCensusHouseholdFittingProcedure._perform_fitting_for_geocode_helper, arg_list)

            results = {}
            for x in results_p:
                results[x[0]] = (x[1], x[2])

            # Post process checking
            unconverged_geocodes = []
            post_results = {}
            for g, r in results.items():
                if r[0] == 0:
                    unconverged_geocodes.append(g)
                post_results[g] = r[1]

            if len(unconverged_geocodes) > 0:
                log("INFO", f"--IPF--: The following geo_codes did not converge\n{unconverged_geocodes}")
                if fit_proc_inst.input_params['ipf_fail_on_nonconvergence']:
                    raise SynthEcoError("--IPF--: There were unconverged geographic areas")
            else:
                log("INFO", "--IPF--: All Geographic Areas Converged")
            t1s = time.time()
            s_argList = []

            for g, f_dict in post_results.items():
                s_argList.append([pums_hier, f_dict, g, fitting_vars, metadata_json, alpha, K])

            arg_list = [tuple(x) for x in s_argList]
            with mp.Pool(fit_proc_inst.input_params["parallel_num_cores"]) as pool:
                results_p = pool.map(IPFCensusHouseholdFittingProcedure._select_households_helper, arg_list)

            sample_results = {}
            for g, x in results_p:
                sample_results[g] = x
            t2s = time.time()
            t1 = time.time()
            # TODO: Move to Main
            num_cores = fit_proc_inst.input_params["parallel_num_cores"]

            new_pums_table = fit_proc_inst.pums_tables.create_new_pums_table_from_household_ids(sample_results)

            t2 = time.time()

            log("INFO", "time to sample {}".format(t2s - t1s))
            log("INFO", "time to create: {}".format(t2 - t1))

            return {"Sample Results": sample_results,
                    "Derived PUMS": new_pums_table}

        except Exception as e:
            raise SynthEcoError("{}".format(e))

    @staticmethod
    def _perform_fitting_for_geocode_helper(args):
        '''
        perform_fitting_for_geocode_helper
        Helper function for parallel execution of the fitting procedure

        args: pass through of the args for the real fucntion
        '''
        return IPFCensusHouseholdFittingProcedure._perform_fitting_for_geocode(*args)

    @staticmethod
    def _perform_fitting_for_geocode(geo_code, summary_geo_tables, pums_freq,
                                     fitting_vars, n_houses, max_iterations,
                                     convergence_rate, rate_tolerance):

        log("INFO", "--IPF--: Starting IPF for {}".format(geo_code))
        IPF = ipfn.ipfn(pums_freq, summary_geo_tables, [[x] for x in fitting_vars],
                        max_iteration=max_iterations,
                        convergence_rate=convergence_rate,
                        rate_tolerance=rate_tolerance, verbose=2)
        results = IPF.iteration()
        log("INFO", "--IPF--: Successfully converged IPF for {}".format(geo_code))

        # results tuple: 0 results; 1 (0 if failed to converge 1 if success);
        # 2 is the convergence at each iteration.
        if results[1] == 0:
            log("DEBUG", "--IPF--: -----------------------------------------------------------------")
            log("INFO", f"--IPF--: Geocode {geo_code} NOT CONVERGED")
            log("DEBUG", f"--IPF--: Variables: \npums_freq\n{pums_freq}\nsumary\n{summary_geo_tables}")
            log("DEBUG", f"--IPF--: Results = {results}")
            log("DEBUG", "--IPF--: -----------------------------------------------------------------")
        else:
            log("INFO", f"--IPF--: Geocode {geo_code} converged in {len(results[2])} iterations")

            # Round the floating point answers to integers (will still be floats)
            results_rounded = results[0].copy()
            results_rounded['total'] = results_rounded['total'].apply(lambda x: random_round_to_integer(x))

            # elminate the zero entries as they are not important anymore
            results_rounded = results_rounded[results_rounded['total'] != 0]

            log("DEBUG", "--IPF--: GEO_CODE: {} SUM: {} NHOUSES: {}".format(geo_code,
                                                                            results_rounded['total'].sum(),
                                                                            n_houses))
            '''
            This is necessary because if the random rounding eliminates all of the houses in
            a geographic area, we need to do something different.
            it means that non of the frequencies are above one, so I will assign 1 to the
            n_house highest answers rather than round
            '''
            previous_sum = -100000.00
            if results_rounded['total'].sum() == 0:
                # If the IPF results in zero (which can happen when there is very
                # few houses in the area) set the highest fractional answer to 1.0
                results_rounded = results[0].nlargest(int(n_houses), 'total')
                results_rounded['total'] = results_rounded['total'].apply(lambda x: 1.0)
            else:
                # This part ensures that the number of houses in the fitting is consitent
                # basically if the sum of the results is higher or lower than the number
                # of households in an area, increment or decrement randomly till we they
                # are the same
                while results_rounded['total'].sum() < n_houses:
                    current_sum = results_rounded['total'].sum()
                    if current_sum == previous_sum:
                        raise SynthEcoError("--IPF--: There was a problem in IPF rounding" +
                                            " procedure for {}".format(geo_code))
                    random_hh = rn.randint(0, results_rounded.shape[0]-1)
                    results_rounded.loc[results_rounded.index[random_hh], 'total'] = \
                        results_rounded.loc[results_rounded.index[random_hh], 'total'] + 1
                    previous_sum = current_sum
                while results_rounded['total'].sum() > n_houses:
                    current_sum = results_rounded['total'].sum()
                    if current_sum == previous_sum:
                        raise SynthEcoError("--IPF--: There was a problem in IPF rounding" +
                                            " procedure for {}".format(geo_code))
                    random_hh = rn.randint(0, results_rounded.shape[0]-1)
                    results_rounded.loc[results_rounded.index[random_hh], 'total'] = \
                        results_rounded.loc[results_rounded.index[random_hh], 'total'] - 1
                    results_rounded = results_rounded[results_rounded['total'] != 0]
                    previous_sum = current_sum

            # We don't need no stinking zeros
            results_rounded = results_rounded[results_rounded['total'] != 0]
            log("DEBUG", "--IPF--: FINAL RESULTS: GEO_CODE: " +
                         " {} SUM: {} NHOUSES: {}".format(geo_code,
                                                          results_rounded['total'].sum(),
                                                          n_houses))
            return (geo_code, results[1], results_rounded)

    @staticmethod
    def calculate_ordinal_distance(pums_val, tab_val, r, k):
        '''
        calculate_ordinal_distance

        calculates the distance between two variables if the range is ordinal
        i.e. the range has some progression and is not "categorical", such as it is a size, or an age range

        pums_val: the value of the fitted variable from pums
        tab_val: the summary table value
        r:  distance parameter
        k: fitting constant

        Returns:
            ordinal distance between the pums_val and tab_val
        '''
        return 1-abs((pums_val - tab_val)/r)**k

    @staticmethod
    def calculate_categorical_distance(pums_val, tab_val, alpha):
        '''
        Document
        '''
        return alpha if pums_val == tab_val else 1.0-alpha

    @staticmethod
    def _select_households(pums, fit_table, geo_code, fitting_vars,
                           metadata_json, alpha=0.0, k=0.001):
        try:
            t1 = time.time()
            log("INFO", "Running select households {}".format(geo_code))
            mat_array = np.array([1.0 for i in range(0, fit_table.shape[0]*pums.shape[0])])
            distance_matrix = mat_array.reshape(fit_table.shape[0], pums.shape[0])
            c_o_d = IPFCensusHouseholdFittingProcedure.calculate_ordinal_distance
            c_c_d = IPFCensusHouseholdFittingProcedure.calculate_categorical_distance
            for var in fitting_vars:
                pums_ds = metadata_json[var]
                table_values = fit_table[var]
                table_values = table_values.astype(float)
                pums_values = pums[var]
                pums_values = pums_values.astype(float)
                # r is the difference between the maximum and minimum value of the fitting var
                if pums_ds['sample_type'] == "ordinal":
                    r = int(pums_values.max()) - int(pums_values.min())
                    for i in range(0, distance_matrix.shape[0]):
                        table_value = table_values[table_values.index[i]]
                        distance_tmp = np.array([c_o_d(x, table_value, r, k) for x in list(pums_values)])
                    distance_matrix[i] = distance_matrix[i] * distance_tmp
                else:
                    for i in range(0, distance_matrix.shape[0]):
                        table_value = table_values[table_values.index[i]]
                        distance_tmp = np.array([c_c_d(x, table_value, 0.0) for x in list(pums_values)])
                        distance_matrix[i] = distance_matrix[i] * distance_tmp

            distance_sums = distance_matrix.sum(axis=1)
            prob_matrix = np.apply_along_axis(lambda x: x/distance_sums, 0, distance_matrix)
            t2 = time.time()
            t11 = time.time()
            sample_inds = []
            for i in range(0, fit_table.shape[0]):
                t_i = list(fit_table.index)[i]
                n_samples = int(fit_table.loc[t_i, 'total'])
                prob_row = prob_matrix[i]
                if (prob_row < 0).any():
                    log("WARNING", "There are zeros in the probablility row for geocode " +
                        "{} row {} which could produce erroneous results".format(geo_code, i))
                if (np.isinf(prob_row)).any():
                    log("WARNING", "There are infinities in the probablility row for geocode " +
                        "{} row {}which could produce erroneous results".format(geo_code, i))
                inds_samp = pd.Series(pums.index)
                sample_inds = sample_inds + list(inds_samp.sample(n_samples, replace=True, weights=prob_row))

            t12 = time.time()
            log("INFO", "For Geocode {}, times are {}, {}".format(geo_code, t2-t1, t12-t11))

            return (geo_code, sample_inds)
        except Exception as e:
            SynthEcoError("There was a problem in parallel select_housholds:\n{}".format(e))

    @staticmethod
    def _select_households_helper(args):
        return IPFCensusHouseholdFittingProcedure._select_households(*args)
