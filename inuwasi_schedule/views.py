import re
import html
from datetime import datetime
from dateutil import parser
from googleapiclient.discovery import build
from django.shortcuts import render, get_list_or_404
from .models import Schedule_info
from django.conf import settings

API_KEY = settings.GOOGLE_API_KEY
CALENDAR_ID = settings.GOOGLE_CALENDAR_ID

import html
import re


def parse_event_description(description_text):
    venue_name = "위치 없음"
    address = "주소 없음"

    if description_text:
        # 1. HTML 엔티티(&nbsp; 등) 해제
        text = html.unescape(description_text)

        # 2. <p>, <br>, <div> 등 블록 태그를 줄바꿈(\n)으로 변환
        text = re.sub(r'</?(p|br|div|tr|td)\s*/?>', '\n', text, flags=re.IGNORECASE)

        # 3. 나머지 모든 HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)

        # 4. 특수 공백(\xa0, \t 등)을 일반 공백으로 변환 및 \r 제거
        text = text.replace('\xa0', ' ').replace('\r', '')

        # 5. 会場 (회장명) 추출
        # '会場:' 뒤부터 줄바꿈(\n) 전까지 추출하며, 중간에 ［, 【, [ 기호가 나오면 그 직전까지만 잘라냄
        venue_match = re.search(
            r"(?:会場)\s*[:：\-\】\s]\s*([^\n［【\[]+)",
            text,
            re.IGNORECASE,
        )
        if venue_match:
            venue_name = venue_match.group(1).strip()

        # 6. 住所 (주소) 추출
        # '住所:' 뒤부터 줄바꿈(\n) 전까지 추출하며, 중간에 ［, 【, [ 기호가 나오면 그 직전까지만 잘라냄
        address_match = re.search(
            r"(?:住所)\s*[:：\-\】\s]\s*([^\n［【\[]+)",
            text,
            re.IGNORECASE,
        )
        if address_match:
            address = address_match.group(1).strip()

    return venue_name, address


def get_schedule():
    try:
        service = build("calendar", "v3", developerKey=API_KEY)
        page_token = None
        success_cnt = 0
        total_cnt = 0

        print("=== 구글 캘린더 데이터 추출 시작 ===")

        while True:
            events_result = (
                service.events()
                .list(
                    calendarId=CALENDAR_ID,
                    singleEvents=True,
                    orderBy="startTime",
                    pageToken=page_token,
                    maxResults=250,
                )
                .execute()
            )

            events = events_result.get("items", [])

            for event in events:
                total_cnt += 1
                start_str = event["start"].get("dateTime", event["start"].get("date"))
                event_date = parser.parse(start_str).date()
                title = event.get("summary", "제목 없음")[:200]

                # description 파싱
                description = event.get("description", "")
                venue_name, address = parse_event_description(description)

                # description에 회장이 없는데 location 필드는 존재하는 경우
                if venue_name == "위치 없음" and event.get("location"):
                    venue_name = event.get("location")[:200]

                # DB 저장 (update_or_create)
                Schedule_info.objects.update_or_create(
                    event_title=title,
                    event_date=event_date,
                    defaults={
                        "idol_name": "inuwasi",
                        "event_category": "공식일정",
                        "event_location": venue_name[:200],
                        "event_address": address[:300],
                    },
                )

                if venue_name != "위치 없음" or address != "주소 없음":
                    success_cnt += 1
                    print(f"[성공] 날짜: {event_date} | 회장: {venue_name} | 주소: {address}")

            page_token = events_result.get("nextPageToken")
            if not page_token:
                break

        print(f"=== 동기화 완료 (전체 {total_cnt}건 중 장소/주소 추출 {success_cnt}건) ===")

    except Exception as e:
        print(f"구글 캘린더 연동 에러 발생: {e}")

def index(request):
    # get_schedule()
    return render(request, "index.html")


# 2. API 호출 없이 DB에서 지정한 기간의 데이터를 조회하는 뷰
# 2. DB에서 지정한 기간의 데이터를 조회하는 뷰 (DateField용 간소화)
def view_schedule(request):
    start_date = request.GET.get('start')  # 형식: 'YYYY-MM-DD'
    end_date = request.GET.get('end')      # 형식: 'YYYY-MM-DD'

    filter_kwargs = {}
    if start_date and end_date:
        # DateField 필터링: 문자열('YYYY-MM-DD') 그대로 range 검색 가능
        filter_kwargs['event_date__range'] = [start_date, end_date]

    # DB에서 필터링된 데이터 조회
    schedule_list = get_list_or_404(Schedule_info, **filter_kwargs)
    context = {"schedule_list": schedule_list}

    return render(request, "schedule.html", context)