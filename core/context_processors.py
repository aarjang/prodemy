def unread_notifications(request):
    """The navbar badge count: unread notifications for the signed-in user, else None."""
    if not request.user.is_authenticated:
        return {"unread_notifications": None}
    return {
        "unread_notifications": request.user.notifications.filter(read_at__isnull=True).count()
    }
