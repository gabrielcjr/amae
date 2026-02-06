from django.shortcuts import get_object_or_404, render

from .forms import ContactForm
from .models import FAQ, Page, Testimonial


def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "pages/page_detail.html", {"page": page})


def faq(request):
    faqs = FAQ.objects.filter(is_published=True)
    return render(request, "pages/faq.html", {"faqs": faqs})


def contact(request):
    success = False
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            success = True
            form = ContactForm()
    else:
        form = ContactForm()
    return render(request, "pages/contact.html", {"form": form, "success": success})


def testimonials(request):
    testimonials_list = Testimonial.objects.filter(is_published=True).select_related(
        "mission_field"
    )
    return render(
        request, "pages/testimonials.html", {"testimonials": testimonials_list}
    )
