from flask import Flask, render_template, request
import requests
from collections import defaultdict

app = Flask(__name__)

API_KEY = "1037010b96c78c7e5efbd3e69f7cdd44"
LAT = 37.5665
LON = 126.9780

def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        rain = data.get("rain", {}).get("1h", 0)
        return {
            "temp": temp,
            "humidity": humidity,
            "wind": wind,
            "rain": rain
        }, None
    except Exception as e:
        return None, str(e)

def get_forecast():
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        forecast_list = []
        for entry in data["list"][:8]:
            temp = entry["main"]["temp"]
            humidity = entry["main"]["humidity"]
            wind = entry["wind"]["speed"]
            rain = entry.get("rain", {}).get("3h", 0)
            time = entry["dt_txt"]
            forecast_list.append({
                "time": time,
                "temp": temp,
                "humidity": humidity,
                "wind": wind,
                "rain": rain
            })
        return forecast_list, None
    except Exception as e:
        return None, str(e)

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
    return "판단 불가"

def generate_task_schedule(forecast_list):
    task_schedule = defaultdict(list)
    for entry in forecast_list:
        for task in tasks:
            result = check_conditions(task, entry["temp"], entry["humidity"], entry["wind"], entry["rain"])
            if result.startswith("✅"):
                task_schedule[entry["time"]].append(task)
    return task_schedule

tasks = ["콘크리트 타설", "방수공사", "도장공사", "철근 배근", "골조 작업"]

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    weather = None
    error = None
    task = None
    forecast_result = []
    task_schedule = {}

    if request.method == "POST":
        task = request.form.get("task")
        weather, error = get_weather()
        forecast, f_error = get_forecast()
        if not error:
            result = check_conditions(task, **weather)
        if not f_error:
            for f in forecast:
                judgment = check_conditions(task, f["temp"], f["humidity"], f["wind"], f["rain"])
                f["judgment"] = judgment
            forecast_result = forecast
            task_schedule = generate_task_schedule(forecast)

    return render_template("index.html", tasks=tasks, result=result, weather=weather, error=error, selected_task=task, forecast=forecast_result, schedule=task_schedule)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
