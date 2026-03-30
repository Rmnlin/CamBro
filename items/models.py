import uuid
from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    category_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, default='📦')
    order = models.PositiveIntegerField(default=0, help_text="กำหนดลำดับการแสดงผล")
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name

class Item(models.Model):
    CONDITION_CHOICES = [
        ('new', 'ใหม่'),
        ('good', 'ดี'),
        ('fair', 'พอใช้'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'ใช้งาน'),
        ('borrowed', 'ถูกยืม'),
        ('inactive', 'ไม่ใช้งาน'),
    ]
    
    CAMPUS_CHOICES = [
        ('rangsit', 'รังสิต'),
        ('tha_prachan', 'ท่าพระจันทร์'),
        ('lampang', 'ลำปาง'),
    ]
    
    item_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    photo = models.ImageField(upload_to='items/', blank=True, null=True)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    
    is_free = models.BooleanField(default=True)
    deposit_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    max_days = models.IntegerField(default=7)
    insurance_plan = models.CharField(max_length=20, default='none')
    
    campus = models.CharField(max_length=20, choices=CAMPUS_CHOICES, default='rangsit')
    pickup_location = models.CharField(max_length=200)
    
    is_available = models.BooleanField(default=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class BorrowRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'รอดำเนินการ'),
        ('approved', 'อนุมัติ'),
        ('declined', 'ปฏิเสธ'),
        ('active', 'กำลังยืม'),
        ('returning', 'กำลังคืน'),
        ('returned', 'คืนแล้ว'),
    ]
    
    request_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='requests')
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrow_requests')
    lender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lend_requests')
    
    start_date = models.DateField()
    end_date = models.DateField()
    borrower_message = models.TextField(blank=True)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    delivery_status = models.CharField(max_length=20, default='order_confirmed', verbose_name="สถานะการจัดส่ง")
    rider = models.ForeignKey('Rider', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.borrower.username} -> {self.item.title}"
class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='chat_rooms')
    
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrowed_chats')
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_chats')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"แชทของ {self.item.title} ({self.borrower.username} คุยกับ {self.owner.username})"

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp'] 

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True, null=True) 
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"
    
class Rider(models.Model):
    name = models.CharField(max_length=100, verbose_name="ชื่อไรเดอร์")
    vehicle_type = models.CharField(max_length=50, verbose_name="ยานพาหนะ", default="Honda PCX-150 9999")
    phone_number = models.CharField(max_length=15, verbose_name="เบอร์โทรศัพท์")

    def __str__(self):
        return self.name

class Review(models.Model):
    RATING_CHOICES = [(i, i) for i in range(1, 6)]

    borrow_request = models.OneToOneField(BorrowRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='review')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    reviewee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reviewer.username} รีวิว {self.reviewee.username} ({self.rating}⭐)"