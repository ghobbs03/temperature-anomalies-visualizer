import xarray as xr

class DataHandler:
    def __init__(self, netcdf_file):
        xr_dataset = xr.open_dataset(netcdf_file)
        df = xr_dataset.to_dataframe()
        df = df.reset_index()

        df['lat'] = df['lat'].astype('float64')
        df['lon'] = df['lon'].astype('float64')
        df['time'] = df['time'].dt.strftime('%Y')
        df.drop(columns=['nv', 'time_bnds'])
        agg_df = df.groupby(['lat', 'lon', 'time']).agg({'tempanomaly': 'mean'}).reset_index()
        agg_df['time'] = agg_df['time'].astype(int)

        self.dataframe = agg_df

        for i in range(1,4):
            if i == 1:
                dat_slice = int(2332800/3)
                dat1 = agg_df[:dat_slice]
            elif i == 2:
                dat2 = agg_df[dat_slice:dat_slice*2]
            elif i == 3:
                dat3 = agg_df[dat_slice*2:]

        dat = [dat1, dat2, dat3]

        for i in range(3):
            dat[i].to_csv(f"./temp-anomaly-files/gistemp1200_GHCNv4_ERSSTv5{'_' + str(i+1)}.csv", encoding = 'utf-8-sig')