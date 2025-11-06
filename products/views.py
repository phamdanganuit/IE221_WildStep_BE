from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Banner, Brand, Product, ParentCategory, ChildCategory, CustomerReview, HeroContent
from rest_framework import status


def _pick_lang(value, lang: str, default_lang: str = 'vi'):
    """Return localized string from value which may be a dict or a plain string."""
    if isinstance(value, dict):
        return value.get(lang) or value.get(default_lang) or next(iter(value.values()), None)
    return value


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
