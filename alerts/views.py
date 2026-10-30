from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from alerts.forms import AlertForm
from alerts.models import Notification, PriceAlert


class OwnAlertsMixin(LoginRequiredMixin):
    def get_queryset(self):
        return self.request.user.alerts.all()


class AlertListView(OwnAlertsMixin, ListView):
    template_name = "alerts/alert_list.html"
    context_object_name = "alerts"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_count"] = self.request.user.alerts.filter(
            state__in=PriceAlert.ACTIVE_STATES
        ).count()
        context["max_active"] = PriceAlert.MAX_ACTIVE_PER_USER
        return context


class AlertFormMixin(OwnAlertsMixin):
    form_class = AlertForm
    template_name = "alerts/alert_form.html"
    success_url = reverse_lazy("alerts:list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class AlertCreateView(AlertFormMixin, CreateView):
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "هشدار ساخته شد.")
        return response


class AlertUpdateView(AlertFormMixin, UpdateView):
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "هشدار ویرایش شد.")
        return response


class AlertDeleteView(OwnAlertsMixin, DeleteView):
    template_name = "alerts/alert_confirm_delete.html"
    success_url = reverse_lazy("alerts:list")

    def form_valid(self, form):
        messages.success(self.request, "هشدار حذف شد. اعلان‌های قبلی آن در تاریخچه می‌مانند.")
        return super().form_valid(form)


def _own_alert_or_404(request, pk):
    return get_object_or_404(PriceAlert, pk=pk, user=request.user)


@login_required
@require_POST
def alert_pause(request, pk):
    alert = _own_alert_or_404(request, pk)
    alert.state = PriceAlert.State.PAUSED
    alert.save(update_fields=["state", "updated_at"])
    messages.success(request, "هشدار متوقف شد.")
    return redirect("alerts:list")


@login_required
@require_POST
def alert_resume(request, pk):
    alert = _own_alert_or_404(request, pk)
    active = request.user.alerts.filter(state__in=PriceAlert.ACTIVE_STATES).count()
    if active >= PriceAlert.MAX_ACTIVE_PER_USER:
        messages.error(request, "بیشتر از ۲۰ هشدار فعال نمی‌توانید داشته باشید. یکی را متوقف یا حذف کنید.")
    elif alert.state == PriceAlert.State.PAUSED:
        alert.state = PriceAlert.State.ARMED
        alert.save(update_fields=["state", "updated_at"])
        messages.success(request, "هشدار دوباره فعال شد و از خواندن بعدی قیمت بررسی می‌شود.")
    return redirect("alerts:list")


class NotificationListView(LoginRequiredMixin, ListView):
    template_name = "alerts/notification_list.html"
    paginate_by = 20
    context_object_name = "notifications"

    def get_queryset(self):
        return self.request.user.notifications.select_related("price_reading")


@login_required
@require_POST
def notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return redirect("alerts:notifications")


@login_required
@require_POST
def notifications_read_all(request):
    request.user.notifications.filter(read_at__isnull=True).update(read_at=timezone.now())
    messages.success(request, "همه اعلان‌ها خوانده‌شده علامت خوردند.")
    return redirect("alerts:notifications")


@require_GET
def unread_count_json(request):
    if not request.user.is_authenticated:
        return JsonResponse({"unread": None}, status=401)
    count = request.user.notifications.filter(read_at__isnull=True).count()
    response = JsonResponse({"unread": count})
    response["Cache-Control"] = "no-store"
    return response
