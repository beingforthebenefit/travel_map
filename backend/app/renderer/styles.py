from dataclasses import dataclass


@dataclass
class TileStyle:
    name: str
    label: str
    url_template: str
    requires_api_key: bool
    attribution: str
    # Color palette for route, labels, banner overlays
    route_color: tuple[int, int, int, int]  # RGBA
    route_shadow_color: tuple[int, int, int, int]
    label_bg_color: tuple[int, int, int, int]
    label_text_color: tuple[int, int, int]
    label_accent_color: tuple[int, int, int]
    banner_bg_color: tuple[int, int, int, int]
    banner_text_color: tuple[int, int, int]
    marker_color: tuple[int, int, int]
    photo_border_color: tuple[int, int, int]


STYLES: dict[str, TileStyle] = {
    "watercolor": TileStyle(
        name="watercolor",
        label="Stamen Watercolor",
        url_template="https://tiles.stadiamaps.com/tiles/stamen_watercolor/{z}/{x}/{y}.jpg?api_key={api_key}",
        requires_api_key=True,
        attribution="Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.",
        route_color=(139, 69, 19, 200),
        route_shadow_color=(0, 0, 0, 60),
        label_bg_color=(255, 255, 255, 200),
        label_text_color=(60, 40, 20),
        label_accent_color=(139, 69, 19),
        banner_bg_color=(255, 255, 255, 180),
        banner_text_color=(60, 40, 20),
        marker_color=(139, 69, 19),
        photo_border_color=(255, 255, 255),
    ),
    "toner": TileStyle(
        name="toner",
        label="Stamen Toner Lite",
        url_template="https://tiles.stadiamaps.com/tiles/stamen_toner_lite/{z}/{x}/{y}.png?api_key={api_key}",
        requires_api_key=True,
        attribution="Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.",
        route_color=(220, 50, 50, 220),
        route_shadow_color=(0, 0, 0, 40),
        label_bg_color=(255, 255, 255, 220),
        label_text_color=(30, 30, 30),
        label_accent_color=(200, 50, 50),
        banner_bg_color=(255, 255, 255, 200),
        banner_text_color=(30, 30, 30),
        marker_color=(220, 50, 50),
        photo_border_color=(220, 50, 50),
    ),
    "terrain": TileStyle(
        name="terrain",
        label="Stamen Terrain",
        url_template="https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}.png?api_key={api_key}",
        requires_api_key=True,
        attribution="Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.",
        route_color=(0, 100, 0, 200),
        route_shadow_color=(0, 0, 0, 50),
        label_bg_color=(255, 255, 240, 220),
        label_text_color=(40, 60, 40),
        label_accent_color=(0, 100, 0),
        banner_bg_color=(255, 255, 240, 200),
        banner_text_color=(40, 60, 40),
        marker_color=(0, 100, 0),
        photo_border_color=(255, 255, 240),
    ),
    "positron": TileStyle(
        name="positron",
        label="CartoDB Positron",
        url_template="https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
        requires_api_key=False,
        attribution="Map tiles by CartoDB, under CC BY 3.0. Data by OpenStreetMap, under ODbL.",
        route_color=(52, 73, 94, 220),
        route_shadow_color=(0, 0, 0, 40),
        label_bg_color=(255, 255, 255, 230),
        label_text_color=(44, 62, 80),
        label_accent_color=(52, 152, 219),
        banner_bg_color=(255, 255, 255, 210),
        banner_text_color=(44, 62, 80),
        marker_color=(52, 152, 219),
        photo_border_color=(52, 152, 219),
    ),
    "dark": TileStyle(
        name="dark",
        label="CartoDB Dark Matter",
        url_template="https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
        requires_api_key=False,
        attribution="Map tiles by CartoDB, under CC BY 3.0. Data by OpenStreetMap, under ODbL.",
        route_color=(231, 76, 60, 220),
        route_shadow_color=(0, 0, 0, 80),
        label_bg_color=(30, 30, 30, 220),
        label_text_color=(236, 240, 241),
        label_accent_color=(231, 76, 60),
        banner_bg_color=(30, 30, 30, 200),
        banner_text_color=(236, 240, 241),
        marker_color=(231, 76, 60),
        photo_border_color=(231, 76, 60),
    ),
    "osm": TileStyle(
        name="osm",
        label="OpenStreetMap",
        url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        requires_api_key=False,
        attribution="Map data by OpenStreetMap contributors, under ODbL.",
        route_color=(0, 102, 204, 220),
        route_shadow_color=(0, 0, 0, 50),
        label_bg_color=(255, 255, 255, 220),
        label_text_color=(30, 30, 30),
        label_accent_color=(0, 102, 204),
        banner_bg_color=(255, 255, 255, 200),
        banner_text_color=(30, 30, 30),
        marker_color=(0, 102, 204),
        photo_border_color=(0, 102, 204),
    ),
}


def get_style(name: str) -> TileStyle:
    if name not in STYLES:
        raise ValueError(f"Unknown style: {name}. Available: {list(STYLES.keys())}")
    return STYLES[name]


def get_available_styles(has_api_key: bool) -> list[TileStyle]:
    return [s for s in STYLES.values() if not s.requires_api_key or has_api_key]
