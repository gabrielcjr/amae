from django.db import models
from django.utils.translation import gettext_lazy as _


class Page(models.Model):
    title = models.CharField(_("Title"), max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField(_("Content"))
    is_published = models.BooleanField(_("Published"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = _("Page")
        verbose_name_plural = _("Pages")

    def __str__(self):
        return self.title


class FAQ(models.Model):
    question = models.CharField(_("Question"), max_length=300)
    answer = models.TextField(_("Answer"))
    category = models.CharField(_("Category"), max_length=100)
    order = models.PositiveIntegerField(_("Order"), default=0)
    is_published = models.BooleanField(_("Published"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "order"]
        verbose_name = _("FAQ")
        verbose_name_plural = _("FAQs")

    def __str__(self):
        return self.question


class Testimonial(models.Model):
    author_name = models.CharField(_("Author name"), max_length=200)
    author_role = models.CharField(_("Role"), max_length=200, blank=True)
    content = models.TextField(_("Testimonial"))
    mission_field = models.ForeignKey(
        "missions.MissionField",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Mission field"),
    )
    is_published = models.BooleanField(_("Published"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Testimonial")
        verbose_name_plural = _("Testimonials")

    def __str__(self):
        return f"{self.author_name} - {self.author_role}"


class SiteImage(models.Model):
    key = models.SlugField(
        _("Identifier"), unique=True, help_text=_("E.g.: home_hero, login_side")
    )
    description = models.CharField(
        _("Description"), max_length=200, help_text=_("Where this image is used")
    )
    image = models.ImageField(_("Image (upload)"), upload_to="site/", blank=True)
    external_url = models.URLField(
        _("External URL"), blank=True, help_text=_("External image URL (e.g. Unsplash)")
    )
    alt_text = models.CharField(_("Alt text"), max_length=300, blank=True)

    class Meta:
        ordering = ["key"]
        verbose_name = _("Site Image")
        verbose_name_plural = _("Site Images")

    def __str__(self):
        return f"{self.key} - {self.description}"

    @property
    def url(self):
        if self.image:
            return self.image.url
        return self.external_url


class ContactMessage(models.Model):
    name = models.CharField(_("Name"), max_length=200)
    email = models.EmailField(_("Email"))
    subject = models.CharField(_("Subject"), max_length=300)
    message = models.TextField(_("Message"))
    is_read = models.BooleanField(_("Read"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Contact Message")
        verbose_name_plural = _("Contact Messages")

    def __str__(self):
        return f"{self.name} - {self.subject}"
