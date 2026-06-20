"""MAS Investment - Notifications Views"""
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification


@login_required
def notifications_list_view(request):
    notifications = request.user.notifications.order_by('-created_at')
    return render(request, 'base/notifications.html', {'notifications': notifications})


@login_required
def mark_read_view(request, notification_id):
    n = get_object_or_404(Notification, pk=notification_id, user=request.user)
    n.is_read = True
    n.save(update_fields=['is_read'])
    if n.link:
        return redirect(n.link)
    return redirect('notifications:list')


@login_required
def mark_all_read_view(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect(request.META.get('HTTP_REFERER', '/'))
