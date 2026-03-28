from django.db import models 
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Item, Category, BorrowRequest, ChatRoom, Message, Notification

def create_notification(user, message, link='/dashboard/'):
    Notification.objects.create(user=user, message=message, link=link)

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('dashboard')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('item_list')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        if not username or not email or not password:
            messages.error(request, 'กรุณากรอกข้อมูลให้ครบ')
        elif password != password2:
            messages.error(request, 'รหัสผ่านไม่ตรงกัน')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'ชื่อผู้ใช้นี้ถูกใช้แล้ว')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(request, f'ยินดีต้อนรับ {username}!')
            return redirect('item_list')
    return render(request, 'accounts/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('item_list')
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

def item_list(request):
    items = Item.objects.filter(is_available=True, status='active').select_related('owner', 'category')
    
    category_filter = request.GET.get('category')
    campus_filter = request.GET.get('campus')
    search = request.GET.get('search')
    
    if category_filter:
        items = items.filter(category__slug=category_filter)
    if campus_filter:
        items = items.filter(campus=campus_filter)
    if search:
        items = items.filter(title__icontains=search)
    
    categories = Category.objects.all()
    
    context = {
        'items': items,
        'categories': categories,
        'selected_category': category_filter,
        'selected_campus': campus_filter,
    }
    
    return render(request, 'items/list.html', context)

def item_detail(request, item_id):
    item = get_object_or_404(Item.objects.select_related('owner', 'category'), item_id=item_id)
    
    context = {
        'item': item,
    }
    
    return render(request, 'items/detail.html', context)

@login_required
def create_item(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')
        condition = request.POST.get('condition', 'good')
        campus = request.POST.get('campus', 'rangsit')
        pickup_location = request.POST.get('pickup_location', '').strip()
        is_free = request.POST.get('is_free') == 'true'
        deposit_amount = request.POST.get('deposit_amount', 0) or 0
        max_days = request.POST.get('max_days', 7) or 7
        photo = request.FILES.get('photo')
        insurance_plan = request.POST.get('insurance_plan', 'none')

        if not title or not description or not pickup_location or not category_id:
            messages.error(request, 'กรุณากรอกข้อมูลให้ครบ')
        else:
            item = Item.objects.create(
                owner=request.user,
                category_id=category_id,
                title=title,
                description=description,
                condition=condition,
                campus=campus,
                pickup_location=pickup_location,
                is_free=is_free,
                deposit_amount=deposit_amount,
                max_days=max_days,
                photo=photo,
                insurance_plan=insurance_plan,
            )
            messages.success(request, 'โพสต์สิ่งของสำเร็จ!')
            return redirect('item_detail', item_id=item.item_id)

    return render(request, 'items/create_item.html', {'categories': categories})


@login_required
def create_request(request, item_id):
    item = get_object_or_404(Item, item_id=item_id)
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        message = request.POST.get('message', '')
        
        BorrowRequest.objects.create(
            item=item,
            borrower=request.user,
            lender=item.owner,
            start_date=start_date,
            end_date=end_date,
            borrower_message=message,
        )
        
        create_notification(item.owner, f"มีคนสนใจขอยืม {item.title} จากคุณ!")

        messages.success(request, 'ส่งคำขอยืมสำเร็จ!')
        return redirect('item_detail', item_id=item.item_id)
    
    return render(request, 'items/request_form.html', {'item': item})

@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, item_id=item_id, owner=request.user)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'ลบสิ่งของแล้ว')
        return redirect('dashboard')
    return render(request, 'items/confirm_delete.html', {'item': item})

@login_required
def dashboard(request):

    my_borrowing = BorrowRequest.objects.filter(
        borrower=request.user
    ).select_related('item', 'lender').order_by('-created_at')

    incoming_requests = BorrowRequest.objects.filter(
        lender=request.user
    ).select_related('item', 'borrower').order_by('-created_at')

    my_items = Item.objects.filter(owner=request.user).order_by('-created_at')

    return render(request, 'items/dashboard.html', {
        'my_borrowing': my_borrowing,
        'incoming_requests': incoming_requests,
        'my_items': my_items,
    })


