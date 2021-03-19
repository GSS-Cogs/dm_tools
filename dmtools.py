import gssutils 
import os
import pandas as pd

def search_codelists_for_codes(codes, pth, colnme, dimension):
    """
    This method searches through a directory of codelist csv files looking for instances of each value within the codes list.
    It records in what file it finds the instance and outputs a csv file with a list of the codes, the file it found it in and the number of times it was found.
    It also outputs a csv file giving the percentage of split between the files, which codes were found in. 
    Method assumes directory only has files with extensions .csv and .csv-metadata.json.
    This methods takes as its arguments:
        codes: A list of unique values taken from a datasets column within a transform
        pth: This is the path to the codelists you want to search through
        colnme: This is the column within each codelist to want to search through
        dimension: This is the name of the dimension for naming output files
    """
    try:
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

        out = dimension + "-code-search"
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


def check_all_codes_in_codelist(codes, pth, colnme, dimension):
    try:
        dimension = pathify(dimension)
        print('Search File: ' + pth + '\n')   

        try:
            df1 = pd.read_csv(pth)
            list1 = list(df1[colnme])
            list2 = codes
            
            output = []
            for i in list2:
                try:
                    if pd.isna(i):
                        output.append([i,'----NANANANANA----','ITS A NAN'])
                    elif i in list1:
                        output.append([i,list1[list1.index(i)],'Found'])
                    else:
                        output.append([i,'----','NOT FOUND'])
                except Exception as e:
                    output.append([i,'ERROR',e])
            output = pd.DataFrame(output)
            output = output.rename(columns={0:'Dataset Codes', 1:'Codelist Codes', 2:'Result'})

            out = dimension + "-check-all-codes-search"
            if not os.path.exists(out):
                os.mkdir(out)
        
            output.to_csv(f'{out}/{dimension}-code-search.csv', index=False)
            del df1, df2, df3
        except Exception as x:
            print(x)

    except Exception as e:
        print(e)