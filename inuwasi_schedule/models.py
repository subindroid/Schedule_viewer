from django.db import models

# Create your models here.
class Schedule_info(models.Model):
    idol_name = models.CharField(max_length=50)
    event_category = models.CharField(max_length=100)
    event_title = models.CharField(max_length=200)
    event_date = models.DateField()
    def __str__(self):
        return f"[{self.idol.name}] {self.event_title}"

