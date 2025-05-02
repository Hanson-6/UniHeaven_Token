# serializers.py

from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta, datetime
from .models import (
    Accommodation, Member, Specialist, Reservation, Rating, Campus, Owner, ActionLog, 
    University, AccommodationUniversity, AvailabilitySlot
)

class OwnerSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if self.context.get('allow_existing_email', False):
            try:
                Owner.objects.get(email=value)
                return value
            except Owner.DoesNotExist:
                pass
        else:
            if Owner.objects.filter(email=value).exists():
                raise serializers.ValidationError("This email is already in use.")
        return value

    class Meta:
        model = Owner
        fields = ['name', 'email', 'phone', 'address']

class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = ['name', 'country', 'address']

class CampusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = ['name', 'latitude', 'longitude', 'university']

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['id', 'name', 'phone', 'email', 'university']

class CEDARSSpecialistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialist
        fields = ['id', 'name', 'email', 'phone', 'university']

class ActionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionLog
        fields = '__all__'

class AvailabilitySlotSerializer(serializers.ModelSerializer):
    duration_days = serializers.SerializerMethodField()
    
    class Meta:
        model = AvailabilitySlot
        fields = ['id', 'start_date', 'end_date', 'is_available', 'duration_days']
        
    def get_duration_days(self, obj):
        return (obj.end_date - obj.start_date).days + 1

class AccommodationSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    owner_details = OwnerSerializer(write_only=True)
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    universities = UniversitySerializer(many=True, read_only=True)
    university_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=University.objects.all(),
        write_only=True
    )
    availability_slots = AvailabilitySlotSerializer(many=True, read_only=True)
    min_reservation_days = serializers.IntegerField(default=1)
    
    # Fields for creating initial availability slots
    initial_available_from = serializers.DateField(write_only=True, required=False)
    initial_available_to = serializers.DateField(write_only=True, required=False)

    class Meta:
        model = Accommodation
        fields = [
            'id', 'name', 'building_name', 'room_number', 'flat_number', 'floor_number',
            'description', 'type', 'type_display', 'num_bedrooms', 'num_beds', 'address', 'geo_address',
            'latitude', 'longitude', 'monthly_rent', 'owner', 'owner_details',
            'is_available', 'photo', 'average_rating', 'rating_count', 'universities', 'university_ids',
            'availability_slots', 'min_reservation_days', 'initial_available_from', 'initial_available_to'
        ]

    def create(self, validated_data):
        owner_data = validated_data.pop('owner_details', None)
        university_ids = validated_data.pop('university_ids', [])
        initial_available_from = validated_data.pop('initial_available_from', None)
        initial_available_to = validated_data.pop('initial_available_to', None)
        
        if owner_data:
            email = owner_data.get('email')
            try:
                owner = Owner.objects.get(email=email)
            except Owner.DoesNotExist:
                owner = Owner.objects.create(**owner_data)
            validated_data['owner'] = owner
            
        accommodation = Accommodation.objects.create(**validated_data)
        accommodation.universities.set(university_ids)
        
        # Create initial availability slot if dates provided
        if initial_available_from and initial_available_to:
            AvailabilitySlot.objects.create(
                accommodation=accommodation,
                start_date=initial_available_from,
                end_date=initial_available_to,
                is_available=True
            )
        
        return accommodation

    def update(self, instance, validated_data):
        owner_data = validated_data.pop('owner_details', None)
        university_ids = validated_data.pop('university_ids', [])
        initial_available_from = validated_data.pop('initial_available_from', None)
        initial_available_to = validated_data.pop('initial_available_to', None)
        
        if owner_data:
            owner, created = Owner.objects.get_or_create(
                email=owner_data['email'],
                defaults={'name': owner_data['name'], 'phone': owner_data.get('phone', ''), 'address': owner_data.get('address', '')}
            )
            validated_data['owner'] = owner
            
        instance = super().update(instance, validated_data)
        instance.universities.set(university_ids)
        
        # Create new availability slot if dates provided and no slots exist
        if initial_available_from and initial_available_to and not instance.availability_slots.exists():
            AvailabilitySlot.objects.create(
                accommodation=instance,
                start_date=initial_available_from,
                end_date=initial_available_to,
                is_available=True
            )
            
        return instance

    def get_average_rating(self, obj):
        ratings = obj.ratings.all()
        if ratings.exists():
            try:
                avg = sum(rating.score for rating in ratings) / ratings.count()
                return round(avg, 1)
            except Exception:
                return None
        return None
        
    def get_rating_count(self, obj):
        return obj.ratings.count()

