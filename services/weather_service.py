import os
import requests
from requests.adapters import HTTPAdapter
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

load_dotenv()

CWA_API_KEY = os.getenv("OPENDATA_CWA_API_KEY", "").strip()
BASE_URL    = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
FILEAPI_URL = "https://opendata.cwa.gov.tw/fileapi/v1/opendataapi"

# CWA SSL 憑證指紋（SHA256），到期日約 2027 年，到期後需重新取得
_CWA_FINGERPRINT = (
    "e9:fa:94:92:46:63:25:9a:af:82:79:df:6c:b7:87:6e"
    ":23:2f:1c:bf:0f:7b:64:af:bf:f5:e6:88:69:e6:3c:8f"
)

DATASET_HELPER = "F-C0032-015"  # 天氣小幫手（今明文字描述）
DATASET_3DAY   = "F-D0047-045"  # 後3天，逐3小時
DATASET_7DAY   = "F-D0047-047"  # 後7天，逐12小時

LOCATIONS        = ["馬公市", "湖西鄉", "白沙鄉", "西嶼鄉", "望安鄉", "七美鄉"]
DEFAULT_LOCATION = "馬公市"

# 澎湖各月歷史氣候統計（來源：中央氣象署氣候資料）
# 欄位：平均溫(°C)、最高溫、最低溫、降雨量(mm)、降雨天數、平均濕度(%)
CLIMATE_DATA = {
    1:  {"平均溫": 17.2, "最高溫": 20.1, "最低溫": 14.5, "降雨量": 22,  "降雨天數": 7,  "濕度": 78},
    2:  {"平均溫": 17.6, "最高溫": 20.4, "最低溫": 15.0, "降雨量": 30,  "降雨天數": 8,  "濕度": 80},
    3:  {"平均溫": 19.7, "最高溫": 22.6, "最低溫": 17.1, "降雨量": 33,  "降雨天數": 9,  "濕度": 81},
    4:  {"平均溫": 23.2, "最高溫": 26.2, "最低溫": 20.5, "降雨量": 49,  "降雨天數": 9,  "濕度": 82},
    5:  {"平均溫": 26.8, "最高溫": 29.6, "最低溫": 24.2, "降雨量": 97,  "降雨天數": 11, "濕度": 83},
    6:  {"平均溫": 29.1, "最高溫": 31.8, "最低溫": 26.7, "降雨量": 112, "降雨天數": 10, "濕度": 82},
    7:  {"平均溫": 29.8, "最高溫": 32.4, "最低溫": 27.5, "降雨量": 97,  "降雨天數": 9,  "濕度": 80},
    8:  {"平均溫": 29.5, "最高溫": 32.0, "最低溫": 27.3, "降雨量": 131, "降雨天數": 11, "濕度": 81},
    9:  {"平均溫": 27.8, "最高溫": 30.5, "最低溫": 25.4, "降雨量": 68,  "降雨天數": 8,  "濕度": 78},
    10: {"平均溫": 25.1, "最高溫": 28.0, "最低溫": 22.5, "降雨量": 23,  "降雨天數": 6,  "濕度": 74},
    11: {"平均溫": 21.8, "最高溫": 25.0, "最低溫": 18.9, "降雨量": 18,  "降雨天數": 6,  "濕度": 74},
    12: {"平均溫": 18.3, "最高溫": 21.4, "最低溫": 15.5, "降雨量": 17,  "降雨天數": 6,  "濕度": 76},
}


# ── Session ────────────────────────────────────
class _FingerprintAdapter(HTTPAdapter):
    def send(self, request, **kwargs):
        kwargs["verify"] = False
        return super().send(request, **kwargs)
    def init_poolmanager(self, *args, **kwargs):
        kwargs["assert_fingerprint"] = _CWA_FINGERPRINT
        super().init_poolmanager(*args, **kwargs)

def _session():
    s = requests.Session()
    s.mount("https://opendata.cwa.gov.tw", _FingerprintAdapter())
    return s


# ── Cache ───────────────────────────────────────
_cache: dict = {}

def _fetch(dataset_id, location_name):
    cache_key = (dataset_id, location_name)
    if cache_key in _cache:
        return _cache[cache_key]
    resp = _session().get(
        f"{BASE_URL}/{dataset_id}",
        params={"Authorization": CWA_API_KEY, "LocationName": location_name},
        timeout=15,
    )
    data = resp.json()
    locations = data.get("records", {}).get("Locations", [])
    if not locations:
        return None
    location_list = locations[0].get("Location", [])
    result = next((l for l in location_list if l["LocationName"] == location_name), None)
    _cache[cache_key] = result
    return result

def _elements(location_data):
    return {e["ElementName"]: e["Time"] for e in location_data.get("WeatherElement", [])}

def _val(elems, elem_name, key, match_time):
    """取指定時間的欄位值，自動處理 DataTime / StartTime 兩種格式。"""
    for e in elems.get(elem_name, []):
        t = e.get("DataTime") or e.get("StartTime", "")
        if t == match_time:
            return e["ElementValue"][0].get(key, "")
    return ""

