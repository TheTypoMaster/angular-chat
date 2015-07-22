from django.contrib import admin
from chat.models import *

# Register your models here.
class TpaAdmin(admin.ModelAdmin):
    list_display = ("id","name", "domain", "timeout_chating")
admin.site.register(Tpa, TpaAdmin)

class ChatUserAdmin(admin.ModelAdmin):
    list_display = ("name", "avatar", "gender", "age", "country", "city", "culture", "is_online", "image", "profile_url", "is_camera_active", "is_invisible", "tpa")
    search_fields = ("name", "country", "city")
    list_filter = ("tpa", "is_online", "gender")
    def avatar(self, instance):
        return u'<img width="100" src="{0}" />'.format(instance.image)
    avatar.allow_tags = True
admin.site.register(ChatUser, ChatUserAdmin)

class ChatMessageAdminInline(admin.TabularInline):
    model = ChatMessage
    fields = ["message", "user", "avatar"]
    readonly_fields = ["message", "user", "avatar"]
    def avatar(self, instance):
        return u'<img width="100" src="{0}" />'.format(instance.user.image)
    avatar.allow_tags = True


class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("duration", "sign", "tpa", "is_charging")
    search_fields = ("sign", )
    list_filter = ("tpa", )
    inlines = [
        ChatMessageAdminInline,
    ]
    def participants(self, instance):
        out = ''
        for u in instance.get_participants():
            out = out + u'<img title="{1}" width="100" src="{0}" />'.format(u.image, u.name)
        return out
    participants.allow_tags = True
admin.site.register(ChatRoom, ChatRoomAdmin)

class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "message", "tpa")
    list_filter = ("tpa", "room" )
admin.site.register(ChatMessage, ChatMessageAdmin)


class ChatTransactionsAdmin(admin.ModelAdmin):
    list_display = ("man", "woman", "room", "tpa")
    list_filter = ("tpa", "room", "tpa")
admin.site.register(ChatTransactions, ChatTransactionsAdmin)


class ChatTemplatesAdmin(admin.ModelAdmin):
    list_display = ("message_ru", "message_en")
admin.site.register(ChatTemplates, ChatTemplatesAdmin)


class ChatStopwordAdmin(admin.ModelAdmin):
    list_display = ("word", "replace")
admin.site.register(ChatStopword, ChatStopwordAdmin)

class ChatContactsAdmin(admin.ModelAdmin):
    list_display = ("owner", "contact")
admin.site.register(ChatContacts, ChatContactsAdmin)
