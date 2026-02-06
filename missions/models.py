from django.db import models


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
    region = models.CharField(
        max_length=20, choices=BrazilianRegion.choices, blank=True
    )
    state = models.CharField(max_length=2, choices=BrazilianState.choices)
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "missionaries"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Church(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2, choices=BrazilianState.choices)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    denomination = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "churches"
        ordering = ["name"]

    def __str__(self):
        return self.name


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
    church = models.ForeignKey(
        Church,
        on_delete=models.CASCADE,
        related_name="adoptions",
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
        return f"{self.church.name} -> {self.missionary.name}"
