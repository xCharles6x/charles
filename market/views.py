from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from .models import Product, Profile, Cart, Conversation, Message, Rating, ProductView
from .forms import UserRegistrationForm, ProfileUpdateForm, ProductForm, MessageForm, RatingForm


def home(request):
    products = Product.objects.filter(is_available=True).select_related('seller')[:12]
    categories = Product.CATEGORY_CHOICES
    
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'market/home.html', context)


def register(request):
    """User registration"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create profile
            Profile.objects.create(
                user=user,
                role=form.cleaned_data['role'],
                phone=form.cleaned_data.get('phone', ''),
                location=form.cleaned_data.get('location', ''),
            )
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'market/register.html', {'form': form})


@login_required
def profile_view(request, username=None):
    """View user profile"""
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    profile = get_object_or_404(Profile, user=user)
    products = Product.objects.filter(seller=user, is_available=True)
    
    # Get seller ratings
    ratings = Rating.objects.filter(seller=user).select_related('buyer', 'product')
    avg_rating = profile.average_rating()
    total_ratings = profile.total_ratings()
    
    context = {
        'profile': profile,
        'user_profile': user,
        'products': products,
        'ratings': ratings,
        'avg_rating': avg_rating,
        'total_ratings': total_ratings,
        'is_own_profile': request.user == user,
    }
    return render(request, 'market/profile.html', context)


@login_required
def profile_edit(request):
    """Edit user profile"""
    profile = get_object_or_404(Profile, user=request.user)
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile)
    
    return render(request, 'market/profile_edit.html', {'form': form})


def product_list(request):
    """List all products with filtering and search"""
    products = Product.objects.filter(is_available=True).select_related('seller')
    
    # Search
    query = request.GET.get('q', '')
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # Filter by category
    category = request.GET.get('category', '')
    if category:
        products = products.filter(category=category)
    
    # Filter by condition
    condition = request.GET.get('condition', '')
    if condition:
        products = products.filter(condition=condition)
    
    # Sort
    sort = request.GET.get('sort', '-created_at')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'popular':
        products = products.order_by('-views_count')
    else:
        products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'category': category,
        'condition': condition,
        'sort': sort,
        'categories': Product.CATEGORY_CHOICES,
        'conditions': Product.CONDITION_CHOICES,
    }
    return render(request, 'market/product_list.html', context)


def product_detail(request, pk):
    """Product detail page"""
    product = get_object_or_404(Product, pk=pk)
    
    # Track view
    if request.user.is_authenticated and request.user != product.seller:
        product.increment_views()
        ProductView.objects.create(user=request.user, product=product)
    
    # Get seller ratings
    seller_profile = product.seller.profile
    avg_rating = seller_profile.average_rating()
    total_ratings = seller_profile.total_ratings()
    
    # Similar products (same category)
    similar_products = Product.objects.filter(
        category=product.category,
        is_available=True
    ).exclude(pk=product.pk)[:4]
    
    context = {
        'product': product,
        'seller_profile': seller_profile,
        'avg_rating': avg_rating,
        'total_ratings': total_ratings,
        'similar_products': similar_products,
        'can_message': request.user.is_authenticated and request.user != product.seller,
    }
    return render(request, 'market/product_detail.html', context)


@login_required
def product_create(request):
    """Create new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            messages.success(request, 'Product listed successfully!')
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm()
    
    return render(request, 'market/product_form.html', {'form': form, 'action': 'Create'})


@login_required
def product_edit(request, pk):
    """Edit product"""
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'market/product_form.html', {'form': form, 'action': 'Edit', 'product': product})


@login_required
def product_delete(request, pk):
    """Delete product"""
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('profile')
    
    return render(request, 'market/product_confirm_delete.html', {'product': product})


@login_required
def cart_view(request):
    """View shopping cart"""
    cart_items = Cart.objects.filter(buyer=request.user).select_related('product', 'product__seller')
    total = sum(item.get_total_price() for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'market/cart.html', context)


@login_required
@require_POST
def cart_add(request, pk):
    """Add product to cart"""
    product = get_object_or_404(Product, pk=pk)
    
    if product.seller == request.user:
        return JsonResponse({'error': 'Cannot add your own product to cart'}, status=400)
    
    cart_item, created = Cart.objects.get_or_create(
        buyer=request.user,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    cart_count = Cart.objects.filter(buyer=request.user).count()
    
    return JsonResponse({
        'success': True,
        'message': 'Product added to cart',
        'cart_count': cart_count
    })


@login_required
@require_POST
def cart_remove(request, pk):
    """Remove item from cart"""
    cart_item = get_object_or_404(Cart, pk=pk, buyer=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart')
    return redirect('cart')


@login_required
@require_POST
def cart_update(request, pk):
    """Update cart item quantity"""
    cart_item = get_object_or_404(Cart, pk=pk, buyer=request.user)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, 'Cart updated')
    else:
        cart_item.delete()
        messages.success(request, 'Item removed from cart')
    
    return redirect('cart')


@login_required
def conversations_list(request):
    """List all conversations"""
    conversations = Conversation.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).select_related('product', 'buyer', 'seller').prefetch_related('messages')
    
    # Add unread count to each conversation
    for conv in conversations:
        conv.unread = conv.unread_count(request.user)
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'market/conversations_list.html', context)


