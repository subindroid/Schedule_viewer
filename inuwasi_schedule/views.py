from django.shortcuts import get_list_or_404, render
from .models import Country_info, Schedule_info


def index(request):
    # 등록된 모든 국가 목록 조회 (아이돌 목록도 함께 불러오기 최적화)
    countries = Country_info.objects.prefetch_related("idols").all()
    context = {"countries": countries}
    return render(request, "index.html", context)


def view_schedule(request):
    start_date = request.GET.get("start")
    end_date = request.GET.get("end")
    idol_id = request.GET.get("idol_id")  # 선택된 아이돌 ID

    filter_kwargs = {}

    if start_date and end_date:
        filter_kwargs["event_date__range"] = [start_date, end_date]

    if idol_id:
        filter_kwargs["idol_id"] = idol_id  # 외래키 ID로 필터링

    schedule_queryset = Schedule_info.objects.filter(
        **filter_kwargs
    ).select_related("idol", "idol__country")

    schedule_list = get_list_or_404(schedule_queryset)
    context = {"schedule_list": schedule_list}

    return render(request, "schedule.html", context)