from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "event_type", "title", "is_read", "created_at")
    list_filter = ("is_read", "event_type")
    search_fields = ("user__username", "user__email", "event_type", "title", "message")
    readonly_fields = ("created_at", "content_type", "object_id", "source_object", "data")
    date_hierarchy = "created_at"

    actions = ["mark_as_read"]

    @admin.action(description="Marcar como leídas")
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
