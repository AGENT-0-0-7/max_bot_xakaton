from rest_framework import serializers
from apps.events.models import Event, Registration
from apps.users.serializers import UserSerializer

class LocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()

class EventListSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()
    available_seats = serializers.IntegerField(read_only=True)
    distance_meters = serializers.SerializerMethodField()
    is_registered = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'category', 'address',
            'location', 'start_time', 'end_time', 'max_participants',
            'status', 'available_seats', 'registered_count',
            'distance_meters', 'is_registered'
        ]

    def get_location(self, obj):
        return {
            'latitude': obj.latitude,
            'longitude': obj.longitude
        }

    def get_distance_meters(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        try:
            lat = float(request.query_params.get('lat'))
            lon = float(request.query_params.get('lon'))
            dist_km = obj.calculate_distance_km(lat, lon)
            return int(round(dist_km * 1000))
        except (TypeError, ValueError):
            return None

    def get_is_registered(self, obj):
        request = self.context.get('request')
        if not request or not request.user or request.user.is_anonymous:
            return False
        return Registration.objects.filter(user=request.user, event=obj).exists()


class EventCreateSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)
    location = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'category', 'address',
            'latitude', 'longitude', 'location', 'start_time',
            'end_time', 'max_participants', 'status'
        ]
        read_only_fields = ['id', 'status']

    def get_location(self, obj):
        return {
            'latitude': obj.latitude,
            'longitude': obj.longitude
        }

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['organizer'] = user
        validated_data['status'] = 'pending'
        return super().create(validated_data)


class EventDetailSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()
    organizer = UserSerializer(read_only=True)
    available_seats = serializers.IntegerField(read_only=True)
    registered_count = serializers.IntegerField(read_only=True)
    is_registered = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'organizer', 'title', 'description', 'category',
            'address', 'location', 'latitude', 'longitude',
            'start_time', 'end_time', 'max_participants', 'status',
            'available_seats', 'registered_count', 'is_registered',
            'created_at'
        ]

    def get_location(self, obj):
        return {
            'latitude': obj.latitude,
            'longitude': obj.longitude
        }

    def get_is_registered(self, obj):
        request = self.context.get('request')
        if not request or not request.user or request.user.is_anonymous:
            return False
        return Registration.objects.filter(user=request.user, event=obj).exists()


class RegistrationSerializer(serializers.ModelSerializer):
    event = EventListSerializer(read_only=True)

    class Meta:
        model = Registration
        fields = ['id', 'event', 'registered_at']
