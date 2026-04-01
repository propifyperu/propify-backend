from rest_framework import serializers

from apps.crm.models import Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"
        read_only_fields = ["id", "assigned_agent", "created_at", "updated_at"]
