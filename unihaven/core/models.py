# models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import math
import uuid  # 用于生成唯一的 Token
from datetime import timedelta, datetime

class Owner(models.Model):
    """
    Property owner who offers accommodations for rent
    Primary Key:
        - email: Unique email address for the owner
    """
    name = models.CharField(max_length=200, blank=False, null=False)
    email = models.EmailField(primary_key=True, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Owner"
        verbose_name_plural = "Owners"

    def __str__(self):
        return self.name

class University(models.Model):
    """
    University that owns the campus
    Primary Key:
        - (country, name): The combination of country and university name
    """
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100, blank=False)
    address = models.TextField(blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # 添加 Token 字段
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('country', 'name')
        verbose_name = "University"
        verbose_name_plural = "Universities"

    def __str__(self):
        return self.name

class Campus(models.Model):
    """
    Campus or premises of a university for distance calculation
    """
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    university = models.ForeignKey(
        University,
        related_name='campuses',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('university', 'name')
        verbose_name = "Campus"
        verbose_name_plural = "Campuses"

    def __str__(self):
        return f"{self.name}"

class Member(models.Model):
    """Member of a university who can search and reserve accommodations"""
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, unique=True)
    university = models.ForeignKey(
        University,
        related_name='members',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Member"
        verbose_name_plural = "Members"

    def __str__(self):
        return self.name

class Specialist(models.Model):
    """
    Specialist who manages accommodations and reservations
    """
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    university = models.ForeignKey(
        University,
        related_name='specialists',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Specialist"
        verbose_name_plural = "Specialists"

    def __str__(self):
        return self.name

class AccommodationUniversity(models.Model):
    """
    Intermediate table for many-to-many relationship between Accommodation and University
    """
    accommodation = models.ForeignKey(
        'Accommodation',
        on_delete=models.CASCADE,
        related_name='university_mappings'
    )
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='accommodation_mappings'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('accommodation', 'university')
        verbose_name = "Relation between Accommodation and University"
        verbose_name_plural = "Relations between Accommodation and University"

    def __str__(self):
        return f"{self.accommodation.name} - {self.university.name}"

class Accommodation(models.Model):
    """
    Accommodation that can be rented by university members
    """
    name = models.CharField(max_length=200)
    building_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='photos', blank=True, null=True)
    room_number = models.CharField(max_length=20, blank=True)
    flat_number = models.CharField(max_length=20, blank=True)
    floor_number = models.CharField(max_length=20, blank=True)
    universities = models.ManyToManyField(
        University,
        through='AccommodationUniversity',
        related_name='accommodations'
    )
    TYPE_CHOICES = [
        ('APARTMENT', 'Apartment'),
        ('HOUSE', 'House'),
        ('SHARED', 'Shared Room'),
        ('STUDIO', 'Studio'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    num_bedrooms = models.PositiveIntegerField()
    num_beds = models.PositiveIntegerField()
    address = models.TextField()
    geo_address = models.CharField(max_length=19)
    latitude = models.FloatField()
    longitude = models.FloatField()
    # available_from and available_to are removed and replaced by AvailabilitySlot
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    owner = models.ForeignKey(
        Owner,
        related_name='accommodations',
        on_delete=models.CASCADE,
        to_field='email'
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Minimum reservation period in days
    min_reservation_days = models.PositiveIntegerField(default=1)

    def calculate_distance(self, campus: Campus):
        R = 6371.0
        lat1 = math.radians(self.latitude)
        lon1 = math.radians(self.longitude)
        lat2 = math.radians(campus.latitude)
        lon2 = math.radians(campus.longitude)
        x = (lon2 - lon1) * math.cos((lat1 + lat2) / 2)
        y = (lat2 - lat1)
        d = R * math.sqrt(x*x + y*y)
        return d

    def average_rating(self):
        ratings = self.ratings.all()
        if not ratings:
            return None
        return sum(rating.score for rating in ratings) / len(ratings)

    def rating_count(self):
        return self.ratings.count()
    
    def get_available_slots(self):
        """Return all available slots sorted by start date"""
        return self.availability_slots.filter(is_available=True).order_by('start_date')
    
    def is_available_for_dates(self, start_date, end_date):
        """Check if the accommodation is available for the given date range"""
        if not self.is_available:
            return False
        
        # 确保日期是date对象而不是字符串
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
        # 检查预订期是否至少最短天数
        if (end_date - start_date).days + 1 < self.min_reservation_days:
            return False
            
        # 查找包含请求时间段的slot
        slots = self.availability_slots.filter(
            is_available=True,
            start_date__lte=start_date,
            end_date__gte=end_date
        )
        return slots.exists()
    
    def update_availability_status(self):
        """
        Update is_available status based on whether there are any available slots
        """
        has_available_slots = self.availability_slots.filter(is_available=True).exists()
        if self.is_available != has_available_slots:
            self.is_available = has_available_slots
            self.save(update_fields=['is_available'])


    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Accommodation"
        verbose_name_plural = "Accommodations"


class AvailabilitySlot(models.Model):
    """
    Time period when an accommodation is available for reservation
    """
    accommodation = models.ForeignKey(
        Accommodation,
        related_name='availability_slots',
        on_delete=models.CASCADE
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Availability Slot"
        verbose_name_plural = "Availability Slots"
        
    def __str__(self):
        return f"{self.accommodation.name}: {self.start_date} to {self.end_date}"
    
    def duration_days(self):
        """Return the duration of the slot in days"""
        return (self.end_date - self.start_date).days + 1
    
    def split_slot(self, start_date, end_date):
        """
        Split this slot into up to 3 slots based on the reservation dates
        Returns a tuple of (before_slot, after_slot) which may be None if not created
        """
        before_slot = None
        after_slot = None
        
        # 确保日期是date对象而不是字符串
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # 创建预订前的slot（如果需要）
        if start_date > self.start_date:
            before_slot = AvailabilitySlot.objects.create(
                accommodation=self.accommodation,
                start_date=self.start_date,
                end_date=start_date - timedelta(days=1),
                is_available=True
            )
        
        # 创建预订后的slot（如果需要）
        if end_date < self.end_date:
            after_slot = AvailabilitySlot.objects.create(
                accommodation=self.accommodation,
                start_date=end_date + timedelta(days=1),
                end_date=self.end_date,
                is_available=True
            )
            
        return (before_slot, after_slot)
    
    def save(self, *args, **kwargs):
        """Override save to update accommodation availability status"""
        super().save(*args, **kwargs)
        if self.is_available:
            self.accommodation.update_availability_status()

    def delete(self, *args, **kwargs):
        """Override delete to update accommodation availability status"""
        accommodation = self.accommodation
        super().delete(*args, **kwargs)
        accommodation.update_availability_status()
            
    @classmethod
    def merge_adjacent_slots(cls, accommodation):
        """
        Find and merge adjacent availability slots for the given accommodation
        """
        slots = accommodation.availability_slots.filter(is_available=True).order_by('start_date')
        if not slots or slots.count() <= 1:
            return
            
        # Iterate through slots and merge adjacent ones
        i = 0
        while i < slots.count() - 1:
            current = slots[i]
            next_slot = slots[i+1]
            
            # Check if slots are adjacent (end date of current + 1 day is start date of next)
            if current.end_date + timedelta(days=1) == next_slot.start_date:
                # Merge slots
                current.end_date = next_slot.end_date
                current.save()
                next_slot.delete()
                
                # Refresh queryset after modification
                slots = accommodation.availability_slots.filter(is_available=True).order_by('start_date')
            else:
                i += 1

class Reservation(models.Model):
    """
    Reservation of accommodation by a university member
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    reserved_from = models.DateField()
    reserved_to = models.DateField()
    contact_name = models.CharField(max_length=200)
    contact_phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_be_rated(self):
        return self.status == 'COMPLETED' and not hasattr(self, 'rating')

    def can_be_cancelled(self):
        return self.status in ['PENDING'] #, 'CONFIRMED']
        
    def is_cancelled(self):
        return self.status == 'CANCELLED'

    def cancel(self):
        """
        Cancel a reservation and create availability slot for the reserved period
        Returns True if successfully cancelled, False otherwise
        """
        if self.is_cancelled():
            return False
            
        if self.can_be_cancelled():
            self.status = 'CANCELLED'
            self.save()
            
            # Create a new availability slot for the cancelled reservation
            AvailabilitySlot.objects.create(
                accommodation=self.accommodation,
                start_date=self.reserved_from,
                end_date=self.reserved_to,
                is_available=True
            )
            
            # Merge adjacent slots if possible
            AvailabilitySlot.merge_adjacent_slots(self.accommodation)
                    
            return True
        return False
        

    def __str__(self):
        return f"{self.member.name}'s reservation of {self.accommodation.name}"

    class Meta:
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"

class Rating(models.Model):
    """
    Rating given by a university member for an accommodation after stay
    """
    accommodation = models.ForeignKey(Accommodation, related_name='ratings', on_delete=models.CASCADE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE)
    score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=True)
    moderated_by = models.ForeignKey(Specialist, null=True, blank=True, on_delete=models.SET_NULL)
    moderation_date = models.DateTimeField(null=True, blank=True)
    moderation_note = models.TextField(blank=True)

    class Meta:
        unique_together = ('accommodation', 'member', 'reservation')
        verbose_name = "Rating"
        verbose_name_plural = "Ratings"

    def __str__(self):
        return f"{self.member.name}'s {self.score}-star rating for {self.accommodation.name}"

class ActionLog(models.Model):
    """
    Log of actions performed in the system for audit purposes
    """
    ACTION_TYPES = [
        ('CREATE_ACCOMMODATION', 'Create Accommodation'),
        ('UPDATE_ACCOMMODATION', 'Update Accommodation'),
        ('DELETE_ACCOMMODATION', 'Delete Accommodation'),
        ('MARK_UNAVAILABLE', 'Mark Unavailable'),
        ('CREATE_RESERVATION', 'Create Reservation'),
        ('UPDATE_RESERVATION', 'Update Reservation'),
        ('CANCEL_RESERVATION', 'Cancel Reservation'),
        ('CREATE_RATING', 'Create Rating'),
        ('MODERATE_RATING', 'Moderate Rating'),
        ('UPLOAD_PHOTO', 'Upload Photo'),
        ('DELETE_PHOTO', 'Delete Photo'),
    ]
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    user_type = models.CharField(max_length=20, default='SPECIALIST')
    user_id = models.PositiveIntegerField(null=True, blank=True)
    accommodation_id = models.PositiveIntegerField(null=True, blank=True)
    reservation_id = models.PositiveIntegerField(null=True, blank=True)
    rating_id = models.PositiveIntegerField(null=True, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at', 'id']
        verbose_name = "Action Log"
        verbose_name_plural = "Action Logs"
    
    def __str__(self):
        return f"{self.action_type} at {self.created_at}"