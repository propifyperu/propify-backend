from rest_framework import serializers

from apps.crm.models import RequirementMatch


class RequirementMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequirementMatch
        fields = "__all__"
        read_only_fields = [f.name for f in RequirementMatch._meta.get_fields() if hasattr(f, 'name')]
