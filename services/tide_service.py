import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://www.penghu-nsa.gov.tw"


# 澎管處 SSL 憑證指紋（SHA256）
# 到期日：2026-11-24，到期後需更新此值
# 憑證更新時此值會變，需重新執行 get_cert_fingerprint() 更新。
_CERT_FINGERPRINT = (
    "d2:4b:1b:6d:06:a9:21:ff:32:d4:a3:33:0b:63:e0:9f"
    ":c5:fe:b7:dd:7b:56:92:82:64:4e:c8:56:82:4f:c1:61"
)


class _FingerprintAdapter(HTTPAdapter):
    """停用憑證鏈驗證，但強制比對伺服器憑證 SHA256 指紋。"""
    def send(self, request, **kwargs):
        kwargs["verify"] = False
        kwargs.setdefault("timeout", 10)
        response = super().send(request, **kwargs)
        return response

    def init_poolmanager(self, *args, **kwargs):
        kwargs["assert_fingerprint"] = _CERT_FINGERPRINT
        super().init_poolmanager(*args, **kwargs)


def _session():
    s = requests.Session()
    s.mount("https://www.penghu-nsa.gov.tw", _FingerprintAdapter())
    return s


def _roc_year_month(year=None, month=None):
    """回傳民國年月。未傳入時使用當月。"""
    if year is None or month is None:
        now = datetime.now()
        return now.year - 1911, now.month
    return year, month


def get_tide(year=None, month=None):
    """
    爬取澎湖當月潮汐資料。

    參數：
        year  : 民國年（int，預設當年）
        month : 月份（int，預設當月）

    回傳：
        list[dict]，每筆資料格式：
        {
            "日期":  "1",
            "星期":  "日",
            "潮汐":  [
                {"滿潮": "10:15", "乾潮": "15:49", "安全通行": "13:30-17:30"},
                {"滿潮": "...",   "乾潮": "...",   "安全通行": "..."},  # 部分天有兩組
            ]
        }
    """
    roc_year, roc_month = _roc_year_month(year, month)
    filename = f"{roc_year:03d}{roc_month:02d}tide.htm"
    url = f"{BASE_URL}/Services/Tidenew/{filename}"

    resp = _session().get(url, timeout=10)
    resp.encoding = "utf-8"

    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    rows = table.find_all("tr")[1:]  # 跳過表頭

    results = []
    current_entry = None

    for row in rows:
        tds = row.find_all("td")

        if len(tds) >= 5:
            # 新的一天。欄位數可能是 5（舊格式）或 6（新格式，多一欄備註）
            # 用負索引取最後三欄，確保兩種格式都能正確解析
            current_entry = {
                "日期": tds[0].get_text(strip=True),
                "星期": tds[1].get_text(strip=True),
                "備註": tds[2].get_text(strip=True) if len(tds) == 6 else "",
                "潮汐": [{
                    "滿潮":     tds[-3].get_text(strip=True),
                    "乾潮":     tds[-2].get_text(strip=True),
                    "安全通行": tds[-1].get_text(strip=True),
                }]
            }
            results.append(current_entry)

        elif len(tds) == 3 and current_entry is not None:
            # 同一天第二組潮汐（rowspan 造成的延續列）
            current_entry["潮汐"].append({
                "滿潮":     tds[0].get_text(strip=True),
                "乾潮":     tds[1].get_text(strip=True),
                "安全通行": tds[2].get_text(strip=True),
            })

    return results


def get_today_tide():
    """回傳今日潮汐資料（dict），查無則回傳 None。"""
    now = datetime.now()
    return get_tide_by_date(now.year, now.month, now.day)


def get_tide_by_date(year, month, day):
    """
    查詢指定日期的潮汐資料。
    year, month, day 為西元年月日（int）。
    回傳 dict 或 None。
    """
    roc_year = year - 1911
    tides = get_tide(roc_year, month)
    for entry in tides:
        if entry["日期"] == str(day):
            return entry
    return None


def parse_date_input(text):
    """
    解析使用者輸入的日期字串。
    支援格式：2026/05/16、2026-05-16、05/16（預設今年）
    回傳 (year, month, day) 或 None（格式錯誤）。
    """
    import re
    text = text.strip()
    # 2026/05/16 或 2026-05-16
    m = re.fullmatch(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", text)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    # 05/16 或 5/16（省略年份，預設今年）
    m = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})", text)
    if m:
        return datetime.now().year, int(m.group(1)), int(m.group(2))
    return None


def format_tide_entry(entry, year=None, month=None):
    """格式化單筆潮汐資料為文字。year/month 為西元年月（用於顯示日期）。"""
    if year is None or month is None:
        now = datetime.now()
        year, month = now.year, now.month
    date_str = f"{year}/{month:02d}/{int(entry['日期']):02d}（{entry['星期']}）"
    lines = [f"🌊 {date_str} 潮汐"]
    for t in entry["潮汐"]:
        lines.append(f"  滿潮 {t['滿潮']}  乾潮 {t['乾潮']}")
        lines.append(f"  🚶 安全通行：{t['安全通行']}")
    return "\n".join(lines)


def format_tide_month(tides, max_days=7):
    """格式化多天潮汐（預設顯示 7 天）。"""
    if not tides:
        return "查無潮汐資料"
    lines = ["🌊 澎湖潮汐預報", "─" * 22]
    for entry in tides[:max_days]:
        lines.append(format_tide_entry(entry))
        lines.append("")
    return "\n".join(lines).strip()


# ── 測試 ──────────────────────────────────────
def _print_table(entry, year, month):
    """以表格形式印出單筆潮汐資料。"""
    date_str = f"{year}/{month:02d}/{int(entry['日期']):02d}（{entry['星期']}）"
    note = entry.get("備註", "")
    header = f"  日期：{date_str}" + (f"  備註：{note}" if note else "")
    print(header)
    print(f"  {'組別':<4} {'滿潮':<8} {'乾潮':<8} {'安全通行'}")
    print(f"  {'─'*4} {'─'*8} {'─'*8} {'─'*14}")
    for i, t in enumerate(entry["潮汐"], 1):
        print(f"  {i:<4} {t['滿潮']:<8} {t['乾潮']:<8} {t['安全通行']}")


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    now = datetime.now()

    print("=== 今日潮汐 ===")
    today = get_today_tide()
    if today:
        _print_table(today, now.year, now.month)
    else:
        print("  查無今日資料")

    print("\n=== 日期查詢測試（2026/05/07）===")
    parsed = parse_date_input("2026/05/07")
    if parsed:
        y, mo, d = parsed
        entry = get_tide_by_date(y, mo, d)
        if entry:
            _print_table(entry, y, mo)
        else:
            print("  查無資料")

    print("\n=== 日期查詢測試（省略年份：07/09）===")
    parsed = parse_date_input("07/09")
    if parsed:
        y, mo, d = parsed
        entry = get_tide_by_date(y, mo, d)
        if entry:
            _print_table(entry, y, mo)
        else:
            print("  查無資料（該月資料尚未上線）")


# 目前可抓今年，但是否能抓當日即時資訊，還要研究
