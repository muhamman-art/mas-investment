from rest_framework import serializers
from .models import Category, Product, ProductImage, Wishlist, ProductReview


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'image', 'parent']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'order']


class ProductListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    discount_percent = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'price', 'compare_price', 'discount_percent',
                  'stock', 'is_in_stock', 'rating', 'review_count', 'total_sold',
                  'is_featured', 'primary_image', 'vendor_name', 'category_name', 'status']

    def get_primary_image(self, obj):
        img = obj.get_primary_image()
        return img.image.url if img else None


class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    description = serializers.CharField()
    short_description = serializers.CharField()
    sku = serializers.CharField()
    weight = serializers.DecimalField(max_digits=8, decimal_places=2)
    views = serializers.IntegerField(read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            'description', 'short_description', 'sku', 'weight', 'views', 'images'
        ]


class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'user_name', 'rating', 'title', 'comment',
                  'is_verified_purchase', 'created_at']
        read_only_fields = ['is_verified_purchase', 'created_at']
