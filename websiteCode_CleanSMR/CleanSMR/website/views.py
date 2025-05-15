from datetime import datetime, timedelta, timezone
from venv import logger
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
import base64
import json
import stripe
import pyotp
from io import BytesIO
from qrcode import make as make_qr
from .forms import RegisterForm
from .models import CustomUserManager, PaymentHistory, Subscription, SubscriptionTier, User, APIUsage, Reactor, Cart, UserReactor
from django.views.decorators.csrf import csrf_exempt
# Public Views
def index(request):
    """Homepage view."""
    return render(request, 'homepage/index.html')

def about_view(request):
    """About page with team information and contact form."""
    team_members = [
        {
            'name': 'John Doe',
            'position': 'CEO',
            'image': {'url': 'images/team/john-doe.jpg'},
            'linkedin': '#',
            'twitter': '#'
        },
        {
            'name': 'Jane Smith',
            'position': 'CTO',
            'image': {'url': 'images/team/jane-smith.jpg'},
            'linkedin': '#',
            'twitter': '#'
        },
        {
            'name': 'Alice Johnson',
            'position': 'COO',
            'image': {'url': 'images/team/alice-johnson.jpg'},
        }
    ]

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # TODO: Implement email sending logic
        messages.success(request, 'Message sent successfully!')
        
    return render(request, 'homepage/about.html', {'team_members': team_members})

# Authentication Views
def login_view(request):
    """Handle user login with optional 2FA."""
    if request.method == 'GET':
        return render(request, 'account/login.html')
    
    username = request.POST.get('username')
    password = request.POST.get('password')
    two_factor_code = request.POST.get('two_factor_code', '')
    
    user = authenticate(request, username=username, password=password)
    if user is not None:
        # Handle 2FA verification
        if user.two_factor_enabled and two_factor_code:
            if user.verify_2fa(two_factor_code):
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('index')
            messages.error(request, 'Invalid 2FA code')
            return render(request, 'account/login.html')
        
        # Show 2FA field if enabled but code not provided
        elif user.two_factor_enabled and not two_factor_code:
            context = {'requires_2fa': True, 'username': username}
            return render(request, 'account/login.html', context)
        
        # Standard login without 2FA
        login(request, user)
        messages.success(request, 'Login successful!')
        return redirect('index')
    
    messages.error(request, 'Invalid username or password')
    return render(request, 'account/login.html')

def register_view(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                password=form.cleaned_data['password'],
            )
            login(request, user)
            messages.success(request, 'Successfully registered and logged in!')
            return redirect('index')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = RegisterForm()
    return render(request, 'account/register.html', {'form': form})

def logout_view(request):
    """Handle user logout."""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Successfully logged out!')
        return redirect('index')

# Profile and Account Management Views
@login_required
def profile_view(request):
    """User profile view with 2FA setup."""
    user = request.user
    
    # Initialize 2FA if not exists
    if not user.two_factor_secret:
        user.two_factor_secret = pyotp.random_base32()
        user.save()
    
    # Handle 2FA verification
    if request.method == 'POST':
        auth_code = request.POST.get('auth_code')
        if user.verify_2fa(auth_code):
            user.two_factor_enabled = True
            user.save()
            messages.success(request, "Two-Factor Authentication enabled successfully!")
            return redirect('profile')
        messages.error(request, "Invalid authentication code. Please try again.")
    
    # Generate QR code for 2FA setup
    qr_code_image = None
    if not user.two_factor_enabled:
        totp = pyotp.TOTP(user.two_factor_secret)
        provisioning_uri = totp.provisioning_uri(user.email, issuer_name="CleanSMR")
        qr = make_qr(provisioning_uri)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_code_image = base64.b64encode(buffer.getvalue()).decode()

    context = {
        'user': user,
        'qr_code_image': qr_code_image,
        'two_factor_enabled': user.two_factor_enabled
    }
    return render(request, 'account/account-details.html', context)

@login_required
def settings_view(request):
    """User settings view."""
    return render(request, 'account/settings.html')

@login_required
def subscription_view(request):
    products = stripe.Product.list(active=True)
    subscription_tiers = []

    for product in products:
        prices = stripe.Price.list(product=product.id, active=True)
        for price in prices:
            if price.recurring:
                subscription_tiers.append({
                    'name': product.name,
                    'description': product.description,
                    'price': price.unit_amount / 100,
                    'currency': price.currency,
                    'interval': price.recurring.interval,
                    'stripe_price_id': price.id,
                    'metadata': product.metadata,
                    'image': product.images[0] if product.images else None,
                })

    return render(request, 'shop/subscription-details.html', {
        'subscription_tiers': subscription_tiers,
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
    })

