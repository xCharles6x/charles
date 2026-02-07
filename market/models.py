from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.utils import timezone


class Profile(models.Model):
    """Extended user profile with contact info and role"""
    ROLE_CHOICES = [
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('both', 'Buyer & Seller'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True, max_length=500)
    avatar = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile ({self.get_role_display()})"
    
    def average_rating(self):
        """Calculate average rating for sellers"""
        ratings = self.user.received_ratings.all()  # FIXED: Use self.user
        if ratings.exists():
            return ratings.aggregate(Avg('rating'))['rating__avg']
        return None
    
    def total_ratings(self):
        """Get total number of ratings"""
        return self.user.received_ratings.count()  # FIXED: Use self.user


class Product(models.Model):
    """Product listings"""
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('books', 'Books & Stationery'),
        ('clothing', 'Clothing & Accessories'),
        ('furniture', 'Furniture'),
        ('sports', 'Sports & Fitness'),
        ('other', 'Other'),
    ]
    
    CONDITION_CHOICES = [
        ('new', 'Brand New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_available = models.BooleanField(default=True)
    views_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def increment_views(self):
        """Increment product view count"""
        self.views_count += 1
        self.save(update_fields=['views_count'])


class Cart(models.Model):
    """Shopping cart items"""
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['buyer', 'product']
    
    def __str__(self):
        return f"{self.buyer.username}'s cart - {self.product.name}"
    
    def get_total_price(self):
        return self.product.price * self.quantity


class Conversation(models.Model):
    """Conversation between two users about a product"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='conversations')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_conversations')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'buyer', 'seller']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation: {self.buyer.username} & {self.seller.username} about {self.product.name}"
    
    def get_last_message(self):
        return self.messages.first()
    
    def unread_count(self, user):
        """Count unread messages for a specific user"""
        return self.messages.filter(receiver=user, read=False).count()


class Message(models.Model):
    """Individual messages in a conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"


class Rating(models.Model):
    """Ratings for sellers"""
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')  # Changed this line
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_ratings')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings', null=True, blank=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['seller', 'buyer', 'product']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.buyer.username} rated {self.seller.username}: {self.rating}/5"
    
class ProductView(models.Model):
    """Track user views for personalized recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_views')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='user_views')
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"{self.user.username} viewed {self.product.name}"