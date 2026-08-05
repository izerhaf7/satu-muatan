"""Server-only Google geo adapter."""

import json
import re
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Literal

from app.adapters.geo.base import AddressResult, CoordinateResult, PlaceResolutionResult, SuggestionResult


_PLACE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._~-]{0,255}$")
_AUTOCOMPLETE_MASK = (
    "suggestions.placePrediction.placeId,suggestions.placePrediction.text.text,"
    "suggestions.placePrediction.structuredFormat.mainText.text,"
    "suggestions.placePrediction.structuredFormat.secondaryText.text"
)
_RESOLVE_MASK = "formattedAddress,addressComponents,location,granularity,placeId"
_DEFAULT_MAX_RESPONSE_BYTES = 32_768


class GoogleGeoAdapter:
    def __init__(
        self,
        api_key: str,
        timeout: float = 4.0,
        request_json: Callable | None = None,
        max_response_bytes: int = _DEFAULT_MAX_RESPONSE_BYTES,
    ):
        if max_response_bytes < 1:
            raise ValueError("Batas respons penyedia alamat tidak valid")
        self._api_key = api_key
        self._timeout = timeout
        self._max_response_bytes = max_response_bytes
        self._request_json = request_json or self._request

    def _request(
        self,
        url: str,
        timeout: float,
        headers: dict[str, str] | None = None,
        method: str = "GET",
        body: bytes | None = None,
    ) -> dict:
        request = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            declared_length = response.headers.get("Content-Length")
            if declared_length is not None:
                try:
                    if int(declared_length) > self._max_response_bytes:
                        raise ValueError("Respons penyedia alamat terlalu besar")
                except ValueError as error:
                    if str(error) == "Respons penyedia alamat terlalu besar":
                        raise
            raw = response.read(self._max_response_bytes + 1)
            if len(raw) > self._max_response_bytes:
                raise ValueError("Respons penyedia alamat terlalu besar")
            return json.loads(raw.decode("utf-8"))

    def _call(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        method: str = "GET",
        body: bytes | None = None,
    ) -> dict:
        if headers is None:
            return self._request_json(url, self._timeout)
        if method == "GET" and body is None:
            return self._request_json(url, self._timeout, headers)
        return self._request_json(url, self._timeout, headers, method, body)

    def reverse(self, lat: float, lng: float) -> AddressResult | None:
        params = urllib.parse.urlencode({"languageCode": "id"})
        data = self._call(
            f"https://geocode.googleapis.com/v4/geocode/location/{lat},{lng}?{params}",
            {"X-Goog-Api-Key": self._api_key, "X-Goog-FieldMask": "results.formattedAddress,results.addressComponents"},
        )
        if not data.get("results"):
            return None
        return self._address_from_result(data["results"][0])

    def forward(self, query: str) -> CoordinateResult | None:
        params = urllib.parse.urlencode({"languageCode": "id"})
        data = self._call(
            f"https://geocode.googleapis.com/v4/geocode/address/{urllib.parse.quote(query, safe='')}?{params}",
            {"X-Goog-Api-Key": self._api_key, "X-Goog-FieldMask": "results.location,results.formattedAddress"},
        )
        if not data.get("results"):
            return None
        result = data["results"][0]
        location = result.get("location", {})
        lat = location.get("lat", location.get("latitude"))
        lng = location.get("lng", location.get("longitude"))
        if lat is None or lng is None:
            return None
        return CoordinateResult(
            lat,
            lng,
            result.get("formatted_address", result.get("formattedAddress")),
            "GOOGLE",
        )

    def autocomplete(
        self,
        query: str,
        limit: int = 5,
        bias: tuple[float, float, float] | None = None,
        max_input: int = 200,
        max_radius: float = 50_000,
    ) -> list[SuggestionResult]:
        payload: dict = {
            "input": query[:max_input],
            "includedRegionCodes": ["id"],
            "languageCode": "id",
            "regionCode": "id",
            "includeQueryPredictions": False,
        }
        if bias is not None:
            lat, lng, radius = bias
            payload["locationBias"] = {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": min(radius, max_radius),
                }
            }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "X-Goog-Api-Key": self._api_key,
            "X-Goog-FieldMask": _AUTOCOMPLETE_MASK,
            "Content-Type": "application/json",
        }
        data = self._call("https://places.googleapis.com/v1/places:autocomplete", headers, "POST", body)
        hasil = []
        for suggestion in data.get("suggestions", []):
            prediction = suggestion.get("placePrediction", {})
            text = prediction.get("text", {}).get("text")
            structured = prediction.get("structuredFormat", {})
            utama = structured.get("mainText", {}).get("text") or text
            sekunder = structured.get("secondaryText", {}).get("text")
            place_id = prediction.get("placeId")
            if text and utama and place_id and _PLACE_ID.fullmatch(place_id):
                hasil.append(
                    SuggestionResult(place_id, utama, text, sumber="GOOGLE", teks_sekunder=sekunder)
                )
            if len(hasil) >= min(limit, 5):
                break
        return hasil

    def resolve_place(self, place_id: str) -> PlaceResolutionResult:
        if not _PLACE_ID.fullmatch(place_id):
            raise ValueError("place_id tidak valid")
        encoded = urllib.parse.quote(place_id, safe="")
        params = urllib.parse.urlencode({"languageCode": "id", "regionCode": "ID"})
        data = self._call(
            f"https://geocode.googleapis.com/v4/geocode/places/{encoded}?{params}",
            {"X-Goog-Api-Key": self._api_key, "X-Goog-FieldMask": _RESOLVE_MASK},
        )
        alamat = data.get("formattedAddress")
        location = data.get("location")
        if not isinstance(alamat, str) or not alamat or not isinstance(location, dict):
            raise ValueError("Respons penyedia alamat tidak valid")
        lat = location.get("latitude", location.get("lat"))
        lng = location.get("longitude", location.get("lng"))
        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            raise ValueError("Respons penyedia alamat tidak valid")
        bagian: dict[str, str] = {}
        for component in data.get("addressComponents", []):
            text = component.get("longText")
            if isinstance(text, str):
                for tipe in component.get("types", []):
                    bagian[tipe] = text
        route = bagian.get("route")
        number = bagian.get("street_number")
        jalan = " ".join(x for x in (route, number) if x) or None
        raw_granularity = data.get("granularity")
        granularitas_map: dict[str, Literal["ALAMAT", "JALAN"]] = {
            "ROOFTOP": "ALAMAT",
            "RANGE_INTERPOLATED": "JALAN",
        }
        raw_granularity = raw_granularity if isinstance(raw_granularity, str) else ""
        granularitas = granularitas_map.get(raw_granularity)
        return PlaceResolutionResult(
            alamat=alamat,
            jalan=jalan,
            kode_pos=bagian.get("postal_code"),
            desa=bagian.get("administrative_area_level_4") or bagian.get("sublocality_level_1"),
            kecamatan=bagian.get("administrative_area_level_3"),
            kabupaten=bagian.get("administrative_area_level_2"),
            provinsi=bagian.get("administrative_area_level_1"),
            lat=float(lat),
            lng=float(lng),
            granularitas=granularitas,
            sumber="GOOGLE",
            koordinat_presisi=raw_granularity == "ROOFTOP",
        )

    @staticmethod
    def _address_from_result(result: dict) -> AddressResult:
        bagian = {}
        components = result.get("address_components", result.get("addressComponents", []))
        for component in components:
            for tipe in component.get("types", []):
                bagian[tipe] = component.get("long_name", component.get("longText"))
        return AddressResult(
            alamat=result.get("formatted_address", result.get("formattedAddress", "")),
            desa=bagian.get("administrative_area_level_4") or bagian.get("sublocality_level_1"),
            kecamatan=bagian.get("administrative_area_level_3"),
            kabupaten=bagian.get("administrative_area_level_2"),
            provinsi=bagian.get("administrative_area_level_1"),
            kode_pos=bagian.get("postal_code"),
            sumber="GOOGLE",
        )
