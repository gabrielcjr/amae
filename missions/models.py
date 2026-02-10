from django.db import models

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
    NORTE = "Norte", "Norte"
    NORDESTE = "Nordeste", "Nordeste"
    CENTRO_OESTE = "Centro-Oeste", "Centro-Oeste"
    SUDESTE = "Sudeste", "Sudeste"
    SUL = "Sul", "Sul"


class MissionField(models.Model):
    class Status(models.TextChoices):
        ASSISTED = "assisted", "Assistido"
        UNASSISTED = "unassisted", "Não assistido"

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    country = models.CharField(
        "País",
        max_length=2,
        choices=COUNTRY_CHOICES,
        default="BR",
    )
    region = models.CharField(
        max_length=20, choices=BrazilianRegion.choices, blank=True
    )
    state = models.CharField(max_length=2, choices=BrazilianState.choices, blank=True)
    population = models.PositiveIntegerField("População aproximada", default=0)
    status = models.CharField(
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
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2, choices=BrazilianState.choices)
    photo = models.ImageField(upload_to="missionaries/", blank=True)
    mission_fields = models.ManyToManyField(
        MissionField,
        related_name="missionaries",
        blank=True,
    )
    is_public = models.BooleanField(
        "Exibir no site público",
        default=False,
        help_text="Define se o missionário aparece na listagem pública do site",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "missionaries"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Investor(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2, choices=BrazilianState.choices)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    display_full_name = models.BooleanField(
        "Exibir nome completo",
        default=True,
        help_text="Se desmarcado, apenas a primeira e última letra do nome serão exibidas no site público",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "investors"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_display_name(self):
        """Retorna o nome para exibição pública, respeitando a preferência de privacidade"""
        if self.display_full_name:
            return self.name
        # Pega a primeira e última letra do nome
        if len(self.name) <= 1:
            return self.name[0] if self.name else ""
        return f"{self.name[0]}...{self.name[-1]}"


class Adoption(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Ativo"
        COMPLETED = "completed", "Concluído"
        CANCELLED = "cancelled", "Cancelado"

    missionary = models.ForeignKey(
        Missionary,
        on_delete=models.CASCADE,
        related_name="adoptions",
    )
    investor = models.ForeignKey(
        Investor,
        on_delete=models.CASCADE,
        related_name="adoptions",
        verbose_name="Investidor",
    )
    mission_field = models.ForeignKey(
        MissionField,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="adoptions",
        verbose_name="Campo Missionário",
    )
    monthly_value = models.DecimalField(
        "Valor mensal (R$)",
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.investor.name} -> {self.missionary.name}"
