from django.db import models

class Attendance(models.Model):
    attendance_id = models.AutoField(primary_key=True)
    
    # Exact column mappings from your SQL
    staff_id = models.CharField(max_length=32, db_column='staff_id')
    surname = models.CharField(max_length=80, db_column='surname')
    other_name = models.CharField(max_length=120, blank=True, null=True, db_column='other_name')
    
    date = models.DateField(db_column='work_date')
    time_in = models.TimeField(null=True, blank=True, db_column='time_in')
    time_out = models.TimeField(null=True, blank=True, db_column='time_out')

    photo_in = models.ImageField(upload_to="", blank=True, null=True, db_column='photo_in')
    photo_out = models.ImageField(upload_to="", blank=True, null=True, db_column='photo_out')
    
    # photo_in = models.ImageField(upload_to="attendance/photos/", blank=True, null=True, db_column='photo_in')
    # photo_out = models.ImageField(upload_to="attendance/photos/", blank=True, null=True, db_column='photo_out')

    class Meta:
        managed = False
        db_table = 'Attendance'  # Exact casing for PostgreSQL

    def __str__(self):
        return f"{self.staff_id} - {self.date} {self.time_in}"