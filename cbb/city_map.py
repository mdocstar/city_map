import os
import socket

import folium
import requests
import urllib3.util.connection as _urllib3_conn
from folium.plugins import AntPath

# AMap IP whitelist only matches a public IPv4. Force requests over IPv4 so
# they do not go out via this machine's IPv6 default (which AMap rejects).
_urllib3_conn.allowed_gai_family = lambda: socket.AF_INET

class CityMap:
    # place_type -> (marker color, FontAwesome icon), used to draw different labels by type
    PLACE_TYPES = {
        "station":     ("blue",      "train"),          # train station
        "metro":       ("blue",      "subway"),         # metro station
        "bus_station": ("darkblue",  "bus"),            # bus station
        "airport":     ("cadetblue", "plane"),          # airport
        "hotel":       ("red",       "hotel"),          # hotel
        "restaurant":  ("orange",    "cutlery"),        # restaurant
        "cafe":        ("beige",     "coffee"),         # cafe
        "business":    ("darkred",   "building"),       # business center
        "scenic":      ("green",     "camera"),         # scenic spot
        "hospital":    ("red",       "hospital-o"),     # hospital
        "school":      ("purple",    "graduation-cap"), # school
        "shopping":    ("pink",      "shopping-cart"),  # shopping mall
    }

    # AMap direction API endpoints for each travel mode
    AMAP_DIRECTION_URLS = {
        "driving":   "https://restapi.amap.com/v3/direction/driving",
        "walking":   "https://restapi.amap.com/v3/direction/walking",
        "bicycling": "https://restapi.amap.com/v4/direction/bicycling",
        "transit":   "https://restapi.amap.com/v3/direction/transit/integrated",
    }

    # route mode -> default line color / display label
    MODE_COLORS = {
        "driving":   "blue",
        "walking":   "green",
        "bicycling": "orange",
        "transit":   "red",
    }
    MODE_LABELS = {
        "driving":   "驾车",
        "walking":   "步行",
        "bicycling": "骑行",
        "transit":   "公交",
    }

    def __init__(self, name, center, zoom_start=13, amap_key=None):
        self.name = name
        self.center = center # city center coordinates
        self.zoom_start = zoom_start
        # AMap Web Service key; falls back to the AMAP_KEY environment variable
        self.amap_key = amap_key or os.environ.get("AMAP_KEY")
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
        loc  = dict_kwargs.get("location", self.center)  # fall back to city center if no coordinates given
        name = dict_kwargs.get("name", "Unnamed Place")

        # 1. New input type variable: station / hotel / restaurant, etc.
        place_type = dict_kwargs.get("place_type", None)

        # 2. Match preset icon & color by type (explicit color/icon takes priority)
        color = dict_kwargs.get("color_name", None)
        icon  = dict_kwargs.get("icon_name", None)
        if place_type in self.PLACE_TYPES:
            preset_color, preset_icon = self.PLACE_TYPES[place_type]
            color = color or preset_color
            icon  = icon or preset_icon
        # fall back to defaults when no type given or type not matched
        color = color or "blue"
        icon  = icon or "info-circle"

        # hover tooltip: prefixed with type to distinguish types at a glance
        type_label = f"[{place_type}] " if place_type else ""
        tooltip = f"{type_label}{name}"

        popup_content = f"<b>{name}</b>"
        custom_popup = folium.Popup(popup_content, max_width=200)

        folium_icon = folium.Icon(
            color=color,
            icon=icon,
            prefix="fa"  # required: FontAwesome icon prefix
        )

        # add the marker to the map
        folium.Marker(
            location=loc,
            popup=custom_popup,
            icon=folium_icon,
            tooltip=tooltip  # hover shows the name without clicking; fallback to guarantee the name is visible
        ).add_to(self.map)

    def add_route(self, origin, destination, mode="driving", **kwargs):
        """
        Draw a real route between two points via the AMap direction API.

        origin/destination: [lat, lng] pairs (same format as marker locations).
        mode: "driving" | "walking" | "bicycling" | "transit".
        kwargs:
            amap_key: override the key set on the instance / AMAP_KEY env var.
            color / weight / opacity: line style (defaults: color by mode / 4 / 0.8).
            ant_path: True to use an animated AntPath instead of a plain PolyLine.
            city / cityd: origin/destination city name or adcode (transit mode only).
        Returns the list of [[lat, lng], ...] points drawn on the map.
        """
        key = kwargs.get("amap_key", self.amap_key)
        if not key:
            raise ValueError("AMap key is required. Pass amap_key=... or set env var AMAP_KEY.")

        url = self.AMAP_DIRECTION_URLS.get(mode)
        if url is None:
            raise ValueError(f"Unsupported mode '{mode}'. Use driving / walking / bicycling / transit.")

        # AMap expects "lng,lat", while markers use [lat, lng]
        origin_str = f"{origin[1]},{origin[0]}"
        destination_str = f"{destination[1]},{destination[0]}"

        params = {
            "key": key,
            "origin": origin_str,
            "destination": destination_str,
            "extensions": "base",
        }
        if mode == "transit":
            params["city"] = kwargs.get("city", self.name)
            params["cityd"] = kwargs.get("cityd", self.name)

        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # v3 uses status/info; v4 (bicycling) uses errcode/errmsg
        is_ok = (data.get("status") == "1") or (data.get("errcode") == 0)
        if not is_ok:
            errmsg = data.get("info") or data.get("errmsg")
            raise RuntimeError(f"AMap route request failed: {errmsg}")

        points = self._extract_route_points(data, mode)
        distance_m, duration_s = self._extract_route_summary(data, mode)

        # 1. color by route mode (explicit color still wins)
        label = self.MODE_LABELS.get(mode, mode)
        color = kwargs.get("color", self.MODE_COLORS.get(mode, "blue"))
        weight = kwargs.get("weight", 4)
        opacity = kwargs.get("opacity", 0.8)

        # 2. hover tooltip shows the total time & distance
        tooltip = f"{label}: {self._format_distance(distance_m)} · {self._format_duration(duration_s)}"

        # 3. transit: click popup shows method, transfers and per-leg time
        popup = folium.Popup(self._build_transit_itinerary(data), max_width=320) if mode == "transit" else None

        if kwargs.get("ant_path", False):
            AntPath(points, color=color, weight=weight, opacity=opacity, delay=400,
                    tooltip=tooltip, popup=popup).add_to(self.map)
        else:
            folium.PolyLine(points, color=color, weight=weight, opacity=opacity,
                            tooltip=tooltip, popup=popup).add_to(self.map)

        return points

    @staticmethod
    def _parse_amap_polyline(polyline_str):
        # AMap polyline "lng,lat;lng,lat;..." -> folium [[lat, lng], ...]
        points = []
        for pair in polyline_str.split(";"):
            lng, lat = pair.split(",")
            points.append([float(lat), float(lng)])
        return points

    def _extract_route_points(self, data, mode):
        points = []
        if mode in ("driving", "walking", "bicycling"):
            # v3 uses route.paths; v4 (bicycling) may return data.paths
            route = data.get("route") or data.get("data")
            steps = route["paths"][0]["steps"]
            for step in steps:
                points.extend(self._parse_amap_polyline(step["polyline"]))
        elif mode == "transit":
            transit = data["route"]["transits"][0]
            for segment in transit["segments"]:
                for step in segment.get("walking", {}).get("steps", []):
                    points.extend(self._parse_amap_polyline(step["polyline"]))
                for busline in segment.get("bus", {}).get("buslines", []):
                    points.extend(self._parse_amap_polyline(busline["polyline"]))
        return points

    @staticmethod
    def _format_duration(seconds):
        seconds = int(seconds or 0)
        if seconds < 60:
            return f"{seconds}秒"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}分钟"
        return f"{minutes // 60}小时{minutes % 60}分钟"

    @staticmethod
    def _format_distance(meters):
        meters = int(meters or 0)
        if meters < 1000:
            return f"{meters}米"
        return f"{meters / 1000:.1f}公里"

    def _extract_route_summary(self, data, mode):
        if mode == "transit":
            transit = data["route"]["transits"][0]
            return int(transit.get("distance") or 0), int(transit.get("duration") or 0)
        route = data.get("route") or data.get("data")
        path = route["paths"][0]
        return int(path.get("distance") or 0), int(path.get("duration") or 0)

    def _build_transit_itinerary(self, data):
        transit = data["route"]["transits"][0]
        lines = [
            f"<b>全程 {self._format_distance(transit.get('distance'))}"
            f" · {self._format_duration(transit.get('duration'))}</b>"
        ]
        step = 0
        for seg in transit["segments"]:
            walk = seg.get("walking") or {}
            if walk.get("duration"):
                step += 1
                lines.append(
                    f"{step}. 步行 {self._format_duration(walk.get('duration'))}"
                    f"（{self._format_distance(walk.get('distance'))}）"
                )
            for bl in (seg.get("bus") or {}).get("buslines", []):
                step += 1
                frm = (bl.get("departure_stop") or {}).get("name", "?")
                to = (bl.get("arrival_stop") or {}).get("name", "?")
                via = len(bl.get("via_stops") or [])
                lines.append(
                    f"{step}. 乘坐 <b>{bl.get('name', '?')}</b>（{bl.get('type', '')}）<br>"
                    f"&nbsp;&nbsp;{frm} → {to} · {self._format_duration(bl.get('duration'))} · 经{via}站"
                )
            railway = seg.get("railway") or {}
            if railway.get("name"):
                step += 1
                frm = (railway.get("departure_stop") or {}).get("name", "?")
                to = (railway.get("arrival_stop") or {}).get("name", "?")
                lines.append(
                    f"{step}. 乘坐 <b>{railway.get('name')}</b>（{railway.get('type', '')}）<br>"
                    f"&nbsp;&nbsp;{frm} → {to} · {self._format_duration(railway.get('duration'))}"
                )
        return "<br>".join(lines)

    def save_map(self, file_name):
        self.map.save(file_name)
        print(f"{self.name} map saved as: {file_name}")

if __name__ == "__main__":
    print("This is a basic class for city map plots, please import this file into other py files.")
