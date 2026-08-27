from datetime import datetime
from dateutil import parser
from googleapiclient.discovery import build
from django.shortcuts import render, get_list_or_404
from .models import Schedule_info
from django.conf import settings

API_KEY = settings.GOOGLE_API_KEY
CALENDAR_ID = settings.GOOGLE_CALENDAR_ID

def get_schedule():
    try:
        service = build("calendar", "v3", developerKey=API_KEY)
        page_token = None
        total_created = 0
        total_skipped = 0
        page_cnt = 1

        print("=== 구글 캘린더 동기화 시작 ===")

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
            print(f"[{page_cnt}페이지] {len(events)}개 일정 가져오는 중...")

            for event in events:
                try:
                    start_str = event["start"].get("dateTime", event["start"].get("date"))

                    # 타임존에 상관없이 naive datetime으로 변환
                    # parsed_dt = parser.parse(start_str)
                    # event_date = parsed_dt.replace(tzinfo=None)
                    event_date = parser.parse(start_str).date()

                    # DB max_length 에러 방지를 위해 200자 제한 (필요시 조절)
                    title = event.get("summary", "제목 없음")[:200]

                    # DB에 저장
                    _, created = Schedule_info.objects.get_or_create(
                        event_title=title,
                        event_date=event_date,
                        defaults={
                            "idol_name": "아이돌명",
                            "event_category": "공식일정",
                        },
                    )

                    if created:
                        total_created += 1
                    else:
                        total_skipped += 1

                except Exception as event_err:
                    print(f"개별 일정 저장 실패 (건너뜀) - 제목: {event.get('summary')}, 에러: {event_err}")

            page_token = events_result.get("nextPageToken")
            if not page_token:
                break

            page_cnt += 1

        print(f"=== 동기화 완료: 신규 추가 {total_created}건 / 기존 건너뜀 {total_skipped}건 ===")

    except Exception as e:
        print(f"구글 캘린더 연동 중 치명적 에러 발생: {e}")

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