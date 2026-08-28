from django.db import models

# Create your models here.
class Schedule_info(models.Model):
    idol_name = models.CharField(max_length=50)
    event_category = models.CharField(max_length=100)
    event_title = models.CharField(max_length=200)
    event_date = models.DateField()

    # 장소명 및 주소 필드 분리
    event_location = models.CharField(max_length=200, default="위치 없음")
    event_address = models.CharField(
        max_length=300, null=True, blank=True, default="주소 없음"
    )
    def __str__(self):
        return f"[{self.idol.name}] {self.event_title}"