@login_required
def create_checkout_session_purchase(request):
    # Retrieve the user's cart
    cart = get_object_or_404(Cart, user=request.user)

    if not cart.items.exists():
        return JsonResponse({'error': 'Cart is empty.'}, status=400)

    # Prepare line items for Stripe Checkout
    line_items = []
    for item in cart.items.all():
        line_items.append({
            'price_data': {
                'currency': 'usd',  # Change to your preferred currency
                'product_data': {
                    'name': item.name,
                    'description': item.description,
                },
                'unit_amount': int(item.price * 100),  # Price in cents
            },
            'quantity': 1,  # Update quantity logic as needed
        })

    # Create the Stripe Checkout Session
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            line_items=line_items,
            success_url=request.build_absolute_uri('checkout/success'),  
            cancel_url=request.build_absolute_uri('/checkout/cancel/'),  
        )
        return redirect(checkout_session.url)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@login_required
def create_checkout_session_subscription(request):
    price_id = request.POST.get('price_id')
    
    try:
        subscription = request.user.subscription
        stripe_customer_id = subscription.stripe_customer_id
    except Subscription.DoesNotExist:
        customer = stripe.Customer.create(
            email=request.user.email,
            metadata={'user_id': request.user.id}
        )
        stripe_customer_id = customer.id

    # Create checkout session
    checkout_session = stripe.checkout.Session.create(
        customer=stripe_customer_id,
        payment_method_types=['card'],
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        mode='subscription',
        success_url=request.build_absolute_uri('/success/') + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri('/cancel/'),
        metadata={
            'user_id': request.user.id,
            'price_id': price_id
        }
    )
    
    return redirect(checkout_session.url)


def success_subscription(request):
    session_id = request.GET.get('session_id')
    
    if session_id:
        # Retrieve all the necessary data
        session = stripe.checkout.Session.retrieve(session_id)
        subscription = stripe.Subscription.retrieve(session.subscription)
        product = stripe.Product.retrieve(subscription.plan.product)
        
        # Create or get the subscription tier
        tier, created = SubscriptionTier.objects.get_or_create(
            stripe_price_id=subscription.plan.id,
            defaults={
                'name': product.name,
                'price': subscription.plan.amount / 100,
                'description': product.description,
                'daily_api_calls': product.metadata.get('daily_api_calls', 1000),  # Default value
                'monthly_api_calls': product.metadata.get('monthly_api_calls', 30000),  # Default value
                'features': product.metadata
            }
        )
        
        # Create or update subscription
        subscription_obj, created = Subscription.objects.update_or_create(
            user=request.user,
            defaults={
                'tier': tier,
                'stripe_customer_id': session.customer,
                'stripe_subscription_id': subscription.id,
                'subscription_type': tier.name.lower(),
                'is_active': True,
                'start_date': datetime.now(tz=timezone.utc),
                'end_date': datetime.now(tz=timezone.utc) + timedelta(days=30),  # Assuming a 30-day subscription
                'auto_renew': True
            }
        )
        
        # Record payment
    
        PaymentHistory.objects.create(
        user=request.user,
        payment_type='subscription',
        amount=subscription.plan.amount / 100,
        currency=subscription.plan.currency,
        metadata={
            'subscription_id': subscription_obj.id,
            'tier_name': tier.name,
            'stripe_subscription_id': subscription.id,
        }
    )
    return render(request, 'shop/success-subscription.html')

@login_required
def success_purchase(request):
    session_id = request.GET.get('session_id')

    if session_id:
        try:
            # Retrieve the Stripe checkout session
            session = stripe.checkout.Session.retrieve(session_id)

            # Check if the session is for a one-time purchase
            if session.mode == 'payment':
                # Retrieve the product details from the session line items
                line_item = session.line_items.data[0]  # Assuming one item for simplicity
                product_name = line_item.description  # Name of the product
                product_description = line_item.description  # Description of the product
                product_price = line_item.amount_total / 100  # Convert from cents to decimal
                stripe_product_id = line_item.price.product  # Stripe product ID

                # Create or get the Reactor purchase
                UserReactor.objects.create(
                    user=request.user,
                    reactor__stripe_product_id=stripe_product_id,
                    defaults={
                        'quantity': 1,  # Update quantity if exists
                        'name': product_name,
                        'description': product_description,
                        'price': product_price,
                    }
                )

                # Record payment history
                PaymentHistory.objects.create(
                    user=request.user,
                    payment_type='smr_purchase',  # Use 'smr_purchase' as the type
                    amount=product_price,
                    currency='USD',  # Assuming default currency is USD
                    stripe_payment_id=session.payment_intent,  # Use the payment intent ID from Stripe
                    metadata={
                        'reactor_serial_number': stripe_product_id
                    }
                )
                
        except Exception as e:
            # Handle exceptions (e.g., invalid session ID, Stripe errors)
            print(f"Error retrieving Stripe session: {e}")
            return redirect('/error/')  # Redirect to an error page or handle as needed

    return render(request, 'shop/success-purchase.html')