def _parse_iso(iso):
    try:
        return datetime.fromisoformat(iso)
    except Exception:
        return None

def _fmt_time(iso, fmt="%m/%d %H:%M"):
    dt = _parse_iso(iso)
    return dt.strftime(fmt) if dt else iso


# ── 資料取得 ─────────────────────────────────────
def get_weather_helper():
    """天氣小幫手：今明文字描述（含風浪、提醒）。"""
    if "helper" in _cache:
        return _cache["helper"]
    resp = _session().get(
        f"{FILEAPI_URL}/{DATASET_HELPER}",
        params={"Authorization": CWA_API_KEY, "downloadType": "WEB", "format": "JSON"},
        timeout=15,
    )
    root = resp.json()["cwaopendata"]
    issued = root.get("Sent", "")
    descs = (
        root["Dataset"]["Locations"]["Location"]
        ["WeatherElement"]["ElementValue"]["WeatherDescription"]
    )
    result = {
        "發布時間": issued,
        "摘要":    descs[0] if len(descs) > 0 else "",
        "白天": {
            "天氣": descs[1] if len(descs) > 1 else "",
            "風浪": descs[2] if len(descs) > 2 else "",
            "提醒": descs[3] if len(descs) > 3 else "",
        },
        "夜晚": {
            "天氣": descs[4] if len(descs) > 4 else "",
            "風浪": descs[5] if len(descs) > 5 else "",
            "提醒": descs[6] if len(descs) > 6 else "",
        },
    }
    _cache["helper"] = result
    return result


def get_weather_3day(location=DEFAULT_LOCATION):
    """後3天逐3小時天氣。"""
    data = _fetch(DATASET_3DAY, location)
    if not data:
        return []
    elems = _elements(data)
    result = []
    for t in elems.get("天氣現象", []):
        start = t["StartTime"]
        result.append({
            "開始": start, "結束": t["EndTime"],
            "天氣":   t["ElementValue"][0].get("Weather", ""),
            "溫度":   _val(elems, "溫度", "Temperature", start),
            "降雨機率": _val(elems, "3小時降雨機率", "ProbabilityOfPrecipitation", start),
            "風向":   _val(elems, "風向", "WindDirection", start),
            "風速":   _val(elems, "風速", "BeaufortScale", start),
        })
    return result


def get_weather_7day(location=DEFAULT_LOCATION):
    """後7天逐12小時天氣。"""
    data = _fetch(DATASET_7DAY, location)
    if not data:
        return []
    elems = _elements(data)
    result = []
    for t in elems.get("天氣現象", []):
        start = t["StartTime"]
        uv = next((e for e in elems.get("紫外線指數", []) if e.get("StartTime") == start), None)
        result.append({
            "開始": start, "結束": t["EndTime"],
            "天氣":   t["ElementValue"][0].get("Weather", ""),
            "最高溫": _val(elems, "最高溫度", "MaxTemperature", start),
            "最低溫": _val(elems, "最低溫度", "MinTemperature", start),
            "降雨機率": _val(elems, "12小時降雨機率", "ProbabilityOfPrecipitation", start),
            "風向":   _val(elems, "風向", "WindDirection", start),
            "風速":   _val(elems, "風速", "BeaufortScale", start),
            "紫外線": uv["ElementValue"][0].get("UVExposureLevel", "") if uv else "",
        })
    return result


# ── 日期區間查詢（統一入口）──────────────────────────
def get_weather_by_range(start: date, end: date, location=DEFAULT_LOCATION):
    """
    依日期區間自動選擇資料來源：
      今天         → 天氣小幫手
      今天～3天內  → 後3天（逐3小時）
      4～7天       → 後7天（逐12小時）
      7天以上      → 歷史氣候統計（各月平均）
    回傳 (類型, 資料)，類型為 "helper" / "3day" / "7day" / "climate"
    """
    today = date.today()
    days_from_now = (end - today).days

    if start == today and end == today:
        return "helper", get_weather_helper()

    if days_from_now <= 3:
        forecasts = get_weather_3day(location)
        filtered = _filter_by_range(forecasts, start, end)
        return "3day", filtered

    if days_from_now <= 7:
        forecasts = get_weather_7day(location)
        filtered = _filter_by_range(forecasts, start, end)
        return "7day", filtered

    # 超過 7 天：回傳查詢區間涵蓋的月份氣候統計
    months = set()
    d = start
    while d <= end:
        months.add(d.month)
        d += timedelta(days=1)
    climate = {m: CLIMATE_DATA[m] for m in sorted(months) if m in CLIMATE_DATA}
    return "climate", climate


def _filter_by_range(forecasts, start: date, end: date):
    """過濾只保留 start～end 日期範圍內的時段。"""
    result = []
    for f in forecasts:
        dt = _parse_iso(f["開始"])
        if dt and start <= dt.date() <= end:
            result.append(f)
    return result


