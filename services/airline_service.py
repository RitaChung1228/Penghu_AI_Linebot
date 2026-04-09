import requests
from bs4 import BeautifulSoup

def search_flights(departure, arrival, date, passengers=1, return_date=None):
    url = "https://www.mandarin-airlines.com/b2c/BookingNPurchase/SearchFlight"

    itin_type = "2" if return_date else "1"

    params = {
        "searchModel.DepartureCity": departure,
        "searchModel.ArrivalCity": arrival,
        "searchModel.DepartureDate": date,
        "searchModel.ItinType": itin_type,
        "searchModel.PassengerNo": passengers,
        "searchModel.InfantNo": "0"
    }
    if return_date:
        params["searchModel.ReturnDate"] = return_date

    response = requests.get(url, params=params)
    soup = BeautifulSoup(response.text, "html.parser")

    flights = []

    for item in soup.select(".ticket-list"):
        flight_no = item.select_one(".air-type p").text.strip()
        times = item.select(".flight-time p")
        depart = times[0].text.replace("起飛", "").strip()
        arrive = times[1].text.replace("抵達", "").strip()
        price2 = item.select_one(".price2 p").text.strip()
        price3 = item.select_one(".price3 p").text.strip()
        flights.append({
            "航班": flight_no,
            "起飛": depart,
            "抵達": arrive,
            "促銷價": price2,
            "居民價": price3,
            "狀態": "✅ 可購票"
        })

    for item in soup.select(".booking-list"):
        flight_no = item.select_one(".booking-type p").text.strip()
        times = item.select(".booking-time p")
        depart = times[0].text.replace("起飛", "").strip()
        arrive = times[1].text.replace("抵達", "").strip()
        flights.append({
            "航班": flight_no,
            "起飛": depart,
            "抵達": arrive,
            "促銷價": "--",
            "居民價": "--",
            "狀態": "⚠️ 額滿可候補"
        })

    return flights


def format_result(departure, arrival, date, flights, passengers):
    lines = [
        f"✈️ {departure} → {arrival}  {date}  {passengers}人",
        "─" * 20
    ]
    if not flights:
        lines.append("查無航班資料")
    for f in flights:
        lines.append(f"{f['航班']}  {f['起飛']}→{f['抵達']}")
        lines.append(f"  促銷價：{f['促銷價']}  居民價：{f['居民價']}")
        lines.append(f"  {f['狀態']}")
        lines.append("")
    return "\n".join(lines)


# 測試
if __name__ == "__main__":
    # 測試 1：單程
    print("=== 單程測試 ===")
    flights = search_flights("RMQ", "MZG", "2026/03/24", passengers=1)
    print(format_result("RMQ", "MZG", "2026/03/24", flights, 1))

    # 測試 2：來回
    print("=== 來回測試 ===")
    flights = search_flights("TSA", "MZG", "2026/05/16", passengers=1, return_date="2026/05/18")
    print(format_result("TSA", "MZG", "2026/05/16", flights, 1))