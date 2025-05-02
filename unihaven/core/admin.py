from django.contrib import admin
from .models import (
    Accommodation, Member, Specialist,
    Reservation, Rating, Campus, Owner, University, 
    AccommodationUniversity, AvailabilitySlot
)

@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'address')
    search_fields = ('name', 'email')

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'address', 'token', 'created_at')
    search_fields = ('name', 'country')

@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'university')

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'university')
    search_fields = ('name', 'phone', 'email', 'university__name')

@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'university')
    search_fields = ('name', 'email', 'university__name')

class AvailabilitySlotInline(admin.TabularInline):
    model = AvailabilitySlot
    extra = 1
    fields = ('start_date', 'end_date', 'is_available')

class AccommodationUniversityInline(admin.TabularInline):
    model = AccommodationUniversity
    extra = 1
    verbose_name = "University"
    verbose_name_plural = "Universities"

@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'num_bedrooms', 'num_beds', 'monthly_rent', 'is_available', 'min_reservation_days')
    list_filter = ('type', 'is_available', 'num_bedrooms')
    search_fields = ('name', 'building_name', 'address')
    inlines = [AvailabilitySlotInline, AccommodationUniversityInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'building_name', 'description', 'photo', 'type')
        }),
        ('Room Details', {
            'fields': ('room_number', 'flat_number', 'floor_number', 'num_bedrooms', 'num_beds')
        }),
        ('Location', {
            'fields': ('address', 'geo_address', 'latitude', 'longitude')
        }),
        ('Rental Details', {
            'fields': ('monthly_rent', 'min_reservation_days', 'is_available')
        }),
        ('Ownership', {
            'fields': ('owner',)
        }),
    )

@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ('accommodation', 'start_date', 'end_date', 'is_available', 'duration_days')
    list_filter = ('is_available', 'start_date', 'end_date')
    search_fields = ('accommodation__name',)
    
    def duration_days(self, obj):
        return (obj.end_date - obj.start_date).days + 1
    duration_days.short_description = 'Duration (days)'

class ReservationInline(admin.TabularInline):
    model = Reservation
    extra = 0
    fields = ('member', 'reserved_from', 'reserved_to', 'status')
    readonly_fields = ('member',)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('accommodation', 'member', 'reserved_from', 'reserved_to', 'status')
    list_filter = ('status',)
    search_fields = ('accommodation__name', 'member__name')
    actions = ['mark_as_cancelled', 'mark_as_completed']
    
    def mark_as_cancelled(self, request, queryset):
        for reservation in queryset:
            if reservation.can_be_cancelled():
                reservation.cancel()
        self.message_user(request, "Selected reservations have been cancelled")
    mark_as_cancelled.short_description = "Cancel selected reservations"
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='COMPLETED')
        self.message_user(request, "Selected reservations have been marked as completed")
    mark_as_completed.short_description = "Mark selected reservations as completed"

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('accommodation', 'member', 'score', 'created_at', 'is_approved')
    list_filter = ('score', 'is_approved')
    search_fields = ('accommodation__name', 'member__name')

@admin.register(AccommodationUniversity)
class AccommodationUniversityAdmin(admin.ModelAdmin):
    list_display = ('accommodation', 'university')