@login_required
def decline_request(request, request_id):
    borrow_request = get_object_or_404(BorrowRequest, request_id=request_id, lender=request.user)
    borrow_request.status = 'declined'
    borrow_request.save()
    messages.success(request, 'ปฏิเสธคำขอแล้ว')
    return redirect('dashboard')


@login_required
def approve_request(request, request_id):
    borrow_request = get_object_or_404(BorrowRequest, request_id=request_id, lender=request.user)
    
    borrow_request.status = 'approved'
    borrow_request.approved_at = timezone.now()
    borrow_request.item.status = 'borrowed'
    borrow_request.item.is_available = False
    borrow_request.item.save()
    borrow_request.save()
    create_notification(borrow_request.borrower, f"เย้! เจ้าของอนุมัติให้คุณยืม {borrow_request.item.title} แล้ว")
    messages.success(request, 'อนุมัติคำขอแล้ว')
    return redirect('dashboard')


@login_required
def start_chat(request, item_id):
    """ฟังก์ชันสำหรับกดปุ่มแชทจากหน้า Detail เพื่อสร้างหรือเปิดห้องเดิม"""
    item = get_object_or_404(Item, item_id=item_id)
    
    if item.owner == request.user:
        messages.warning(request, "คุณไม่สามารถแชทกับตัวเองได้")
        return redirect('item_detail', item_id=item_id)

    chat_room, created = ChatRoom.objects.get_or_create(
        item=item,
        borrower=request.user,
        owner=item.owner
    )
    
    return redirect('chat_room', room_id=chat_room.id)

@login_required
def chat_room(request, room_id):
    """หน้าแสดงข้อความในห้องแชท"""
    chat_room = get_object_or_404(ChatRoom, id=room_id)
    
   
    if request.user != chat_room.borrower and request.user != chat_room.owner:
        return redirect('item_list')

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                room=chat_room,
                sender=request.user,
                content=content
            )
           
            return redirect('chat_room', room_id=chat_room.id)

    messages_list = chat_room.messages.all().order_by('timestamp')
    
    return render(request, 'items/chat_room.html', {
        'chat_room': chat_room,
        'messages_list': messages_list,
    })

@login_required
def inbox(request):
    
    chat_rooms = ChatRoom.objects.filter(
        models.Q(borrower=request.user) | models.Q(owner=request.user)
    ).select_related('item', 'borrower', 'owner').order_by('-created_at')
    
    return render(request, 'items/inbox.html', {'chat_rooms': chat_rooms})

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import BorrowRequest 

@login_required
def cancel_request(request, request_id):
   
    borrow_request = get_object_or_404(BorrowRequest, request_id=request_id, borrower=request.user)
    
    if borrow_request.status == 'pending':
        borrow_request.delete()  
        messages.success(request, "ยกเลิกคำขอยืมเรียบร้อยแล้ว")
    else:
        messages.error(request, "ไม่สามารถยกเลิกได้ เนื่องจากเจ้าของดำเนินการไปแล้ว")
        
    return redirect('dashboard')

@login_required
def return_item(request, request_id):
   
    borrow_request = get_object_or_404(BorrowRequest, request_id=request_id, lender=request.user)
    
    if borrow_request.status in ['approved', 'returning']:
       
        borrow_request.status = 'returned'
        borrow_request.save()

        item = borrow_request.item
        item.status = 'active'     
        item.is_available = True   
        item.save()

        messages.success(request, f"ได้รับคืน {item.title} เรียบร้อย! ตอนนี้คนอื่นสามารถยืมต่อได้แล้ว")
    
    return redirect('dashboard')

@login_required
def notify_return(request, request_id):
   
    borrow_request = get_object_or_404(BorrowRequest, request_id=request_id, borrower=request.user)
    
    if borrow_request.status == 'approved':
        borrow_request.status = 'returning'  
        borrow_request.save()
        create_notification(borrow_request.lender, f"{borrow_request.borrower.username} แจ้งว่าส่งคืน {borrow_request.item.title} ให้คุณแล้ว!")
        messages.success(request, "แจ้งเจ้าของว่าคืนของเรียบร้อยแล้ว รอเจ้าของยืนยันครับ")
    
    return redirect('dashboard')