from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Category, Product, Order, OrderItem,
    ShoppingCart, CartItem, Review, UserAddress, Payment
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'phone', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'is_superuser')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_active')}
         ),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')
    prepopulated_fields = {'name': ()}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('price', 'stock', 'is_active')
    raw_id_fields = ('category',)
    readonly_fields = ('created_at', 'updated_at')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('orderItemId', 'get_total_price')
    fields = ('orderItemId', 'product', 'quantity', 'price', 'get_total_price')

    def get_total_price(self, obj):
        return obj.get_total_price()

    get_total_price.short_description = 'Total Price'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('orderId', 'user', 'orderDate', 'totalAmount', 'status', 'created_at')
    list_filter = ('status', 'orderDate', 'created_at')
    search_fields = ('orderId', 'user__email', 'user__username')
    readonly_fields = ('orderId', 'orderDate', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    actions = ['mark_as_shipped', 'mark_as_delivered']

    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')

    mark_as_shipped.short_description = "Mark selected orders as shipped"

    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')

    mark_as_delivered.short_description = "Mark selected orders as delivered"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('orderItemId', 'order', 'product', 'quantity', 'price', 'get_total_price')
    list_filter = ('order__status',)
    search_fields = ('order__orderId', 'product__name')
    readonly_fields = ('orderItemId',)

    def get_total_price(self, obj):
        return obj.get_total_price()

    get_total_price.short_description = 'Total Price'


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('get_total_price',)
    fields = ('product', 'quantity', 'get_total_price')

    def get_total_price(self, obj):
        return obj.get_total_price()

    get_total_price.short_description = 'Total Price'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('cartId', 'user', 'createdAt', 'get_total_items', 'get_total_price')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('cartId', 'createdAt', 'updated_at')
    inlines = [CartItemInline]

    def get_total_items(self, obj):
        return obj.cart_items.count()

    get_total_items.short_description = 'Total Items'

    def get_total_price(self, obj):
        return sum(item.get_total_price() for item in obj.cart_items.all())

    get_total_price.short_description = 'Total Price'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cartItemId', 'cart', 'product', 'quantity', 'get_total_price')
    list_filter = ('cart__user',)
    search_fields = ('cart__user__email', 'product__name')
    readonly_fields = ('cartItemId',)

    def get_total_price(self, obj):
        return obj.get_total_price()

    get_total_price.short_description = 'Total Price'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewId', 'product', 'user', 'rating', 'created_at', 'updated_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__email', 'comment')
    readonly_fields = ('reviewId', 'created_at', 'updated_at')
    raw_id_fields = ('product', 'user')


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('addressId', 'user', 'street', 'city', 'state', 'zipCode', 'is_default')
    list_filter = ('city', 'state', 'is_default')
    search_fields = ('user__email', 'street', 'city', 'state', 'zipCode')
    readonly_fields = ('addressId', 'created_at', 'updated_at')
    list_editable = ('is_default',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('paymentId', 'order', 'amount', 'paymentMethod', 'payment_status', 'paymentDate')
    list_filter = ('paymentMethod', 'payment_status', 'paymentDate')
    search_fields = ('paymentId', 'order__orderId', 'transaction_id')
    readonly_fields = ('paymentId', 'paymentDate', 'created_at')
    actions = ['mark_as_completed', 'mark_as_failed']

    def mark_as_completed(self, request, queryset):
        queryset.update(payment_status='completed')
        # Also update related orders
        for payment in queryset:
            payment.order.status = 'confirmed'
            payment.order.save()

    mark_as_completed.short_description = "Mark selected payments as completed"

    def mark_as_failed(self, request, queryset):
        queryset.update(payment_status='failed')

    mark_as_failed.short_description = "Mark selected payments as failed"


# Custom admin site header
admin.site.site_header = "Shopping App Administration"
admin.site.site_title = "Shopping App Admin"
admin.site.index_title = "Welcome to Shopping App Admin"