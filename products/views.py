from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Banner, Brand, Product, ParentCategory, ChildCategory, CustomerReview, HeroContent
from rest_framework import status
import re
import unicodedata
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def _pick_lang(value, lang: str, default_lang: str = 'vi'):
    """Return localized string from value which may be a dict or a plain string."""
    if isinstance(value, dict):
        return value.get(lang) or value.get(default_lang) or next(iter(value.values()), None)
    return value


def _normalize_vietnamese(text):
    """
    Normalize Vietnamese text by removing diacritics for search.
    Example: "Tiếng Việt" -> "tieng viet"
    """
    if not text:
        return ""
    # Convert to lowercase
    text = text.lower()
    # Normalize unicode characters
    nfd = unicodedata.normalize('NFD', text)
    # Remove diacritics
    without_diacritics = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    # Additional Vietnamese character mapping
    char_map = {
        'đ': 'd',
        'Đ': 'd'
    }
    for viet_char, replacement in char_map.items():
        without_diacritics = without_diacritics.replace(viet_char, replacement)
    return without_diacritics.strip()


def _calculate_relevance_score(product, query, lang='vi'):
    """
    Calculate relevance score for a product based on query.
    Higher score = more relevant
    """
    score = 0
    query_normalized = _normalize_vietnamese(query)
    
    # Get product name in specified language
    product_name = _pick_lang(product.name, lang)
    if not product_name:
        return 0
    
    product_name_normalized = _normalize_vietnamese(product_name)
    
    # Exact match (highest priority)
    if query_normalized == product_name_normalized:
        score += 1000
    
    # Starts with query (high priority)
    elif product_name_normalized.startswith(query_normalized):
        score += 500
    
    # Contains query in name (medium priority)
    elif query_normalized in product_name_normalized:
        score += 250
    
    # Check in description
    product_desc = _pick_lang(product.description, lang)
    if product_desc:
        desc_normalized = _normalize_vietnamese(product_desc)
        if query_normalized in desc_normalized:
            score += 50
    
    # Check in tags
    if product.tags:
        for tag in product.tags:
            tag_normalized = _normalize_vietnamese(tag)
            if query_normalized in tag_normalized:
                score += 100
                break
    
    # Boost by popularity metrics
    score += (product.sold or 0) * 0.1
    score += (product.rate or 0) * 5
    
    return score


def _text_search(query, lang='vi', filters=None):
    """
    Perform text search on products with optional filters.
    Returns queryset matching the search criteria.
    """
    if not query:
        return Product.objects.none()
    
    # Start with active products only
    qs = Product.objects(status="active")
    
    # Apply filters if provided
    if filters:
        if filters.get('brand'):
            brand_names = [b.strip() for b in filters['brand'].split(',') if b.strip()]
            if brand_names:
                # Brand.name is DynamicField, so we need to check all brands
                all_brands = list(Brand.objects(status="active"))
                matching_brands = []
                for brand in all_brands:
                    brand_name = _pick_lang(brand.name, lang)
                    if brand_name and brand_name in brand_names:
                        matching_brands.append(brand)
                if matching_brands:
                    qs = qs(brand__in=matching_brands)
        
        if filters.get('category_slug'):
            child = ChildCategory.objects(slug=filters['category_slug']).first()
            if child:
                qs = qs(category=child)
            else:
                parent = ParentCategory.objects(slug=filters['category_slug']).first()
                if parent:
                    children = list(ChildCategory.objects(parent=parent))
                    if children:
                        qs = qs(category__in=children)
        
        if filters.get('priceFrom'):
            qs = qs(original_price__gte=filters['priceFrom'])
        
        if filters.get('priceTo'):
            qs = qs(original_price__lte=filters['priceTo'])
        
        if filters.get('min_rating'):
            qs = qs(rate__gte=filters['min_rating'])
        
        if filters.get('in_stock', True):
            qs = qs(stock__gt=0)
    
    # Get all matching products
    all_products = list(qs)
    
    # Filter products by text match using relevance score
    query_normalized = _normalize_vietnamese(query)
    matching_products = []
    
    for product in all_products:
        # Check if product matches query
        product_name = _pick_lang(product.name, lang)
        if product_name:
            product_name_normalized = _normalize_vietnamese(product_name)
            if query_normalized in product_name_normalized:
                matching_products.append(product)
                continue
        
        # Check description
        product_desc = _pick_lang(product.description, lang)
        if product_desc:
            desc_normalized = _normalize_vietnamese(product_desc)
            if query_normalized in desc_normalized:
                matching_products.append(product)
                continue
        
        # Check tags
        if product.tags:
            for tag in product.tags:
                tag_normalized = _normalize_vietnamese(tag)
                if query_normalized in tag_normalized:
                    matching_products.append(product)
                    break
    
    return matching_products


class PublicBannerListView(APIView):
    """GET /api/content/banners - Public list of active banners"""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        lang = (request.query_params.get('lang') or 'vi').strip() or 'vi'
        banners = Banner.objects(status="active").order_by('order')
        data = [
            {
                "id": str(b.id),
                "image": b.image,
                "link": b.link,
                "title": _pick_lang(b.title, lang),
                "order": b.order,
            }
            for b in banners
        ]
        return Response({"data": data})


class PublicBrandListView(APIView):
    """GET /api/brands - Public list of active brands"""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        lang = (request.query_params.get('lang') or 'vi').strip() or 'vi'
        brands = Brand.objects(status="active").order_by('name')
        data = [
            {
                "id": str(br.id),
                "name": _pick_lang(br.name, lang),
                "slug": br.slug,
                "logo": br.logo,
                "website": br.website,
            }
            for br in brands
        ]
        return Response({"data": data})


