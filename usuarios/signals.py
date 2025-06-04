#usuarios/signals.py

# Signals para criar perfis automaticamente
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Usuario, PerfilSeguranca

@receiver(post_save, sender=Usuario)
def criar_perfil_seguranca(sender, instance, created, **kwargs):
    """
    Signal para criar automaticamente um perfil de segurança
    quando um novo usuário é criado
    """
    if created:
        PerfilSeguranca.objects.create(usuario=instance)