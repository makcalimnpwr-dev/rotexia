"""
Management command to send automated emails based on schedule
Usage: 
  - python manage.py send_automated_emails (one-time run)
  - python manage.py send_automated_emails --loop (continuous loop, for Render)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.core.models import AutomatedEmail
from apps.core.views import _send_automated_email
import time


class Command(BaseCommand):
    help = 'Send automated emails based on their schedule'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--loop',
            action='store_true',
            help='Run in continuous loop (check every 5 minutes). Use this for Render workers.',
        )

    def handle(self, *args, **options):
        if options['loop']:
            # Render worker için sürekli döngü modu
            self.stdout.write('[LOOP MODE] Starting continuous email check loop (every 5 minutes)...')
            while True:
                try:
                    self._check_and_send_emails()
                except KeyboardInterrupt:
                    self.stdout.write('\n[LOOP MODE] Stopping...')
                    break
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'[LOOP MODE] Error in loop: {str(e)}')
                    )
                # 5 dakika bekle
                self.stdout.write('[LOOP MODE] Sleeping for 5 minutes...')
                time.sleep(5 * 60)  # 5 dakika = 300 saniye
        else:
            # Tek seferlik çalıştırma (Windows Task Scheduler için)
            self._check_and_send_emails()
    
    def _check_and_send_emails(self):
        now = timezone.now()
        self.stdout.write(f'[{now}] Checking automated emails...')
        
        # Aktif otomatik mailleri al
        active_emails = AutomatedEmail.objects.filter(is_active=True)
        
        self.stdout.write(f'Found {active_emails.count()} active automated email(s)')
        
        sent_count = 0
        error_count = 0
        skipped_count = 0
        
        for email in active_emails:
            try:
                self.stdout.write(f'\n--- Checking: {email.subject} (ID: {email.id}) ---')
                self.stdout.write(f'  To: {email.to_email}')
                self.stdout.write(f'  Send time: {email.send_time}')
                self.stdout.write(f'  Period: {email.period}')
                self.stdout.write(f'  Start date: {email.send_start_date}')
                self.stdout.write(f'  End date: {email.send_end_date}')
                self.stdout.write(f'  Last sent: {email.last_sent_at}')
                
                success, message = _send_automated_email(email, force=False)
                if success:
                    sent_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'[OK] Sent: {email.subject} to {email.to_email}')
                    )
                else:
                    # Zamanlama uygun değilse hata değil, sadece log
                    if "henüz" in message.lower() or "gelmedi" in message.lower() or "geçti" in message.lower():
                        skipped_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'[SKIP] Skipped: {email.subject} - {message}')
                        )
                    else:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'[ERROR] Error: {email.subject} - {message}')
                        )
            except Exception as e:
                error_count += 1
                import traceback
                self.stdout.write(
                    self.style.ERROR(f'[EXCEPTION] Exception: {email.subject} - {str(e)}')
                )
                self.stdout.write(traceback.format_exc())
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted: {sent_count} sent, {skipped_count} skipped, {error_count} errors'
            )
        )

