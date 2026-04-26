from django.db import models
from decimal import Decimal
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Item, Category, BorrowRequest, ChatRoom, Message, Notification, Rider, Review, ItemPhoto

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
    search_query = request.GET.get('search', '')
    items = Item.objects.filter(is_available=True, status='active').select_related('owner', 'category').order_by('-created_at')
    if search_query:
        items = items.filter(models.Q(title__icontains=search_query) | models.Q(description__icontains=search_query))
    else:
        items = items[:8]
    categories = Category.objects.all()
    return render(request, 'items/list.html', {'items': items, 'categories': categories, 'search_query': search_query})

def all_items(request):
    search_query = request.GET.get('search', '')
    campus_filter = request.GET.get('campus', '')
    category_slug = request.GET.get('category', '')
    items = Item.objects.filter(is_available=True, status='active').select_related('owner', 'category')
    if search_query:
        items = items.filter(models.Q(title__icontains=search_query) | models.Q(description__icontains=search_query))
    if campus_filter: items = items.filter(campus=campus_filter)
    if category_slug: items = items.filter(category__slug=category_slug)
    categories = Category.objects.all()
    return render(request, 'items/all_items.html', {'items': items, 'categories': categories, 'selected_category': category_slug, 'selected_campus': campus_filter, 'search_query': search_query})

def item_detail(request, item_id):
    item = get_object_or_404(Item.objects.select_related('owner', 'category'), item_id=item_id)
    reviews = Review.objects.filter(borrow_request__item=item).select_related('reviewer').order_by('-created_at')
    avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
    photos = item.photos.all()
    return render(request, 'items/detail.html', {'item': item, 'reviews': reviews, 'avg_rating': avg_rating, 'photos': photos})

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
                insurance_plan=request.POST.get('insurance_plan', 'none')
            )
            photos = request.FILES.getlist('photos')
            for i, photo in enumerate(photos):
                ItemPhoto.objects.create(item=item, image=photo, order=i)
            if photos:
                item.photo = photos[0]
                item.save()
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
def edit_item(request, item_id):
    item = get_object_or_404(Item, item_id=item_id, owner=request.user)
    categories = Category.objects.all()
    if request.method == 'POST':
        item.title = request.POST.get('title', '').strip()
        item.description = request.POST.get('description', '').strip()
        item.category_id = request.POST.get('category')
        item.condition = request.POST.get('condition', 'good')
        item.campus = request.POST.get('campus', 'rangsit')
        item.pickup_location = request.POST.get('pickup_location', '')
        item.is_free = request.POST.get('is_free') == 'true'
        item.deposit_amount = request.POST.get('deposit_amount', 0) or 0
        item.max_days = request.POST.get('max_days', 7) or 7
        item.save()
        return redirect('item_detail', item_id=item.item_id)
    return render(request, 'items/edit_item.html', {'item': item, 'categories': categories})

@login_required
def dashboard(request):
    my_borrowing = BorrowRequest.objects.filter(borrower=request.user).select_related('item', 'lender').order_by('-created_at')
    incoming_requests = BorrowRequest.objects.filter(lender=request.user).select_related('item', 'borrower').order_by('-created_at')

    activity = []
    for req in incoming_requests:
        if req.status == 'pending':
            activity.append({'type': 'requested', 'user': req.borrower, 'item': req.item, 'time': req.created_at})
        elif req.status in ['returning', 'returned']:
            activity.append({'type': 'returned', 'user': req.borrower, 'item': req.item, 'time': req.approved_at or req.created_at})
    for req in my_borrowing:
        if req.status == 'approved':
            activity.append({'type': 'borrowed', 'user': req.borrower, 'item': req.item, 'time': req.approved_at or req.created_at})

    activity.sort(key=lambda x: x['time'], reverse=True)

    return render(request, 'items/dashboard.html', {
        'my_borrowing': my_borrowing,
        'incoming_requests': incoming_requests,
        'my_items': Item.objects.filter(owner=request.user).order_by('-created_at'),
        'my_active_items': Item.objects.filter(owner=request.user, status='borrowed').order_by('-created_at'),
        'pending_count': BorrowRequest.objects.filter(lender=request.user, status='pending').count(),
        'activity': activity,
    })

