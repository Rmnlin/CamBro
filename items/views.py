from django.db import models 
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Item, Category, BorrowRequest, ChatRoom, Message, Notification, Rider

# --- Utility ---
def create_notification(user, message, link='/dashboard/'):
    Notification.objects.create(user=user, message=message, link=link)

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect(notification.link)

def register_view(request):
    if request.user.is_authenticated: return redirect('item_list')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        if not username or not email or not password: messages.error(request, 'กรุณากรอกข้อมูลให้ครบ')
        elif password != password2: messages.error(request, 'รหัสผ่านไม่ตรงกัน')
        elif User.objects.filter(username=username).exists(): messages.error(request, 'ชื่อผู้ใช้นี้ถูกใช้แล้ว')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(request, f'ยินดีต้อนรับ {username}!')
            return redirect('item_list')
    return render(request, 'accounts/register.html')

def login_view(request):
    if request.user.is_authenticated: return redirect('item_list')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'item_list'))
        messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('item_list')

# --- Item Management ---
def item_list(request):
    search_query = request.GET.get('search', '')
    campus_filter = request.GET.get('campus', '')
    category_slug = request.GET.get('category', '') 
    items = Item.objects.filter(is_available=True, status='active').select_related('owner', 'category')
    if search_query:
        items = items.filter(models.Q(title__icontains=search_query) | models.Q(description__icontains=search_query))
    if campus_filter: items = items.filter(campus=campus_filter)
    if category_slug: items = items.filter(category__slug=category_slug)
    categories = Category.objects.all()
    return render(request, 'items/list.html', {'items': items, 'categories': categories, 'selected_category': category_slug, 'selected_campus': campus_filter, 'search_query': search_query})

def item_detail(request, item_id):
    item = get_object_or_404(Item.objects.select_related('owner', 'category'), item_id=item_id)
    return render(request, 'items/detail.html', {'item': item})

@login_required
def create_item(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        title, description = request.POST.get('title', '').strip(), request.POST.get('description', '').strip()
        category_id = request.POST.get('category')
        if not title or not description or not category_id: messages.error(request, 'กรุณากรอกข้อมูลให้ครบ')
        else:
            item = Item.objects.create(
                owner=request.user, category_id=category_id, title=title, description=description,
                condition=request.POST.get('condition', 'good'), campus=request.POST.get('campus', 'rangsit'),
                pickup_location=request.POST.get('pickup_location', ''), is_free=request.POST.get('is_free') == 'true',
                deposit_amount=request.POST.get('deposit_amount', 0) or 0, max_days=request.POST.get('max_days', 7) or 7,
                photo=request.FILES.get('photo'), insurance_plan=request.POST.get('insurance_plan', 'none')
            )
            return redirect('item_detail', item_id=item.item_id)
    return render(request, 'items/create_item.html', {'categories': categories})

@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, item_id=item_id, owner=request.user)
    if request.method == 'POST':
        item.delete()
        return redirect('dashboard')
    return render(request, 'items/confirm_delete.html', {'item': item})

@login_required
def dashboard(request):
    return render(request, 'items/dashboard.html', {
        'my_borrowing': BorrowRequest.objects.filter(borrower=request.user).select_related('item', 'lender').order_by('-created_at'),
        'incoming_requests': BorrowRequest.objects.filter(lender=request.user).select_related('item', 'borrower').order_by('-created_at'),
        'my_items': Item.objects.filter(owner=request.user).order_by('-created_at'),
    })

@login_required
def create_request(request, item_id):
    item = get_object_or_404(Item, item_id=item_id)
    if request.method == 'POST':
        BorrowRequest.objects.create(item=item, borrower=request.user, lender=item.owner, start_date=request.POST.get('start_date'), end_date=request.POST.get('end_date'), borrower_message=request.POST.get('message', ''))
        create_notification(item.owner, f"มีคนสนใจขอยืม {item.title}!")
        return redirect('item_detail', item_id=item.item_id)
    return render(request, 'items/request_form.html', {'item': item})

@login_required
def approve_request(request, request_id):
    req = get_object_or_404(BorrowRequest, request_id=request_id, lender=request.user)
    req.status, req.approved_at = 'approved', timezone.now()
    req.item.status, req.item.is_available = 'borrowed', False
    req.item.save(); req.save()
    create_notification(req.borrower, f"เจ้าของอนุมัติให้คุณยืม {req.item.title} แล้ว!")
    return redirect('dashboard')

@login_required
def decline_request(request, request_id):
    req = get_object_or_404(BorrowRequest, request_id=request_id, lender=request.user)
    req.status = 'declined'; req.save()
    return redirect('dashboard')

@login_required
def cancel_request(request, request_id):
    req = get_object_or_404(BorrowRequest, request_id=request_id, borrower=request.user)
    if req.status == 'pending': req.delete()
    return redirect('dashboard')

@login_required
def notify_return(request, request_id):
    req = get_object_or_404(BorrowRequest, request_id=request_id, borrower=request.user)
    if req.status == 'approved':
        req.status = 'returning'; req.save()
        create_notification(req.lender, f"{req.borrower.username} ส่งคืน {req.item.title} แล้ว!")
    return redirect('dashboard')

@login_required
def return_item(request, request_id):
    req = get_object_or_404(BorrowRequest, request_id=request_id, lender=request.user)
    if req.status in ['approved', 'returning']:
        req.status = 'returned'; req.save()
        req.item.status, req.item.is_available = 'active', True
        req.item.save()
        return redirect('return_completed', request_id=request_id)
    return redirect('dashboard')

@login_required
def start_chat(request, item_id):
    item = get_object_or_404(Item, item_id=item_id)
    if item.owner == request.user: return redirect('item_detail', item_id=item_id)
    chat, _ = ChatRoom.objects.get_or_create(item=item, borrower=request.user, owner=item.owner)
    return redirect('chat_room', room_id=chat.id)

@login_required
def chat_room(request, room_id):
    chat = get_object_or_404(ChatRoom, id=room_id)
    if request.user not in [chat.borrower, chat.owner]: return redirect('item_list')
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(room=chat, sender=request.user, content=content)
            receiver = chat.owner if request.user == chat.borrower else chat.borrower
            create_notification(receiver, f"ข้อความใหม่จาก {request.user.username}", link=f"/chats/{chat.id}/")
            return redirect('chat_room', room_id=chat.id)
    return render(request, 'items/chat_room.html', {'chat_room': chat, 'messages_list': chat.messages.all().order_by('timestamp')})

@login_required
def inbox(request):
    rooms = ChatRoom.objects.filter(models.Q(borrower=request.user) | models.Q(owner=request.user)).select_related('item', 'borrower', 'owner').prefetch_related('messages').order_by('-created_at')
    return render(request, 'items/inbox.html', {'chat_rooms': rooms})

@login_required
def delivery_details(request, request_id):
    req = get_object_or_404(BorrowRequest, request_id=request_id)
    if not req.rider:
        rider, _ = Rider.objects.get_or_create(name="พี่ BRO (CamBro Rider)", defaults={'vehicle_type': 'Honda PCX - TU Edition', 'phone_number': '081-234-5678'})
        req.rider = rider; req.save()
    return render(request, 'items/delivery_details.html', {'borrow_request': req})

@login_required
def return_completed(request, request_id):
    req = get_object_or_404(BorrowRequest, request_id=request_id)
    return render(request, 'items/return_completed.html', {'borrow_request': req})