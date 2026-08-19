import folium

class CityMap:
    def __init__(self, name, center, zoom_start=13):
        self.name = name
        self.center = center # city center coordinates
        self.zoom_start = zoom_start
        self.map = folium.Map(
            location=self.center,
            zoom_start=self.zoom_start,
            tiles="https://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}",
            attr="高德地图",
            control_scale=False, # forbid scale control
            zoom_control=True    # keep zoom control
        )
        
    def add_marker(self, **dict_kwargs):    
        #### a. Extract parameters with defaults
        loc  = dict_kwargs.get("location", self.center)  # 无经纬度则定位到城市中心
        name = dict_kwargs.get("name", "Unnamed Place")
        color = dict_kwargs.get("color_name", "blue")
        icon  = dict_kwargs.get("icon_name", "info-circle")
        
        popup_content = f"<b>{name}</b>"
        custom_popup = folium.Popup(popup_content, max_width=200)
        
        folium_icon = folium.Icon(
            color=color,
            icon=icon,
            prefix="fa"  # 必须保留，FA图标核心前缀
        )
        
        # 添加标记到地图
        folium.Marker(
            location=loc,
            popup=custom_popup,
            icon=folium_icon,
            tooltip=name  # 新增：鼠标悬停直接显示文字，无需点击，双重保障能看到名称
        ).add_to(self.map)
        
    def save_map(self, file_name):
        self.map.save(file_name)
        print(f"{self.name} map saved as: {file_name}")
        
if __name__ == "__main__":
    print("This is a basic class for city map plots, please import this file into other py files.")

