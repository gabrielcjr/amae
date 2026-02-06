from .models import SiteImage


def site_images(request):
    images = SiteImage.objects.all()
    return {'site_images': {img.key: img for img in images}}
