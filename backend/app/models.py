from pydantic import BaseModel, Field


# --- Trip ---

class TripCreate(BaseModel):
    title: str
    subtitle: str = ""


class TripUpdate(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    style: str | None = None
    print_width: float | None = None
    print_height: float | None = None
    dpi: int | None = None
    show_title: bool | None = None
    loop_route: bool | None = None
    api_key_ref: str | None = None


class Trip(BaseModel):
    id: str
    title: str
    subtitle: str
    created_at: str
    updated_at: str
    style: str
    print_width: float
    print_height: float
    dpi: int
    show_title: bool
    loop_route: bool
    api_key_ref: str | None


class TripSummary(BaseModel):
    id: str
    title: str
    subtitle: str
    updated_at: str
    stop_count: int
    has_output: bool


class TripDetail(Trip):
    stops: list["Stop"] = []


# --- Stop ---

class StopCreate(BaseModel):
    city: str
    dates: str
    lat: float | None = None
    lon: float | None = None
    label: str | None = None
    nights: int = 0
    highlight: bool = False


class StopUpdate(BaseModel):
    city: str | None = None
    dates: str | None = None
    lat: float | None = None
    lon: float | None = None
    label: str | None = None
    nights: int | None = None
    highlight: bool | None = None


class StopReorder(BaseModel):
    stop_ids: list[str]


class Stop(BaseModel):
    id: str
    trip_id: str
    sort_order: int
    city: str
    label: str | None
    lat: float
    lon: float
    dates: str
    nights: int
    highlight: bool
    photo_path: str | None
    created_at: str


# --- Render ---

class RenderRequest(BaseModel):
    style: str | None = None
    all_styles: bool = False


class RenderStatus(BaseModel):
    status: str  # pending | rendering | done | error
    progress: float | None = None
    styles_complete: list[str] | None = None
    error: str | None = None


# --- Settings ---

class SettingsResponse(BaseModel):
    stadia_api_key_set: bool = False
    default_style: str = "watercolor"
    default_print_width: float = 24.0
    default_print_height: float = 18.0
    default_dpi: int = 300


class SettingsUpdate(BaseModel):
    stadia_api_key: str | None = None
    default_style: str | None = None
    default_print_width: float | None = None
    default_print_height: float | None = None
    default_dpi: int | None = None


# --- Geocode ---

class GeocodeResult(BaseModel):
    display_name: str
    lat: float
    lon: float