# ── 格式化（表格）──────────────────────────────────
def _table(headers, rows, col_widths=None):
    """
    產生純文字表格。
    headers: list[str]
    rows:    list[list[str]]
    """
    if col_widths is None:
        col_widths = [max(len(str(r[i])) for r in ([headers] + rows)) for i in range(len(headers))]

    def _row(cells, widths):
        return "│ " + " │ ".join(str(c).ljust(w) for c, w in zip(cells, widths)) + " │"

    sep_top = "┌─" + "─┬─".join("─" * w for w in col_widths) + "─┐"
    sep_mid = "├─" + "─┼─".join("─" * w for w in col_widths) + "─┤"
    sep_bot = "└─" + "─┴─".join("─" * w for w in col_widths) + "─┘"

    lines = [sep_top, _row(headers, col_widths), sep_mid]
    for row in rows:
        lines.append(_row(row, col_widths))
    lines.append(sep_bot)
    return "\n".join(lines)


def format_weather_helper(data):
    if not data:
        return "查無天氣資料"
    issued = _fmt_time(data["發布時間"])
    rows = [
        ["🌞 白天", "天氣", data["白天"]["天氣"]],
        ["",        "風浪", data["白天"]["風浪"]],
        ["",        "提醒", data["白天"]["提醒"]],
        ["🌙 夜晚", "天氣", data["夜晚"]["天氣"]],
        ["",        "風浪", data["夜晚"]["風浪"]],
        ["",        "提醒", data["夜晚"]["提醒"]],
    ]
    header = f"🌤️ 澎湖天氣小幫手（{issued} 發布）\n📋 {data['摘要']}\n"
    return header + _table(["時段", "項目", "內容"], rows)


def format_weather_3day(forecasts):
    if not forecasts:
        return "查無天氣資料"
    rows = [
        [
            f"{_fmt_time(f['開始'])}~{_fmt_time(f['結束'], '%H:%M')}",
            f["天氣"],
            f"{f['溫度']}°C",
            f"{f['降雨機率']}%",
            f"{f['風向']} {f['風速']}級",
        ]
        for f in forecasts
    ]
    header = "☁️ 澎湖後3天天氣預報（逐3小時）\n"
    return header + _table(["時段", "天氣", "溫度", "降雨", "風"], rows)


def format_weather_7day(forecasts):
    if not forecasts:
        return "查無天氣資料"
    rows = [
        [
            f"{_fmt_time(f['開始'])}~{_fmt_time(f['結束'], '%m/%d %H:%M')}",
            f["天氣"],
            f"{f['最低溫']}~{f['最高溫']}°C",
            f"{f['降雨機率']}%",
            f"{f['風向']} {f['風速']}級",
            f["紫外線"],
        ]
        for f in forecasts
    ]
    header = "☁️ 澎湖後7天天氣預報（逐12小時）\n"
    return header + _table(["時段", "天氣", "溫度", "降雨", "風", "紫外線"], rows)


def format_weather_climate(climate: dict, start: date, end: date):
    if not climate:
        return "查無氣候資料"
    month_names = {1:"一月",2:"二月",3:"三月",4:"四月",5:"五月",6:"六月",
                   7:"七月",8:"八月",9:"九月",10:"十月",11:"十一月",12:"十二月"}
    rows = [
        [
            month_names.get(m, f"{m}月"),
            f"{v['最低溫']}~{v['最高溫']}°C",
            f"{v['平均溫']}°C",
            f"{v['降雨量']}mm",
            f"{v['降雨天數']}天",
            f"{v['濕度']}%",
        ]
        for m, v in climate.items()
    ]
    header = (
        f"📊 澎湖歷史氣候統計\n"
        f"（查詢區間：{start} ～ {end}，超過7天預報範圍，以歷史平均值供參考）\n"
    )
    return header + _table(["月份", "溫度範圍", "平均溫", "降雨量", "降雨天數", "濕度"], rows)


def format_by_range(kind, data, start=None, end=None):
    """統一格式化入口，對應 get_weather_by_range 的回傳。"""
    if kind == "helper":
        return format_weather_helper(data)
    if kind == "3day":
        return format_weather_3day(data)
    if kind == "7day":
        return format_weather_7day(data)
    if kind == "climate":
        return format_weather_climate(data, start, end)
    return "查無資料"


# ── 測試 ──────────────────────────────────────
if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    today = date.today()

    print("=== 今天（小幫手）===")
    kind, data = get_weather_by_range(today, today)
    print(format_by_range(kind, data))

    print("\n=== 後3天區間 ===")
    kind, data = get_weather_by_range(today, today + timedelta(days=2))
    print(format_by_range(kind, data))

    print("\n=== 後7天區間 ===")
    kind, data = get_weather_by_range(today, today + timedelta(days=6))
    print(format_by_range(kind, data))

    print("\n=== 3個月後（歷史氣候統計）===")
    far_start = today + timedelta(days=90)
    far_end   = far_start + timedelta(days=6)
    kind, data = get_weather_by_range(far_start, far_end)
    print(format_by_range(kind, data, far_start, far_end))
