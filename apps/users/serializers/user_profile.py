from rest_framework import serializers
from apps.users.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    country_name = serializers.CharField(source="country.name", read_only=True, allow_null=True, default=None)
    city_name = serializers.CharField(source="city.name", read_only=True, allow_null=True, default=None)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "user_username",
            "avatar_url",
            "birth_date",
            "nro_document",
            "phone",
            "address",
            "country",
            "country_name",
            "city",
            "city_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_username", "country_name", "city_name", "created_at", "updated_at"]
