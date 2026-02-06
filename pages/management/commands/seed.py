from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Carrega todas as fixtures do diretório fixtures/"

    def add_arguments(self, parser):
        parser.add_argument(
            "--refresh",
            action="store_true",
            help="Limpa as tabelas antes de carregar as fixtures",
        )

    def handle(self, *args, **options):
        fixtures_dir = settings.BASE_DIR / "fixtures"

        # Order matters: tables with foreign keys must be loaded after their dependencies
        fixture_order = [
            "missions_missionfield",
            "missions_location",
            "missions_missionary",
            "missions_church",
            "missions_adoption",
            "pages_page",
            "pages_faq",
            "pages_testimonial",
            "pages_siteimage",
            "finance_category",
        ]

        if options["refresh"]:
            self.stdout.write("Limpando tabelas...")
            from finance.models import FinancialCategory, Transaction
            from missions.models import (
                Adoption,
                Church,
                Location,
                Missionary,
                MissionField,
            )
            from pages.models import FAQ, ContactMessage, Page, SiteImage, Testimonial

            Transaction.objects.all().delete()
            FinancialCategory.objects.all().delete()
            Adoption.objects.all().delete()
            Church.objects.all().delete()
            Missionary.objects.all().delete()
            Location.objects.all().delete()
            MissionField.objects.all().delete()
            Testimonial.objects.all().delete()
            FAQ.objects.all().delete()
            Page.objects.all().delete()
            SiteImage.objects.all().delete()
            ContactMessage.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Tabelas limpas."))

        loaded = 0
        for name in fixture_order:
            path = fixtures_dir / f"{name}.json"
            if path.exists():
                call_command("loaddata", str(path), verbosity=0)
                self.stdout.write(f"  {name}.json")
                loaded += 1

        self.stdout.write(
            self.style.SUCCESS(f"\n{loaded} fixtures carregadas com sucesso.")
        )
