from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta, time
from django.utils import timezone

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'În așteptare'),
        ('confirmed', 'Confirmată'),
        ('canceled', 'Anulată'),
        ('completed', 'Finalizată'),
        ('no_show', 'Nu s-a prezentat'),
    ]

    SERVICE_CHOICES = [
        ('manicure_classic', 'Manichiură clasică'),
        ('manicure_semi', 'Manichiură semipermanentă'),
        ('gel_build', 'Construcție gel'),
        ('gel_slim', 'Construcție slim'),
        ('gel_maintenance', 'Întreținere gel'),
        ('pedicure_classic', 'Pedichiură clasică'),
        ('pedicure_semi', 'Pedichiură ojă semipermanentă'),
        ('epilat_long', 'Epilat lung'),
        ('epilat_short', 'Epilat scurt'),
        ('epilat_inghinal', 'Epilat inghinal total'),
        ('epilat_axila', 'Epilat axilă'),
        ('epilat_brate', 'Epilat brațe'),
        ('epilat_mustata', 'Epilat mustață'),
        ('epilat_spate_abdomen', 'Epilat spate & abdomen'),
        ('pensat', 'Pensat'),
        ('vopsit_sprancene_gene', 'Vopsit sprâncene/gene'),
    ]

    SERVICE_DURATIONS = {
        'manicure_classic': 35,
        'manicure_semi': 100,
        'gel_build': 180,
        'gel_slim': 210,
        'gel_maintenance': 120,
        'pedicure_classic': 60,
        'pedicure_semi': 80,
        'epilat_long': 30,
        'epilat_short': 15,
        'epilat_inghinal': 30,
        'epilat_axila': 10,
        'epilat_brate': 15,
        'epilat_mustata': 10,
        'epilat_spate_abdomen': 20,
        'pensat': 30,
        'vopsit_sprancene_gene': 10,
    }
    

    MAX_APPOINTMENTS_PER_DAY = 12  # poți modifica limita aici

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    service = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Verifică suprapunerea programărilor doar dacă nu e anulată
        if self.status != 'canceled':
            duration = timedelta(minutes=self.SERVICE_DURATIONS.get(self.service, 30))
            start_time = datetime.combine(self.date, self.time)
            end_time = start_time + duration

            overlapping = Appointment.objects.filter(
                date=self.date,
                time__range=(start_time.time(), (end_time - timedelta(minutes=1)).time())
            ).exclude(id=self.id).exclude(status='canceled')

            if overlapping.exists():
                raise ValidationError('Această oră este ocupată pentru durata selectată!')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.service} pe {self.date} la {self.time} [{self.status}]"


class Notification(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notificare pentru {self.appointment.name}: {self.message[:30]}"