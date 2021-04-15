from gssutils import *
import os
import pandas as pd
import Levenshtein as lev
import numpy as np
import re
from fuzzywuzzy import fuzz
from IPython.display import display

# =======================================================
# This code follows the KISS methodology. If it works its fine, leave it alone!
# =======================================================
# Global variable declaration
output_folder = "-codelist-analysis"
exnot = 'csv-metadata' # This is the type of file you don't want to look into
long_dotted_line = "=================================================================================="
# =======================================================

def search_codelists_for_codes(codes, pth, colnme, dimension):
    """
    CHECK IF ANY OF YOUR DIMENSION VALUES (CODES) ARE ALREADY DEFINED IN A CODELIST(S)
    This method searches through a directory of codelist csv files looking for instances of each value within the passed unique list (codes).
    It records in what file it finds the instance and outputs a csv file with a list of the codes, the file it found it in and the number of times it was found.
    It also outputs a csv file giving the percentage split between the files where codes were found.
    Once the search has completed it creates a folder called {dimension}-codelist-analysis within your current directory and saves files called:
         1. {dimension}-code-search.csv (Columns = Code, Filename, Count)
         2. {dimension}-percentage-split.csv (Columns = Filename, Codes Looking For, Codes Found, Percentage)
    Method assumes directory only has files with extensions .csv and .csv-metadata.json.
    This methods takes as its arguments:
        codes: A list of unique values taken from a datasets column within a transform
        pth: This is the path to the codelists you want to search through
        colnme: This is the column within each codelist to want to search through
        dimension: This is the name of the dimension for naming output files
    """
    try:
        codes = list(set(codes))
        
        print('Search Directory: ' + pth + '\n')
        print('Dimension: ' + dimension)
        print(long_dotted_line)
        
        dimension = dimension.lower().replace(' ', '-') # Remove stuff from dimension (if any) so the filename is nice and lovely
        dimension = re.sub('[^A-Za-z0-9]+', '',  dimension)
        
        entries = os.listdir(pth)     

        output = pd.DataFrame(columns=['Code','Filename'])
        for e in entries:
            try:
                if exnot not in e:
                    df = pd.read_csv(pth + e)
                    f = df.loc[df[colnme].isin(codes)]
                    if f[colnme].count() > 0:
                        fnd = pd.DataFrame(f[colnme])
                        fnd['Code'] = fnd[colnme]
                        del fnd[colnme]
                        fnd['Filename'] = e
                        output = pd.concat([output,fnd])
            except Exception as x:
                # Ignore directory errors
                if 'Is a directory:' not in str(x):
                    print('---- Loop Error: ' + str(x) + ' - in file: ' + str(e))

        if (output.shape[0] > 0):
            out = dimension + output_folder
            if not os.path.exists(out):
                os.mkdir(out)

            output = output.sort_values(by=['Code'])
            unq = output.groupby('Code').count()
            output = pd.merge(output, unq, on='Code')
            output = output.rename(columns={'Filename_x': 'Filename', 'Filename_y': 'Count'})
            rowCount = output['Filename'].count()
            output_filename = '-codelist-folder-search.csv'
            print(long_dotted_line)
            print('Outputting File: ' + f'{dimension}{output_filename} with {rowCount} rows')
            print('In Folder: ' + out)
            print(long_dotted_line)
            output.to_csv(f'{out}/{dimension}{output_filename}', index=False)
        
            filenamecount = pd.DataFrame(output['Filename'])
            filenamecount = filenamecount.groupby(['Filename']).size().reset_index(name='Codes Found')
            filenamecount['Total Codes'] = len(codes)
            #filenamecount['Percentage'] = ((filenamecount['Counts'] / filenamecount.Counts.sum()) * 100).round(2)
            filenamecount['Percentage Found'] = ((filenamecount['Codes Found'] / filenamecount['Total Codes']) * 100).round(2)
            filenamecount = filenamecount.sort_values(by=['Percentage Found'], ascending=False)
            #filenamecount = filenamecount.rename(columns={'Counts':'Codes Found'})
            try:
                highest_scoring_codelist_file = pd.DataFrame(filenamecount['Filename'][filenamecount['Percentage Found']==filenamecount['Percentage Found'].max()])
                highest_scoring_codelist_file = str(filenamecount.iloc[0,0])
            except:
                highest_scoring_codelist_file = ''

            output_filename = "-codelist-folder-search-percentage-split.csv"
            print('Outputting File: ' + f'{dimension}{output_filename} with {rowCount} rows')
            print('In Folder: ' + out)
            print(long_dotted_line)
            filenamecount.to_csv(f'{out}/{dimension}{output_filename}', index=False)
        else:
            print('No codes have been found during search.')
            highest_scoring_codelist_file = ''
        return highest_scoring_codelist_file
    except Exception as e:
        print(e)
        return ''


