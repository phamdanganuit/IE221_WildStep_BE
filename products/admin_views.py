"""
Admin views for Products management
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from users.auth import require_admin
from .models import Brand, ParentCategory, ChildCategory, Product
from bson import ObjectId
from bson.errors import InvalidId


class BrandListView(APIView):
    """GET /api/admin/brands - List brands with pagination"""
    @require_admin
    def get(self, request):
        # TODO: Implement pagination, search, filters
        brands = Brand.objects.all()
        
        result = []
        for brand in brands:
            result.append({
                "id": str(brand.id),
                "name": brand.name,
                "slug": brand.slug,
                "description": brand.description,
                "logo": brand.logo,
                "website": brand.website,
                "country": brand.country,
                "status": brand.status,
                "createdAt": brand.created_at.isoformat(),
                "updatedAt": brand.updated_at.isoformat()
            })
        
        return Response({
            "data": result,
            "pagination": {
                "page": 1,
                "limit": 50,
                "total": len(result),
                "totalPages": 1
            }
        })
    
    @require_admin
    def post(self, request):
        """POST /api/admin/brands - Create brand"""
        name = request.data.get('name')
        if not name:
            return Response(
                {"error": {"code": "MISSING_FIELD", "message": "Name is required"}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        brand = Brand(
            name=name,
            slug=request.data.get('slug', ''),  # Auto-gen if empty
            description=request.data.get('description', ''),
            website=request.data.get('website', ''),
            country=request.data.get('country', ''),
            status=request.data.get('status', 'active')
        )
        
        try:
            brand.save()
            return Response({
                "id": str(brand.id),
                "name": brand.name,
                "slug": brand.slug,
                "description": brand.description,
                "logo": brand.logo,
                "website": brand.website,
                "country": brand.country,
                "status": brand.status,
                "createdAt": brand.created_at.isoformat(),
                "updatedAt": brand.updated_at.isoformat()
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": {"code": "CREATE_FAILED", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )


class BrandDetailView(APIView):
    """Admin brand detail operations"""
    
    @require_admin
    def get(self, request, brand_id):
        """GET /api/admin/brands/:id - Get brand detail"""
        try:
            brand = Brand.objects.get(id=ObjectId(brand_id))
        except (InvalidId, Brand.DoesNotExist):
            return Response(
                {"error": {"code": "RESOURCE_NOT_FOUND", "message": "Brand not found"}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            "id": str(brand.id),
            "name": brand.name,
            "slug": brand.slug,
            "description": brand.description,
            "logo": brand.logo,
            "website": brand.website,
            "country": brand.country,
            "status": brand.status,
            "createdAt": brand.created_at.isoformat(),
            "updatedAt": brand.updated_at.isoformat()
        })
    
    @require_admin
    def put(self, request, brand_id):
        """PUT /api/admin/brands/:id - Update brand"""
        try:
            brand = Brand.objects.get(id=ObjectId(brand_id))
        except (InvalidId, Brand.DoesNotExist):
            return Response(
                {"error": {"code": "RESOURCE_NOT_FOUND", "message": "Brand not found"}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update fields
        if 'name' in request.data:
            brand.name = request.data['name']
        if 'slug' in request.data:
            brand.slug = request.data['slug']
        if 'description' in request.data:
            brand.description = request.data['description']
        if 'website' in request.data:
            brand.website = request.data['website']
        if 'country' in request.data:
            brand.country = request.data['country']
        if 'status' in request.data:
            brand.status = request.data['status']
        
        try:
            brand.save()
            return Response({
                "id": str(brand.id),
                "name": brand.name,
                "slug": brand.slug,
                "description": brand.description,
                "logo": brand.logo,
                "website": brand.website,
                "country": brand.country,
                "status": brand.status,
                "createdAt": brand.created_at.isoformat(),
                "updatedAt": brand.updated_at.isoformat()
            })
        except Exception as e:
            return Response(
                {"error": {"code": "UPDATE_FAILED", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @require_admin
    def delete(self, request, brand_id):
        """DELETE /api/admin/brands/:id - Delete brand"""
        try:
            brand = Brand.objects.get(id=ObjectId(brand_id))
        except (InvalidId, Brand.DoesNotExist):
            return Response(
                {"error": {"code": "RESOURCE_NOT_FOUND", "message": "Brand not found"}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if brand has products
        product_count = Product.objects(brand=brand).count()
        if product_count > 0:
            return Response(
                {"error": {"code": "CANNOT_DELETE", "message": f"Cannot delete brand with {product_count} products"}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        brand.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# TODO: Implement CategoryListView, CategoryDetailView, ProductListView, ProductDetailView
# Following same pattern as BrandListView and BrandDetailView

