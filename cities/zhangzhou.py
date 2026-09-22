import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cbb.city_map import CityMap
from config import AMAP_KEY

class zhangzhou_map():
    def __init__(self):
        self.zhangzhou_center = [24.497595,117.677782] # city center coordinates
        self.zhangzhou = CityMap("Zhangzhou", self.zhangzhou_center, zoom_start=13,
                                 amap_key=AMAP_KEY)
        
        # a. add train station marker
        Train_station = {'name': 'ZhangZhou Train Station', 'location': [24.457661,117.71604],
                         'place_type': 'station'}
        self.zhangzhou.add_marker(**Train_station)

        # b. add business center
        zhangzhou_City_Business = {'name': 'Business_center', 'location': [24.500182,117.694665],
                         'place_type': 'business'}
        zhangzhou_xiangcheng_Business = {'name': 'Business_center', 'location': [24.523581,117.685797],
                         'place_type': 'business'}
        
        self.zhangzhou.add_marker(**zhangzhou_City_Business)
        self.zhangzhou.add_marker(**zhangzhou_xiangcheng_Business)
        

if __name__ == "__main__":
    map = zhangzhou_map()
    map.zhangzhou.save_map("zhangzhou_map.html")
    