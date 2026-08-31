from django.core.management.base import BaseCommand
from main.utils import sync_existing_files_to_library


class Command(BaseCommand):
    help = 'همگام‌سازی فایل‌های موجود با Media Library'

    def add_arguments(self, parser):
        parser.add_argument('--app', type=str, help='نام اپلیکیشن (اختیاری)')
        parser.add_argument('--used-in', type=str, help='برچسب استفاده (اختیاری)')

    def handle(self, *args, **options):
        app = options.get('app', '')
        used_in = options.get('used_in', '')
        
        self.stdout.write('در حال همگام‌سازی فایل‌ها...')
        count = sync_existing_files_to_library(app_label=app, used_in=used_in)
        
        self.stdout.write(self.style.SUCCESS(f'✅ {count} فایل با موفقیت ثبت شد.'))