import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cbb.city_map import CityMap
from config import AMAP_KEY

class wuxi_map():
    def __init__(self):
        self.wuxi_center = [31.590259, 120.361006] # city center coordinates
        self.wuxi_map = CityMap("Wuxi", self.wuxi_center, zoom_start=13,
                                amap_key=AMAP_KEY)
        
        # a. add wuxi train station marker
        Train_station = {'name': 'Wuxi Train Station', 'location': [31.588016, 120.306343],
                         'place_type': 'station'}
        East_Train_station = {'name': 'Wuxi East Train Station', 'location': [31.596805, 120.460133],
                         'place_type': 'station'}
        self.wuxi_map.add_marker(**Train_station)
        self.wuxi_map.add_marker(**East_Train_station)

        # b. add wedding hotel marker (hotel type, but keep the heart icon to override the default)
        Wedding_hotel = {'name': 'Wuxi Wedding Hotel', 'location': [31.590259, 120.361006],
                         'place_type': 'hotel', 'icon_name': 'heart'}
        self.wuxi_map.add_marker(**Wedding_hotel)

        # c. draw routes between markers (line color is auto-mapped by mode)
        self.wuxi_map.add_route(Train_station['location'], East_Train_station['location'],
                                mode='driving')
        self.wuxi_map.add_route(Wedding_hotel['location'], Train_station['location'],
                                mode='walking', ant_path=True)
        # transit route: click the red line for the itinerary (method / transfers / per-leg time)
        self.wuxi_map.add_route(Train_station['location'], East_Train_station['location'],
                                mode='transit', city='无锡', cityd='无锡')


if __name__ == "__main__":
    map = wuxi_map()
    map.wuxi_map.save_map("wixu_map.html")
    