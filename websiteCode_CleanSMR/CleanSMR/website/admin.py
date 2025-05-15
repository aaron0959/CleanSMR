from django.contrib import admin
from .models import User, CustomUserManager, SubscriptionTier, Subscription, APIUsage, PaymentHistory

# Register your models here.
admin.site.register(User)
admin.site.register(SubscriptionTier)
admin.site.register(Subscription)
admin.site.register(APIUsage)
admin.site.register(PaymentHistory) 