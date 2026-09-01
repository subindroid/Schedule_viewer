import html
import re
from datetime import datetime
from dateutil import parser
from googleapiclient.discovery import build

from django.conf import settings
from django.shortcuts import render, get_list_or_404
from .models import Country_info, Idol_info, Schedule_info

API_KEY = settings.GOOGLE_API_KEY

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
        venue_match = re.search(
            r"(?:会場)\s*[:：\-\】\s]\s*([^\n［【\[]+)",
            text,
            re.IGNORECASE,
        )
        if venue_match:
            venue_name = venue_match.group(1).strip()

        # 6. 住所 (주소) 추출
        address_match = re.search(
            r"(?:住所)\s*[:：\-\】\s]\s*([^\n［【\[]+)",
            text,
            re.IGNORECASE,
        )
        if address_match:
            address = address_match.group(1).strip()

    return venue_name, address


def process_title_and_category(raw_title):
    """
    구글 캘린더 summary에서 [카테고리]와 「제목」을 분리하는 함수
    """
    category = "[공식일정]"
    title = raw_title.strip()

    # [카테고리], ［카테고리］, 【카테고리】 패턴 분리
    match = re.match(r"^[\(\[\［\【](.+?)[\)\]\］\】]\s*(.+)$", title)
    if match:
        category = f"[{match.group(1)}]"
        title = match.group(2).strip()

    # 「 」 감싸기 포맷팅
    title = re.sub(r'^[「\s]+|[」\s]+$', '', title)  # 기존 「 」 및 공백 정돈
    title = f"「{title}」"

    return category, title[:250]

def get_schedule():
    try:
        service = build("calendar", "v3", developerKey=API_KEY)

        # 2. DB에 등록된 모든 아이돌(또는 특정 아이돌)을 조회합니다.
        idols = Idol_info.objects.all()

        for idol_obj in idols:
            # DB에 저장된 각 아이돌의 calendar_id를 사용합니다.
            calendar_id = idol_obj.calendar_id

            if not calendar_id:
                print(f"[{idol_obj.idol}] calendar_id가 설정되어 있지 않습니다.")
                continue

            page_token = None
            success_cnt = 0
            total_cnt = 0

            print(f"=== [{idol_obj.idol}] 구글 캘린더 데이터 추출 시작 ===")

            while True:
                events_result = (
                    service.events()
                    .list(
                        calendarId=calendar_id,  # DB에서 가져온 calendar_id 사용
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
                    start_str = event["start"].get(
                        "dateTime", event["start"].get("date")
                    )
                    event_date = parser.parse(start_str).date()
                    raw_summary = event.get("summary", "제목 없음")

                    category, formatted_title = process_title_and_category(
                        raw_summary
                    )
                    description = event.get("description", "")
                    venue_name, address = parse_event_description(description)

                    if venue_name == "위치 없음" and event.get("location"):
                        venue_name = event.get("location")[:200]

                    # 해당 idol_obj 객체와 매핑하여 저장
                    Schedule_info.objects.update_or_create(
                        idol=idol_obj,
                        event_title=formatted_title,
                        event_date=event_date,
                        defaults={
                            "event_category": category,
                            "event_location": venue_name[:200],
                            "event_address": address[:300],
                        },
                    )

                    if venue_name != "위치 없음" or address != "주소 없음":
                        success_cnt += 1

                page_token = events_result.get("nextPageToken")
                if not page_token:
                    break

            print(
                f"=== [{idol_obj.idol}] 동기화 완료 (전체 {total_cnt}건 중 장소/주소 추출 {success_cnt}건) ==="
            )

    except Exception as e:
        print(f"구글 캘린더 연동 에러 발생: {e}")

def index(request):
    return render(request, "index.html")


def view_schedule(request):
    start_date = request.GET.get('start')  # 'YYYY-MM-DD'
    end_date = request.GET.get('end')      # 'YYYY-MM-DD'

    filter_kwargs = {}
    if start_date and end_date:
        filter_kwargs['event_date__range'] = [start_date, end_date]

    # Foreign Key 조회를 위해 select_related 적용 (DB 쿼리 최적화)
    schedule_queryset = Schedule_info.objects.filter(**filter_kwargs).select_related('idol', 'idol__country')
    
    schedule_list = get_list_or_404(schedule_queryset)
    context = {"schedule_list": schedule_list}

    return render(request, "schedule.html", context)