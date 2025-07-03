from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Appointment
from datetime import datetime, time, timedelta
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from .models import Appointment, Notification
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView




def index(request):
    return render(request, 'booking/index.html')

def success(request):
    return render(request, 'booking/success.html')

def pret(request):
    services = [
        {"name": "Manichiură clasică", "duration": "35 min", "price": 50, "icon": "fa-solid fa-hand-sparkles"},
        {"name": "Manichiură semipermanentă", "duration": "1 h 40 min", "price": 120, "icon": "fa-solid fa-brush"},
        {"name": "Construcție gel", "duration": "3 h", "price": 250, "icon": "fa-solid fa-gem"},
        {"name": "Construcție slim", "duration": "3 h 30 min", "price": 270, "icon": "fa-solid fa-star"},
        {"name": "Întreținere gel", "duration": "2 h", "price": 150, "icon": "fa-solid fa-wand-magic"},
        {"name": "Pedichiură clasică", "duration": "1 h", "price": 80, "icon": "fa-solid fa-shoe-prints"},
        {"name": "Pedichiură oja semipermanentă", "duration": "1 h 20 min", "price": 100, "icon": "fa-solid fa-paintbrush"},
        {"name": "Epilat lung", "duration": "30 min", "price": 60, "icon": "fa-solid fa-water"},
        {"name": "Epilat scurt", "duration": "15 min", "price": 40, "icon": "fa-solid fa-scissors"},
        {"name": "Epilat inghinal total", "duration": "30 min", "price": 60, "icon": "fa-solid fa-droplet"},
        {"name": "Epilat axilă", "duration": "10 min", "price": 20, "icon": "fa-solid fa-wind"},
        {"name": "Epilat brațe", "duration": "15 min", "price": 40, "icon": "fa-solid fa-hand-back-fist"},
        {"name": "Epilat mustață", "duration": "10 min", "price": 20, "icon": "fa-solid fa-face-grin"},
        {"name": "Epilat spate & abdomen", "duration": "20 min", "price": 50, "icon": "fa-solid fa-person"},
        {"name": "Pensat", "duration": "30 min", "price": 35, "icon": "fa-solid fa-eye"},
        {"name": "Vopsit sprâncene/gene", "duration": "10 min", "price": 30, "icon": "fa-solid fa-magic-wand-sparkles"},
    ]
    return render(request, 'booking/preturi.html', {'services': services})


def book(request):
    available_times = []
    selected_date = None
    selected_service = None

    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        service = request.POST.get('service')
        date = request.POST.get('date')
        time_str = request.POST.get('time')

        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            time_obj = datetime.strptime(time_str, '%H:%M').time()

            # Verificare suprapunere
            exists = Appointment.objects.filter(date=date_obj, time=time_obj).exists()
            if exists:
                messages.warning(request, 'Această oră este deja rezervată!')
                return redirect('book')

            Appointment.objects.create(
                name=name,
                phone=phone,
                service=service,
                date=date_obj,
                time=time_obj
            )
            
            messages.success(request, 'Programare realizată cu succes!')
            return redirect('success')
        except ValueError:
            messages.error(request, 'Data sau ora introduse nu sunt valide!')
        except ValidationError as e:
            messages.error(request, str(e))

    if request.GET.get('date') and request.GET.get('service'):
        try:
            selected_date = datetime.strptime(request.GET.get('date'), '%Y-%m-%d').date()
            selected_service = request.GET.get('service')
            duration = Appointment.SERVICE_DURATIONS.get(selected_service, 30)
            booked = Appointment.objects.filter(date=selected_date).values('time', 'service')

            all_times = [f"{h:02d}:{m:02d}" for h in range(9, 24) for m in (0, 30)]
            for t in all_times:
                start = datetime.combine(selected_date, datetime.strptime(t, '%H:%M').time())
                end = start + timedelta(minutes=duration)
                conflict = False
                for appt in booked:
                    appt_start = datetime.combine(selected_date, appt['time'])
                    appt_end = appt_start + timedelta(minutes=Appointment.SERVICE_DURATIONS.get(appt['service'], 30))
                    if not (end <= appt_start or start >= appt_end):
                        conflict = True
                        break
                if not conflict and end.time() <= time(23, 59):
                    available_times.append(t)
        except ValueError:
            available_times = []

    context = {
        'available_times': available_times,
        'selected_date': request.GET.get('date', ''),
        'selected_service': request.GET.get('service', ''),
        'service_choices': Appointment.SERVICE_CHOICES,
    }
    return render(request, 'booking/book.html', context)



