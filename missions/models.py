from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .countries import COUNTRY_CHOICES


class BrazilianState(models.TextChoices):
    AC = "AC", "Acre"
    AL = "AL", "Alagoas"
    AP = "AP", "Amapá"
    AM = "AM", "Amazonas"
    BA = "BA", "Bahia"
    CE = "CE", "Ceará"
    DF = "DF", "Distrito Federal"
    ES = "ES", "Espírito Santo"
    GO = "GO", "Goiás"
    MA = "MA", "Maranhão"
    MT = "MT", "Mato Grosso"
    MS = "MS", "Mato Grosso do Sul"
    MG = "MG", "Minas Gerais"
    PA = "PA", "Pará"
    PB = "PB", "Paraíba"
    PR = "PR", "Paraná"
    PE = "PE", "Pernambuco"
    PI = "PI", "Piauí"
    RJ = "RJ", "Rio de Janeiro"
    RN = "RN", "Rio Grande do Norte"
    RS = "RS", "Rio Grande do Sul"
    RO = "RO", "Rondônia"
    RR = "RR", "Roraima"
    SC = "SC", "Santa Catarina"
    SP = "SP", "São Paulo"
    SE = "SE", "Sergipe"
    TO = "TO", "Tocantins"


class BrazilianRegion(models.TextChoices):
    NORTE = "Norte", _("North")
    NORDESTE = "Nordeste", _("Northeast")
    CENTRO_OESTE = "Centro-Oeste", _("Central-West")
    SUDESTE = "Sudeste", _("Southeast")
    SUL = "Sul", _("South")


class MissionField(models.Model):
    class Status(models.TextChoices):
        ASSISTED = "assisted", _("Assisted")
        PARTIALLY_ASSISTED = "partially_assisted", _("Partially assisted")
        UNASSISTED = "unassisted", _("Unassisted")

    name = models.CharField(_("Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    country = models.CharField(
        _("Country"),
        max_length=2,
        choices=COUNTRY_CHOICES,
        default="BR",
    )
    region = models.CharField(
        _("Region"), max_length=20, choices=BrazilianRegion.choices, blank=True
    )
    state = models.CharField(
        _("State"), max_length=2, choices=BrazilianState.choices, blank=True
    )
    population = models.PositiveIntegerField(_("Approximate population"), default=0)
    missionaries_needed = models.PositiveIntegerField(
        _("Missionaries needed"),
        default=1,
        help_text=_("Number of missionaries needed to serve this field"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.UNASSISTED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_current_missionaries_count(self):
        """Retorna o número de missionários atualmente trabalhando neste campo (com adoções ativas)"""
        if not self.pk:
            return 0
        from django.db.models import Q

        return (
            self.missionaries.model.objects.filter(
                Q(adoptions__mission_field=self, adoptions__status="active")
                | Q(mission_fields=self, adoptions__status="active")
            )
            .distinct()
            .count()
        )

    def get_calculated_status(self):
        """Calcula o status baseado no número de missionários alocados vs necessários"""
        current = self.get_current_missionaries_count()
        needed = self.missionaries_needed

        if current >= needed:
            return self.Status.ASSISTED
        elif current == 0:
            return self.Status.UNASSISTED
        else:
            return self.Status.PARTIALLY_ASSISTED

    def save(self, *args, **kwargs):
        self.status = self.get_calculated_status()
        super().save(*args, **kwargs)


class Location(models.Model):
    mission_field = models.ForeignKey(
        MissionField,
        on_delete=models.CASCADE,
        related_name="locations",
    )
    name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.mission_field.name})"


class Missionary(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="missionary_profile",
        verbose_name=_("User"),
        help_text=_("Login account linked to this missionary profile"),
    )
    name = models.CharField(_("Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    city = models.CharField(_("City"), max_length=100, blank=True)
    state = models.CharField(
        _("State"), max_length=2, choices=BrazilianState.choices, blank=True
    )
    photo = models.ImageField(_("Photo"), upload_to="missionaries/", blank=True)
    mission_fields = models.ManyToManyField(
        MissionField,
        related_name="missionaries",
        blank=True,
        verbose_name=_("Mission fields"),
    )
    is_public = models.BooleanField(
        _("Show on public site"),
        default=False,
        help_text=_("Defines if the missionary appears on the public site listing"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Missionary")
        verbose_name_plural = _("Missionaries")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Investor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="investor_profile",
        verbose_name=_("User"),
        help_text=_("Login account linked to this investor profile"),
    )
    name = models.CharField(_("Name"), max_length=200)
    city = models.CharField(_("City"), max_length=100, blank=True)
    state = models.CharField(
        _("State"), max_length=2, choices=BrazilianState.choices, blank=True
    )
    contact_email = models.EmailField(_("Contact email"), blank=True)
    contact_phone = models.CharField(_("Contact phone"), max_length=20, blank=True)
    display_full_name = models.BooleanField(
        _("Display full name"),
        default=True,
        help_text=_(
            "If unchecked, only the first and last letters of the name will be displayed publicly"
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Investor")
        verbose_name_plural = _("Investors")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_display_name(self):
        """Retorna o nome para exibição pública, respeitando a preferência de privacidade"""
        if self.display_full_name:
            return self.name
        if not self.name:
            return ""
        if len(self.name) == 1:
            return self.name
        return f"{self.name[0]}...{self.name[-1]}"


class Adoption(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        ACTIVE = "active", _("Active")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")

    missionary = models.ForeignKey(
        Missionary,
        on_delete=models.CASCADE,
        related_name="adoptions",
        verbose_name=_("Missionary"),
    )
    investor = models.ForeignKey(
        Investor,
        on_delete=models.CASCADE,
        related_name="adoptions",
        verbose_name=_("Investor"),
    )
    mission_field = models.ForeignKey(
        MissionField,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="adoptions",
        verbose_name=_("Mission Field"),
    )
    monthly_value = models.DecimalField(
        _("Monthly amount (R$)"),
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    start_date = models.DateField(_("Start date"))
    end_date = models.DateField(_("End date"), null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Adoption")
        verbose_name_plural = _("Adoptions")
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.investor.name} -> {self.missionary.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.mission_field_id:
            field = self.mission_field
            field.status = field.get_calculated_status()
            MissionField.objects.filter(pk=field.pk).update(status=field.status)

    def delete(self, *args, **kwargs):
        field = self.mission_field
        super().delete(*args, **kwargs)
        if field:
            field.status = field.get_calculated_status()
            MissionField.objects.filter(pk=field.pk).update(status=field.status)


class MissionFieldRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")

    missionary = models.ForeignKey(
        Missionary,
        on_delete=models.CASCADE,
        related_name="field_requests",
        verbose_name=_("Missionary"),
    )
    mission_field = models.ForeignKey(
        MissionField,
        on_delete=models.CASCADE,
        related_name="requests",
        verbose_name=_("Mission Field"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    message = models.TextField(
        _("Message"),
        blank=True,
        help_text=_(
            "Optional message from the missionary about interest in this field"
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(_("Reviewed at"), null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_field_requests",
        verbose_name=_("Reviewed by"),
    )

    class Meta:
        verbose_name = _("Mission Field Request")
        verbose_name_plural = _("Mission Field Requests")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["missionary", "mission_field"],
                name="unique_missionary_field_request",
            ),
        ]

    def __str__(self):
        return f"{self.missionary.name} -> {self.mission_field.name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status == self.Status.APPROVED:
            self.missionary.mission_fields.add(self.mission_field)
            if self.mission_field_id:
                field = self.mission_field
                field.status = field.get_calculated_status()
                MissionField.objects.filter(pk=field.pk).update(status=field.status)
