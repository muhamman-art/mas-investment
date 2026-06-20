"""
MAS Investment - REST API Views for Products
"""
from rest_framework import generics, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Product, Category, Wishlist
from .serializers import ProductListSerializer, ProductDetailSerializer, CategorySerializer


class CategoryListAPI(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductListAPI(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Product.objects.filter(status=Product.STATUS_ACTIVE).select_related('vendor', 'category').prefetch_related('images')
        search = self.request.query_params.get('search', '')
        category = self.request.query_params.get('category', '')
        min_price = self.request.query_params.get('min_price', '')
        max_price = self.request.query_params.get('max_price', '')
        sort = self.request.query_params.get('sort', '-created_at')
        featured = self.request.query_params.get('featured', '')

        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
        if category:
            qs = qs.filter(category__slug=category)
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        if featured:
            qs = qs.filter(is_featured=True)

        sort_map = {
            'price_asc': 'price', 'price_desc': '-price',
            'name': 'name', 'rating': '-rating', 'popular': '-total_sold',
        }
        return qs.order_by(sort_map.get(sort, '-created_at'))


class ProductDetailAPI(generics.RetrieveAPIView):
    queryset = Product.objects.filter(status=Product.STATUS_ACTIVE).select_related('vendor', 'category').prefetch_related('images', 'reviews')
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views += 1
        instance.save(update_fields=['views'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def wishlist_api(request):
    if request.method == 'GET':
        items = Wishlist.objects.filter(user=request.user).select_related('product')
        return Response([{
            'id': str(item.id),
            'product': ProductListSerializer(item.product).data,
            'added_at': item.added_at
        } for item in items])

    product_id = request.data.get('product_id')
    if not product_id:
        return Response({'error': 'product_id required'}, status=status.HTTP_400_BAD_REQUEST)
    product = get_object_or_404(Product, pk=product_id)
    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        obj.delete()
        return Response({'added': False, 'message': 'Removed from wishlist'})
    return Response({'added': True, 'message': 'Added to wishlist'}, status=status.HTTP_201_CREATED)
