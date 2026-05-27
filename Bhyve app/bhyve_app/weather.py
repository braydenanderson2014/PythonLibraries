from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from aiohttp import ClientSession


class WeatherClientError(RuntimeError):
    """Raised when the weather provider request fails."""


@dataclass(slots=True)
class TemperatureReading:
    value: float
    unit: str
    observed_at: datetime


@dataclass(slots=True)
class ForecastEntry:
    at: datetime
    temperature: float | None
    precipitation_probability: float
    precipitation: float


@dataclass(slots=True)
class WeatherForecast:
    entries: list[ForecastEntry]
    max_precipitation_probability: float
    total_precipitation: float
    lookahead_hours: int


@dataclass(slots=True)
class WeatherSnapshot:
    temperature: TemperatureReading
    forecast: WeatherForecast


@dataclass(slots=True)
class LocationMatch:
    name: str
    latitude: float
    longitude: float
    admin1: str | None
    country: str | None
    timezone: str | None


class OpenMeteoClient:
    def __init__(self, session: ClientSession) -> None:
        self._session = session

    @staticmethod
    def _parse_api_time(value: object) -> datetime:
        parsed = datetime.fromisoformat(str(value))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed

    @staticmethod
    def _candidate_queries(query: str) -> list[str]:
        cleaned = " ".join(query.split())
        candidates = [cleaned]
        if "," in cleaned:
            no_commas = " ".join(part.strip() for part in cleaned.split(",") if part.strip())
            first_part = cleaned.split(",", 1)[0].strip()
            if no_commas and no_commas not in candidates:
                candidates.append(no_commas)
            if first_part and first_part not in candidates:
                candidates.append(first_part)
        return candidates

    async def _search_locations_once(self, query: str, count: int) -> list[LocationMatch]:
        params = {
            "name": query,
            "count": count,
            "language": "en",
            "format": "json",
        }
        url = "https://geocoding-api.open-meteo.com/v1/search"
        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
        except Exception as exc:  # noqa: BLE001
            raise WeatherClientError(f"Open-Meteo geocoding request failed: {exc}") from exc

        results = data.get("results") or []
        matches: list[LocationMatch] = []
        for result in results:
            matches.append(
                LocationMatch(
                    name=str(result.get("name") or "Unknown location"),
                    latitude=float(result["latitude"]),
                    longitude=float(result["longitude"]),
                    admin1=result.get("admin1"),
                    country=result.get("country"),
                    timezone=result.get("timezone"),
                )
            )
        return matches

    async def search_locations(
        self,
        query: str,
        count: int = 5,
    ) -> list[LocationMatch]:
        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        limited_count = max(1, min(count, 10))
        for candidate in self._candidate_queries(cleaned_query):
            matches = await self._search_locations_once(candidate, limited_count)
            if matches:
                return matches
        return []

    async def get_weather_snapshot(
        self,
        latitude: float,
        longitude: float,
        unit: str,
        lookahead_hours: int = 12,
    ) -> WeatherSnapshot:
        limited_hours = max(1, min(int(lookahead_hours), 48))
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m",
            "hourly": "temperature_2m,precipitation_probability,precipitation",
            "forecast_hours": limited_hours,
            "temperature_unit": unit,
        }
        url = "https://api.open-meteo.com/v1/forecast"
        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
        except Exception as exc:  # noqa: BLE001
            raise WeatherClientError(f"Open-Meteo request failed: {exc}") from exc

        current = data.get("current") or {}
        if "temperature_2m" not in current:
            raise WeatherClientError("Open-Meteo response did not include temperature_2m")

        observed_at = current.get("time")
        if observed_at:
            observed = self._parse_api_time(observed_at)
        else:
            observed = datetime.now(timezone.utc)

        hourly = data.get("hourly") or {}
        times = hourly.get("time") or []
        temperatures = hourly.get("temperature_2m") or []
        probabilities = hourly.get("precipitation_probability") or []
        precipitation_values = hourly.get("precipitation") or []

        entries: list[ForecastEntry] = []
        for index, forecast_time in enumerate(times[:limited_hours]):
            temperature = (
                float(temperatures[index])
                if index < len(temperatures) and temperatures[index] is not None
                else None
            )
            probability = (
                float(probabilities[index])
                if index < len(probabilities) and probabilities[index] is not None
                else 0.0
            )
            precipitation = (
                float(precipitation_values[index])
                if index < len(precipitation_values) and precipitation_values[index] is not None
                else 0.0
            )
            entries.append(
                ForecastEntry(
                    at=self._parse_api_time(forecast_time),
                    temperature=temperature,
                    precipitation_probability=probability,
                    precipitation=precipitation,
                )
            )

        temperature = TemperatureReading(
            value=float(current["temperature_2m"]),
            unit=unit,
            observed_at=observed,
        )

        forecast = WeatherForecast(
            entries=entries,
            max_precipitation_probability=max(
                (entry.precipitation_probability for entry in entries),
                default=0.0,
            ),
            total_precipitation=sum(entry.precipitation for entry in entries),
            lookahead_hours=limited_hours,
        )

        return WeatherSnapshot(temperature=temperature, forecast=forecast)

    async def get_current_temperature(
        self,
        latitude: float,
        longitude: float,
        unit: str,
    ) -> TemperatureReading:
        snapshot = await self.get_weather_snapshot(latitude, longitude, unit, lookahead_hours=1)
        return snapshot.temperature
