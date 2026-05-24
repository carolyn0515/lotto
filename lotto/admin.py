from django.contrib import admin

from .models import Draw, Ticket, WinningResult, UserProfile

admin.site.register(UserProfile)
admin.site.register(Draw)
admin.site.register(Ticket)
admin.site.register(WinningResult)