from flask import Flask, render_template, request
import requests

app = Flask(__name__)

API_KEY = "1037010b96c78c7e5efbd3e69f7cdd44"
LAT = 37.5665  # 서울 위도
LON = 126.9780 # 서울 경도

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

tasks = ["콘크리트 타설", "방수공사", "도장공사", "철근 배근", "골조 작업"]

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    weather = None
    error = None
    task = None

    if request.method == "POST":
        task = request.form.get("task")
        weather, error = get_weather()
        if not error:
            result = check_conditions(task, **weather)

    return render_template("index.html", tasks=tasks, result=result, weather=weather, error=error, selected_task=task)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
