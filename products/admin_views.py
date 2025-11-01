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
from django.core.files.storage import default_storage
from django.conf import settings
import os
import uuid


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


class CategoryListView(APIView):
    """GET /api/admin/categories - List categories"""
    @require_admin
    def get(self, request):
        # Get parent categories
        parent_categories = ParentCategory.objects.all()
        
        result = []
        for parent in parent_categories:
            # Get child categories
            children = ChildCategory.objects(parent=parent)
            
            result.append({
                "id": str(parent.id),
                "name": parent.name,
                "slug": parent.slug,
                "description": parent.description,
                "image": parent.image,
                "status": parent.status,
                "type": "parent",
                "productCount": Product.objects(category__in=children).count(),
                "createdAt": parent.created_at.isoformat(),
                "updatedAt": parent.updated_at.isoformat(),
                "children": [
                    {
                        "id": str(child.id),
                        "name": child.name,
                        "slug": child.slug,
                        "description": child.description,
                        "image": child.image,
                        "status": child.status,
                        "productCount": Product.objects(category=child).count(),
                        "createdAt": child.created_at.isoformat(),
                        "updatedAt": child.updated_at.isoformat()
                    }
                    for child in children
                ]
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
        """POST /api/admin/categories - Create category"""
        name = request.data.get('name')
        category_type = request.data.get('type', 'child')  # 'parent' or 'child'
        parent_id = request.data.get('parentId')
        
        if not name:
            return Response(
                {"error": {"code": "MISSING_FIELD", "message": "Name is required"}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if category_type == 'parent':
                category = ParentCategory(
                    name=name,
                    slug=request.data.get('slug', ''),
                    description=request.data.get('description', ''),
                    status=request.data.get('status', 'active')
                )
                category.save()
                
                return Response({
                    "id": str(category.id),
                    "name": category.name,
                    "slug": category.slug,
                    "description": category.description,
                    "image": category.image,
                    "status": category.status,
                    "type": "parent",
                    "createdAt": category.created_at.isoformat(),
                    "updatedAt": category.updated_at.isoformat()
                }, status=status.HTTP_201_CREATED)
            else:
                # Child category
                if not parent_id:
                    return Response(
                        {"error": {"code": "MISSING_FIELD", "message": "Parent ID is required for child category"}},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                parent = ParentCategory.objects.get(id=ObjectId(parent_id))
                category = ChildCategory(
                    name=name,
                    slug=request.data.get('slug', ''),
                    description=request.data.get('description', ''),
                    parent=parent,
                    status=request.data.get('status', 'active')
                )
                category.save()
                
                return Response({
                    "id": str(category.id),
                    "name": category.name,
                    "slug": category.slug,
                    "description": category.description,
                    "image": category.image,
                    "status": category.status,
                    "type": "child",
                    "parentId": str(parent.id),
                    "createdAt": category.created_at.isoformat(),
                    "updatedAt": category.updated_at.isoformat()
                }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": {"code": "CREATE_FAILED", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProductListView(APIView):
    """GET /api/admin/products - List products with filters"""
    @require_admin
    def get(self, request):
        # TODO: Implement pagination, search, filters, sort
        products = Product.objects.all().order_by('-created_at')[:20]
        
        result = []
        for product in products:
            result.append({
                "id": str(product.id),
                "name": product.name,
                "slug": product.slug,
                "description": product.description,
                "category": {
                    "id": str(product.category.id),
                    "name": product.category.name,
                    "slug": product.category.slug
                } if product.category else None,
                "brand": {
                    "id": str(product.brand.id),
                    "name": product.brand.name,
                    "slug": product.brand.slug
                } if product.brand else None,
                "price": product.original_price,
                "discountPrice": product.discount_price,
                "stock": product.stock,
                "sold": product.sold,
                "images": product.images,
                "status": product.status,
                "specifications": product.specifications,
                "createdAt": product.created_at.isoformat(),
                "updatedAt": product.updated_at.isoformat()
            })
        
        return Response({
            "data": result,
            "pagination": {
                "page": 1,
                "limit": 20,
                "total": Product.objects.count(),
                "totalPages": (Product.objects.count() + 19) // 20
            }
        })
    
    @require_admin
    def post(self, request):
        """POST /api/admin/products - Create product"""
        name = request.data.get('name')
        category_id = request.data.get('categoryId')
        brand_id = request.data.get('brandId')
        price = request.data.get('price')
        
        if not all([name, category_id, brand_id, price]):
            return Response(
                {"error": {"code": "MISSING_FIELD", 
                          "message": "Name, categoryId, brandId, and price are required"}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            category = ChildCategory.objects.get(id=ObjectId(category_id))
            brand = Brand.objects.get(id=ObjectId(brand_id))
            
            # Handle images - can be array of URLs
            images = request.data.get('images', [])
            if not isinstance(images, list):
                images = []
            
            product = Product(
                name=name,
                slug=request.data.get('slug', ''),
                description=request.data.get('description', ''),
                original_price=float(price),
                discount=request.data.get('discount', 0),
                stock=request.data.get('stock', 0),
                brand=brand,
                category=category,
                status=request.data.get('status', 'active'),
                specifications=request.data.get('specifications', {}),
                tags=request.data.get('tags', []),
                images=images  # Support images in body
            )
            product.save()
            
            return Response({
                "id": str(product.id),
                "name": product.name,
                "slug": product.slug,
                "description": product.description,
                "price": product.original_price,
                "discountPrice": product.discount_price,
                "stock": product.stock,
                "status": product.status,
                "images": product.images,
                "createdAt": product.created_at.isoformat()
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": {"code": "CREATE_FAILED", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProductDetailView(APIView):
    """Product detail operations"""
    
    @require_admin
    def get(self, request, product_id):
        """GET /api/admin/products/:id"""
        try:
            product = Product.objects.get(id=ObjectId(product_id))
        except (InvalidId, Product.DoesNotExist):
            return Response(
                {"error": {"code": "RESOURCE_NOT_FOUND", "message": "Product not found"}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            "id": str(product.id),
            "name": product.name,
            "slug": product.slug,
            "description": product.description,
            "category": {
                "id": str(product.category.id),
                "name": product.category.name,
                "slug": product.category.slug
            } if product.category else None,
            "brand": {
                "id": str(product.brand.id),
                "name": product.brand.name,
                "slug": product.brand.slug
            } if product.brand else None,
            "price": product.original_price,
            "discountPrice": product.discount_price,
            "stock": product.stock,
            "sold": product.sold,
            "images": product.images,
            "status": product.status,
            "specifications": product.specifications,
            "tags": product.tags,
            "createdAt": product.created_at.isoformat(),
            "updatedAt": product.updated_at.isoformat()
        })
    
    @require_admin
    def put(self, request, product_id):
        """PUT /api/admin/products/:id"""
        try:
            product = Product.objects.get(id=ObjectId(product_id))
        except (InvalidId, Product.DoesNotExist):
            return Response(
                {"error": {"code": "RESOURCE_NOT_FOUND", "message": "Product not found"}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update fields
        if 'name' in request.data:
            product.name = request.data['name']
        if 'description' in request.data:
            product.description = request.data['description']
        if 'price' in request.data:
            product.original_price = float(request.data['price'])
        if 'discount' in request.data:
            product.discount = request.data['discount']
        if 'stock' in request.data:
            product.stock = request.data['stock']
        if 'status' in request.data:
            product.status = request.data['status']
        if 'categoryId' in request.data:
            product.category = ChildCategory.objects.get(id=ObjectId(request.data['categoryId']))
        if 'brandId' in request.data:
            product.brand = Brand.objects.get(id=ObjectId(request.data['brandId']))
        if 'specifications' in request.data:
            product.specifications = request.data['specifications']
        if 'tags' in request.data:
            product.tags = request.data['tags']
        if 'images' in request.data:
            images = request.data['images']
            if isinstance(images, list):
                product.images = images
        
        try:
            product.save()
            return Response({
                "id": str(product.id),
                "name": product.name,
                "slug": product.slug,
                "price": product.original_price,
                "discountPrice": product.discount_price,
                "stock": product.stock,
                "status": product.status,
                "updatedAt": product.updated_at.isoformat()
            })
        except Exception as e:
            return Response(
                {"error": {"code": "UPDATE_FAILED", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @require_admin
    def delete(self, request, product_id):
        """DELETE /api/admin/products/:id"""
        try:
            product = Product.objects.get(id=ObjectId(product_id))
        except (InvalidId, Product.DoesNotExist):
            return Response(
                {"error": {"code": "RESOURCE_NOT_FOUND", "message": "Product not found"}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductImageUploadView(APIView):
    """POST /api/admin/products/:id/images - Upload product images"""
    parser_classes = [MultiPartParser, FormParser]
    
    @require_admin
    def post(self, request, product_id):
        try:
            product = Product.objects.get(id=ObjectId(product_id))
        except (InvalidId, Product.DoesNotExist):
            return Response(
                {"error": {"code": "RESOURCE_NOT_FOUND", "message": "Product not found"}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get files from request
        images = request.FILES.getlist('images')
        
        if not images:
            return Response(
                {"error": {"code": "MISSING_FIELD", "message": "No images provided"}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate: max 5 files
        if len(images) > 5:
            return Response(
                {"error": {"code": "FILE_TOO_LARGE", 
                          "message": "Maximum 5 images allowed per upload"}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_urls = []
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        max_size = 5 * 1024 * 1024  # 5MB
        
        # Get storage backend
        azure_conn = getattr(settings, 'AZURE_STORAGE_CONNECTION_STRING', '') or os.getenv('AZURE_STORAGE_CONNECTION_STRING', '')
        azure_account = getattr(settings, 'AZURE_STORAGE_ACCOUNT_NAME', '') or os.getenv('AZURE_STORAGE_ACCOUNT_NAME', '')
        
        if azure_conn and azure_account:
            from storages.backends.azure_storage import AzureStorage
            storage = AzureStorage()
        else:
            storage = default_storage
        
        for file_obj in images:
            # Validate file type
            if file_obj.content_type not in allowed_types:
                continue  # Skip invalid files
            
            # Validate file size
            if file_obj.size > max_size:
                continue  # Skip oversized files
            
            try:
                # Generate filename
                ext = file_obj.name.split('.')[-1] if '.' in file_obj.name else 'jpg'
                filename = f"products/{product_id}_{uuid.uuid4().hex[:8]}.{ext}"
                
                # Save file
                saved_path = storage.save(filename, file_obj)
                
                if not saved_path:
                    continue
                
                # Generate URL
                try:
                    if azure_conn:
                        account_name = getattr(settings, 'AZURE_STORAGE_ACCOUNT_NAME', '')
                        container = getattr(settings, 'AZURE_STORAGE_CONTAINER', 'media')
                        
                        blob_path = saved_path
                        if blob_path.startswith(container + '/'):
                            blob_path = blob_path[len(container) + 1:]
                        elif blob_path.startswith('/' + container + '/'):
                            blob_path = blob_path[len('/' + container) + 1:]
                        
                        image_url = f"https://{account_name}.blob.core.windows.net/{container}/{blob_path}"
                        
                        # Try to get URL from storage
                        try:
                            storage_url = storage.url(saved_path)
                            if storage_url and storage_url.startswith('http'):
                                image_url = storage_url
                        except Exception:
                            pass
                    else:
                        image_url = default_storage.url(saved_path)
                        if not image_url.startswith('http') and not image_url.startswith('/media/'):
                            image_url = f"/media/{image_url}"
                    
                    uploaded_urls.append(image_url)
                except Exception:
                    # Fallback URL generation
                    if azure_conn:
                        account_name = getattr(settings, 'AZURE_STORAGE_ACCOUNT_NAME', '')
                        container = getattr(settings, 'AZURE_STORAGE_CONTAINER', 'media')
                        blob_path = saved_path
                        if blob_path.startswith(container + '/'):
                            blob_path = blob_path[len(container) + 1:]
                        image_url = f"https://{account_name}.blob.core.windows.net/{container}/{blob_path}"
                    else:
                        image_url = f"/media/{saved_path}"
                    uploaded_urls.append(image_url)
                    
            except Exception as e:
                # Skip file if upload fails
                continue
        
        if not uploaded_urls:
            return Response(
                {"error": {"code": "UPLOAD_FAILED", "message": "No valid images were uploaded"}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add new images to product (append, not replace)
        existing_images = product.images or []
        product.images = existing_images + uploaded_urls
        product.save()
        
        return Response({
            "images": product.images
        }, status=status.HTTP_200_OK)

