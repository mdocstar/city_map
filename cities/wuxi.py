import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cbb.city_map import CityMap

class wuxi_map():
    def __init__(self):
        self.wuxi_center = [31.590259, 120.361006] # city center coordinates
        self.wuxi_map = CityMap("Wuxi", self.wuxi_center, zoom_start=13)
        
        # a. add wuxi train station marker
        Train_station = {'name': 'Wuxi Train Station', 'location': [31.588016, 120.306343],
                         'color_name': 'blue', 'icon_name': 'train'}
        East_Train_station = {'name': 'Wuxi East Train Station', 'location': [31.596805, 120.460133],
                         'color_name': 'blue', 'icon_name': 'train'}
        self.wuxi_map.add_marker(**Train_station)
        self.wuxi_map.add_marker(**East_Train_station)

        # b. add wedding hotel marker
        Wedding_hotel = {'name': 'Wuxi Wedding Hotel', 'location': [31.590259, 120.361006],
                         'color_name': 'red', 'icon_name': 'heart'}
        self.wuxi_map.add_marker(**Wedding_hotel)
        

if __name__ == "__main__":
    map = wuxi_map()
    map.wuxi_map.save_map("wixu_map.html")
    