import os
import pandas as pd
import django

# Django 환경 설정
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")  # 프로젝트명에 맞게 수정
django.setup()

from inuwasi_schedule.models import Idol_info, Schedule_info

df_schedule = pd.read_csv("../sv_mod-country_info,sv_mod-idol_info,sv_mod-raw/sv_mod-schedule_info.csv", encoding="utf-8-sig")

# ★ 날짜 포맷을 Django가 인식하는 YYYY-MM-DD 문자열 형태로 일괄 변환
df_schedule["event_date"] = pd.to_datetime(df_schedule["event_date"]).dt.strftime("%Y-%m-%d")

# pandas NaN(빈값)을 None(SQL NULL)으로 치환
df_schedule = df_schedule.where(pd.notnull(df_schedule), None)

for _, row in df_schedule.iterrows():
    idol_obj = Idol_info.objects.get(idol_id=row["idol_id"])
    Schedule_info.objects.update_or_create(
        id=row["id"],
        defaults={
            "idol": idol_obj,
            "event_category": row.get("event_category"),
            "event_title": row["event_title"],
            "event_date": row["event_date"], # YYYY-MM-DD
            "event_address": row.get("event_address"),
            "event_location": row.get("event_location"),
        }
    )

print("=== 모든 CSV 데이터가 DB에 성공적으로 저장되었습니다! ===")