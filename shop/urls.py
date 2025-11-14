from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'categories', views.CategoryViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'cart', views.ShoppingCartViewSet, basename='cart')
router.register(r'reviews', views.ReviewViewSet, basename='review')
router.register(r'addresses', views.UserAddressViewSet, basename='address')
router.register(r'payments', views.PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
]