@login_required
def conversation_detail(request, pk):
    """View conversation and send messages"""
    conversation = get_object_or_404(Conversation, pk=pk)
    
    # Ensure user is part of this conversation
    if request.user not in [conversation.buyer, conversation.seller]:
        return HttpResponseForbidden("You are not part of this conversation.")
    
    if request.method == 'POST':
        content = request.POST.get('content')
        
        if content and content.strip():
            # Determine who the receiver is (the other person in the conversation)
            if conversation.buyer == request.user:
                receiver = conversation.seller
            else:
                receiver = conversation.buyer
            
            # Create the message with both sender and receiver
            msg = Message.objects.create(
                sender=request.user,
                receiver=receiver,
                conversation=conversation,
                content=content.strip()
            )
            
            messages.success(request, 'Message sent!')
            return redirect('conversation_detail', pk=pk)
    
    # Get all messages in this conversation
    conv_messages = conversation.messages.all().order_by('timestamp')
    
    # Mark messages as read
    conversation.messages.filter(receiver=request.user, read=False).update(read=True)
    
    # Determine the other user in the conversation
    if conversation.buyer == request.user:
        other_user = conversation.seller
    else:
        other_user = conversation.buyer
    
    context = {
        'conversation': conversation,
        'messages': conv_messages,
        'other_user': other_user,
    }
    return render(request, 'market/conversation_detail.html', context)


@login_required
def start_conversation(request, product_pk):
    """Start a new conversation about a product"""
    product = get_object_or_404(Product, pk=product_pk)
    
    if product.seller == request.user:
        messages.error(request, 'You cannot message yourself about your own product')
        return redirect('product_detail', pk=product_pk)
    
    # Check if conversation already exists
    existing_conversation = Conversation.objects.filter(
        product=product,
        buyer=request.user,
        seller=product.seller
    ).first()
    
    if request.method == 'POST':
        content = request.POST.get('message', '').strip()
        
        if content:
            # Get or create conversation
            conversation, created = Conversation.objects.get_or_create(
                product=product,
                buyer=request.user,
                seller=product.seller
            )
            
            # Create the initial message
            Message.objects.create(
                sender=request.user,
                receiver=product.seller,
                conversation=conversation,
                content=content
            )
            
            messages.success(request, 'Message sent successfully!')
            return redirect('conversation_detail', pk=conversation.pk)
        else:
            messages.error(request, 'Please write a message')
    
    # If conversation exists, redirect to it
    if existing_conversation:
        return redirect('conversation_detail', pk=existing_conversation.pk)
    
    # Show the form to write initial message
    context = {
        'product': product,
    }
    return render(request, 'market/start_conversation.html', context)


@login_required
def rate_seller(request, username):
    """Rate a seller"""
    seller = get_object_or_404(User, username=username)
    
    if seller == request.user:
        messages.error(request, 'You cannot rate yourself')
        return redirect('profile', username=username)
    
    product_pk = request.GET.get('product')
    product = get_object_or_404(Product, pk=product_pk) if product_pk else None
    
    # Check if already rated
    existing_rating = Rating.objects.filter(
        seller=seller,
        buyer=request.user,
        product=product
    ).first()
    
    if request.method == 'POST':
        form = RatingForm(request.POST, instance=existing_rating)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.seller = seller
            rating.buyer = request.user
            rating.product = product
            rating.save()
            messages.success(request, 'Rating submitted successfully!')
            return redirect('profile', username=username)
    else:
        form = RatingForm(instance=existing_rating)
    
    context = {
        'form': form,
        'seller': seller,
        'product': product,
        'existing_rating': existing_rating,
    }
    return render(request, 'market/rate_seller.html', context)


@login_required
def recommendations(request):
    """Personalized product recommendations"""
    # Get user's viewed products
    viewed_products = ProductView.objects.filter(user=request.user).values_list('product__category', flat=True)
    
    # Get user's cart items
    cart_categories = Cart.objects.filter(buyer=request.user).values_list('product__category', flat=True)
    
    # Combine categories
    interested_categories = list(set(list(viewed_products) + list(cart_categories)))
    
    # Get products from interested categories
    if interested_categories:
        recommended = Product.objects.filter(
            category__in=interested_categories,
            is_available=True
        ).exclude(seller=request.user).order_by('-views_count', '-created_at')[:12]
    else:
        # Fallback to popular products
        recommended = Product.objects.filter(
            is_available=True
        ).exclude(seller=request.user).order_by('-views_count')[:12]
    
    context = {
        'recommended_products': recommended,
    }
    return render(request, 'market/recommendations.html', context)