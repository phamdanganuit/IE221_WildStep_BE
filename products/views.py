from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Banner


class PublicBannerListView(APIView):
    """GET /api/content/banners - Public list of active banners"""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        banners = Banner.objects(status="active").order_by('order')
        data = [
            {
                "id": str(b.id),
                "image": b.image,
                "link": b.link,
                "title": b.title,
                "order": b.order,
            }
            for b in banners
        ]
        return Response({"data": data})