def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        appointment.delete()
        messages.success(request, 'Programarea a fost anulată cu succes.')
        return redirect('cancel')

    return render(request, 'booking/cancel_confirm.html', {'appointment': appointment})

def cancel(request):
    return render(request, 'booking/cancel.html')

@login_required
def appointments_list(request):
    appointments = Appointment.objects.all().order_by('date', 'time')
    return render(request, 'booking/appointments_list.html', {'appointments': appointments})

@login_required
def change_appointment_status(request, appointment_id, new_status):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    if new_status not in ['confirmed', 'canceled']:
        messages.error(request, "Status invalid!")
        return redirect('appointments_list')

    appointment.status = new_status
    appointment.save()

    # Creează o notificare pentru client
    if new_status == 'confirmed':
        msg = "Programarea ta a fost confirmată. Te așteptăm!"
    else:
        msg = "Programarea ta a fost anulată. Ne pare rău!"

    Notification.objects.create(appointment=appointment, message=msg)
    messages.success(request, f"Programarea a fost {new_status}.")
    return redirect('appointments_list')

def notifications(request):
    phone = request.GET.get('phone')
    notifications = []
    if phone:
        notifications = Notification.objects.filter(
            appointment__phone=phone
        ).order_by('-created_at')
    return render(request, 'booking/notifications.html', {'notifications': notifications, 'phone': phone})


def check_appointments(request):
    appointments = []
    searched = False
    phone = ""

    if request.method == "POST":
        phone = request.POST.get("phone")
        searched = True
        appointments = Appointment.objects.filter(phone=phone).order_by('-date', '-time')

    return render(request, 'booking/check_appointments.html', {
        'appointments': appointments,
        'phone': phone,
        'searched': searched
    })


class RestrictedLoginView(LoginView):
    template_name = 'booking/login.html'

    def dispatch(self, request, *args, **kwargs):
        # Verificăm dacă utilizatorul este deja autentificat
        if request.user.is_authenticated:
            return redirect('index')

        # Verificăm dacă utilizatorul este în grupul "staff_salon" sau este superuser
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        if request.user.is_superuser or request.user.groups.filter(name='staff_salon').exists():
            return super().dispatch(request, *args, **kwargs)
        else:
            messages.error(request, "Nu ai permisiunea de a accesa pagina de autentificare.")
            return redirect('index')

def servicii(request):
    servicii_list = [
        {'nume': 'Manichiură clasică', 'descriere': 'Îngrijire perfectă pentru unghii elegante.'},
        {'nume': 'Manichiură semipermanentă', 'descriere': 'Frumusețe care ține până la 3 săptămâni.'},
        {'nume': 'Construcție gel', 'descriere': 'Unghii rezistente și perfecte.'},
        {'nume': 'Pedichiură clasică', 'descriere': 'Relaxare și prospețime pentru picioarele tale.'},
        {'nume': 'Epilat', 'descriere': 'Piele fină și netedă – adio fire de păr nedorite!'},
        {'nume': 'Pensat', 'descriere': 'Sprâncene perfect conturate.'},
        {'nume': 'Vopsit sprâncene/gene', 'descriere': 'Privire intensă și expresivă.'},
        # adaugă aici ce servicii vrei cu descrieri
    ]
    return render(request, 'booking/servicii.html', {'servicii': servicii_list})
