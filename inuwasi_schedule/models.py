from django.db import models


class Country_info(models.Model):
    # Django 기본 PK(id) 대신 엑셀의 country_id를 PK로 사용하는 경우
    country_id = models.AutoField(primary_key=True)
    country = models.CharField(max_length=50)

    class Meta:
        db_table = 'country'
        verbose_name = '국가'
        verbose_name_plural = '국가 목록'

    def __str__(self):
        return self.country


class Idol_info(models.Model):
    idol_id = models.AutoField(primary_key=True)
    idol = models.CharField(max_length=100)

    # Country_info 참조 (외래키)
    country = models.ForeignKey(
        Country_info,
        on_delete=models.CASCADE,
        db_column="country_id",  # DB의 실제 컬럼명을 country_id로 지정
        related_name="idols",
    )
    calendar_id = models.CharField(max_length=255)

    class Meta:
        db_table = 'idol'
        verbose_name = '아이돌'
        verbose_name_plural = '아이돌 목록'

    def __str__(self):
        return self.idol


class Schedule_info(models.Model):
    # Idol_info 참조 (외래키)
    idol = models.ForeignKey(
        Idol_info,
        on_delete=models.CASCADE,
        db_column="idol_id",  # DB의 실제 컬럼명을 idol_id로 지정
        related_name="schedules",
    )

    event_category = models.CharField(max_length=100, null=True, blank=True)
    event_title = models.CharField(max_length=250)
    event_date = models.DateField()
    event_address = models.CharField(
        max_length=300, null=True, blank=True, default="주소 없음"
    )
    event_location = models.CharField(
        max_length=200, null=True, blank=True, default="위치 없음"
    )

    class Meta:
        db_table = 'schedule'
        verbose_name = '스케줄'
        verbose_name_plural = '스케줄 목록'

    def __str__(self):
        return f"[{self.idol.idol}] {self.event_title}"