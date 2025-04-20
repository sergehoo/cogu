from allauth.account.forms import SignupForm
from django import forms
from django.core.exceptions import ValidationError
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from django_select2.forms import Select2MultipleWidget
from django.utils.translation import gettext_lazy as _
from cogu.models import Patient, MajorEvent, SanitaryIncident, ContactMessage
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
        label="Coordonnées GPS (manuel)",
        widget=forms.TextInput(attrs={
            "placeholder": "POINT(longitude latitude)",
            "class": "form-control",
            "name": "auto_location",
            "id": "location_text_field"
        }),
        help_text="Format : POINT(longitude latitude) - Exemple: POINT(-1.654 12.345)"
    )

    auto_location = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        label="Coordonnées GPS automatiques"
    )

    patients_related = forms.ModelMultipleChoiceField(
        queryset=Patient.objects.all(),
        required=False,
        widget=Select2MultipleWidget(
            attrs={"class": "form-control select2-multiple", 'id': 'kt_select2_3', 'name': 'param'}),
        label="Patients concernés",
        help_text="Sélectionnez un ou plusieurs patients concernés par cet incident"
    )

    class Meta:
        model = SanitaryIncident
        exclude = ['location', 'status', 'message', 'posted_by', 'validated_by']
        labels = {
            'incident_type': "Type d'incident",
            'date_time': "Date et heure de l'incident",
            'description': "Description détaillée",
            'city': "Ville/Commune",
            'number_of_people_involved': "Nombre de personnes impliquées",
            'outcome': "Conséquence Majeure",
            'event': "Événement associé",
            'source': "Source de l'information",
            'deces_nbr': "Nombre de décès",
            'blessure_nbr': " nombre de blessés"
        }
        widgets = {
            'incident_type': forms.Select(
                attrs={'class': 'form-control select2', 'id': 'kt_select2_2', 'name': 'param'}),
            'date_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'help_text': "Sélectionnez la date et l'heure exactes de l'incident"
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': "Décrivez l'incident en détail..."
            }),
            'city': forms.Select(attrs={
                'class': 'form-control',
                'id': "kt_select2_1",
                "name": "param",
                'help_text': "Sélectionnez la localité concernée"
            }),
            'centre_sante': forms.Select(attrs={
                'class': 'form-control',
                'id': "kt_select2_1",
                "name": "param",
                'help_text': "Sélectionnez la localité concernée"
            }),
            'number_of_people_involved': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'help_text': "Nombre total de personnes affectées"
            }),
            'outcome': forms.Select(attrs={
                'class': 'form-select',
                'help_text': "Quel a été le résultat de cet incident?"
            }),
            'deces_nbr': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'help_text': "Nombre total de personnes affectées"
            }),
            'blessure_nbr': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'help_text': "Nombre total de personnes affectées"
            }),
            'event': forms.Select(attrs={
                'class': 'form-select',
                'help_text': "Sélectionnez l'événement associé si applicable"
            }),
            'source': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Qui a rapporté cet incident?",
                'help_text': "Personne ou entité ayant signalé l'incident"
            }),
        }


class PublicIncidentForm(forms.ModelForm):
    location_text = forms.CharField(
        required=False,
        label="Coordonnées GPS (manuel)",
        widget=forms.TextInput(attrs={
            "placeholder": "POINT(longitude latitude)",
            "class": "form-control",
            "id": "location_text_field"
        }),
        help_text="Format : POINT(longitude latitude) - Exemple: POINT(-1.654 12.345)"
    )

    auto_location = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        label="Coordonnées GPS automatiques"
    )

    class Meta:
        model = SanitaryIncident
        exclude = ['location', 'patients_related', 'status', 'source', 'posted_by',
                   'validated_by', 'outcome', 'message', 'event', 'created_at']
        labels = {
            'incident_type': "Type d'incident",
            'date_time': "Date et heure de l'incident",
            'description': "Description détaillée",
            'city': "Ville/Commune",
            'number_of_people_involved': "Nombre de personnes impliquées",
        }
        widgets = {
            'incident_type': forms.Select(attrs={
                'class': 'form-select',
                'help_text': "Sélectionnez le type d'incident sanitaire"
            }),
            'date_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'help_text': "Quand cet incident s'est-il produit?"
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': "Décrivez ce que vous avez observé...",
                'help_text': "Décrivez l'incident avec le plus de détails possible"
            }),
            'city': forms.Select(attrs={
                'class': 'form-select',
                'help_text': "Dans quelle localité cet incident s'est-il produit?"
            }),
            'number_of_people_involved': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'help_text': "Nombre approximatif de personnes affectées"
            }),
        }


class ContactForm(forms.ModelForm):
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre nom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Votre email'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sujet'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Votre message'}),
        }

        def clean_honeypot(self):
            data = self.cleaned_data.get('honeypot')
            if data:
                raise forms.ValidationError("Bot détecté.")
            return data


class CustomSignupForm(SignupForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

    def save(self, request):
        return super().save(request)
