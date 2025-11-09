from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Banner, Brand, Product, ParentCategory, ChildCategory, CustomerReview, HeroContent
from rest_framework import status
import re
import unicodedata


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
    """GET /api/products with sort and optional category filter"""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        lang = (request.query_params.get('lang') or 'vi').strip() or 'vi'
        sort = (request.query_params.get('sort') or '').strip()
        page = int(request.query_params.get('page') or 1)
        page_size = int(request.query_params.get('page_size') or 12)
        category_slug = (request.query_params.get('category_slug') or '').strip()

        qs = Product.objects(status="active")

        # Category filter by child slug; if not found, try parent and include its children
        if category_slug:
            child = ChildCategory.objects(slug=category_slug).first()
            if child:
                qs = qs(category=child)
            else:
                parent = ParentCategory.objects(slug=category_slug).first()
                if parent:
                    children = list(ChildCategory.objects(parent=parent))
                    qs = qs(category__in=children)

        products = list(qs)

        # Sorting strategies
        if sort == 'popular':
            products.sort(key=lambda p: ((p.sold or 0), (p.rate or 0)), reverse=True)
        elif sort == 'best_sellers':
            products.sort(key=lambda p: (p.sold or 0), reverse=True)
        else:
            products.sort(key=lambda p: p.created_at or 0, reverse=True)

        total = len(products)
        start = max((page - 1) * page_size, 0)
        end = start + page_size
        page_items = products[start:end]

        data = [
            {
                "id": str(p.id),
                "name": _pick_lang(p.name, lang),
                "slug": p.slug,
                "price": p.original_price,
                "discountPrice": p.discount_price,
                "rate": p.rate,
                "sold": p.sold,
                "images": p.images,
                "brand": {"id": str(p.brand.id), "name": _pick_lang(p.brand.name, lang), "slug": p.brand.slug} if p.brand else None,
                "category": {"id": str(p.category.id), "name": _pick_lang(p.category.name, lang), "slug": p.category.slug} if p.category else None,
            }
            for p in page_items
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