@login_required
def reactor_shop(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    # Fetch products from Stripe
    products = stripe.Product.list()  # Retrieve all active products
    reactors = []

    for product in products:
        prices = stripe.Price.list(product=product.id)
        for price in prices:
            if not price.recurring and price.type == 'one_time':  # Ensure it's a one-time payment
                reactors.append({
                    'name': product.name,
                    'description': product.description,
                    'price': price.unit_amount / 100,  # Convert to decimal
                    'stripe_price_id': price.id,
                    'currency': price.currency,
                    'metadata': product.metadata
                })

    # Get or create the user's cart
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Handle adding items to the cart
    if request.method == "POST":
        stripe_price_id = request.POST.get('price_id')
        if stripe_price_id:
            # Find the corresponding product
            product = next((item for item in reactors if item['stripe_price_id'] == stripe_price_id), None)
            if product:
                # Create or get the Reactor object for this Stripe product
                reactor, _ = Reactor.objects.get_or_create(
                    name=product['name'],
                    description=product['description'],
                    price=product['price'],
                    stripe_product_id=stripe_price_id,
                )
                cart.items.add(reactor)
                messages.success(request, f"{reactor.name} has been added to your cart!")

        return redirect('shop')  # Redirect to avoid form re-submission

    # Pass cart items and reactors to the template
    cart_items = cart.items.all()

    return render(request, 'shop/reactor-shop.html', {
        'reactors': reactors,
        'cart_items': cart_items,
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
    })
def enable_2fa_view(request):
    """Enable 2FA for user."""
    user = request.user
    if request.method == 'POST':
        user.enable_2fa()
        messages.success(request, "2FA has been enabled.")
        return redirect('verify_2fa')

    qr_code_url = user.get_2fa_qr_url()
    qr_code_image = None
    if qr_code_url:
        img = make_qr(qr_code_url)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return render(request, 'account/enable_2fa.html', {
        'qr_code_image': qr_code_image,
    })

@login_required
def generate_2fa_qr(request):
    """Generate QR code for 2FA setup."""
    if not request.user.two_factor_enabled:
        request.user.enable_2fa()
    qr_url = request.user.get_2fa_qr_url()
    return JsonResponse({'qr_url': qr_url})

@login_required
def disable_2fa(request):
    """Disable 2FA for user."""
    if request.method == 'POST':
        user = request.user
        user.two_factor_enabled = False
        user.totp_secret = None
        user.save()
        messages.success(request, "Two-Factor Authentication has been disabled.")
    return redirect('profile')

from django.views.decorators.http import require_http_methods

@require_http_methods(["POST"])
def verify_2fa_code(request):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    pending_user_id = request.session.get('pending_user_id')
    if not pending_user_id:
        return JsonResponse({
            'success': False,
            'error': 'No pending authentication'
        })


def delete_subscription(request):
    user = request.user
    try:
        # Delete associated models
        Subscription.objects.filter(user=user).delete()
        APIUsage.objects.filter(user=user).delete()
        PaymentHistory.objects.filter(user=user).delete()
        
        # Redirect to a success page or home
        return redirect('index')  
    except Exception as e:
        # Handle exceptions if necessary
        print(f"Error deleting subscription: {e}")
        return redirect('error_page')  # replace with your error page



@login_required
def cart_view(request):
    # Get the cart for the current user, or create one if it doesn't exist
    cart, created = Cart.objects.get_or_create(user=request.user)
    # Retrieve all items in the cart
    cart_items = cart.items.all()

    # Calculate the total price
    total_price = sum(item.price for item in cart_items)

    return render(request, 'shop/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })

@login_required
def remove_from_cart(request, item_id):
    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(Reactor, id=item_id)
    cart.items.remove(item)
    return redirect('cart-view')
