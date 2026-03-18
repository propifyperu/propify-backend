from rest_framework import serializers

from apps.crm.models import Match


class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
