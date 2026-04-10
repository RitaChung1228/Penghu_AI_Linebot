#%%
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 機場代碼對照表
AIRPORTS = {
    "1": ("TSA", "松山"),
    "2": ("KHH", "高雄"),
    "3": ("RMQ", "台中"),
    "4": ("HUN", "花蓮"),
    "5": ("TTT", "台東"),
    "6": ("MZG", "澎湖"),
    "7": ("KNH", "金門"),
    "8": ("LZN", "南竿")
}

AIRPORTS_INV = {v[0]: v[1] for k, v in AIRPORTS.items()}


def get_flight_info(driver, direction_text):
    print(f"\n--- {direction_text} 航班資訊 ---")
    tickets = driver.find_elements(By.CLASS_NAME, "ticket-list")
    if not tickets:
        print("查無此區間航班資訊，或是該日期尚未開放訂位。")
        return []

    # 定義表格標頭與分隔線
    print(f"| {'航班':<10} | {'起飛時間':<12} | {'抵達時間':<12} | {'狀態':<8} |")
    print("|" + "-"*12 + "|" + "-"*14 + "|" + "-"*14 + "|" + "-"*10 + "|")

    available_flights = []
    for ticket in tickets:
        try:
            air_type = ticket.find_element(By.CLASS_NAME, "air-type").text
            flight_times = ticket.find_elements(By.CLASS_NAME, "flight-time")
            dep_time = flight_times[0].text.replace("\n", " ")
            arr_time = flight_times[1].text.replace("\n", " ")

            # 判斷是購票還是候補
            is_waitlist = False
            try:
                ticket.find_element(By.CLASS_NAME, "buybt01")
                is_waitlist = True
            except:
                pass

            status = "候補" if is_waitlist else "可購票"

            # 格式化表格列輸出
            # 由於終端機對中文字寬度處理不同，這裡使用較寬的間距確保對齊
            print(f"| {air_type:<10} | {dep_time:<12} | {arr_time:<12} | {status:<8} |")

            if not is_waitlist:
                available_flights.append({
                    "air_type": air_type,
                    "dep_time": dep_time,
                    "arr_time": arr_time
                })
        except:
            continue
    return available_flights


def run_search(driver, wait, dep_code, arr_code, date_str, adult_count):
    driver.get("https://www.mandarin-airlines.com/")

    # 選擇單程模式進行查詢 (較為穩定)
    itin_type_label = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='itinType1']")))
    driver.execute_script("arguments[0].click();", itin_type_label)

    # 出發地
    Select(driver.find_element(By.ID, "depstn")).select_by_value(dep_code)
    time.sleep(1)
    # 目的地
    Select(driver.find_element(By.ID, "arrstn")).select_by_value(arr_code)
    # 日期
    dep_date_inputs = driver.find_elements(By.NAME, "departureDate")
    driver.execute_script(f"arguments[0].value = '{date_str}';", dep_date_inputs[0])
    # 成人
    Select(driver.find_element(By.NAME, "adult")).select_by_value(str(adult_count))
    # 搜尋
    search_btn = driver.find_element(By.XPATH, "//button[contains(text(), '搜 尋') and contains(@onclick, 'beforeSub')]")
    driver.execute_script("arguments[0].click();", search_btn)

    wait.until(lambda d: d.find_elements(By.CLASS_NAME, "ticket-list") or "目前無此航班資訊" in d.page_source)
    return get_flight_info(driver, f"{date_str} {AIRPORTS_INV[dep_code]} -> {AIRPORTS_INV[arr_code]}")


def search_flights(dep_code, arr_code, date_str, passengers=1):
    """
    建立 Chrome driver，查詢單程航班，回傳航班 list。

    參數：
        dep_code  : 出發機場代碼（如 "TSA"）
        arr_code  : 抵達機場代碼（如 "MZG"）
        date_str  : 出發日期（格式 "YYYY/MM/DD"）
        passengers: 成人人數（預設 1）

    回傳：
        list[dict]，每筆格式：
        {"航班": ..., "起飛": ..., "抵達": ..., "狀態": ...}
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)

    try:
        raw = run_search(driver, wait, dep_code, arr_code, date_str, passengers)
    finally:
        driver.quit()

    # 統一回傳格式，供 format_result 使用
    return [
        {
            "航班": f["air_type"],
            "起飛": f["dep_time"],
            "抵達": f["arr_time"],
            "狀態": "✅ 可購票"
        }
        for f in raw
    ]


def format_result(dep_name, arr_name, date, flights, passengers):
    """將航班 list 格式化為 LINE 訊息文字"""
    lines = [
        f"✈️ {dep_name} → {arr_name}",
        f"📅 {date}　👤 {passengers} 人",
        "─" * 20
    ]
    if not flights:
        lines.append("查無可購票航班（該日可能已滿或尚未開放）")
    for f in flights:
        lines.append(f"🛫 {f['航班']}　{f['起飛']} → {f['抵達']}")
        lines.append(f"   {f['狀態']}")
    return "\n".join(lines)


def main():
    print("=== 華信航空自動查詢系統 ===")

    # 選單顯示
    for k, v in AIRPORTS.items():
        print(f"{k}. {v[1]} ({v[0]})")

    dep_idx = input("\n請選擇出發地序號: ")
    arr_idx = input("請選擇目的地序號: ")

    dep_code = AIRPORTS.get(dep_idx, ("TSA", ""))[0]
    arr_code = AIRPORTS.get(arr_idx, ("MZG", ""))[0]

    is_roundtrip = input("是否為來回票? (y/n): ").lower() == 'y'

    dep_date = input("請輸入去程日期 (格式: YYYY/MM/DD, 例如 2026/05/01): ")
    ret_date = ""
    if is_roundtrip:
        ret_date = input("請輸入回程日期 (格式: YYYY/MM/DD, 例如 2026/05/04): ")

    adult_count = input("請輸入成人人數 (1-4): ")

    print("\n系統準備中，請稍候...")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)

    try:
        # 執行去程查詢
        print(f"\n正在查詢去程...")
        dep_results = run_search(driver, wait, dep_code, arr_code, dep_date, adult_count)

        ret_results = None
        if is_roundtrip:
            # 執行回程查詢 (起訖點對調)
            print(f"\n正在查詢回程...")
            ret_results = run_search(driver, wait, arr_code, dep_code, ret_date, adult_count)

        print("\n" + "="*30)
        print("最終查詢總結:")
        if is_roundtrip:
            if dep_results and ret_results:
                print(f"恭喜！{dep_date} ~ {ret_date} 期間『有』足夠來回機票。")
            else:
                if not dep_results: print(f"警告: {dep_date} 去程目前無位 (需候補)。")
                if not ret_results: print(f"警告: {ret_date} 回程目前無位 (需候補)。")
        else:
            if dep_results:
                print(f"恭喜！{dep_date} 去程『有』足夠機票。")
            else:
                print(f"遺憾！{dep_date} 去程目前無位 (需候補)。")
        print("="*30)

    except Exception as e:
        print(f"\n查詢過程中發生錯誤: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
