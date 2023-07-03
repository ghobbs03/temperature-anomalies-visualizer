import pandas as pd
import csv

class TemperatureDataFinder:
    def __init__(self, anomalies_file, country_capitals_file):
        self.anomalies_file = anomalies_file
        self.country_capitals_file = country_capitals_file

        with open(anomalies_file, newline='') as csvfile:
            temp_anomaly_dat = list(csv.reader(csvfile))

        
        no_na = [dat for dat in temp_anomaly_dat if dat[4] != ''][1:]
        self.temp_anomaly_dat = no_na


    def lookup_by_country(self, country_name, year):
        coordinates = self.country_to_coordinates_map()[country_name]

        lat = coordinates[0]
        lon = coordinates[1]

        return self.lookup_by_coordinates(lat, lon, year)

    def lookup_by_coordinates(self, lat, lon, year):
        dats = []

        for dat_point in self.temp_anomaly_dat:
            if ((lat - 0.5 <= float(dat_point[1])) <= lat + 0.5) and (lon - 0.5 <= float(dat_point[2]) <= lon + 0.5):
                if (int(dat_point[3]) == year):
                    dats.append(float(dat_point[4]))
      
        return list(set(dats))
    
                
    def country_to_coordinates_map(self):
        ''' Creates dictionary with countries as keys and
        (capital latitude, capital longitude) as values.'''
    
        coord_dict = {}
        dat = pd.read_csv(self.country_capitals_file)

        for index, row in dat.iterrows():
            coord_dict[row['CountryName']] = [round(float(row['CapitalLatitude']), 2), round(float(row['CapitalLongitude']),2)]
        return coord_dict