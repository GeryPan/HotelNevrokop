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
    price_per_night = models.DecimalField(max_digits=6, decimal_places=2, default=50.00, verbose_name="Цена на нощувка")

    @property
    def is_cleaned_today(self):
        return self.housekeeping_set.filter(date=date.today(), is_cleaned=True).exists()

    @property
    def active_room_service_total(self):
        # currnet reservation for the room
        current_res = self.reservation_set.order_by('-check_in').first()
        if current_res:
            return sum(order.order_total for order in current_res.roomserviceorder_set.all())
        return 0

    @property
    def today_cleaner(self):
        last_cleaning = self.housekeeping_set.filter(date=date.today(), is_cleaned=True).last()
        return last_cleaning.cleaner_name if last_cleaning else None

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

    @property
    def total_price(self):
        stay_duration = (self.check_out - self.check_in).days
        # incorrect dates handling
        if stay_duration <= 0:
            return 0
            
        return stay_duration * self.room.price_per_night

    def clean(self):
        # if fields are missing
        if not self.check_in or not self.check_out or not self.room:
            return

        # past check-in date
        if not self.pk and self.check_in < date.today():
            raise ValidationError("Датата на настаняване не може да бъде в миналото.")
        
        if self.check_out <= self.check_in:
            raise ValidationError("Датата на напускане трябва да е след датата на настаняване.")
        
        if self.number_of_guests < 1:
            raise ValidationError("Нужен е поне един гост да има.")
        
        if self.number_of_guests > self.room.capacity:
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


class Housekeeping(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name="Стая")
    date = models.DateField(default=date.today, verbose_name="Дата на почистване")
    is_cleaned = models.BooleanField(default=False, verbose_name="Почистена")
    cleaner_name = models.CharField(max_length=100, default="Дежурна камериерка", verbose_name="Име на камериерка")
    notes = models.TextField(blank=True, verbose_name="Бележки")

    def clean(self):
        if self.date > date.today():
            raise ValidationError("Датата на почистване не може да бъде в бъдещето.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        status = "Изчистена" if self.is_cleaned else "За почистване"
        return f"Стая {self.room.number} - {self.cleaner_name} ({status})"


class RoomServiceItem(models.Model):
    name = models.CharField(max_length=100, verbose_name="Име на продукта")
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Цена (лв.)")

    def __str__(self):
        return f"{self.name} - {self.price} лв."


def populate_default_menu():
    default_items = {
        'Бяло вино (бутилка)': 20.00, 'Червено вино (бутилка)': 22.00,
        'Шотландско уиски (50ml)': 8.00, 'Ирландско уиски (50ml)': 7.50,
        'Водка Премиум (50ml)': 6.00, 'Шампанско (бутилка)': 25.00,
        'Домашна ракия (50ml)': 5.00, 'Мастика (50ml)': 4.50, 'Узо (50ml)': 5.00,
        'Микс ядки': 5.00, 'Шоколад': 4.00, 'Солети': 1.50, 'Чипс Голям': 3.50,
        'Натурален сок': 3.50, 'Минерална вода': 2.00, 'Кока-Кола': 3.00,
        'Фанта': 3.00, 'Спрайт': 3.00, 'Домашна лимонада': 4.50,
        'Кафе Еспресо': 2.50, 'Капучино': 3.50, 'Билков чай': 2.50, 'Фрапе': 4.00,
        'Лед': 0.00, 'Резенчета лимон': 0.10, 'Прясно мляко (30ml)': 0.50,
        'Сладолед (1 топка)': 3.00, 'Сметана (20ml)': 0.50
    }
    return default_items

class RoomServiceOrder(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, verbose_name="Резервация за стая")
    item = models.ForeignKey(RoomServiceItem, on_delete=models.CASCADE, verbose_name="Продукт")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    ordered_at = models.DateTimeField(auto_now_add=True, verbose_name="Час на поръчка")

    @property
    def order_total(self):
        return self.item.price * self.quantity

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Количеството на поръчката трябва да бъде поне 1.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Стая {self.reservation.room.number} - {self.item.name} x{self.quantity}"


from django.db.models.signals import post_migrate
from django.dispatch import receiver

# au6tomatically populate the RoomServiceItem menu after migrations
@receiver(post_migrate)
def load_default_menu(sender, **kwargs):
    # current app check for the signal to avoid running this for other apps
    if sender.name == 'hotel_system':
        menu = populate_default_menu()
        for name, price in menu.items():
            # duplicate check to avoid creating the same item multiple times
            RoomServiceItem.objects.get_or_create(name=name, defaults={'price': price})