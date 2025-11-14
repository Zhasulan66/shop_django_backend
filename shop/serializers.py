from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import (
    User, Category, Product, Order, OrderItem,
    ShoppingCart, CartItem, Review, UserAddress, Payment
)
from django.db import transaction
import uuid


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'address', 'first_name', 'last_name')
        read_only_fields = ('id',)


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'phone', 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
            return attrs
        raise serializers.ValidationError('Must include "email" and "password"')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ('orderItemId', 'product', 'product_name', 'quantity', 'price', 'total_price')

    def get_total_price(self, obj):
        return obj.get_total_price()


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'


class CreateOrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ('user', 'order_items', 'totalAmount', 'status')

    def create(self, validated_data):
        order_items_data = validated_data.pop('order_items')

        with transaction.atomic():
            order = Order.objects.create(**validated_data)

            for item_data in order_items_data:
                OrderItem.objects.create(order=order, **item_data)

            # Update product stock
            for item_data in order_items_data:
                product = item_data['product']
                quantity = item_data['quantity']
                product.stock -= quantity
                product.save()

        return order


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ('cartItemId', 'product', 'product_name', 'product_price', 'quantity', 'total_price')

    def get_total_price(self, obj):
        return obj.get_total_price()


class ShoppingCartSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = ShoppingCart
        fields = '__all__'

    def get_total_price(self, obj):
        return sum(item.get_total_price() for item in obj.cart_items.all())


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        product_id = attrs['product_id']
        quantity = attrs['quantity']

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")

        if product.stock < quantity:
            raise serializers.ValidationError("Insufficient stock")

        attrs['product'] = product
        return attrs


class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ('user',)


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = '__all__'
        read_only_fields = ('user',)


class PaymentSerializer(serializers.ModelSerializer):
    order_amount = serializers.DecimalField(source='order.totalAmount', max_digits=10, decimal_places=2, read_only=True)
    user_email = serializers.CharField(source='order.user.email', read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'