def search_for_codes_using_levenshtein_and_fuzzywuzzy(codes, pth, colnme, dimension, setDistance, setRatio):
    """
    Use Levenshtein and FuzzyWuzzy packages to fuzzy match codes with all codelists within a directory. Only output results based on values passed in setDistance and setRatio
    This method searches through a directory of codelist csv files comparing each code within the a codelists the each of the passed code values.
    It records in what file it finds the instance and outputs a csv file with a list of the codes, the file it found it in and the number of times it was found.
    It also outputs a csv file giving the percentage split between the files where codes were found.
    Once the search has completed it creates a folder called {dimension}-codelist-levenshtein-fuzzy within your current directory and creates a file called:
         1. {dimension}-dimension-levenshtein-fuzzy.csv (Columns = Source Code, Codelist Code, Filename, Distance, Ratio, Token Sort Ratio, Token Set Ratio, Partial Ratio)
    Method assumes directory only has files with extensions .csv and .csv-metadata.json.
    This methods takes as its arguments:
        codes: A list of unique values taken from a datasets column within a transform
        pth: This is the path to the codelists you want to search through
        colnme: This is the column within each codelist to want to search through
        dimension: This is the name of the dimension for naming output files
        setDistance: How many changes have to be made to the codelist code so it matches the source code (set as 'less than or equal to' (<=)) . I use a value of 3
        setRatio: What ratio of similarity should the match attain (set to 'more than or equal to' in the code (>=)). I use a value of 0.7 or 0.8
    
    Output Results
        Distance:
            Represents how many edits you would have to make to the codelist string to match it to the compared code string, also includes lower and upper case changes
        Ratio:
            This represents how similar the strings are to each other
        Token Sort Ratio:
            This represents how similar both strings are when they are changed to lowercase, punctuation has been removed and remaining characters sorted alphabetically  
        Token Set Ratio:
            Can be used to see if differing strings have the same meaning
        Partial Ratio:
            This represents if both codes have any matching substrings
    """
    try:
        dimension = dimension.lower().replace(' ', '-') # Remove stuff from dimension (if any) so the filename is nice and lovely
        dimension = re.sub('[^A-Za-z0-9]+', '',  dimension)
        setRatioPerc = setRatio * 100 # setRation should be less than or equal to 1 for Levenshtein Ratios but needs to be between 0 and 100 for FuzzyWuzzy results comparison
        
        print(long_dotted_line)
        print('Searching in Codelist Directory: ' + pth)
        print('in Column: ' + colnme)
        print('Levenshtein Distance set to : ' + str(setDistance))
        print('Levenshtein Ratio set to : ' + str(setRatio))
        print('FuzzyWuzzy Ratio set to : ' + str(setRatioPerc))
        print(long_dotted_line)
        # get the list of files in the directory
        entries = os.listdir(pth)     
        
        output = []
        for e in entries:
            try:
                if exnot not in e:
                    df = pd.read_csv(pth + e)
                    df = list(df[colnme])
                    for l in df:
                        for c in codes:
                            sc = str(c)
                            cc = str(l)
                            distance = lev.distance(sc,cc)
                            ratio = lev.ratio(sc,cc)
                            partialRatio = fuzz.partial_ratio(sc,cc)
                            tokenSortRatio = fuzz.token_sort_ratio(sc,cc)
                            tokenSetRatio = fuzz.token_set_ratio(sc,cc)

                            if ((distance <= setDistance) & (ratio >= setRatio)) or (partialRatio >= setRatioPerc) or (tokenSortRatio >= setRatioPerc) or (tokenSetRatio >= setRatioPerc):
                                output.append([c, l, e, distance, round(ratio,2), round(partialRatio,2), round(tokenSortRatio,2), round(tokenSetRatio,2)])
                                
                            del distance, ratio, partialRatio, tokenSortRatio, tokenSetRatio
            except Exception as x:
                print('---- Loop Error: ' + str(x) + ' - in file: ' + str(e))
        
        out = dimension + output_folder
        if not os.path.exists(out):
            os.mkdir(out)
            
        output = pd.DataFrame(output)
        output = output.rename(columns={0:'Source Code', 1:'Codelist Code', 2:'Filename', 3:'Distance', 4:'Ratio', 5:'Partial Ratio', 6:'Token Sort Ratio', 7:'Token Set Ratio'})
        output = output.sort_values(by=['Source Code', 'Distance', 'Ratio', 'Partial Ratio','Token Sort Ratio','Token Set Ratio'])
        rowCount = output['Source Code'].count()
        output_filename = "-dimension-levenshtein-fuzzy.csv"
        print(long_dotted_line)
        print('Outputting File: ' + f'{dimension}{output_filename} with {rowCount} rows')
        print('In Folder: ' + out)
        print(long_dotted_line)
        output.to_csv(f'{out}/{dimension}{output_filename}', index=False)

    except Exception as e:
        print('---- Outer Error: ' + str(e))