class PublicProductsListView(APIView):
    """GET /api/products - Full featured product list with filters, search, and sorting"""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        try:
            # Parse query parameters
            lang = (request.query_params.get('lang') or 'vi').strip() or 'vi'
            sort = (request.query_params.get('sort') or 'popular').strip()
            search = (request.query_params.get('search') or '').strip()
            brand = (request.query_params.get('brand') or '').strip()
            gender = (request.query_params.get('gender') or '').strip()
            parent_category = (request.query_params.get('parent_category') or '').strip()
            color = (request.query_params.get('color') or '').strip()
            size = (request.query_params.get('size') or '').strip()
            price_from = request.query_params.get('priceFrom')
            price_to = request.query_params.get('priceTo')
            category = (request.query_params.get('category') or '').strip()
            category_slug = (request.query_params.get('category_slug') or '').strip()
            
            # Pagination parameters
            try:
                page = max(1, int(request.query_params.get('page') or 1))
            except ValueError:
                page = 1
            
            try:
                page_size = int(request.query_params.get('page_size') or 12)
                if page_size < 1:
                    page_size = 12
                elif page_size > 100:
                    return Response(
                        {
                            "error": {
                                "code": "INVALID_PARAMS",
                                "message": "page_size must be between 1 and 100"
                            }
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except ValueError:
                page_size = 12

            # Start with active products
            qs = Product.objects(status="active")

            # Apply search filter
            if search:
                # Use text search function
                search_results = _text_search(search, lang)
                search_ids = [str(p.id) for p in search_results]
                if search_ids:
                    qs = qs(id__in=search_ids)
                else:
                    # No results found
                    return Response({
                        "data": [],
                        "pagination": {
                            "page": page,
                            "page_size": page_size,
                            "total": 0,
                            "total_pages": 0
                        },
                        "filters": self._get_empty_filters()
                    })

            # Apply brand filter
            if brand:
                brand_names = [b.strip() for b in brand.split(',') if b.strip()]
                if brand_names:
                    all_brands = list(Brand.objects(status="active"))
                    matching_brands = []
                    for br in all_brands:
                        brand_name = _pick_lang(br.name, lang)
                        if brand_name and brand_name in brand_names:
                            matching_brands.append(br)
                    if matching_brands:
                        qs = qs(brand__in=matching_brands)
                    else:
                        # No matching brands
                        return Response({
                            "data": [],
                            "pagination": {
                                "page": page,
                                "page_size": page_size,
                                "total": 0,
                                "total_pages": 0
                            },
                            "filters": self._get_empty_filters()
                        })

            # Apply parent category filter (filter by parent category slug)
            if parent_category:
                parent_cat = ParentCategory.objects(slug=parent_category, status="active").first()
                if parent_cat:
                    # Get all child categories under this parent
                    child_categories = list(ChildCategory.objects(parent=parent_cat, status="active"))
                    if child_categories:
                        # Filter products by these child categories
                        qs = qs(category__in=child_categories)
                    else:
                        # No child categories found
                        return Response({
                            "data": [],
                            "pagination": {
                                "page": page,
                                "page_size": page_size,
                                "total": 0,
                                "total_pages": 0
                            },
                            "filters": self._get_empty_filters()
                        })
                else:
                    # Parent category not found
                    return Response({
                        "data": [],
                        "pagination": {
                            "page": page,
                            "page_size": page_size,
                            "total": 0,
                            "total_pages": 0
                        },
                        "filters": self._get_empty_filters()
                    })

            # Apply gender filter
            if gender:
                gender_values = [g.strip() for g in gender.split(',') if g.strip()]
                if gender_values:
                    # Normalize gender values
                    gender_map = {
                        'Nam': ['Nam', 'Male', '男性'],
                        'Nữ': ['Nữ', 'Female', '女性'],
                        'Unisex': ['Unisex', 'Unisex', 'ユニセックス']
                    }
                    matching_genders = []
                    for gv in gender_values:
                        for key, values in gender_map.items():
                            if gv in values or any(gv.lower() == v.lower() for v in values):
                                matching_genders.extend(values)
                                break
                    
                    # Filter products by gender
                    all_products = list(qs)
                    filtered_products = []
                    for p in all_products:
                        product_gender = _pick_lang(p.gender, lang) if p.gender else None
                        if product_gender:
                            product_gender_normalized = _normalize_vietnamese(product_gender.lower())
                            for mg in matching_genders:
                                if _normalize_vietnamese(mg.lower()) in product_gender_normalized or product_gender_normalized in _normalize_vietnamese(mg.lower()):
                                    filtered_products.append(p)
                                    break
                    if filtered_products:
                        product_ids = [str(p.id) for p in filtered_products]
                        qs = qs(id__in=product_ids)
                    else:
                        return Response({
                            "data": [],
                            "pagination": {
                                "page": page,
                                "page_size": page_size,
                                "total": 0,
                                "total_pages": 0
                            },
                            "filters": self._get_empty_filters()
                        })

            # Apply color filter
            if color:
                color_names = [c.strip() for c in color.split(',') if c.strip()]
                if color_names:
                    all_products = list(qs)
                    filtered_products = []
                    for p in all_products:
                        if p.colors:
                            for color_variant in p.colors:
                                color_name = _pick_lang(color_variant.color_name, lang)
                                if color_name:
                                    color_name_normalized = _normalize_vietnamese(color_name.lower())
                                    for cn in color_names:
                                        if _normalize_vietnamese(cn.lower()) in color_name_normalized or color_name_normalized in _normalize_vietnamese(cn.lower()):
                                            filtered_products.append(p)
                                            break
                                    if p in filtered_products:
                                        break
                    if filtered_products:
                        product_ids = [str(p.id) for p in filtered_products]
                        qs = qs(id__in=product_ids)
                    else:
                        return Response({
                            "data": [],
                            "pagination": {
                                "page": page,
                                "page_size": page_size,
                                "total": 0,
                                "total_pages": 0
                            },
                            "filters": self._get_empty_filters()
                        })

            # Apply size filter
            if size:
                size_values = [s.strip() for s in size.split(',') if s.strip()]
                if size_values:
                    all_products = list(qs)
                    filtered_products = []
                    for p in all_products:
                        if p.sizes:
                            for size_variant in p.sizes:
                                size_name = _pick_lang(size_variant.size_name, lang)
                                if size_name:
                                    size_name_normalized = _normalize_vietnamese(size_name.lower())
                                    for sv in size_values:
                                        if _normalize_vietnamese(sv.lower()) in size_name_normalized or size_name_normalized in _normalize_vietnamese(sv.lower()):
                                            filtered_products.append(p)
                                            break
                                    if p in filtered_products:
                                        break
                    if filtered_products:
                        product_ids = [str(p.id) for p in filtered_products]
                        qs = qs(id__in=product_ids)
                    else:
                        return Response({
                            "data": [],
                            "pagination": {
                                "page": page,
                                "page_size": page_size,
                                "total": 0,
                                "total_pages": 0
                            },
                            "filters": self._get_empty_filters()
                        })

            # Apply price filters
            if price_from:
                try:
                    price_from_val = float(price_from)
                    qs = qs(original_price__gte=price_from_val)
                except (ValueError, TypeError):
                    pass

            if price_to:
                try:
                    price_to_val = float(price_to)
                    qs = qs(original_price__lte=price_to_val)
                except (ValueError, TypeError):
                    pass

            # Apply category_slug filter (supports both ParentCategory and ChildCategory slugs)
            if category_slug:
                # First, try to find a ChildCategory with this slug
                child = ChildCategory.objects(slug=category_slug, status="active").first()
                if child:
                    # Filter by this specific child category
                    qs = qs(category=child)
                else:
                    # If not found, try to find a ParentCategory with this slug
                    parent = ParentCategory.objects(slug=category_slug, status="active").first()
                    if parent:
                        # Filter by all child categories under this parent
                        children = list(ChildCategory.objects(parent=parent, status="active"))
                        if children:
                            qs = qs(category__in=children)
                        else:
                            # No child categories found under this parent
                            return Response({
                                "data": [],
                                "pagination": {
                                    "page": page,
                                    "page_size": page_size,
                                    "total": 0,
                                    "total_pages": 0
                                },
                                "filters": self._get_empty_filters()
                            })
                    else:
                        # Category slug not found
                        return Response({
                            "data": [],
                            "pagination": {
                                "page": page,
                                "page_size": page_size,
                                "total": 0,
                                "total_pages": 0
                            },
                            "filters": self._get_empty_filters()
                        })

            # Apply special category filter
            if category:
                if category == 'Sản-phẩm-mới' or category == 'San-pham-moi':
                    # New products (created in last 30 days)
                    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                    qs = qs(created_at__gte=thirty_days_ago)
                elif category == 'Giảm-giá' or category == 'Giam-gia':
                    # Products with discount
                    qs = qs(discount__gt=0)
                elif category == 'Phụ-kiện' or category == 'Phu-kien':
                    # Accessories - filter by category name containing "phụ kiện" or "accessory"
                    all_products = list(qs)
                    filtered_products = []
                    for p in all_products:
                        if p.category:
                            cat_name = _pick_lang(p.category.name, lang)
                            if cat_name:
                                cat_name_lower = _normalize_vietnamese(cat_name.lower())
                                if 'phu kien' in cat_name_lower or 'accessory' in cat_name_lower or 'phụ kiện' in cat_name_lower:
                                    filtered_products.append(p)
                    if filtered_products:
                        product_ids = [str(p.id) for p in filtered_products]
                        qs = qs(id__in=product_ids)
                    else:
                        return Response({
                            "data": [],
                            "pagination": {
                                "page": page,
                                "page_size": page_size,
                                "total": 0,
                                "total_pages": 0
                            },
                            "filters": self._get_empty_filters()
                        })

            # Get all products and ensure reference fields are loaded
            products = list(qs)
            
            # Reload reference fields to avoid lazy loading issues
            for product in products:
                try:
                    if product.brand:
                        product.brand.reload()
                    if product.category:
                        product.category.reload()
                        if product.category.parent:
                            product.category.parent.reload()
                except Exception:
                    # If reload fails, continue - fields may already be loaded
                    pass

            # Apply sorting
            if sort == 'popular':
                products.sort(key=lambda p: ((p.sold or 0), (p.rate or 0)), reverse=True)
            elif sort == 'best_sellers':
                # Sort by sold count only (top selling products)
                products.sort(key=lambda p: (p.sold or 0), reverse=True)
            elif sort == 'newest':
                products.sort(key=lambda p: p.created_at or datetime.min, reverse=True)
            elif sort == 'oldest':
                products.sort(key=lambda p: p.created_at or datetime.max)
            elif sort == 'price_asc':
                products.sort(key=lambda p: p.original_price or 0)
            elif sort == 'price_desc':
                products.sort(key=lambda p: p.original_price or 0, reverse=True)
            elif sort == 'rating_desc':
                products.sort(key=lambda p: p.rate or 0, reverse=True)
            elif sort == 'name_asc':
                products.sort(key=lambda p: _pick_lang(p.name, lang) or '')
            elif sort == 'name_desc':
                products.sort(key=lambda p: _pick_lang(p.name, lang) or '', reverse=True)
            else:
                # Default to popular
                products.sort(key=lambda p: ((p.sold or 0), (p.rate or 0)), reverse=True)

            # Calculate filters from filtered products (before pagination)
            filters = self._calculate_filters(products, lang)

            # Pagination
            total = len(products)
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            start = max((page - 1) * page_size, 0)
            end = start + page_size
            page_items = products[start:end]

            # Build response data
            data = []
            for p in page_items:
                # Get first color's name and hex if available
                color_name = None
                color_hex = None
                if p.colors and len(p.colors) > 0:
                    first_color = p.colors[0]
                    if first_color:
                        # Get color name (multilingual)
                        color_name_raw = getattr(first_color, 'color_name', None)
                        if color_name_raw:
                            color_name = _pick_lang(color_name_raw, lang)
                        # Get hex color
                        color_hex = getattr(first_color, 'hex_color', None)

                # Build brand info
                brand_info = None
                if p.brand:
                    brand_info = {
                        "_id": str(p.brand.id),
                        "name": _pick_lang(p.brand.name, lang)
                    }

                # Build category info with parent
                category_info = None
                if p.category:
                    category_info = {
                        "_id": str(p.category.id),
                        "name": _pick_lang(p.category.name, lang)
                    }
                    # Add parent category if exists
                    if p.category.parent:
                        category_info["parentId"] = {
                            "_id": str(p.category.parent.id),
                            "name": _pick_lang(p.category.parent.name, lang)
                        }

                # Calculate discount percentage
                discount_pct = int(p.discount) if p.discount else 0

                product_data = {
                    "_id": str(p.id),
                    "name": _pick_lang(p.name, lang),
                    "originalPrice": int(p.original_price) if p.original_price else 0,
                    "discount": discount_pct,
                    "sold": p.sold or 0,
                    "rate": p.rate or 0,
                    "stock": p.stock or 0,
                    "images": p.images or [],
                    "brandId": brand_info,
                    "categoryId": category_info,
                    "createdAt": p.created_at.isoformat() if p.created_at else None,
                }

                # Add color and colorHex if available
                if color_name:
                    product_data["color"] = color_name
                if color_hex:
                    product_data["colorHex"] = color_hex

                data.append(product_data)

            return Response({
                "data": data,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages
                },
                "filters": filters
            })

        except Exception as e:
            logger.error(f"Error in PublicProductsListView: {str(e)}", exc_info=True)
            return Response(
                {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Có lỗi xảy ra khi tải sản phẩm"
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_empty_filters(self):
        """Return empty filters structure"""
        return {
            "availableBrands": [],
            "availableColors": [],
            "availableSizes": [],
            "availableGenders": [],
            "priceRange": {
                "min": 0,
                "max": 0
            }
        }

    def _calculate_filters(self, products, lang):
        """
        Calculate available filters from filtered products.
        Filters are based on the filtered results, not all products.
        """
        try:
            available_brands = {}
            available_colors = {}
            available_sizes = {}
            available_genders = {}
            prices = []
            
            # Debug: Count products with colors/sizes
            products_with_colors = 0
            products_with_sizes = 0
            total_colors = 0
            total_sizes = 0

            for product in products:
                try:
                    # Debug: Count products with colors/sizes
                    if product.colors and len(product.colors) > 0:
                        products_with_colors += 1
                        total_colors += len(product.colors)
                    if product.sizes and len(product.sizes) > 0:
                        products_with_sizes += 1
                        total_sizes += len(product.sizes)
                    
                    # Count brands
                    if product.brand:
                        try:
                            # Ensure brand is loaded
                            if hasattr(product.brand, 'name'):
                                brand_name = _pick_lang(product.brand.name, lang)
                                if brand_name:
                                    if brand_name not in available_brands:
                                        available_brands[brand_name] = 0
                                    available_brands[brand_name] += 1
                        except Exception as e:
                            logger.warning(f"Error processing brand for product {product.id}: {str(e)}")
                            continue

                    # Count colors from colors array
                    if product.colors and len(product.colors) > 0:
                        for color_variant in product.colors:
                            try:
                                if not color_variant:
                                    continue
                                
                                # Access color_name directly (it's a DynamicField)
                                # Try both direct access and getattr
                                color_name_raw = None
                                if hasattr(color_variant, 'color_name'):
                                    color_name_raw = color_variant.color_name
                                else:
                                    color_name_raw = getattr(color_variant, 'color_name', None)
                                
                                if not color_name_raw:
                                    logger.debug(f"Color variant has no color_name: {color_variant}")
                                    continue
                                
                                color_name = _pick_lang(color_name_raw, lang)
                                if not color_name:
                                    logger.debug(f"Color name is empty after _pick_lang: {color_name_raw}")
                                    continue
                                
                                # Use color name as key, store hex and count
                                if color_name not in available_colors:
                                    hex_color = None
                                    if hasattr(color_variant, 'hex_color'):
                                        hex_color = color_variant.hex_color
                                    else:
                                        hex_color = getattr(color_variant, 'hex_color', None)
                                    
                                    available_colors[color_name] = {
                                        "hex": hex_color if hex_color else None,
                                        "count": 0
                                    }
                                available_colors[color_name]["count"] += 1
                            except Exception as e:
                                logger.warning(f"Error processing color variant for product {product.id}: {str(e)}", exc_info=True)
                                # Continue to next color variant, not skip entire product
                                continue

                    # Count sizes from sizes array
                    if product.sizes and len(product.sizes) > 0:
                        for size_variant in product.sizes:
                            try:
                                if not size_variant:
                                    continue
                                
                                # Access size_name directly (it's a DynamicField)
                                # Try both direct access and getattr
                                size_name_raw = None
                                if hasattr(size_variant, 'size_name'):
                                    size_name_raw = size_variant.size_name
                                else:
                                    size_name_raw = getattr(size_variant, 'size_name', None)
                                
                                if not size_name_raw:
                                    logger.debug(f"Size variant has no size_name: {size_variant}")
                                    continue
                                
                                size_name = _pick_lang(size_name_raw, lang)
                                if not size_name:
                                    logger.debug(f"Size name is empty after _pick_lang: {size_name_raw}")
                                    continue
                                
                                if size_name not in available_sizes:
                                    available_sizes[size_name] = 0
                                available_sizes[size_name] += 1
                            except Exception as e:
                                logger.warning(f"Error processing size variant for product {product.id}: {str(e)}", exc_info=True)
                                # Continue to next size variant, not skip entire product
                                continue

                    # Count genders from category parent (parentId.name)
                    if product.category:
                        try:
                            # Ensure category is loaded
                            if hasattr(product.category, 'parent') and product.category.parent:
                                # Ensure parent is loaded
                                parent = product.category.parent
                                if hasattr(parent, 'name'):
                                    gender_name = _pick_lang(parent.name, lang)
                                    if gender_name:
                                        if gender_name not in available_genders:
                                            available_genders[gender_name] = 0
                                        available_genders[gender_name] += 1
                        except Exception as e:
                            logger.warning(f"Error processing category/gender for product {product.id}: {str(e)}")
                            continue

                    # Collect prices for price range
                    if product.original_price:
                        try:
                            prices.append(float(product.original_price))
                        except (ValueError, TypeError):
                            pass
                except Exception as e:
                    logger.warning(f"Error processing product {product.id}: {str(e)}")
                    continue

            # Format available brands
            brands_list = [
                {"name": name, "count": count}
                for name, count in sorted(available_brands.items())
            ]

            # Format available colors
            colors_list = [
                {
                    "name": name,
                    "hex": data["hex"],
                    "count": data["count"]
                }
                for name, data in sorted(available_colors.items())
            ]

            # Format available sizes
            sizes_list = [
                {"size": size, "count": count}
                for size, count in sorted(available_sizes.items())
            ]

            # Format available genders
            genders_list = [
                {"name": name, "count": count}
                for name, count in sorted(available_genders.items())
            ]

            # Calculate price range
            price_range = {
                "min": int(min(prices)) if prices else 0,
                "max": int(max(prices)) if prices else 0
            }
            
            # Debug logging
            logger.info(f"Filters calculated: {len(products)} products, "
                       f"{products_with_colors} with colors ({total_colors} total), "
                       f"{products_with_sizes} with sizes ({total_sizes} total), "
                       f"Found {len(colors_list)} unique colors, {len(sizes_list)} unique sizes")

            return {
                "availableBrands": brands_list,
                "availableColors": colors_list,
                "availableSizes": sizes_list,
                "availableGenders": genders_list,
                "priceRange": price_range
            }
        except Exception as e:
            logger.error(f"Error in _calculate_filters: {str(e)}", exc_info=True)
            # Return empty filters on error
            return self._get_empty_filters()


class PublicCategoriesView(APIView):
    """GET /api/categories - parents with children and counts"""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        lang = (request.query_params.get('lang') or 'vi').strip() or 'vi'
        parents = ParentCategory.objects(status="active")
        result = []
        for parent in parents:
            children = list(ChildCategory.objects(parent=parent, status="active"))
            result.append({
                "id": str(parent.id),
                "name": _pick_lang(parent.name, lang),
                "slug": parent.slug,
                "children": [
                    {
                        "id": str(ch.id),
                        "name": _pick_lang(ch.name, lang),
                        "slug": ch.slug,
                        "product_count": Product.objects(category=ch, status="active").count(),
                    }
                    for ch in children
                ]
            })
        return Response({"data": result})


class PublicReviewsView(APIView):
    """GET /api/reviews?placement=&page=&page_size="""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        lang = (request.query_params.get('lang') or 'vi').strip() or 'vi'
        placement = (request.query_params.get('placement') or 'home').strip() or 'home'
        page = int(request.query_params.get('page') or 1)
        page_size = int(request.query_params.get('page_size') or 10)

        qs = CustomerReview.objects(placement=placement, status="active").order_by('-created_at')
        total = qs.count()
        start = max((page - 1) * page_size, 0)
        items = list(qs.skip(start).limit(page_size))

        data = [
            {
                "id": str(r.id),
                "author_name": r.author_name,
                "author_avatar": r.author_avatar,
                "rating": r.rating,
                "content": _pick_lang(r.content, lang),
                "createdAt": r.created_at.isoformat() if r.created_at else None,
            }
            for r in items
        ]

        return Response({
            "data": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            }
        })


class PublicHeroView(APIView):
    """GET /api/content/hero - latest active hero content"""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        lang = (request.query_params.get('lang') or 'vi').strip() or 'vi'
        hero = HeroContent.objects(status="active").order_by('-created_at').first()
        if not hero:
            return Response({"data": None})
        return Response({
            "data": {
                "headline": _pick_lang(hero.headline, lang),
                "subtext": _pick_lang(hero.subtext, lang),
                "cta_text": _pick_lang(hero.cta_text, lang),
                "cta_url": hero.cta_url,
                "image": hero.image,
            }
        })


class ProductAutocompleteView(APIView):
    """
    GET /api/products/autocomplete - Autocomplete/Gợi Ý Tìm Kiếm
    Returns suggestions for products and brands based on search query
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        # Get query parameters
        query = (request.query_params.get('q') or '').strip()
        limit = int(request.query_params.get('limit') or 5)
        lang = (request.query_params.get('lang') or 'vi').strip() or 'vi'
        
        # Validate query
        if not query:
            return Response(
                {
                    "error": {
                        "code": "MISSING_QUERY",
                        "message": "Vui lòng nhập từ khóa tìm kiếm"
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(query) < 2:
            return Response(
                {
                    "error": {
                        "code": "INVALID_QUERY",
                        "message": "Từ khóa tìm kiếm phải có ít nhất 2 ký tự"
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Limit max to 10
        if limit > 10:
            limit = 10
        
        # Search for products
        products = _text_search(query, lang, {'in_stock': True})
        
        # Calculate relevance scores and sort
        products_with_scores = [
            (product, _calculate_relevance_score(product, query, lang))
            for product in products
        ]
        products_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        suggestions = []
        
        # Add top products
        for product, score in products_with_scores[:limit]:
            # Calculate discount percentage
            discount_pct = 0
            if product.discount:
                discount_pct = int(product.discount)
            elif product.original_price and product.discount_price:
                discount_pct = int((1 - product.discount_price / product.original_price) * 100)
            
            suggestion = {
                "id": str(product.id),
                "text": _pick_lang(product.name, lang),
                "type": "product",
                "url": f"/product/{product.slug}",
                "price": int(product.original_price) if product.original_price else 0,
                "discountPrice": int(product.discount_price) if product.discount_price else int(product.original_price) if product.original_price else 0,
                "discount": discount_pct
            }
            
            # Add image if available
            if product.images and len(product.images) > 0:
                suggestion["image"] = product.images[0]
            
            suggestions.append(suggestion)
        
        # Search for matching brands if we have room
        if len(suggestions) < limit:
            query_normalized = _normalize_vietnamese(query)
            brands = Brand.objects(status="active")
            matching_brands = []
            
            for brand in brands:
                brand_name = _pick_lang(brand.name, lang)
                if brand_name:
                    brand_name_normalized = _normalize_vietnamese(brand_name)
                    if query_normalized in brand_name_normalized:
                        matching_brands.append(brand)
            
            # Add brand suggestions
            remaining_slots = limit - len(suggestions)
            for brand in matching_brands[:remaining_slots]:
                brand_name = _pick_lang(brand.name, lang)
                suggestion = {
                    "id": f"brand_{str(brand.id)}",
                    "text": brand_name,
                    "type": "brand",
                    "url": f"/products?brand={brand_name}"
                }
                
                if brand.logo:
                    suggestion["logo"] = brand.logo
                
                suggestions.append(suggestion)
        
        return Response({"suggestions": suggestions})


class ProductSearchView(APIView):
    """
    GET /api/products/search - Tìm Kiếm Đầy Đủ
    Full product search with pagination and filters
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        # Get query parameters
        query = (request.query_params.get('q') or '').strip()
        page = int(request.query_params.get('page') or 1)
        page_size = int(request.query_params.get('page_size') or 12)
        sort_by = (request.query_params.get('sort') or 'relevance').strip()
        lang = (request.query_params.get('lang') or 'vi').strip() or 'vi'
        
        # Validate query
        if not query:
            return Response(
                {
                    "error": {
                        "code": "MISSING_QUERY",
                        "message": "Vui lòng nhập từ khóa tìm kiếm"
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate query length (max 100 characters)
        if len(query) > 100:
            return Response(
                {
                    "error": {
                        "code": "INVALID_QUERY",
                        "message": "Từ khóa tìm kiếm không được vượt quá 100 ký tự"
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Limit page_size to max 100
        if page_size > 100:
            page_size = 100
        
        # Build filters
        filters = {}
        
        brand_param = request.query_params.get('brand')
        if brand_param:
            filters['brand'] = brand_param
        
        category_slug = request.query_params.get('category_slug')
        if category_slug:
            filters['category_slug'] = category_slug
        
        price_from = request.query_params.get('priceFrom')
        if price_from:
            try:
                filters['priceFrom'] = float(price_from)
            except ValueError:
                pass
        
        price_to = request.query_params.get('priceTo')
        if price_to:
            try:
                filters['priceTo'] = float(price_to)
            except ValueError:
                pass
        
        min_rating = request.query_params.get('min_rating')
        if min_rating:
            try:
                filters['min_rating'] = float(min_rating)
            except ValueError:
                pass
        
        in_stock = request.query_params.get('in_stock', 'true').lower()
        filters['in_stock'] = in_stock != 'false'
        
        # Perform search
        products = _text_search(query, lang, filters)
        
        # Calculate relevance scores for sorting
        products_with_scores = [
            (product, _calculate_relevance_score(product, query, lang))
            for product in products
        ]
        
        # Sort results
        if sort_by == 'relevance':
            products_with_scores.sort(key=lambda x: x[1], reverse=True)
        elif sort_by == 'popular':
            products_with_scores.sort(key=lambda x: (x[0].sold or 0, x[0].rate or 0), reverse=True)
        elif sort_by == 'newest':
            products_with_scores.sort(key=lambda x: x[0].created_at or 0, reverse=True)
        elif sort_by == 'price_asc':
            products_with_scores.sort(key=lambda x: x[0].original_price or 0)
        elif sort_by == 'price_desc':
            products_with_scores.sort(key=lambda x: x[0].original_price or 0, reverse=True)
        elif sort_by == 'rating_desc':
            products_with_scores.sort(key=lambda x: x[0].rate or 0, reverse=True)
        else:
            # Default to relevance
            products_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        sorted_products = [p for p, _ in products_with_scores]
        
        # Pagination
        total = len(sorted_products)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        start = max((page - 1) * page_size, 0)
        end = start + page_size
        page_items = sorted_products[start:end]
        
        # Build response data
        data = []
        for product in page_items:
            # Calculate discount percentage
            discount_pct = 0
            if product.discount:
                discount_pct = int(product.discount)
            elif product.original_price and product.discount_price:
                discount_pct = int((1 - product.discount_price / product.original_price) * 100)
            
            product_data = {
                "id": str(product.id),
                "slug": product.slug,
                "name": {
                    "vi": _pick_lang(product.name, 'vi'),
                    "en": _pick_lang(product.name, 'en'),
                    "ja": _pick_lang(product.name, 'ja')
                },
                "description": {
                    "vi": _pick_lang(product.description, 'vi'),
                    "en": _pick_lang(product.description, 'en'),
                    "ja": _pick_lang(product.description, 'ja')
                },
                "price": int(product.original_price) if product.original_price else 0,
                "discountPrice": int(product.discount_price) if product.discount_price else int(product.original_price) if product.original_price else 0,
                "discount": discount_pct,
                "rating": product.rate or 0,
                "reviewCount": 0,  # TODO: Implement review count
                "soldCount": product.sold or 0,
                "stock": product.stock or 0,
                "status": product.status
            }
            
            # Add images
            if product.images and len(product.images) > 0:
                product_data["image"] = product.images[0]
                product_data["images"] = product.images
            else:
                product_data["image"] = ""
                product_data["images"] = []
            
            # Add brand info
            if product.brand:
                product_data["brand"] = {
                    "id": str(product.brand.id),
                    "name": {
                        "vi": _pick_lang(product.brand.name, 'vi'),
                        "en": _pick_lang(product.brand.name, 'en'),
                        "ja": _pick_lang(product.brand.name, 'ja')
                    },
                    "logo": product.brand.logo or ""
                }
            
            # Add category info
            if product.category:
                product_data["category"] = {
                    "id": str(product.category.id),
                    "name": {
                        "vi": _pick_lang(product.category.name, 'vi'),
                        "en": _pick_lang(product.category.name, 'en'),
                        "ja": _pick_lang(product.category.name, 'ja')
                    },
                    "slug": product.category.slug
                }
            
            data.append(product_data)
        
        # Generate related search suggestions
        suggestions = self._generate_suggestions(query, sorted_products, lang)
        
        # Build filter options from results
        filter_options = self._build_filter_options(sorted_products, lang)
        
        response_data = {
            "query": query,
            "data": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages
            },
            "suggestions": suggestions,
            "filters": filter_options
        }
        
        return Response(response_data)
    
    def _generate_suggestions(self, query, products, lang):
        """Generate related search suggestions"""
        suggestions = []
        
        # Collect unique brands and categories from results
        brands = set()
        categories = set()
        tags = set()
        
        for product in products[:20]:  # Look at top 20 results
            if product.brand:
                brand_name = _pick_lang(product.brand.name, lang)
                if brand_name:
                    brands.add(brand_name)
            
            if product.category:
                cat_name = _pick_lang(product.category.name, lang)
                if cat_name:
                    categories.add(cat_name)
            
            if product.tags:
                for tag in product.tags[:3]:  # Top 3 tags per product
                    tags.add(tag)
        
        # Generate suggestions from brands
        for brand in list(brands)[:2]:
            suggestions.append(f"{query} {brand}")
        
        # Add some common tags as suggestions
        for tag in list(tags)[:3]:
            if tag.lower() not in query.lower():
                suggestions.append(f"{query} {tag}")
        
        # Limit to 5 suggestions
        return suggestions[:5]
    
    def _build_filter_options(self, products, lang):
        """Build available filter options from search results"""
        # Collect unique brands
        brand_counts = {}
        category_counts = {}
        min_price = float('inf')
        max_price = 0
        
        for product in products:
            # Count brands
            if product.brand:
                brand_id = str(product.brand.id)
                brand_name = _pick_lang(product.brand.name, lang)
                if brand_name:
                    if brand_id not in brand_counts:
                        brand_counts[brand_id] = {
                            "id": brand_id,
                            "name": {"vi": _pick_lang(product.brand.name, 'vi')},
                            "count": 0
                        }
                    brand_counts[brand_id]["count"] += 1
            
            # Count categories
            if product.category:
                cat_id = str(product.category.id)
                cat_name = _pick_lang(product.category.name, lang)
                if cat_name:
                    if cat_id not in category_counts:
                        category_counts[cat_id] = {
                            "id": cat_id,
                            "name": {"vi": _pick_lang(product.category.name, 'vi')},
                            "slug": product.category.slug,
                            "count": 0
                        }
                    category_counts[cat_id]["count"] += 1
            
            # Track price range
            if product.original_price:
                min_price = min(min_price, product.original_price)
                max_price = max(max_price, product.original_price)
        
        return {
            "availableBrands": list(brand_counts.values()),
            "availableCategories": list(category_counts.values()),
            "priceRange": {
                "min": int(min_price) if min_price != float('inf') else 0,
                "max": int(max_price) if max_price > 0 else 0
            }
        }


class ProductDetailView(APIView):
    """
    GET /api/products/{id_or_slug} - Get product detail by ID or slug
    Public endpoint - No authentication required
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, id_or_slug):
        try:
            # Get language from query params
            lang = (request.query_params.get('lang') or 'vi').strip() or 'vi'
            
            # Try to find product by ID first, then by slug
            product = None
            try:
                # Try as ObjectId first
                product = Product.objects(id=id_or_slug, status="active").first()
            except Exception:
                pass
            
            if not product:
                # Try to find by slug
                product = Product.objects(slug=id_or_slug, status="active").first()
            
            if not product:
                return Response(
                    {
                        "error": {
                            "code": "PRODUCT_NOT_FOUND",
                            "message": "Không tìm thấy sản phẩm"
                        }
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Ensure brand and category are loaded
            if product.brand:
                product.brand.reload()
            if product.category:
                product.category.reload()
                if product.category.parent:
                    product.category.parent.reload()
            
            # Build response data
            response_data = {
                "id": str(product.id),
                "slug": product.slug,
                "name": {
                    "vi": _pick_lang(product.name, 'vi'),
                    "en": _pick_lang(product.name, 'en'),
                    "ja": _pick_lang(product.name, 'ja')
                },
                "description": {
                    "vi": _pick_lang(product.description, 'vi') or "",
                    "en": _pick_lang(product.description, 'en') or "",
                    "ja": _pick_lang(product.description, 'ja') or ""
                },
                "price": int(product.original_price) if product.original_price else 0,
                "discountPrice": int(product.discount_price) if product.discount_price else int(product.original_price) if product.original_price else 0,
                "discount": int(product.discount) if product.discount else 0,
                "images": product.images or [],
                "stock": product.stock or 0,
                "soldCount": product.sold or 0,
                "rating": product.rate or 0,
                "reviewCount": 0,  # TODO: Calculate from reviews collection
                "status": product.status,
                "tags": product.tags or [],
                "createdAt": product.created_at.isoformat() if product.created_at else None,
                "updatedAt": product.updated_at.isoformat() if product.updated_at else None
            }
            
            # Add brand info
            if product.brand:
                response_data["brand"] = {
                    "id": str(product.brand.id),
                    "name": {
                        "vi": _pick_lang(product.brand.name, 'vi'),
                        "en": _pick_lang(product.brand.name, 'en'),
                        "ja": _pick_lang(product.brand.name, 'ja')
                    },
                    "logo": product.brand.logo or ""
                }
            
            # Add category info
            if product.category:
                response_data["category"] = {
                    "id": str(product.category.id),
                    "name": {
                        "vi": _pick_lang(product.category.name, 'vi'),
                        "en": _pick_lang(product.category.name, 'en'),
                        "ja": _pick_lang(product.category.name, 'ja')
                    },
                    "slug": product.category.slug
                }
                
                # Add parent category if exists
                if product.category.parent:
                    response_data["category"]["parent"] = {
                        "id": str(product.category.parent.id),
                        "name": {
                            "vi": _pick_lang(product.category.parent.name, 'vi'),
                            "en": _pick_lang(product.category.parent.name, 'en'),
                            "ja": _pick_lang(product.category.parent.name, 'ja')
                        },
                        "slug": product.category.parent.slug
                    }
            
            # Build specifications
            specifications = {}
            
            # Add sizes
            if product.sizes and len(product.sizes) > 0:
                sizes = []
                for size_variant in product.sizes:
                    size_name = _pick_lang(size_variant.size_name, lang)
                    if size_name and size_name not in sizes:
                        sizes.append(size_name)
                if sizes:
                    specifications["sizes"] = sizes
            
            # Add colors
            if product.colors and len(product.colors) > 0:
                colors = []
                for color_variant in product.colors:
                    color_name = _pick_lang(color_variant.color_name, lang)
                    if color_name:
                        color_data = {
                            "name": color_name,
                            "hex": color_variant.hex_color or "#000000"
                        }
                        if color_variant.image:
                            color_data["image"] = color_variant.image
                        colors.append(color_data)
                if colors:
                    specifications["colors"] = colors
            
            # Add other specifications
            if product.material:
                material = _pick_lang(product.material, lang)
                if material:
                    specifications["material"] = material
            
            if product.weight:
                weight = _pick_lang(product.weight, lang)
                if weight:
                    specifications["weight"] = weight
            
            if product.gender:
                gender = _pick_lang(product.gender, lang)
                if gender:
                    specifications["gender"] = gender
            
            # Add size table if exists
            if product.size_table:
                size_table = _pick_lang(product.size_table, lang)
                if size_table:
                    specifications["sizeTable"] = size_table
            
            response_data["specifications"] = specifications
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error in ProductDetailView: {str(e)}", exc_info=True)
            return Response(
                {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Có lỗi xảy ra khi tải thông tin sản phẩm"
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
