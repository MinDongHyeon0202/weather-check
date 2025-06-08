import requests

API_KEY = "1037010b96c78c7e5efbd3e69f7cdd44"
LAT = 37.5665  # 서울 위도
LON = 126.9780 # 서울 경도

# 날씨 요청
url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"
response = requests.get(url)
weather = response.json()

# 값 추출
temp = weather["main"]["temp"]
humidity = weather["main"]["humidity"]
wind = weather["wind"]["speed"]
rain = weather.get("rain", {}).get("1h", 0)

def check_conditions(task, temp, humidity, wind, rain):
    if task == "콘크리트 타설":
        if temp < 5 or temp > 30:
            return "❌ 불가 - 기온"
        elif rain > 0:
            return "❌ 불가 - 강수"
        elif wind > 7:
            return "⚠️ 주의 - 강풍"
        else:
            return "✅ 가능"
    elif task == "방수공사":
        if humidity > 85:
            return "❌ 불가 - 습도"
        elif rain > 0:
            return "❌ 불가 - 강수"
        elif temp < 5:
            return "❌ 불가 - 기온"
        else:
            return "✅ 가능"
    elif task == "도장공사":
        if humidity > 85 or temp < 5:
            return "❌ 불가 - 기온/습도"
        elif rain > 0:
            return "❌ 불가 - 강수"
        else:
            return "✅ 가능"
    elif task == "철근 배근":
        if temp < -2 or rain > 0:
            return "⚠️ 주의 - 결빙/강수"
        else:
            return "✅ 가능"
    elif task == "골조 작업":
        if wind > 10 or rain > 0:
            return "❌ 불가 - 강풍/강수"
        else:
            return "✅ 가능"
    else:
        return "알 수 없는 공정입니다."

tasks = ["콘크리트 타설", "방수공사", "도장공사", "철근 배근", "골조 작업"]
print("🔧 공정 선택:")
for i, task in enumerate(tasks, 1):
    print(f"{i}. {task}")

task_index = int(input("작업 번호를 입력하세요 (1~5): ")) - 1
task_name = tasks[task_index]

print(f"\n➡️ 선택한 공정: {task_name}")
print(f"📡 현재 기온: {temp}℃ / 습도: {humidity}% / 풍속: {wind}m/s / 강수량: {rain}mm")

# 판단 결과
result = check_conditions(task_name, temp, humidity, wind, rain)
print(f"\n📋 판단 결과: {result}")
