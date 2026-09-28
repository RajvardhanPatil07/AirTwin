"""Response models preserve the canonical frontend contract and provenance."""
from typing import Literal
from pydantic import BaseModel, Field

SourceType = Literal['observed', 'modeled', 'synthetic']
Region = Literal['pcmc', 'maharashtra']


class Provenance(BaseModel):
    source_type: SourceType
    assumptions: list[str]


class Cuts(BaseModel):
    traffic: float = Field(ge=0, le=50)
    industry: float = Field(ge=0, le=60)
    dust: float = Field(ge=0, le=70)


class Station(Provenance):
    id: str
    name: str
    short_name: str
    latitude: float
    longitude: float
    pm25: float
    timestamp: str
    pollutants: dict = Field(default_factory=dict)
    weather: dict = Field(default_factory=dict)


class Cell(Provenance):
    id: str
    latitude: float
    longitude: float
    bounds: tuple[tuple[float, float], tuple[float, float]]
    pm25: float
    background: float
    population: int
    population_source_type: SourceType
    local_weights: dict[str, float]


class ScenarioResult(Provenance):
    id: Literal['traffic', 'industry', 'dust', 'combined']
    name: str
    cuts: Cuts
    rank: int
    before: float
    after: float
    reduction: float
    reduction_low: float
    reduction_high: float
    reduction_percent: float
    exposure_benefit: float
    exposure_benefit_low: float
    exposure_benefit_high: float
    population_source_type: SourceType
    cells: list[Cell]


class ScenarioResponse(Provenance):
    scenario_id: str
    location_id: str
    results: list[ScenarioResult]


class StationsResponse(Provenance):
    stations: list[Station]
    warnings: list[str] = []
    data_mode: str
    weather: dict = {}
    zones: dict = {}
    zones_source_type: Literal['mapped', 'illustrative'] = 'illustrative'
    region: dict = Field(default_factory=dict)
    coverage: dict = Field(default_factory=dict)


class HotspotsResponse(Provenance):
    cells: list[Cell]


class SeriesPoint(BaseModel):
    timestamp: str
    actual: float | None
    predicted: float | None
    persistence: float | None
    p10: float | None
    p90: float | None


class ForecastResponse(Provenance):
    location_id: str
    history_source_type: SourceType
    history_reference: str
    series: list[SeriesPoint]
    shap: dict | None = None
    weather_forecast: list[dict] = []


class Metrics(BaseModel):
    mae: float
    rmse: float
    r2: float
    persistence_mae: float
    improvement_percent: float
    interval_coverage: float


class BacktestResponse(Provenance):
    location_id: str
    target_source_type: SourceType
    method: str
    series: list[SeriesPoint]
    metrics: Metrics | None
    available: bool = True
    seasonal_baseline: dict = {}
    cv: list[dict] = []
    skill: list[dict] = []
    model: str = ''


class Share(BaseModel):
    name: str
    value: float
    color: str


class AttributionResponse(Provenance):
    location_id: str
    background: float
    shares: list[Share]
    config: dict


class ScenarioRequest(BaseModel):
    location_id: str
    cuts: Cuts
    replay_at: str | None = None
    region: Region = 'pcmc'


class ChatMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=8000)


class ExplainRequest(BaseModel):
    location_id: str
    question: str = Field(min_length=1, max_length=1000)
    replay_at: str | None = None
    region: Region = 'pcmc'
    cuts: Cuts = Field(default_factory=lambda: Cuts(traffic=20, industry=30, dust=30))
    hours: int = Field(default=24, ge=1, le=72)
    history: list[ChatMessage] = Field(default_factory=list, max_length=8)


class ExplainResponse(Provenance):
    answer: str
    method: str
    context: dict
    claims: list[dict]
    model: str
