from flask import Flask, render_template, request, send_file
import pandas as pd
import matplotlib.pyplot as plt
import requests, os
from datetime import datetime, timedelta
import pytz

VISUAL_API_KEY = os.getenv("R7QNF6MDDL3YE8D5SY3A3XGQH")
CITY = "Seoul"
EXCEL_PATH = "ai_schedule.xlsx"
CHART_PATH = "ai_schedule_gantt_chart.png"

app = Flask(__name__)

JOB_OPTIONS = {
    "formwork": "외부비계설치",
    "concrete_floor": "기초타설",
    "interior_paint": "내부 도장",
    "floor_finish": "방통",
    "floor1": "1층 타설",
    "roof": "지붕 타설"
}

def check_job_feasibility(job_type, temp, humidity, wind, rain):
    label = JOB_OPTIONS.get(job_type, '')
    if rain > 2: return "? 불가 (강수량)"
    if temp < -5 or temp > 35: return "?? 주의 (극한 온도)"
    if humidity > 90 and "도장" in label: return "? 불가 (습도)"
    if "타설" in label and rain > 0: return "? 불가 (비 예보)"
    return "? 가능"

def get_weather(city, start, end):
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}/{start}/{end}?unitGroup=metric&key={VISUAL_API_KEY}&include=days"
    res = requests.get(url)
    return res.json().get("days", []) if res.status_code == 200 else []

def generate_ai_schedule(forecast):
    result, used = [], set()
    for job, name in JOB_OPTIONS.items():
        for day in forecast:
            if day["datetime"] in used: continue
            if check_job_feasibility(job, day["temp"], day["humidity"], day["windspeed"], day["precip"]).startswith("?"):
                result.append({"공정": name, "추천일": day["datetime"], "사유": "? 가능"})
                used.add(day["datetime"])
                break
    return result

@app.route("/", methods=["GET", "POST"])
def index():
    today = datetime.now(pytz.timezone("Asia/Seoul")).date()
    start = request.form.get("start_date", str(today))
    end = request.form.get("end_date", str(today + timedelta(days=7)))
    mode = request.form.get("mode", "judge")
    job = request.form.get("job_type", "formwork")

    forecast = get_weather(CITY, start, end)
    ai_schedule = generate_ai_schedule(forecast) if mode == "ai" else []
    df = pd.DataFrame()

    if mode != "ai":
        df = pd.DataFrame([{
            "시간": datetime.strptime(d["datetime"], "%Y-%m-%d").strftime('%m-%d'),
            "기온 (°C)": d["temp"], "습도 (%)": d["humidity"],
            "풍속 (m/s)": d["windspeed"], "강수량 (mm)": d["precip"],
            "작업 판단": check_job_feasibility(job, d["temp"], d["humidity"], d["windspeed"], d["precip"])
        } for d in forecast])

    if ai_schedule:
        pd.DataFrame(ai_schedule).to_excel(EXCEL_PATH, index=False)
        df_ai = pd.DataFrame(ai_schedule)
        df_ai['시작일'] = pd.to_datetime(df_ai['추천일'])
        df_ai['종료일'] = df_ai['시작일'] + pd.Timedelta(days=1)
        fig, ax = plt.subplots(figsize=(10, 4))
        for _, r in df_ai.iterrows():
            ax.barh(r['공정'], 1, left=r['시작일'], height=0.4)
        plt.tight_layout()
        fig.savefig(CHART_PATH)
        plt.close(fig)

    return render_template("index.html",
        df=df.values.tolist(),
        columns=df.columns.tolist(),
        job_options=JOB_OPTIONS,
        job_key=job,
        start_date=start,
        end_date=end,
        ai_schedule=ai_schedule
    )

@app.route("/download/excel")
def download_excel(): return send_file(EXCEL_PATH, as_attachment=True)

@app.route("/download/chart")
def download_chart(): return send_file(CHART_PATH, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