def check_all_codes_in_codelist(codes, pth, colnme, dimension, outputfoundcodes):
    """
    CHECK IF ALL YOUR DIMENSION VALUES (CODES) ARE IN A SPECIFIC CODELIST
    This methods takes a unique list of values (codes) and checks to see if they are in a specific csv codelist file (pth), column from file is selected with colnme.
    the dimension variable is used to name the resulting file, which lists if the code has been found or not, it also looks for any Nan values.
    Once the search has completed it creates a folder called {dimension}-codelist-analysis within your current directory and saves a file called {dimension}-code-search.csv,
    that lists the results of the search (Columns = Dataset Codes, Codelist Codes, Result: {Found, NOT FOUND, ITS A NAN})
    This methods takes as its arguments:
        codes: A list of unique values taken from a datasets column within a transform
        pth: This is the path to the csv odelist file you want to search through
        colnme: This is the column within each codelist to want to search through
        dimension: This is the name of the dimension for naming output files
        outputfoundcodes: If True then output all found code results to csv file, if False do not output found codes. 
    """
    try:
        dimension = dimension.lower().replace(' ', '-') # Remove stuff from dimension (if any) so the filename is nice and lovely
        dimension = re.sub('[^A-Za-z0-9]+', '',  dimension)
        print('Search File: ' + pth + '\n')   

        try:
            df1 = pd.read_csv(pth)
            list1 = list(df1[colnme])
            list2 = codes
            
            output = []
            for i in list2:
                addtodf = False
                try:
                    if pd.isna(i):
                        row = [i,'----NANANANANA----','ITS A NAN']
                        addtodf = True
                    elif i in list1:
                        row = [i,list1[list1.index(i)],'Found']
                        addtodf = outputfoundcodes
                    else:
                        row = [i,'----','NOT FOUND']
                        addtodf = True
                except Exception as e:
                    row = [i,'ERROR',e]
                    addtodf = True

                if addtodf:
                    output.append(row)

            output = pd.DataFrame(output)
            output = output.rename(columns={0:'Dataset Codes', 1:'Codelist Codes', 2:'Result'})

            try:
                cnt = output['Dataset Codes'].count()
            except:
                cnt = 0

            if cnt > 0:
                out = dimension + output_folder
                if not os.path.exists(out):
                    os.mkdir(out)

                output_filename = '-codelist-search.csv'
                print(long_dotted_line)
                print('Outputting File: ' + f'{dimension}{output_filename} with {cnt} rows')
                print('In Folder: ' + out)
                print(long_dotted_line)
                output.to_csv(f'{out}/{dimension}{output_filename}', index=False)
                return f'{out}/{dimension}{output_filename}'
            else:
                print('----------------- Results are empty so no file has been output.')
                return 'No results'
        except Exception as x:
            print(x)
            reuturn x

    except Exception as e:
        print('---- Loop Error: ' + str(e))
        return e


