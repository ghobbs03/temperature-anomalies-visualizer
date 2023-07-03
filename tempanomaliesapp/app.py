from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QSlider, QFileDialog
import PySide6.QtWebEngineWidgets as qtwe
from PySide6.QtCore import Qt, QTimer

import sys
import folium
import io
import pandas as pd
import statistics as stats
import os.path
import csv
import numpy as np
from shapely.geometry import shape, Point
import json
from folium.plugins import Draw
from temp_data_finder import TemperatureDataFinder

class MainWindow(QMainWindow):
    def __init__(self):
        self.dat_finders = []
        super().__init__()
        for i in range(1,4):
            self.dat_finders.append(TemperatureDataFinder(f"./temp-anomaly-files/gistemp1200_GHCNv4_ERSSTv5_{i}.csv", './coordinate-mapping-files/country-capitals.csv'))

        map = folium.Map(tiles="Stamen Toner", zoom_start=13)
        self.add_points(map)
        data = io.BytesIO()
        map.save(data, close_file=False)
    
        self.map_widget = qtwe.QWebEngineView()
        self.map_widget.setHtml(data.getvalue().decode())
        self.map_widget.page().profile().downloadRequested.connect(self.handle_downloadRequested)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)
        self.year_slider =  QSlider(Qt.Horizontal)
        self.year_slider.setRange(1880, 2023)

        self.button = QPushButton("Animate")
        self.button.setFixedWidth(100)

        layout.addWidget(self.map_widget)
        layout.addWidget(self.year_slider)
        layout.addWidget(self.button)
        layout.setAlignment(self.button, Qt.AlignCenter)

        self.updater = QTimer(self)

        self.updater.timeout.connect(self.update_tick)
        self.year_slider.valueChanged.connect(self.change_value)
        self.button.clicked.connect(self.animate_data)

        self.setWindowTitle(f'Global Temperature Anomalies at Country Capitals, {1880}')



    
    def check_file(self):
        file_exists = os.path.isfile('./coordinate-mapping-files/country_to_coord_map.csv')

        if (not file_exists):
            country_to_coord_map = self.dat_finders[0].country_to_coordinates_map()
            start_year = 1880
            end_year = 2023

            map_df = pd.DataFrame(columns = ['country_capital', 'lat', 'lon', 'year','avg_tempanomaly'])

            for key in country_to_coord_map:
                print(key)
                
                lat = country_to_coord_map[key][0]
                lon = country_to_coord_map[key][1]

                for i in range(start_year, end_year+1):
                    anomalies = self.get_temps(lat, lon, i)

                    if len(anomalies) > 0:
                        avg_anomaly = stats.mean(anomalies)
                        print(avg_anomaly)
                    else:
                        avg_anomaly = np.NaN
                    
                    map_df.loc[len(map_df)] = {'country_capital': key, 'lat': lat, 'lon': lon, 'year': i, 'avg_tempanomaly': avg_anomaly}
            
            map_df.to_csv('./coordinate-mapping-files/country_to_coord_map.csv')




    def get_temps(self, lat, lon, year):
        pts = []

        for dat_obj in self.dat_finders:
            pts.append(dat_obj.lookup_by_coordinates(lat, lon, year))
        
            flat_pts_list = [item for sublist in pts for item in sublist]
            unique_pts = list(set(flat_pts_list))
            return unique_pts


    def add_points(self, map, year = 1880): 
        self.check_file()

        title_html = '''
                <h3 align="center" style="font-size:18px"><b>{}</b></h3>
                '''.format(f'Temperature Anomalies, {year}') 
        
        map.get_root().html.add_child(folium.Element(title_html))

        Draw(export=True, show_geometry_on_click=False).add_to(map)

        no_na_dat = self.open_points_data()
        for dat_point in no_na_dat:
            anomaly = float(dat_point[5])
            lat = dat_point[2]
            lon = dat_point[3]

            if (int(dat_point[4]) == year):
                if anomaly < 0:
                    folium.CircleMarker(location=[lat, lon], radius=2, weight=5, color='#03dffc', popup=folium.Popup(html = f'<center><b>{dat_point[1]}</b><br /><p style=\"display:inline; white-space: nowrap;\">({lat}, {lon})</p><br />{round(anomaly, 3)}</center>')).add_to(map)
                else:
                    folium.CircleMarker(location=[lat, lon], radius=2, weight=5, color='#f28b7c', popup=folium.Popup(html = f'<center><b>{dat_point[1]}</b><br /><p style=\"display:inline; white-space: nowrap;\">({lat}, {lon})</p><br />{round(anomaly, 3)}</center>')).add_to(map)

    


    def open_points_data(self):
        with open('./coordinate-mapping-files/country_to_coord_map.csv', newline='') as csvfile:
            temp_anomaly_dat = list(csv.reader(csvfile))

        no_na_dat = [dat for dat in temp_anomaly_dat if dat[5] != ''][1:]

        return no_na_dat
    


    def handle_points(self, state):
        all_points = []

        print(state)
        
        with open("./data.geojson", 'r') as file: 
            geojson_features = json.load(file)['features']

        for feature in geojson_features:
            geojson = feature['geometry']
            
            drawn_shape = shape(geojson)

            points = []

            no_na_dat = self.open_points_data()

            for dat_point in no_na_dat:
                lat = dat_point[2]
                lon = dat_point[3]
                country = dat_point[1]
                
                if int(dat_point[4]) == self.year_slider.value():
                    points.append([country, Point(lon, lat), dat_point[5]])

            points_inside = [[point[0], point[1].y, point[1].x, point[2]] for point in points if drawn_shape.contains(point[1])]

            unique_pts = []
            for point in points_inside:
                if point not in unique_pts:
                    unique_pts.append(point)
            
            all_points.append(unique_pts)

        all_points = [pt for ls in all_points for pt in ls]
        all_points.insert(0, ['country', 'lat', 'lon', 'tempanomaly'])

        os.remove("./data.geojson")
        
        fileName, _ = QFileDialog.getSaveFileName(self.central_widget, "Save File")

        if fileName:
            pd.DataFrame(all_points[1:], columns=all_points[0]).to_csv(fileName)



    def handle_downloadRequested(self, item):
        download_item = item
        download_item.setDownloadDirectory('.')
        download_item.accept()
        download_item.stateChanged.connect(self.handle_points)


    def change_value(self, value):
        map2 = folium.Map(tiles="Stamen Toner", zoom_start=13)
        self.add_points(map2, value)
        self.setWindowTitle(f'Global Temperature Anomalies at Country Capitals, {value}')

        dat = io.BytesIO()
        map2.save(dat, close_file=False)
        self.map_widget.stop()
        self.map_widget.setHtml(dat.getvalue().decode())
        self.map_widget.update()
        #self.processEvents()

    def animate_data(self):
        if (self.button.text() == "Animate"):   
            self.button.setText("Stop")
            # Reload every second
            self.updater.start(1000)
        elif (self.button.text() == "Stop"):
            self.button.setText("Animate")
            self.updater.stop()


    def update_tick(self):
        self.year_slider.triggerAction(QSlider.SliderSingleStepAdd)

        if (self.year_slider.value() == 2023):
            self.updater.stop()
            self.button.setText("Animate")

if __name__ == "__main__":
    app = QApplication(sys.argv)
   
    window = MainWindow()
    window.show()

    sys.exit(app.exec())
