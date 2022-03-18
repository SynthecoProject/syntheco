# TO DO: match year and region with profile df
# TO DO: handle VARIABLE NAMES / VALUES WITH SPECIAL CHARACTERS in overarching function


# IPF needs: PUMS table representing frquency for each value combination of each fitting variable


"""
Canada PUMS converter

Class converting Canadian PUMS data into IPF readable pandas df
The df will be a frequency table for each value combination of each fitting variable
"""
#%%
import pandas as pd
from converters.converter_base import ConverterBase
#%%
# Creates PUMS data structure file as dict object
pums_data_structures = {
			# AGE
			"AGEGRP":{"longname":"age",
                                  "definition":"Age in completed years.",
                                  "universe":"Persons in private household",
                                  "pums_type":"categorical",
                                  "profile_type":"categorical",
                                  "sample_type":"ordinal",
                                  "values":{1:"0 to 9 years", 2:"10 to 14 years",
                                            3:"15 to 19 years", 4:"20 to 24 years", 
                                            5:"25 to 29 years", 6:"30 to 34 years", 
                                            7:"35 to 39 years", 8:"40 to 44 years", 
                                            9:"45 to 49 years", 10:"50 to 54 years",
                                            11:"55 to 64 years", 12:"65 to 74 years", 
                                            13:"75 years and over",88:"Not available"},
                                  "profile_hh_cats":[(1,"15 to 24 years"),
                                                    (2,"25 to 34 years"),
                                                    (3,"35 to 44 years"),
                                                    (4,"45 to 54 years"),
                                                    (5,"55 to 64 years"),
                                                    (6,"65 to 74 years"),
                                                    (7,"75 to 84 years"),
                                                    (8,"85 years and over")],
                                  "profile_hh_inds": [1659,1660,1661,1662,1663,1664,1665,1666],
                                  "common_var_map":{
                                      1:{"name":"15 to 24 years",
                                         "pums_inds": [3,4],
                                         "profile_inds":[1]},
                                      2:{"name":"25 to 34 years",
                                         "pums_inds": [5,6],
                                          "profile_inds":[2]},
                                      3:{"name":"35 to 44 years",
                                         "pums_inds": [7,8],
                                         "profile_inds":[3]},
                                      4:{"name":"45 to 54 years",
                                         "pums_inds": [9,10],
                                         "profile_inds":[4]},
                                      5:{"name":"55 to 64 years",
                                         "pums_inds": [11],
                                         "profile_inds":[5]},
                                      6:{"name":"65 to 74 years",
                                         "pums_inds": [12],
                                          "profile_inds":[6]},
                                      7:{"name":"75 years and over",
                                         "pums_inds": [13],
                                          "profile_inds":[7,8]}
                                  },
                                 },
			# education = HDGREE 
            	"HDGREE":{"longname":"Education: Highest certificate, diploma or degree",
                                  "definition":"Derived value from list of degrees achieved",
                                  "universe":"Population aged 15 years and over in private households",
                                  "pums_type":"categorical",
                                  "profile_type":"categorical",
                                  "sample_type":"categorical",
                                  "values":{1:"No certificate, diploma or degree", 
                                            2:"High school diploma or equivalent",
                                            3:"Trades certificate or diploma (other than apprenciteship)",
                                            4:"Registered Apprenciteship certificate",
                                            5:"College, CEGEP or other non-university certificate or diploma",
                                            6:"University certificate or diploma below bachelor level",
                                            7:"Bachelor's degree",
                                            8:"University certificate, diploma or degree above bachelor level",
                                            88:"Not available",
                                            99:"Not applicable"},
                                  "profile_hh_cats":[(1,"No certificate, diploma or degree"),
                                                    (2,"Secondary (high) school diploma or equivalency certificate"),
                                                    (3,"Postsecondary certificate, diploma or degree"),
                                                    (4,"College, CEGEP or other non-university certificate or diploma"),
                                                    (5,"University certificate or diploma below bachelor level"),
                                                    (6,"University certificate, diploma or degree at bachelor level or above")],
                                  "profile_hh_inds": [1684,1685,1686,1690,1691,1692],
                                  "common_var_map":{
                                      1:{"name":"No certificate, diploma or degree",
                                         "pums_inds": [1],
                                         "profile_inds":[1]},
                                      2:{"name":"High school diploma or equivalent",
                                         "pums_inds": [2],
                                          "profile_inds":[2]},
                                      3:{"name":"Trades certificate or diploma and apprenticeship",
                                         "pums_inds": [3,4],
                                         "profile_inds":[3]},
                                      4:{"name":"College, CEGEP or other non-university certificate or diploma",
                                         "pums_inds": [5],
                                         "profile_inds":[4]},
                                      5:{"name":"University certificate or diploma below bachelor level",
                                         "pums_inds": [6],
                                         "profile_inds":[5]},
                                      6:{"name":"University certificate, diploma or degree at bachelor level or above",
                                         "pums_inds": [7,8],
                                          "profile_inds":[6]}
                                  },
                                 },
			# marital status = MARSTH
            	"MARSTH":{"longname":"Marital status",
                                  "definition":"Refers to whether or not a person is living in a common-law" 
                                  "union as well as the legal marital status of those who are not living in a common-law union." 
                                  "All persons aged less than 15 are considered as never married and not living" 
                                  "common law.",
                                  "universe":"Population aged 15 years and over in private households",
                                  "pums_type":"categorical",
                                  "profile_type":"categorical",
                                  "sample_type":"categorical",
                                  "values":{1:"Never legally married (and not living common law)", 
                                            2:"Legally married (and not separated)",
                                            3:"Living common law",
                                            4:"Separated (and not living common law)",
                                            5:"Divorced (and not living common law)",
                                            6:"Widowed (and not living common law)"},
                                  "profile_hh_cats":[(1,"Married"),
                                                    (2,"Living common law"),
                                                    (3,"Never married"),
                                                    (4,"Separated"),
                                                    (5,"Divorced"),
                                                    (6,"Widowed")],
                                  "profile_hh_inds": [61,62,64,65,66,67],
                                  "common_var_map":{
                                      1:{"name":"Never married and not living common law",
                                         "pums_inds": [1],
                                         "profile_inds":[3]},
                                      2:{"name":"Legally married",
                                         "pums_inds": [2],
                                          "profile_inds":[1]},
                                      3:{"name":"Living common law",
                                         "pums_inds": [3],
                                         "profile_inds":[2]},
                                      4:{"name":"Separated",
                                         "pums_inds": [4],
                                         "profile_inds":[4]},
                                      5:{"name":"Divorced",
                                         "pums_inds": [5],
                                         "profile_inds":[5]},
                                      6:{"name":"Widowed",
                                         "pums_inds": [6],
                                          "profile_inds":[6]}
                                  },
                                 },			
			# household size = HHSIZE
              "HHSIZE":{"longname":"Number of Persons in Private Household",
                                  "definition":"",
                                  "pums_type":"special",
                                  "profile_type":"categorical",
                                  "sample_type":"ordinal",
                                  "universe":"Persons in private housholds",
                                  "profile_hh_cats":[(1,"1 person"),
                                                     (2,"2 persons"),
                                                     (3,"3 persons"),
                                                     (4,"4 persons"),
                                                     (5,"5 or more persons")],
                                  
                                  "profile_hh_inds":[52, 53, 54, 55, 56],
                              "profile_hh_map":[]
                        },
			# income = TOTINC
              "TOTINC":{"longname":"Income: Total income",
                                  "definition":"Total income groups for the population aged 15 years and over in private households",
                                  "pums_type":"continuous",
                                  "profile_type":"categorical",
                                  "sample_type":"ordinal",
                                  "universe":"Population aged 15 years and over in private households",
                                  "profile_hh_cats":[(1,"Under $10,000 (including loss)"),
                                                     (2,"10,000 to 19,999"),
                                                     (3,"20,000 to 29,999"),                                                      
                                                     (4,"30,000 to 39,999"),
                                                     (5,"40,000 to 49,999"),
                                                     (6,"50,000 to 59,999"),
                                                     (7,"60,000 to 69,999"),
                                                     (8,"70,000 to 79,999"),
                                                     (9,"80,000 to 89,999"),
                                                     (10,"90,000 to 99,999"),
                                                     (11,"100,000 to 149,999"),
                                                     (12,"$150,000 and over")],
                                  "profile_hh_inds":[695, 696, 697, 698, 699, 700, 701, 702, 703, 704, 706,707],
                                  "common_var_map":{
                                                   1:{"name":"Under $10,000 (including loss)",
                                                      "pums_inds": [-99999999,9999],
                                                      "profile_inds":[1]},
                                                   2:{"name":"10,000 to 19,999",
                                                      "pums_inds": [10000,19999],
                                                      "profile_inds":[2]},
                                                   3:{"name":"20,000 to 29,999",
                                                      "pums_inds": [20000,29999],
                                                      "profile_inds":[3]},
                                                   4:{"name":"30,000 to 39,999",
                                                      "pums_inds":[30000,39999],
                                                      "profile_inds": [4]},
                                                   5:{"name":"40,000 to 49,999",
                                                      "pums_inds":[40000,49999],
                                                      "profile_inds": [5]},
                                                   6:{"name":"50,000 to 59,999",
                                                      "pums_inds":[50000,59999],
                                                      "profile_inds": [6]},
                                                   7:{"name":"60,000 to 69,999",
                                                      "pums_inds":[60000,69999],
                                                      "profile_inds": [7]},
                                                   8:{"name":"70,000 to 79,999",
                                                      "pums_inds":[70000,79999],
                                                      "profile_inds": [8]},
                                                   9:{"name":"80,000 to 89,999",
                                                      "pums_inds":[80000,89999],
                                                      "profile_inds": [9]},
                                                  10:{"name":"90,000 to 99,999",
                                                      "pums_inds":[90000,99999],
                                                      "profile_inds": [10]},
                                                  11:{"name":"100,000 to 149,999",
                                                      "pums_inds":[100000,149999],
                                                      "profile_inds": [11]},
                                                  12:{"name":"150,000 and over",
                                                      "pums_inds":[150000,99999999999],
                                                      "profile_inds": [12]}
                                  }       
                        }
                                      }

