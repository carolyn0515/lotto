from django.contrib import admin

from .models import Draw, Ticket, WinningResult

admin.site.register(Draw)
admin.site.register(Ticket)
admin.site.register(WinningResult)