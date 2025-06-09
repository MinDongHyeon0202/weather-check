from flask import Flask, render_template, request, send_file
import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt

load_dotenv()
app = Flask(__name__)

API_KEY = os.getenv("API_KEY")
CITY = "Seoul"
VISUAL_API_KEY = os.getenv("VISUAL_API_KEY")

JOB_OPTIONS = {
    "formwork": "외부비계설치",
    "fence": "휀스설치",
    "excavation": "터파기",
    "soil_reinforce": "지반보강",
    "backfill": "되메우기",
    "concrete_base": "버림콘크리트",
    "concrete_floor": "기초타설",
    "floor1": "1층 타설",
    "floor2": "2층 타설",
    "floor3": "3층 타설",
    "floor4": "4층 타설",
    "floor5": "5층 타설",
    "roof": "지붕 타설",
    "waterproof_bath": "화장실 방수",
    "waterproof_balcony": "발코니 방수",
    "waterproof_roof": "옥상 방수",
    "interior_plaster": "내부 미장",
    "exterior_plaster": "외벽 미장",
    "foam": "기포 타설",
    "floor_finish": "방통",
    "wood_partition": "목공 벽체",
    "wood_ceiling": "목공 천정",
    "wallpaper": "벽지",
    "flooring": "마루 시공",
    "tile_balcony": "발코니 타일",
    "stone_stair": "계단 석재",
    "window_frame": "창문틀",
    "glass": "유리 끼우기",
    "insulate_base": "기초 단열",
    "insulate_wall": "외벽 단열",
    "insulate_roof": "지붕 단열",
    "brick_tile": "벽돌 타일",
    "water_repellent": "발수재 도포",
    "interior_paint": "내부 도장",
    "exterior_paint": "외부 도장",
    "roof_metal": "AL두겁",
    "gutter": "홈통 설치",
    "railing": "난간 설치",
    "sink": "씽크대",
    "cabinet": "신발장",
    "light": "조명",
    "wiring": "배선",
    "telecom": "통신",
    "pipe": "배관",
    "equipment": "설비",
    "fire": "소화기",
    "sewage": "오배수",
    "gas": "가스관",
    "paving": "포장"
}

def check_job_feasibility(job_type, temp, humidity, wind, rain):
    if rain > 2:
        return "❌ 불가 (강수량)"
    if temp < -5 or temp > 35:
        return "⚠️ 주의 (극한 온도)"
    if humidity > 90 and '도장' in JOB_OPTIONS.get(job_type, ''):
        return "❌ 불가 (습도)"
    if '타설' in JOB_OPTIONS.get(job_type, '') and rain > 0:
        return "❌ 불가 (비 예보)"
    return "✅ 가능"

def get_weather_from_visualcrossing(city, start_date, end_date):
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}/{start_date}/{end_date}?unitGroup=metric&key={VISUAL_API_KEY}&include=days"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    data = response.json()
    return data.get("days", [])

def generate_ai_schedule(forecast_list):
    schedule = []
    used_dates = set()
    for job_key, job_name in JOB_OPTIONS.items():
        for day in forecast_list:
            date = day["datetime"]
            if date in used_dates:
                continue
            temp = day.get("temp", 0)
            humidity = day.get("humidity", 0)
            wind = day.get("windspeed", 0)
            rain = day.get("precip", 0)
            result = check_job_feasibility(job_key, temp, humidity, wind, rain)
            if result.startswith("✅"):
                schedule.append({"공정": job_name, "추천일": date, "사유": result})
                used_dates.add(date)
                break
    return schedule

@app.route("/", methods=["GET", "POST"])
def index():
    today = datetime.now(pytz.timezone('Asia/Seoul')).date()
    start_str = request.form.get("start_date")
    end_str = request.form.get("end_date")
    selected_job = request.form.get("job_type", "formwork")

    start_date = datetime.strptime(start_str, "%Y-%m-%d").date() if start_str else today
    end_date = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else today + timedelta(days=14)

    forecast_list = get_weather_from_visualcrossing(CITY, start_date.isoformat(), end_date.isoformat())
    ai_schedule = generate_ai_schedule(forecast_list)

    # 판단 리스트
    times, temps, humidities, winds, rains, judgments = [], [], [], [], [], []
    for day in forecast_list:
        dt = datetime.strptime(day["datetime"], "%Y-%m-%d")
        temp = day.get("temp", 0)
        humidity = day.get("humidity", 0)
        wind = day.get("windspeed", 0)
        rain = day.get("precip", 0)
        result = check_job_feasibility(selected_job, temp, humidity, wind, rain)

        times.append(dt.strftime('%m-%d'))
        temps.append(temp)
        humidities.append(humidity)
        winds.append(wind)
        rains.append(비)
        judgments.append(result)

    df = pd.DataFrame({
        "시간": times,
        "기온 (°C)": temps,
        "습도 (%)": humidities,
        "풍속 (m/s)": winds,
        "강수량 (mm)": rains,
        "작업 판단": judgments
    })

    # Excel 저장
    excel_path = "/mnt/data/ai_schedule.xlsx"
    pd.DataFrame(ai_schedule).to_excel(excel_path, index=False)

    # Gantt 차트 저장
    df_ai = pd.DataFrame(ai_schedule)
    if not df_ai.empty:
        df_ai['시작일'] = pd.to_datetime(df_ai['추천일'])
        df_ai['종료일'] = df_ai['시작일'] + pd.Timedelta(days=1)
        fig, ax = plt.subplots(figsize=(10, 4))
        for i, row in df_ai.iterrows():
            ax.barh(row['공정'], (row['종료일'] - row['시작일']).days, left=row['시작일'], height=0.4)
        ax.set_xlabel("날짜")
        ax.set_ylabel("공정명")
        ax.set_title("🤖 AI 추천 공정 스케줄 (Gantt Chart)")
        plt.tight_layout()
        gantt_path = "/mnt/data/ai_schedule_gantt_chart.png"
        fig.savefig(gantt_path)
        plt.close(fig)

    return render_template("index.html",
        df=df.values.tolist(),
        columns=df.columns.tolist(),
        job_options=JOB_OPTIONS,
        job_key=selected_job,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        ai_schedule=ai_schedule
    )

@app.route("/download/excel")
def download_excel():
    return send_file("/mnt/data/ai_schedule.xlsx", as_attachment=True)

@app.route("/download/chart")
def download_chart():
    return send_file("/mnt/data/ai_schedule_gantt_chart.png", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
