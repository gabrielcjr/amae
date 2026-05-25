from django.conf import settings
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
        PARTIALLY_ASSISTED = "partially_assisted", "Parcialmente assistido"
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
    missionaries_needed = models.PositiveIntegerField(
        "Missionários necessários",
        default=1,
        help_text="Número de missionários necessários para atender este campo",
    )
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

    def get_current_missionaries_count(self):
        """Retorna o número de missionários atualmente trabalhando neste campo (com adoções ativas)"""
        return (
            self.missionaries.filter(
                adoptions__mission_field=self, adoptions__status="active"
            )
            .distinct()
            .count()
        )

    def get_calculated_status(self):
        """Calcula o status baseado no número de missionários alocados vs necessários"""
        current = self.get_current_missionaries_count()
        needed = self.missionaries_needed

        if current == 0:
            return self.Status.UNASSISTED
        elif current >= needed:
            return self.Status.ASSISTED
        else:
            return self.Status.PARTIALLY_ASSISTED

    def save(self, *args, **kwargs):
        if self.pk is not None:
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
        verbose_name="Usuário",
        help_text="Conta de login vinculada a este perfil de missionário",
    )
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
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="investor_profile",
        verbose_name="Usuário",
        help_text="Conta de login vinculada a este perfil de investidor",
    )
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
        if not self.name:
            return ""
        if len(self.name) == 1:
            return self.name
        return f"{self.name[0]}...{self.name[-1]}"


class Adoption(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
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


class MissionFieldRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        APPROVED = "approved", "Aprovado"
        REJECTED = "rejected", "Rejeitado"

    missionary = models.ForeignKey(
        Missionary,
        on_delete=models.CASCADE,
        related_name="field_requests",
        verbose_name="Missionário",
    )
    mission_field = models.ForeignKey(
        MissionField,
        on_delete=models.CASCADE,
        related_name="requests",
        verbose_name="Campo Missionário",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    message = models.TextField(
        "Mensagem",
        blank=True,
        help_text="Mensagem opcional do missionário sobre o interesse neste campo",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField("Revisado em", null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_field_requests",
        verbose_name="Revisado por",
    )

    class Meta:
        verbose_name = "Solicitação de Campo"
        verbose_name_plural = "Solicitações de Campos"
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