class ReservationSerializer(serializers.ModelSerializer):
    accommodation_name = serializers.ReadOnlyField(source='accommodation.name')
    member_name = serializers.ReadOnlyField(source='member.name')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_be_rated = serializers.SerializerMethodField()
    can_be_cancelled = serializers.SerializerMethodField()
    is_cancelled = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            'id', 'accommodation', 'accommodation_name', 'member', 'member_name',
            'reserved_from', 'reserved_to', 'status', 'status_display', 
            'can_be_rated', 'can_be_cancelled', 'is_cancelled', 'created_at', 'updated_at'
        ]

    def get_can_be_rated(self, obj):
        return obj.can_be_rated()
        
    def get_can_be_cancelled(self, obj):
        return obj.can_be_cancelled()
        
    def get_is_cancelled(self, obj):
        return obj.is_cancelled()
    
    def validate(self, data):
        reserved_from = data.get('reserved_from')
        reserved_to = data.get('reserved_to')
        accommodation = data.get('accommodation')
        member = data.get('member')
        
        if not all([reserved_from, reserved_to, accommodation, member]):
            raise serializers.ValidationError("Missing required fields")
        
        # 确保日期是 date 对象而不是字符串
        if isinstance(reserved_from, str):
            reserved_from = datetime.strptime(reserved_from, '%Y-%m-%d').date()
            data['reserved_from'] = reserved_from
        
        if isinstance(reserved_to, str):
            reserved_to = datetime.strptime(reserved_to, '%Y-%m-%d').date()
            data['reserved_to'] = reserved_to
        
        # 检查用户是否只预订与其大学关联的宿舍
        if not accommodation.universities.filter(id=member.university.id).exists():
            raise serializers.ValidationError("You can only reserve accommodations associated with your university")
        
        if reserved_from > reserved_to:
            raise serializers.ValidationError("End date must be after start date")
        
        if self.instance is None and reserved_from < timezone.now().date():
            raise serializers.ValidationError("Reservation start date cannot be in the past")
        
        # 检查预订期是否至少最少天数
        min_days = accommodation.min_reservation_days
        if (reserved_to - reserved_from).days + 1 < min_days:
            raise serializers.ValidationError(f"Reservation must be at least {min_days} days")
        
        # 检查住宿是否有可用时段
        if not accommodation.is_available_for_dates(reserved_from, reserved_to):
            raise serializers.ValidationError("The accommodation is not available for the requested dates")
        
        # 检查重叠预订
        overlapping_reservations = Reservation.objects.filter(
            accommodation=accommodation,
            status__in=['PENDING', 'CONFIRMED'],
            reserved_from__lt=reserved_to,
            reserved_to__gt=reserved_from
        ).exclude(id=self.instance.id if self.instance else None)
        
        if overlapping_reservations.exists():
            raise serializers.ValidationError("The accommodation is already reserved for the selected dates")
            
        return data

class RatingSerializer(serializers.ModelSerializer):
    member_name = serializers.ReadOnlyField(source='member.name')

    class Meta:
        model = Rating
        fields = ['id', 'accommodation', 'member', 'member_name', 'reservation', 'score', 'comment', 'created_at']

    def validate(self, data):
        reservation = data.get('reservation')
        if reservation:
            if reservation.status != 'COMPLETED':
                raise serializers.ValidationError("Can only rate completed reservations")
            if not reservation.can_be_rated():
                raise serializers.ValidationError("This reservation has already been rated")
        else:
            raise serializers.ValidationError("Reservation is required for rating.")
        return data

class AccommodationUniversitySerializer(serializers.ModelSerializer):
    accommodation_name = serializers.CharField(source='accommodation.name')
    university_name = serializers.CharField(source='university.name')

    class Meta:
        model = AccommodationUniversity
        fields = ['accommodation_name', 'university_name']