def display_dataset_unique_values(dataset):
    """
    Displays all the unique values in each column of a dataset ignoring any column called Value
    """
    excluded_values = ['Value']
    print("Number of rows: " + str(dataset.shape[0]))
    print("Number of columns: " + str(dataset.shape[1]))
    print("Column names: ")
    print(dataset.columns)
    display(long_dotted_line)
    for col in dataset.columns:
        if col not in excluded_values:
            dataset[col] = dataset[col].astype('category')
            display(col)
            display(list(dataset[col].cat.categories))
            display(long_dotted_line)


def add_missing_codes_to_codelist(missing_file_path, codelist_path):
    """
    If you have missing codes in a file output from the method check_all_codes_in_codelist you 
    can automatically add them to the codelist file using this one.
    """
    try:
        missingcodes = pd.read_csv(missing_file_path)
        print('Missing codes: ' + str(missingcodes['Dataset Codes'].count()))
        missingcodes = missingcodes[['Dataset Codes']]
        missingcodes['Dataset Codes'] = missingcodes['Dataset Codes'].apply(pathify)
        missingcodes['Label'] = missingcodes['Dataset Codes'].str.replace('-',' ').str.capitalize()
        missingcodes['Parent Notation'] = np.nan
        missingcodes['Sort Priority'] = ''
        missingcodes = missingcodes.rename(columns={'Dataset Codes':'Notation'})

        codelist = pd.read_csv(codelist_path)
        if 'Description' in codelist.columns:
            missingcodes['Description'] = np.nan
        codelist['Sort Priority'] = ''

        try:
            newcodelist = pd.concat([codelist, missingcodes])
            newcodelist = newcodelist[['Label','Notation','Parent Notation','Sort Priority','Description']]
            newcodelist = newcodelist.drop_duplicates()
            newcodelist['Sort Priority'] = np.arange(newcodelist.shape[0]) + 1
            newcodelist.to_csv(codelist_path, index=False)
            print('New codes have been added to file: ')
            print(codelist_path)
            return newcodelist
        except Exception as e:
            print('Something went wrong adding new codelists: ' + e)
    except Exception as e:
        print('Error: ' + e)
    

    
def search_codes_in_codelists_and_then_search_highest_scoring_codelist_file(codes, pth, colnme, dimension, outputfoundcodes):
    """
    Check a whole folder full of codelists against a set of codes and then, if any have been found, look at the highest scoring csv codelist file
    If there is more than one file with the same score then the top one is picked
    """
    print("Seaching codelist folder for codes")
    print("************************************************************************")
    filnme = search_codelists_for_codes(codes, pth, colnme, dimension)
    print("************************************************************************")
    if len(filnme) > 0:
        print("Seaching codes against codelist file: " + filnme)
        filnme = pth + filnme
        check_all_codes_in_codelist(codes, filnme, colnme, dimension, outputfoundcodes)
    else:
        print("No codelist files found with any of the codes in folder " + pth)
    print("************************************************************************")


def remove_superscripts_from_dimension(dataset, dimension):
    """
    Strips the numbers 1 to 10 as well as 1 to 10 plus a , (comma) and then strips any white space.
    This will also remove numbers that are genuinely part of the string
    """
    try:
        for x in range(1, 11):
            comnum = str(x) + ','
            dataset[dimension] = dataset[dimension].str.replace(comnum, '', regex=False) 
            dataset[dimension] = dataset[dimension].str.replace(str(x), '', regex=False) 
            dataset[dimension] = dataset[dimension].str.strip()
            
        return dataset
    except Exception as e:
        print('Remove Superscripts Error: ' + str(e))
        return dataset


def convert_dimension_to_integer(dataset, dimension):
    """
    Converts a dimension to integers taking care of NaNs and empty strings, i hope!
    """
    try:
        dataset[dimension] = dataset[dimension].fillna(-1)
        dataset[dimension] = dataset[dimension].replace('',-1)
        dataset[dimension] = dataset[dimension].astype(int)
        dataset[dimension] = dataset[dimension].astype(str)
        dataset[dimension] = dataset[dimension].replace('-1', np.nan)
        return dataset
    except Exception as e:
        print('Convert Dimension to Integer: ' + str(e))
        return dataset
