"""
Formularios para el sistema de usuarios
"""
from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class LoginForm(AuthenticationForm):
    """
    Formulario de inicio de sesión personalizado
    """
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Usuario",
            "autofocus": True,
        }),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Contraseña",
        }),
    )


class UsuarioCreateForm(UserCreationForm):
    """
    Formulario para crear nuevos usuarios
    """

    class Meta:
        model = Usuario
        # Ajusta esta lista si tu modelo tiene otros campos
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "rol",
            "telefono",
            "whatsapp",
            "activo",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        # Passwords un poco más bonitos
        self.fields["password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Contraseña",
        })
        self.fields["password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Confirmar contraseña",
        })


class UsuarioUpdateForm(forms.ModelForm):
    """
    Formulario para editar usuarios existentes
    """

    class Meta:
        model = Usuario
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "rol",
            "telefono",
            "whatsapp",
            "activo",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class CambiarPasswordForm(forms.Form):
    """
    Formulario para que un admin cambie la contraseña de cualquier usuario.
    """
    password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Nueva contraseña",
            "autocomplete": "new-password",
        }),
        min_length=6,
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Confirmar contraseña",
            "autocomplete": "new-password",
        }),
        min_length=6,
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data
