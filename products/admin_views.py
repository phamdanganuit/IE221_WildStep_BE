"""
Admin views for Products management
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from users.auth import require_admin
from .models import Brand, ParentCategory, ChildCategory, Product, Banner
from bson import ObjectId
from bson.errors import InvalidId
from django.core.files.storage import default_storage
from django.conf import settings
import os
import uuid


def upload_image_files(request_files, product_id=None):
    """
    Helper function to upload image files to storage.
    Returns list of uploaded image URLs.
    
    Args:
        request_files: request.FILES.getlist('images') - list of file objects
        product_id: Optional product ID for filename. If None, generates temp ID.
    
    Returns:
        List of uploaded image URLs
    """
    uploaded_urls = []
    max_size = 5 * 1024 * 1024  # 5MB
    
    # Get storage backend
    azure_conn = getattr(settings, 'AZURE_STORAGE_CONNECTION_STRING', '') or os.getenv('AZURE_STORAGE_CONNECTION_STRING', '')
    azure_account = getattr(settings, 'AZURE_STORAGE_ACCOUNT_NAME', '') or os.getenv('AZURE_STORAGE_ACCOUNT_NAME', '')
    
    if azure_conn and azure_account:
        from storages.backends.azure_storage import AzureStorage
        storage = AzureStorage()
    else:
        storage = default_storage
    
    # Use provided product_id or generate temp ID
    file_prefix = str(product_id) if product_id else str(ObjectId())
    
    for file_obj in request_files:
        # Validate file type - accept all image formats
        if not file_obj.content_type or not file_obj.content_type.startswith('image/'):
            continue  # Skip non-image files
        
        # Validate file size
        if file_obj.size > max_size:
            continue  # Skip oversized files
        
        try:
            # Generate filename
            ext = file_obj.name.split('.')[-1] if '.' in file_obj.name else 'jpg'
            filename = f"products/{file_prefix}_{uuid.uuid4().hex[:8]}.{ext}"
            
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
                
        except Exception:
            # Skip file if upload fails
            continue
    
    return uploaded_urls


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
        # Parse multilingual name
        payload_name = request.data.get('name')
        name = None
        if isinstance(payload_name, dict):
            name = payload_name
        else:
            # Support dot-style fields: name.vi, name.en, name.ja
            name_vi = request.data.get('name.vi')
            name_en = request.data.get('name.en')
            name_ja = request.data.get('name.ja')
            multi = {}
            if name_vi: multi['vi'] = name_vi
            if name_en: multi['en'] = name_en
            if name_ja: multi['ja'] = name_ja
            if multi:
                name = multi
            else:
                name = request.data.get('name')

        if not name:
            return Response(
                {"error": {"code": "MISSING_FIELD", "message": "Name is required"}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse multilingual description
        payload_desc = request.data.get('description')
        description = None
        if isinstance(payload_desc, dict):
            description = payload_desc
        else:
            desc_vi = request.data.get('description.vi')
            desc_en = request.data.get('description.en')
            desc_ja = request.data.get('description.ja')
            multi_d = {}
            if desc_vi: multi_d['vi'] = desc_vi
            if desc_en: multi_d['en'] = desc_en
            if desc_ja: multi_d['ja'] = desc_ja
            description = multi_d if multi_d else payload_desc

        brand = Brand(
            name=name,
            slug=request.data.get('slug', ''),  # Auto-gen if empty
            description=description,
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
        # Update multilingual name
        if 'name' in request.data or 'name.vi' in request.data or 'name.en' in request.data or 'name.ja' in request.data:
            payload_name = request.data.get('name')
            if isinstance(payload_name, dict):
                brand.name = payload_name
            else:
                # merge existing dict
                current = brand.name if isinstance(brand.name, dict) else {}
                if 'name.vi' in request.data: current['vi'] = request.data.get('name.vi')
                if 'name.en' in request.data: current['en'] = request.data.get('name.en')
                if 'name.ja' in request.data: current['ja'] = request.data.get('name.ja')
                if payload_name and not current:
                    brand.name = payload_name
                elif current:
                    brand.name = current
        if 'slug' in request.data:
            brand.slug = request.data['slug']
        # Update multilingual description
        if 'description' in request.data or 'description.vi' in request.data or 'description.en' in request.data or 'description.ja' in request.data:
            payload_desc = request.data.get('description')
            if isinstance(payload_desc, dict):
                brand.description = payload_desc
            else:
                current_d = brand.description if isinstance(brand.description, dict) else {}
                if 'description.vi' in request.data: current_d['vi'] = request.data.get('description.vi')
                if 'description.en' in request.data: current_d['en'] = request.data.get('description.en')
                if 'description.ja' in request.data: current_d['ja'] = request.data.get('description.ja')
                if payload_desc and not current_d:
                    brand.description = payload_desc
                elif current_d:
                    brand.description = current_d
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
        # Parse multilingual name/description
        payload_name = request.data.get('name')
        if isinstance(payload_name, dict):
            name = payload_name
        else:
            n_vi = request.data.get('name.vi')
            n_en = request.data.get('name.en')
            n_ja = request.data.get('name.ja')
            name = {k: v for k, v in [('vi', n_vi), ('en', n_en), ('ja', n_ja)] if v}
            if not name:
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
                    description=(request.data.get('description') if isinstance(request.data.get('description'), dict) else {k: v for k, v in [('vi', request.data.get('description.vi')), ('en', request.data.get('description.en')), ('ja', request.data.get('description.ja'))] if v} or request.data.get('description', '')),
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
                    description=(request.data.get('description') if isinstance(request.data.get('description'), dict) else {k: v for k, v in [('vi', request.data.get('description.vi')), ('en', request.data.get('description.en')), ('ja', request.data.get('description.ja'))] if v} or request.data.get('description', '')),
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


class CategoryDetailView(APIView):
    """Admin category detail operations - supports both parent and child categories"""
    
    @require_admin
    def get(self, request, category_id):
        """GET /api/admin/categories/:id - Get category detail"""
        try:
            category_id_obj = ObjectId(category_id)
        except InvalidId:
            return Response(
                {"error": {"code": "INVALID_ID", "message": "Invalid category ID"}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to find as parent category first
        try:
            category = ParentCategory.objects.get(id=category_id_obj)
            children = ChildCategory.objects(parent=category)
            
            return Response({
                "id": str(category.id),
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "image": category.image,
                "status": category.status,
                "type": "parent",
                "productCount": Product.objects(category__in=children).count(),
                "childrenCount": children.count(),
                "createdAt": category.created_at.isoformat(),
                "updatedAt": category.updated_at.isoformat(),
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
        except ParentCategory.DoesNotExist:
            # Try as child category
            try:
                category = ChildCategory.objects.get(id=category_id_obj)
                
                return Response({
                    "id": str(category.id),
                    "name": category.name,
                    "slug": category.slug,
                    "description": category.description,
                    "image": category.image,
                    "status": category.status,
                    "type": "child",
                    "parentId": str(category.parent.id),
                    "parentName": category.parent.name,
                    "productCount": Product.objects(category=category).count(),
                    "createdAt": category.created_at.isoformat(),
                    "updatedAt": category.updated_at.isoformat()
                })
            except ChildCategory.DoesNotExist:
                return Response(
                    {"error": {"code": "RESOURCE_NOT_FOUND", "message": "Category not found"}},
                    status=status.HTTP_404_NOT_FOUND
                )
    
    @require_admin
    def put(self, request, category_id):
        """PUT /api/admin/categories/:id - Update category"""
        try:
            category_id_obj = ObjectId(category_id)
        except InvalidId:
            return Response(
                {"error": {"code": "INVALID_ID", "message": "Invalid category ID"}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to find as parent category first
        try:
            category = ParentCategory.objects.get(id=category_id_obj)
            category_type = "parent"
        except ParentCategory.DoesNotExist:
            # Try as child category
            try:
                category = ChildCategory.objects.get(id=category_id_obj)
                category_type = "child"
            except ChildCategory.DoesNotExist:
                return Response(
                    {"error": {"code": "RESOURCE_NOT_FOUND", "message": "Category not found"}},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Update fields
        # Multilingual name update
        if 'name' in request.data or 'name.vi' in request.data or 'name.en' in request.data or 'name.ja' in request.data:
            payload_name = request.data.get('name')
            if isinstance(payload_name, dict):
                category.name = payload_name
            else:
                cur = category.name if isinstance(category.name, dict) else {}
                if 'name.vi' in request.data: cur['vi'] = request.data.get('name.vi')
                if 'name.en' in request.data: cur['en'] = request.data.get('name.en')
                if 'name.ja' in request.data: cur['ja'] = request.data.get('name.ja')
                if payload_name and not cur:
                    category.name = payload_name
                elif cur:
                    category.name = cur
        if 'slug' in request.data:
            category.slug = request.data['slug']
        if 'description' in request.data or 'description.vi' in request.data or 'description.en' in request.data or 'description.ja' in request.data:
            payload_desc = request.data.get('description')
            if isinstance(payload_desc, dict):
                category.description = payload_desc
            else:
                curd = category.description if isinstance(category.description, dict) else {}
                if 'description.vi' in request.data: curd['vi'] = request.data.get('description.vi')
                if 'description.en' in request.data: curd['en'] = request.data.get('description.en')
                if 'description.ja' in request.data: curd['ja'] = request.data.get('description.ja')
                if payload_desc and not curd:
                    category.description = payload_desc
                elif curd:
                    category.description = curd
        if 'status' in request.data:
            category.status = request.data['status']
        if 'image' in request.data:
            category.image = request.data['image']
        
        # For child category, can update parent
        if category_type == 'child' and 'parentId' in request.data:
            try:
                new_parent = ParentCategory.objects.get(id=ObjectId(request.data['parentId']))
                category.parent = new_parent
            except (InvalidId, ParentCategory.DoesNotExist):
                return Response(
                    {"error": {"code": "INVALID_PARENT", "message": "Parent category not found"}},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            category.save()
            
            # Return response based on type
            if category_type == "parent":
                children = ChildCategory.objects(parent=category)
                return Response({
                    "id": str(category.id),
                    "name": category.name,
                    "slug": category.slug,
                    "description": category.description,
                    "image": category.image,
                    "status": category.status,
                    "type": "parent",
                    "productCount": Product.objects(category__in=children).count(),
                    "createdAt": category.created_at.isoformat(),
                    "updatedAt": category.updated_at.isoformat()
                })
            else:
                return Response({
                    "id": str(category.id),
                    "name": category.name,
                    "slug": category.slug,
                    "description": category.description,
                    "image": category.image,
                    "status": category.status,
                    "type": "child",
                    "parentId": str(category.parent.id),
                    "createdAt": category.created_at.isoformat(),
                    "updatedAt": category.updated_at.isoformat()
                })
        except Exception as e:
            return Response(
                {"error": {"code": "UPDATE_FAILED", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @require_admin
    def delete(self, request, category_id):
        """DELETE /api/admin/categories/:id - Delete category"""
        try:
            category_id_obj = ObjectId(category_id)
        except InvalidId:
            return Response(
                {"error": {"code": "INVALID_ID", "message": "Invalid category ID"}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to find as parent category first
        try:
            category = ParentCategory.objects.get(id=category_id_obj)
            category_type = "parent"
        except ParentCategory.DoesNotExist:
            # Try as child category
            try:
                category = ChildCategory.objects.get(id=category_id_obj)
                category_type = "child"
            except ChildCategory.DoesNotExist:
                return Response(
                    {"error": {"code": "RESOURCE_NOT_FOUND", "message": "Category not found"}},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Validation: Cannot delete if category has products
        if category_type == "parent":
            # Check if parent has child categories
            children = ChildCategory.objects(parent=category)
            if children.count() > 0:
                # Check if any child has products
                total_products = Product.objects(category__in=children).count()
                if total_products > 0:
                    return Response(
                        {"error": {"code": "CANNOT_DELETE", 
                                  "message": f"Cannot delete parent category with {children.count()} child categories containing {total_products} products"}},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # If no products, delete all children first
                children.delete()
            
            category.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            # Child category - check if it has products
            product_count = Product.objects(category=category).count()
            if product_count > 0:
                return Response(
                    {"error": {"code": "CANNOT_DELETE", 
                              "message": f"Cannot delete category with {product_count} products"}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            category.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class ProductListView(APIView):
    """GET /api/admin/products - List products with filters"""
    # Support both JSON and multipart/form-data (for file upload)
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    @require_admin
    def get(self, request):
        # Query params
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        search = (request.query_params.get('search') or '').strip()
        category_id = (request.query_params.get('category') or '').strip()
        brand_id = (request.query_params.get('brand') or '').strip()
        status_filter = (request.query_params.get('status') or '').strip()
        sort = (request.query_params.get('sort') or 'createdAt').strip()
        order_dir = (request.query_params.get('order') or 'desc').strip().lower()

        qs = Product.objects
        if search:
            qs = qs(name__icontains=search)
        if category_id:
            try:
                qs = qs(category=ObjectId(category_id))
            except Exception:
                pass
        if brand_id:
            try:
                qs = qs(brand=ObjectId(brand_id))
            except Exception:
                pass
        if status_filter:
            qs = qs(status=status_filter)

        products = list(qs.all())

        reverse = (order_dir != 'asc')
        if sort == 'name':
            products.sort(key=lambda p: p.name or '', reverse=reverse)
        elif sort == 'price':
            products.sort(key=lambda p: p.original_price or 0, reverse=reverse)
        elif sort == 'stock':
            products.sort(key=lambda p: p.stock or 0, reverse=reverse)
        elif sort == 'sold':
            products.sort(key=lambda p: p.sold or 0, reverse=reverse)
        elif sort == 'createdAt':
            products.sort(key=lambda p: p.created_at or 0, reverse=reverse)
        else:
            products.sort(key=lambda p: p.created_at or 0, reverse=reverse)

        total = len(products)
        start = (page - 1) * limit
        end = start + limit
        page_items = products[start:end]

        result = []
        for product in page_items:
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
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": (total + limit - 1) // limit,
                "hasNext": end < total,
                "hasPrev": start > 0
            }
        })
    
    @require_admin
    def post(self, request):
        """POST /api/admin/products - Create product with optional image upload"""
        # Multilingual fields parsing
        raw_name = request.data.get('name')
        if isinstance(raw_name, dict):
            name = raw_name
        else:
            nv = request.data.get('name.vi'); ne = request.data.get('name.en'); nj = request.data.get('name.ja')
            nm = {k: v for k, v in [('vi', nv), ('en', ne), ('ja', nj)] if v}
            name = nm if nm else request.data.get('name')
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
            
            # Handle image upload from files (if any)
            uploaded_urls = []
            if request.FILES:
                images_files = request.FILES.getlist('images')
                if images_files:
                    # Validate: max 5 files
                    if len(images_files) > 5:
                        return Response(
                            {"error": {"code": "FILE_TOO_LARGE", 
                                      "message": "Maximum 5 images allowed per upload"}},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    # Upload files (will use temp ID first, then update with product.id after save)
                    uploaded_urls = upload_image_files(images_files, product_id=None)
            
            # Handle images from JSON body (URLs)
            images_from_body = request.data.get('images', [])
            if not isinstance(images_from_body, list):
                images_from_body = []
            
            # Combine uploaded images and images from body
            all_images = uploaded_urls + images_from_body
            
            # description and size_table multilingual
            raw_desc = request.data.get('description')
            if not isinstance(raw_desc, dict):
                dv = request.data.get('description.vi'); de = request.data.get('description.en'); dj = request.data.get('description.ja')
                raw_desc = ({k: v for k, v in [('vi', dv), ('en', de), ('ja', dj)] if v} or request.data.get('description', ''))

            raw_size = request.data.get('size_table')
            if not isinstance(raw_size, dict):
                sv = request.data.get('size_table.vi'); se = request.data.get('size_table.en'); sj = request.data.get('size_table.ja')
                raw_size = ({k: v for k, v in [('vi', sv), ('en', se), ('ja', sj)] if v} or request.data.get('size_table'))

            product = Product(
                name=name,
                slug=request.data.get('slug', ''),
                description=raw_desc,
                original_price=float(price),
                discount=request.data.get('discount', 0),
                stock=request.data.get('stock', 0),
                brand=brand,
                category=category,
                status=request.data.get('status', 'active'),
                specifications=request.data.get('specifications', {}),
                tags=request.data.get('tags', []),
                images=all_images,
                size_table=raw_size,
            )
            product.save()
            
            # Note: Files are uploaded with temp ID in filename, but URLs are already generated correctly
            # No need to rename files - the URLs work fine as-is
            
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
        if 'name' in request.data or 'name.vi' in request.data or 'name.en' in request.data or 'name.ja' in request.data:
            payload = request.data.get('name')
            if isinstance(payload, dict):
                product.name = payload
            else:
                cur = product.name if isinstance(product.name, dict) else {}
                if 'name.vi' in request.data: cur['vi'] = request.data.get('name.vi')
                if 'name.en' in request.data: cur['en'] = request.data.get('name.en')
                if 'name.ja' in request.data: cur['ja'] = request.data.get('name.ja')
                if payload and not cur:
                    product.name = payload
                elif cur:
                    product.name = cur
        if 'description' in request.data or 'description.vi' in request.data or 'description.en' in request.data or 'description.ja' in request.data:
            payload = request.data.get('description')
            if isinstance(payload, dict):
                product.description = payload
            else:
                curd = product.description if isinstance(product.description, dict) else {}
                if 'description.vi' in request.data: curd['vi'] = request.data.get('description.vi')
                if 'description.en' in request.data: curd['en'] = request.data.get('description.en')
                if 'description.ja' in request.data: curd['ja'] = request.data.get('description.ja')
                if payload and not curd:
                    product.description = payload
                elif curd:
                    product.description = curd
        if 'size_table' in request.data or 'size_table.vi' in request.data or 'size_table.en' in request.data or 'size_table.ja' in request.data:
            payload = request.data.get('size_table')
            if isinstance(payload, dict):
                product.size_table = payload
            else:
                curs = product.size_table if isinstance(product.size_table, dict) else {}
                if 'size_table.vi' in request.data: curs['vi'] = request.data.get('size_table.vi')
                if 'size_table.en' in request.data: curs['en'] = request.data.get('size_table.en')
                if 'size_table.ja' in request.data: curs['ja'] = request.data.get('size_table.ja')
                if payload and not curs:
                    product.size_table = payload
                elif curs:
                    product.size_table = curs
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
        
        # Use helper function to upload images
        uploaded_urls = upload_image_files(images, product_id=product_id)
        
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


class BrandLogoUploadView(APIView):
    """POST /api/admin/brands/:id/logo - Upload brand logo"""
    parser_classes = [MultiPartParser, FormParser]

    @require_admin
    def post(self, request, brand_id):
        try:
            brand = Brand.objects.get(id=ObjectId(brand_id))
        except (InvalidId, Brand.DoesNotExist):
            return Response(
                {"error": {"code": "RESOURCE_NOT_FOUND", "message": "Brand not found"}},
                status=status.HTTP_404_NOT_FOUND
            )

        files = request.FILES.getlist('image') or request.FILES.getlist('logo') or request.FILES.getlist('file')
        if not files:
            # Accept single file under 'image'/'logo' as well
            single = request.FILES.get('image') or request.FILES.get('logo') or request.FILES.get('file')
            files = [single] if single else []

        if not files:
            return Response(
                {"error": {"code": "MISSING_FIELD", "message": "No logo image provided"}},
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded = upload_image_files(files, product_id=brand_id)
        if not uploaded:
            return Response(
                {"error": {"code": "UPLOAD_FAILED", "message": "Upload failed"}},
                status=status.HTTP_400_BAD_REQUEST
            )

        brand.logo = uploaded[0]
        brand.save()
        return Response({"id": str(brand.id), "logo": brand.logo}, status=status.HTTP_200_OK)


class BannerListCreateView(APIView):
    """GET/POST /api/admin/banners - List and create banners"""
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @require_admin
    def get(self, request):
        banners = Banner.objects.order_by('order')
        data = [
            {
                "id": str(b.id),
                "image": b.image,
                "link": b.link,
                "title": b.title,
                "order": b.order,
                "status": b.status,
                "createdAt": b.created_at.isoformat(),
                "updatedAt": b.updated_at.isoformat(),
            }
            for b in banners
        ]
        return Response({"data": data})

    @require_admin
    def post(self, request):
        # Multilingual title support
        raw_title = request.data.get('title')
        if isinstance(raw_title, dict):
            title = raw_title
        else:
            t_vi = request.data.get('title.vi')
            t_en = request.data.get('title.en')
            t_ja = request.data.get('title.ja')
            multi_t = {k: v for k, v in [('vi', t_vi), ('en', t_en), ('ja', t_ja)] if v}
            title = multi_t if multi_t else (raw_title or '')
        link = request.data.get('link', '')
        order = int(request.data.get('order', 0) or 0)
        status_val = request.data.get('status', 'active')

        # Accept image from URL (JSON) only if it's a string; otherwise, expect file upload
        image_url = request.data.get('image')
        if not isinstance(image_url, str):
            image_url = None

        if not image_url and request.FILES:
            files = request.FILES.getlist('image') or request.FILES.getlist('file')
            if not files:
                single = request.FILES.get('image') or request.FILES.get('file')
                files = [single] if single else []
            uploaded = upload_image_files(files, product_id=None) if files else []
            image_url = uploaded[0] if uploaded else None

        if not image_url:
            return Response(
                {"error": {"code": "MISSING_FIELD", "message": "image is required"}},
                status=status.HTTP_400_BAD_REQUEST
            )

        banner = Banner(image=image_url, link=link, title=title, order=order, status=status_val)
        banner.save()
        return Response({
            "id": str(banner.id),
            "image": banner.image,
            "link": banner.link,
            "title": banner.title,
            "order": banner.order,
            "status": banner.status,
            "createdAt": banner.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)


class BannerDetailView(APIView):
    """GET/PUT/DELETE /api/admin/banners/:id"""

    @require_admin
    def get(self, request, banner_id):
        try:
            b = Banner.objects.get(id=ObjectId(banner_id))
        except (InvalidId, Banner.DoesNotExist):
            return Response({"error": {"code": "RESOURCE_NOT_FOUND", "message": "Banner not found"}}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "id": str(b.id),
            "image": b.image,
            "link": b.link,
            "title": b.title,
            "order": b.order,
            "status": b.status,
            "createdAt": b.created_at.isoformat(),
            "updatedAt": b.updated_at.isoformat(),
        })

    @require_admin
    def put(self, request, banner_id):
        try:
            b = Banner.objects.get(id=ObjectId(banner_id))
        except (InvalidId, Banner.DoesNotExist):
            return Response({"error": {"code": "RESOURCE_NOT_FOUND", "message": "Banner not found"}}, status=status.HTTP_404_NOT_FOUND)

        if 'title' in request.data or 'title.vi' in request.data or 'title.en' in request.data or 'title.ja' in request.data:
            payload = request.data.get('title')
            if isinstance(payload, dict):
                b.title = payload
            else:
                cur = b.title if isinstance(b.title, dict) else {}
                if 'title.vi' in request.data: cur['vi'] = request.data.get('title.vi')
                if 'title.en' in request.data: cur['en'] = request.data.get('title.en')
                if 'title.ja' in request.data: cur['ja'] = request.data.get('title.ja')
                if payload and not cur:
                    b.title = payload
                elif cur:
                    b.title = cur
        if 'link' in request.data:
            b.link = request.data['link']
        if 'order' in request.data:
            try:
                b.order = int(request.data['order'])
            except Exception:
                pass
        if 'status' in request.data:
            b.status = request.data['status']
        if 'image' in request.data and isinstance(request.data['image'], str) and request.data['image']:
            # Only accept direct URL via JSON; file uploads must use the /image endpoint
            b.image = request.data['image']
        b.save()
        return Response({
            "id": str(b.id),
            "image": b.image,
            "link": b.link,
            "title": b.title,
            "order": b.order,
            "status": b.status,
            "updatedAt": b.updated_at.isoformat(),
        })

    @require_admin
    def delete(self, request, banner_id):
        try:
            b = Banner.objects.get(id=ObjectId(banner_id))
        except (InvalidId, Banner.DoesNotExist):
            return Response({"error": {"code": "RESOURCE_NOT_FOUND", "message": "Banner not found"}}, status=status.HTTP_404_NOT_FOUND)
        b.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BannerImageUploadView(APIView):
    """POST /api/admin/banners/:id/image - Upload banner image"""
    parser_classes = [MultiPartParser, FormParser]

    @require_admin
    def post(self, request, banner_id):
        try:
            b = Banner.objects.get(id=ObjectId(banner_id))
        except (InvalidId, Banner.DoesNotExist):
            return Response({"error": {"code": "RESOURCE_NOT_FOUND", "message": "Banner not found"}}, status=status.HTTP_404_NOT_FOUND)

        files = request.FILES.getlist('image') or request.FILES.getlist('file')
        if not files:
            single = request.FILES.get('image') or request.FILES.get('file')
            files = [single] if single else []
        if not files:
            return Response({"error": {"code": "MISSING_FIELD", "message": "No image provided"}}, status=status.HTTP_400_BAD_REQUEST)

        uploaded = upload_image_files(files, product_id=banner_id)
        if not uploaded:
            return Response({"error": {"code": "UPLOAD_FAILED", "message": "Upload failed"}}, status=status.HTTP_400_BAD_REQUEST)

        b.image = uploaded[0]
        b.save()
        return Response({"id": str(b.id), "image": b.image}, status=status.HTTP_200_OK)
