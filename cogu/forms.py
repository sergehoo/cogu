from django import forms
from django.core.exceptions import ValidationError
from django_select2.forms import Select2MultipleWidget
from django.utils.translation import gettext_lazy as _
from cogu.models import Patient, MajorEvent, SanitaryIncident
from django.contrib.gis.geos import Point


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = '__all__'
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'datepicker'}),
            'date_deces': forms.DateInput(attrs={'type': 'date', 'class': 'datepicker'}),
            'contact': forms.TextInput(attrs={'placeholder': 'Ex: 0703123456'}),
            'accompagnateur_contact': forms.TextInput(attrs={'placeholder': 'Ex: 0504123456'}),
            'status': forms.Select(attrs={'class': 'browser-default'}),
            'commune': forms.Select(attrs={'class': 'browser-default'}),
            'cause_deces': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des labels
        self.fields['patient_mineur'].label = "Patient mineur (moins de 18 ans)"
        self.fields['accompagnateur'].label = "Nom de l'accompagnateur"
        self.fields['accompagnateur_nature'].label = "Lien avec l'accompagnateur"

        # Champs obligatoires
        self.fields['nom'].required = True
        self.fields['prenoms'].required = True
        self.fields['sexe'].required = True
        self.fields['date_naissance'].required = True

    def clean_contact(self):
        contact = self.cleaned_data.get('contact')
        # Ajouter ici une validation personnalisée du numéro de contact
        return contact


class MajorEventForm(forms.ModelForm):
    class Meta:
        model = MajorEvent
        fields = '__all__'
        widgets = {
            'location': forms.Textarea(attrs={'cols': 80, 'rows': 20}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class SanitaryIncidentForm(forms.ModelForm):
    location_text = forms.CharField(
        required=False,
        label="Coordonnées GPS",
        widget=forms.TextInput(attrs={
            "placeholder": "POINT(longitude latitude)",
            "class": "form-control",
            "name": "auto_location",
            "id": "location_text_field"  # 👈 Important pour le JS
        }),
        help_text="Format : POINT(longitude latitude)"
    )
    auto_location = forms.CharField(required=False, widget=forms.HiddenInput())
    patients_related = forms.ModelMultipleChoiceField(
        queryset=Patient.objects.all(),
        required=False,
        widget=Select2MultipleWidget(attrs={"class": "form-select select2-multiple"}),
        label="Patients concernés"
    )

    class Meta:
        model = SanitaryIncident
        exclude = ['location']  # on utilise location_text à la place
        widgets = {
            'incident_type': forms.Select(attrs={'class': 'form-select'}),
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.Select(attrs={'class': 'form-select'}),
            'number_of_people_involved': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'outcome': forms.Select(attrs={'class': 'form-select'}),
            'event': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_location_text(self):
        location_str = self.cleaned_data.get("location_text")
        auto_str = self.cleaned_data.get("auto_location")

        if location_str:
            try:
                if not location_str.startswith("POINT(") or not location_str.endswith(")"):
                    raise ValueError
                lon, lat = map(float, location_str[6:-1].split())
                return Point(lon, lat)
            except Exception:
                raise forms.ValidationError("Le format est invalide. Utilisez : POINT(longitude latitude).")

        elif auto_str:
            try:
                if not auto_str.startswith("POINT(") or not auto_str.endswith(")"):
                    raise ValueError
                lon, lat = map(float, auto_str[6:-1].split())
                return Point(lon, lat)
            except Exception:
                raise forms.ValidationError("Impossible d’utiliser la localisation automatique.")

        raise forms.ValidationError("Veuillez renseigner ou autoriser votre position GPS.")

    def clean_number_of_people_involved(self):
        nb = self.cleaned_data.get("number_of_people_involved")
        if nb is not None and nb <= 0:
            raise forms.ValidationError("Le nombre de personnes doit être supérieur à zéro.")
        return nb

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.location = self.cleaned_data.get("location_text")
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class PublicIncidentForm(forms.ModelForm):
    location_text = forms.CharField(
        required=False,
        label="Coordonnées GPS",
        widget=forms.TextInput(attrs={
            "placeholder": "POINT(longitude latitude)",
            "class": "form-control",
            "id": "location_text_field"  # 👈 Important pour le JS
        }),
        help_text="Format : POINT(longitude latitude)"
    )

    auto_location = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = SanitaryIncident
        exclude = ['location', 'patients_related', 'status', 'source', 'posted_by', 'validated_by', 'outcome',
                   'message', 'event',
                   'created_at']  # handled manually or auto
        widgets = {
            'incident_type': forms.Select(attrs={'class': 'form-select'}),
            'date_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local', 'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.Select(attrs={'class': 'form-select'}),
            'number_of_people_involved': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'outcome': forms.Select(attrs={'class': 'form-select'}),
            'event': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_location_text(self):
        location_raw = self.cleaned_data.get("location_text")
        auto_raw = self.cleaned_data.get("auto_location")

        def parse_point(raw):
            if isinstance(raw, Point):
                return raw
            if not isinstance(raw, str):
                raise ValidationError("Format invalide.")
            if not raw.startswith("POINT(") or not raw.endswith(")"):
                raise ValidationError("Format invalide. Exemple attendu : POINT(-3.978 5.336)")
            try:
                lon, lat = map(float, raw[6:-1].split())
                return Point(lon, lat)
            except Exception:
                raise ValidationError("Coordonnées GPS non valides.")

        if location_raw:
            return parse_point(location_raw)
        elif auto_raw:
            return parse_point(auto_raw)

        raise ValidationError("Veuillez saisir ou autoriser votre position GPS.")

    def clean_number_of_people_involved(self):
        nb = self.cleaned_data.get("number_of_people_involved")
        if nb is not None and nb <= 0:
            raise forms.ValidationError("Le nombre de personnes doit être supérieur à zéro.")
        return nb

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Récupère la valeur nettoyée (déjà un objet Point ou None)
        instance.location = self.cleaned_data.get("location_text")

        if commit:
            instance.save()
            self.save_m2m()

        return instance