@login_required
def create_request(request, item_id):
    item = get_object_or_404(Item, item_id=item_id)
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        message = request.POST.get('message', '')
        if item.is_free and item.deposit_amount == 0:
            BorrowRequest.objects.create(item=item, borrower=request.user, lender=item.owner,
                start_date=start_date, end_date=end_date, borrower_message=message)
            create_notification(item.owner, f"มีคนสนใจขอยืม {item.title}!")
            return redirect('item_detail', item_id=item.item_id)
        else:
            request.session['pending_request'] = {'start_date': start_date, 'end_date': end_date, 'message': message}
            return redirect('payment_review', item_id=item.item_id)
    return render(request, 'items/request_form.html', {'item': item})

@login_required
def payment_review(request, item_id):
    from datetime import date as date_type
    item = get_object_or_404(Item, item_id=item_id)
    pending = request.session.get('pending_request')
    if not pending:
        return redirect('create_request', item_id=item_id)
    start = date_type.fromisoformat(pending['start_date'])
    end = date_type.fromisoformat(pending['end_date'])
    days = (end - start).days
    deposit = item.deposit_amount
    platform_fee = Decimal('0')
    total = deposit
    if request.method == 'POST':
        BorrowRequest.objects.create(item=item, borrower=request.user, lender=item.owner,
            start_date=pending['start_date'], end_date=pending['end_date'], borrower_message=pending.get('message', ''))
        del request.session['pending_request']
        create_notification(item.owner, f"มีคนสนใจขอยืม {item.title}!")
        return redirect('item_detail', item_id=item.item_id)
    return render(request, 'items/payment_review.html', {
        'item': item, 'start_date': start, 'end_date': end,
        'days': days, 'deposit': deposit, 'platform_fee': platform_fee, 'total': total,
    })

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
    return redirect(f'/inbox/?room={chat.id}')

@login_required
def inbox(request):
    rooms = ChatRoom.objects.filter(models.Q(borrower=request.user) | models.Q(owner=request.user)).select_related('item', 'borrower', 'owner').prefetch_related('messages').order_by('-created_at')
    active_room = None
    messages_list = None
    room_id = request.GET.get('room')
    if room_id:
        try:
            active_room = rooms.get(id=room_id)
            if request.method == 'POST':
                content = request.POST.get('content', '').strip()
                if content:
                    Message.objects.create(room=active_room, sender=request.user, content=content)
                    receiver = active_room.owner if request.user == active_room.borrower else active_room.borrower
                    create_notification(receiver, f"ข้อความใหม่จาก {request.user.username}", link=f"/inbox/?room={active_room.id}")
                    return redirect(f'/inbox/?room={active_room.id}')
            messages_list = active_room.messages.all().order_by('timestamp')
        except ChatRoom.DoesNotExist:
            pass
    return render(request, 'items/inbox.html', {'chat_rooms': rooms, 'active_room': active_room, 'messages_list': messages_list})

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
    already_reviewed = Review.objects.filter(borrow_request=req).exists()
    return render(request, 'items/return_completed.html', {'borrow_request': req, 'already_reviewed': already_reviewed})

def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    reviews = Review.objects.filter(reviewee=profile_user, borrow_request__isnull=True).select_related('reviewer').order_by('-created_at')
    avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
    active_items = Item.objects.filter(owner=profile_user, is_available=True, status='active')
    if request.method == 'POST' and request.user.is_authenticated and request.user != profile_user:
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        if rating and rating.isdigit() and 1 <= int(rating) <= 5:
            Review.objects.create(reviewer=request.user, reviewee=profile_user, rating=int(rating), comment=comment)
        return redirect('profile', username=username)

    return render(request, 'items/profile.html', {
        'profile_user': profile_user,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'active_items': active_items,
    })

@login_required
def leave_review(request, request_id):
    req = get_object_or_404(BorrowRequest, request_id=request_id, borrower=request.user)
    if req.status != 'returned' or Review.objects.filter(borrow_request=req).exists():
        return redirect('dashboard')
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        if rating and rating.isdigit() and 1 <= int(rating) <= 5:
            Review.objects.create(borrow_request=req, reviewer=request.user, reviewee=req.lender, rating=int(rating), comment=comment)
    return redirect('item_list')