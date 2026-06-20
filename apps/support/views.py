"""
MAS Investment - Support Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from .models import SupportTicket, SupportReply
from apps.notifications.models import Notification


@login_required
def customer_tickets_view(request):
    tickets = SupportTicket.objects.filter(
        customer=request.user
    ).order_by('-created_at')
    paginator = Paginator(tickets, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'customer/tickets.html', {'page_obj': page_obj})


@login_required
def create_ticket_view(request):
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        if not subject or not message:
            messages.error(request, 'Subject and message are required.')
            return render(request, 'customer/create_ticket.html')
        ticket = SupportTicket.objects.create(
            customer=request.user,
            subject=subject,
            message=message,
            related_order_id=request.POST.get('order_id') or None,
        )
        messages.success(request, f'Ticket #{ticket.ticket_number} created. Our team will respond shortly.')
        return redirect('customer:ticket_detail', ticket_id=ticket.id)
    return render(request, 'customer/create_ticket.html')


@login_required
def customer_ticket_detail_view(request, ticket_id):
    ticket = get_object_or_404(
        SupportTicket.objects.prefetch_related('replies__user'),
        pk=ticket_id,
        customer=request.user
    )
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if message:
            SupportReply.objects.create(
                ticket=ticket,
                user=request.user,
                message=message,
                is_staff_reply=False
            )
            if ticket.status == SupportTicket.STATUS_RESOLVED:
                ticket.status = SupportTicket.STATUS_OPEN
                ticket.save(update_fields=['status'])
            messages.success(request, 'Reply sent.')
        return redirect('customer:ticket_detail', ticket_id=ticket_id)
    return render(request, 'customer/ticket_detail.html', {'ticket': ticket})
