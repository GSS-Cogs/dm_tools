import gssutils 
import os
import pandas as pd
from IPython.display import display

def search_codelists_for_codes(codes, pth, colnme, dimension):
    """
    CHECK IF ANY OF YOUR DIMENSION VALUES (CODES) ARE ALREADY DEFINED IN A CODELIST(S)
    This method searches through a directory of codelist csv files looking for instances of each value within the passed unique list (codes).
    It records in what file it finds the instance and outputs a csv file with a list of the codes, the file it found it in and the number of times it was found.
    It also outputs a csv file giving the percentage split between the files where codes were found.
    Once the search has completed it creates a folder called {dimension}-codelist-analysis within your current directory and saves files called:
         1. {dimension}-code-search.csv (Columns = Code, Filename, Count)
         2. {dimension}-percentage-split.csv (Columns = Filename, Counts, Percentage)
    Method assumes directory only has files with extensions .csv and .csv-metadata.json.
    This methods takes as its arguments:
        codes: A list of unique values taken from a datasets column within a transform
        pth: This is the path to the codelists you want to search through
        colnme: This is the column within each codelist to want to search through
        dimension: This is the name of the dimension for naming output files
    """
    try:
        #dimension = pathify(dimension)
        exnot = 'csv-metadata' # This is the type of file you don't want
        
        print('Search Directory: ' + pth + '\n')
        
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
                print(x)

        out = dimension + "-codelist-analysis"
        if not os.path.exists(out):
            os.mkdir(out)

        output = output.sort_values(by=['Code'])
        unq = output.groupby('Code').count()
        output = pd.merge(output, unq, on='Code')
        output = output.rename(columns={'Filename_x': 'Filename', 'Filename_y': 'Count'})
        output.to_csv(f'{out}/{dimension}-code-search.csv', index=False)
        
        filenamecount = pd.DataFrame(output['Filename'])
        filenamecount = filenamecount.groupby(['Filename']).size().reset_index(name='Counts')
        filenamecount['Percentage'] = ((filenamecount['Counts'] / filenamecount.Counts.sum()) * 100).round(2)
        filenamecount.to_csv(f'{out}/{dimension}-percentage-split.csv', index=False)
    except Exception as e:
        print(e)


def check_all_codes_in_codelist(codes, pth, colnme, dimension, outputfoundcodes):
    """
    CHECK IF ALL YOUR DIMENSION VALUES (CODES) ARE IN A SPECIFIC CODELIST
    This methods takes a unique list of values (codes) and checks to see if they are in a specific csv codelist file (pth), column from file is sleected with colnme.
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
        #dimension = pathify(dimension)
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
                out = dimension + "-codelist-analysis"
                if not os.path.exists(out):
                    os.mkdir(out)
                output.to_csv(f'{out}/{dimension}-code-search.csv', index=False)
            else:
                print('----------------- Results are empty so no file has been output.')
        except Exception as x:
            print(x)

    except Exception as e:
        print(e)


def display_dataset_unique_values(dataset):
    """
    Displays all the unique values in each column of a dataset ignoring any column called Value
    """
    excluded_values = ['Value']
    for col in dataset.columns:
        if col not in excluded_values:
            dataset[col] = dataset[col].astype('category')
            display(col)
            display(dataset[col].cat.categories)