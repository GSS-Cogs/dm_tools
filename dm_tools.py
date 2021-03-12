import gssutils 
import os
import pandas as pd

def find_concepts(codes, pth, colnme, dimension):
    try:
        exnot = 'csv-metadata' # This is the type of file you don't want
        
        print('Search Directory: ' + pth + '\n')
        
        entries = os.listdir(pth)     

        out = dimension + "-concept-search"
        os.mkdir(out)

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
            except Exception as e:
                print(e)

        output = output.sort_values(by=['Code'])
        unq = output.groupby('Code').count()
        output = pd.merge(output, unq, on='Code')
        output = output.rename(columns={'Filename_x': 'Filename', 'Filename_y': 'Count'})
        output.to_csv(f'{out}/{dimension}-concept-search.csv', index=False)
        
        filenamecount = pd.DataFrame(output['Filename'])
        filenamecount = filenamecount.groupby(['Filename']).size().reset_index(name='Counts')
        filenamecount['Percentage'] = ((filenamecount['Counts'] / filenamecount.Counts.sum()) * 100).round(2)
        filenamecount.to_csv(f'{out}/{dimension}-filename-count.csv', index=False)
    except Exception as e:
        print(e)

