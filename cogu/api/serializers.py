from rest_framework import serializers

from cogu.models import Patient, MajorEvent, IncidentType, SanitaryIncident, DistrictSanitaire


class PatientSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()
    contact_formatte = serializers.SerializerMethodField()
    accompagnateur_contact_formatte = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = '__all__'

    def get_age(self, obj):
        return obj.calculate_age

    def get_contact_formatte(self, obj):
        return obj.contact_formatte

    def get_accompagnateur_contact_formatte(self, obj):
        return obj.accompagnateur_contact_formatte


class MajorEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = MajorEvent
        fields = '__all__'


class IncidentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentType
        fields = '__all__'


class SanitaryIncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SanitaryIncident
        fields = '__all__'


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = DistrictSanitaire
        fields = '__all__'
