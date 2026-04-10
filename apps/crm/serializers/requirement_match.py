from rest_framework import serializers
from apps.crm.models import RequirementMatch


class RequirementMatchSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source="property.title", read_only=True)
    property_code = serializers.CharField(source="property.code", read_only=True)
    property_main_image = serializers.SerializerMethodField()

    def get_property_main_image(self, obj):
        media = obj.property.media.filter(order=1).first()
        if not media or not media.file:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(media.file.url) if request else media.file.url

    class Meta:
        model = RequirementMatch
        fields = [
            "id", "requirement", "property", "property_code", "property_title",
            "property_main_image", "score", "details", "computed_at", "is_active",
        ]