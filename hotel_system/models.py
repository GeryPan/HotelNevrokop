from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from datetime import date

class Room(models.Model):
    ROOM_TYPES = [
        ('single', 'Единична стая'),
        ('double', 'Двойна стая'),
        ('suite', 'Апартамент'),
    ]
    
    number = models.CharField(max_length=10, unique=True, verbose_name="Номер на стая")
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='single', verbose_name="Тип стая")
    capacity = models.PositiveIntegerField(verbose_name="Капацитет")
    
    def __str__(self):
        return f"Стая {self.number} ({self.get_room_type_display()})"


class Guest(models.Model):
    name = models.CharField(max_length=100, verbose_name="Име на госта")
    phone_regex = RegexValidator(
        regex=r'^\+?[0-9]{7,15}$',
        message="Телефонният номер трябва да съдържа само цифри и да е между 7 и 15 символа. Допуска се '+' в началото."
    )
    phone = models.CharField(validators=[phone_regex], max_length=20, verbose_name="Телефон")
    email = models.EmailField(verbose_name="Имейл адрес")

    def __str__(self):
        return self.name


class Reservation(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name="Стая")
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, verbose_name="Гост")
    number_of_guests = models.PositiveIntegerField(default=1, verbose_name="Брой гости")
    check_in = models.DateField(verbose_name="Дата на настаняване")
    check_out = models.DateField(verbose_name="Дата на напускане")

    def clean(self):
        if self.check_in and self.check_out:
            if not self.pk and self.check_in < date.today():
                raise ValidationError("Датата на настаняване не може да бъде в миналото.")
            
            if self.check_out <= self.check_in:
                raise ValidationError("Датата на напускане трябва да е след датата на настаняване.")
            
            if self.number_of_guests < 1:
                raise ValidationError("Нужен е поне един гост да има.")
            
            # NoneType error if room is not selected
            if self.room and self.number_of_guests > self.room.capacity:
                raise ValidationError(
                    f"Броят гости ({self.number_of_guests}) надвишава капацитета на стаята ({self.room.capacity} легла)."
                )
            
            overlapping_reservations = Reservation.objects.filter(
                room=self.room,
                check_in__lt=self.check_out,
                check_out__gt=self.check_in
            )
            
            if self.pk:
                overlapping_reservations = overlapping_reservations.exclude(pk=self.pk)
                
            if overlapping_reservations.exists():
                raise ValidationError("Внимание: Тази стая вече е резервирана за избрания период!")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Резервация на {self.guest.name} за Стая {self.room.number} ({self.check_in} до {self.check_out})"