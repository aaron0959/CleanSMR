from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('shop/', views.reactor_shop, name='shop'),  
    path('subscription/', views.subscription_view, name='subscription'),
    path('about/', views.about_view, name='about'),
    path('enable-2fa/', views.enable_2fa_view, name='enable_2fa'),
    path('generate-2fa-qr/', views.generate_2fa_qr, name='generate_2fa_qr'),
    path('profile/', views.verify_2fa_code, name='verify_2fa_code'),
    path('account/disable-2fa/', views.disable_2fa, name='disable_2fa'),
    path('account/details/', views.profile_view, name='account_details'),  
    path('create-checkout-session-subsciption/', views.create_checkout_session_subscription, name='create-checkout-session-subsciption'),
    path('create-checkout-session-purchase/', views.create_checkout_session_purchase, name='create-checkout-session-purchase'),
    path('delete_subscription/', views.delete_subscription, name='delete_subscription'),
    path('shop/success-subscription/', views.success_subscription, name='success'),
    path('create-checkout-session-purchase/success-purchase/', views.success_purchase, name='success_purchase'),
    path('cart/', views.cart_view, name='cart-view'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove-from-cart'),
   
]