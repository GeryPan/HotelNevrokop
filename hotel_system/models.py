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


class RoomServiceOrder(models.Model):
    MENU_ITEMS = [
        # Alcohol
        ('wine_white', 'Бяло вино (бутилка) - 20.00 лв.'),
        ('wine_red', 'Червено вино (бутилка) - 22.00 лв.'),
        ('whiskey_scot', 'Шотландско уиски (50ml) - 8.00 лв.'),
        ('whiskey_irish', 'Ирландско уиски (50ml) - 7.50 лв.'),
        ('vodka', 'Водка Премиум (50ml) - 6.00 лв.'),
        ('champagne', 'Шампанско (бутилка) - 25.00 лв.'),
        ('rakia', 'Домашна ракия (50ml) - 5.00 лв.'),
        ('mastika', 'Мастика (50ml) - 4.50 лв.'),
        ('ouzo', 'Узо (50ml) - 5.00 лв.'),
        # Snacks
        ('nuts', 'Микс ядки - 5.00 лв.'),
        ('chocolate', 'Шоколад - 4.00 лв.'),
        ('pretzels', 'Солети - 1.50 лв.'),
        ('chips', 'Чипс Голям - 3.50 лв.'),
        # Drinks
        ('juice', 'Натурален сок - 3.50 лв.'),
        ('water', 'Минерална вода - 2.00 лв.'),
        ('cola', 'Кока-Кола - 3.00 лв.'),
        ('fanta', 'Фанта - 3.00 лв.'),
        ('sprite', 'Спрайт - 3.00 лв.'),
        ('lemonade', 'Домашна лимонада - 4.50 лв.'),
        ('coffee', 'Кафе Еспресо - 2.50 лв.'),
        ('cappuccino', 'Капучино - 3.50 лв.'),
        ('tea', 'Билков чай - 2.50 лв.'),
        ('frappe', 'Фрапе - 4.00 лв.'),
        # And other things
        ('slice_lemon', 'Резенчета лимон - 0.10 лв.'),
        ('ice', 'Лед - 0.00 лв.', ),
        ('milk', 'Прясно мляко (30ml) - 0.50 лв.'),
        ('ice_cream', 'Сладолед (1 топка) - 3.00 лв.'),
        ('cream', 'Сметана (20ml) - 0.50 лв.'),
    ]

    PRICES = {
        'wine_white': 20.00, 'wine_red': 22.00, 'whiskey_scot': 8.00, 'whiskey_irish': 7.50,
        'vodka': 6.00, 'champagne': 25.00, 'rakia': 5.00, 'mastika': 4.50, 'ouzo': 5.00,
        'nuts': 5.00, 'chocolate': 4.00, 'pretzels': 1.50, 'chips': 3.50,
        'juice': 3.50, 'water': 2.00, 'cola': 3.00, 'fanta': 3.00, 'sprite': 3.00,
        'lemonade': 4.50, 'coffee': 2.50, 'cappuccino': 3.50, 'tea': 2.50, 'frappe': 4.00,
        'slice_lemon': 0.10, 'ice' : 0.00, 'milk': 0.50, 'ice_cream': 3.00, 'cream': 0.50
    }

    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, verbose_name="Резервация за стая")
    item = models.CharField(max_length=50, choices=MENU_ITEMS, verbose_name="Продукт")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    ordered_at = models.DateTimeField(auto_now_add=True, verbose_name="Час на поръчка")

    @property
    def order_total(self):
        return self.PRICES.get(self.item, 0.00) * self.quantity

    def __str__(self):
        return f"Стая {self.reservation.room.number} - {self.get_item_display()} x{self.quantity}"