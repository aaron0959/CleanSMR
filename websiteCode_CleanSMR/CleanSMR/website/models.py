from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.conf import settings
import pyotp

class CustomUserManager(BaseUserManager):
    def _create_user(self, username, email, phone, password, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not username:
            raise ValueError('The Username field must be set')
        if not phone:
            raise ValueError('The Phone field must be set')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, phone, password, **extra_fields)

    def create_superuser(self, username, email, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, phone, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True)
    phone = models.CharField(max_length=15, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)
    
    # Google Authenticator fields
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email', 'phone']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.username} - {self.email}'

    def enable_2fa(self):
        self.two_factor_secret = pyotp.random_base32()
        self.two_factor_enabled = True
        self.save()

    def verify_2fa(self, code):
        if not self.two_factor_enabled:
            return False
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.verify(code)

    def get_2fa_qr_url(self):
        if not self.two_factor_enabled:
            return None
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.provisioning_uri(self.email, issuer_name="CleanSMR")

class SubscriptionTier(models.Model):
    name = models.CharField(max_length=50)
    daily_api_calls = models.IntegerField()
    monthly_api_calls = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_price_id = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    features = models.JSONField(default=dict)
    
    def __str__(self):
        return f"{self.name} - {self.daily_api_calls} calls/day"

class Subscription(models.Model):
    SUBSCRIPTION_TYPES = (
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tier = models.ForeignKey(SubscriptionTier, on_delete=models.PROTECT)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPES)
    is_active = models.BooleanField(default=False)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.subscription_type}"

    def get_api_calls_remaining_today(self):
        today = timezone.now().date()
        calls_today = APIUsage.objects.filter(
            user=self.user,
            timestamp__date=today
        ).count()
        return self.tier.daily_api_calls - calls_today

    def get_api_calls_remaining_month(self):
        today = timezone.now().date()
        first_day = today.replace(day=1)
        calls_this_month = APIUsage.objects.filter(
            user=self.user,
            timestamp__date__gte=first_day
        ).count()
        return self.tier.monthly_api_calls - calls_this_month

    def can_make_api_call(self):
        return (self.is_active and 
                self.get_api_calls_remaining_today() > 0 and 
                self.get_api_calls_remaining_month() > 0)

class APIUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    endpoint = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    response_time = models.FloatField()
    status_code = models.IntegerField()
    request_method = models.CharField(max_length=10)
    response_size = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} - {self.endpoint} - {self.timestamp}"


class PaymentHistory(models.Model):
    PAYMENT_TYPES = (
        ('subscription', 'Subscription'),
        ('smr_purchase', 'SMR Purchase'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    stripe_payment_id = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)
    
    def __str__(self):
        return f"{self.user.username} - {self.payment_type} - {self.timestamp}"
    
class Reactor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_product_id = models.CharField(max_length=100, blank=True, null=True)  
    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    items = models.ManyToManyField(Reactor)

class UserReactor(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reactor = models.ForeignKey(Reactor, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)  
    
    def __str__(self):
        return f"{self.user.username} - {self.reactor.name} - {self.quantity}"