#%%
_required_files = ['pums_h_csv']

class CanadaCensusPUMSConverter(ConverterBase):
	""" 
	CanadaCensusPUMSConverter is a class converting Canadian PUMS data into data table that can be handled by IPF procedure
	Input: pums_h_csv as raw csv file
	Output: pums_freq_df as pre-processed pandas data frame
	"""


	def __init__(self, input_):
	""" 
	Creates necessary functions and objects
	"""
        super().__init__(input_)
        self.census_year = input_.input_params['census_year']
        self.cma = input_.input_params['census_low_res_geo_unit']
        self.pums_data_csv = input_.input_params['census_input_files']['pums_h_csv']
        #self.pums_structures = input_.input_params['census_input_files']['pums_structures.json'] currently being created above
        self.raw_data_df = self._read_raw_data_into_pandas()
        self.processed_data_df = pd.DataFrame()

	def _read_raw_data_into_pandas(self):
	"""
	read_raw_data_into_pandas     
	Actually reads in raw data in csv format and saves as pandas df
	Input: A csv file holding all PUMS data called pums_h_csv
	Output: a pandas data frame with raw PUMS data matched to user-specified low res geo units (CMA) called raw_data_df
	"""

		pums_iter = pd.read_csv(self.pums_h_csv,
                                 	iterator = True,
                                 	dtype = {'CMA':str},
                                 	chunksize = 1000)

        	return pd.concat([chunk[(chunk['CMA'].str.find(self.cma) == 0)]
                          	for chunk in pums_iter])

        # Census year selection? 

	def pre_transform_clean_data(self):
	"""
	pre_transform_clean_data
	Does data cleaning before the data is being transformed to the right format
	Input: pandas df with raw PUMS data called raw_data_df
	Output: pandas df with raw PUMS data which has been cleaned from missing values called processed_data_df
	"""
    
        # draws from pums structure file for chosen variables and excludes pums type 'special' (will be handled separately)
        processed_data_df = raw_data_df[['HH_ID','EF_ID','CF_ID','PP_ID', 'CF_RP', 'WEIGHT'] + \
                                [x for x in fitting_vars if pums_data_structures[x]['pums_type'] != "special"]]
    
        # selecting Census Family Rep 1 or 3 to represent household
        self.processed_data_df = self.raw_data_df[(self.raw_data_df['CF_RP'] != 2)]
    
        # removing NA
        processed_data_df = processed_data_df.dropna()
    
        return TRUE


	def transform(self):
	"""
	transform	
	Data transformations
	Input: Cleaned and pre-processed pandas df called processed_data_df
	Output: processed pums_freq_df as pandas df which is now in the correct format as a frequency table
	"""
    
        # calculate household size and add as new col
        new_col_name = "HHSIZE_m"
        hhsize = self.processed_data_df.groupby('HH_ID').size()
        processed_data_df['HHSIZE_m'] = processed_data_df.apply(lambda row: hhsize[row['HH_ID']] 
                                                        if hhsize[row['HH_ID']] <=5 
                                                        else 5, axis=1)

        ### Renaming columns 
        processed_data_df = processed_data_df.rename(columns = {x:"{}_V".format(x) for x in fitting_vars})
        processed_data_df = processed_data_df.rename(columns = {"{}_m".format(x):x for x in fitting_vars})
    
        # another round of removing NA
        processed_data_df = processed_data_df.dropna()
    
        # create freq table by grouping by fitting var and calculating totals
        processed_data_df = processed_data_df.reset_index()
        pums_freq_df = processed_data_df.groupby(fitting_vars).size()
        pums_freq_df = pums_freq_df.reset_index() \
                           .rename(columns={0:"total"})
        pums_freq_df['total'] = pums_freq_df['total'].astype(np.float64)

        pums_freq_df = pums_freq_df.astype({x:"int64" for x in fitting_vars})
        
    
        return TRUE
    
#%%    

