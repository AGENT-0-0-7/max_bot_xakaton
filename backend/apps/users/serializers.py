from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'max_id', 'first_name', 'last_name', 'username', 'created_at']
        read_only_fields = ['id', 'created_at']

class InitDataAuthSerializer(serializers.Serializer):
    init_data = serializers.CharField(required=True)
