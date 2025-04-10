class PatientListCreateView(generics.ListCreateAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = {
        'nom': ['exact', 'icontains'],
        'prenoms': ['exact', 'icontains'],
        'contact': ['exact'],
        'sexe': ['exact'],
        'commune': ['exact'],
        'status': ['exact'],
        'gueris': ['exact'],
        'decede': ['exact'],
        'created_at': ['gte', 'lte', 'exact'],
    }

    search_fields = ['nom', 'prenoms', 'contact', 'code_patient', 'num_cmu', 'cni_num']
    ordering_fields = ['created_at', 'nom', 'prenoms']
    ordering = ['-created_at']


class PatientRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'code_patient'


class MajorEventListCreateView(generics.ListCreateAPIView):
    queryset = MajorEvent.objects.all()
    serializer_class = MajorEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = {
        'name': ['exact', 'icontains'],
        'start_date': ['gte', 'lte', 'exact'],
        'end_date': ['gte', 'lte', 'exact'],
        'organizer': ['exact', 'icontains'],
    }

    search_fields = ['name', 'description', 'organizer']
    ordering_fields = ['start_date', 'end_date', 'name']
    ordering = ['-start_date']


class MajorEventRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MajorEvent.objects.all()
    serializer_class = MajorEventSerializer
    permission_classes = [permissions.IsAuthenticated]


class IncidentTypeListCreateView(generics.ListCreateAPIView):
    queryset = IncidentType.objects.all()
    serializer_class = IncidentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']


class IncidentTypeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = IncidentType.objects.all()
    serializer_class = IncidentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


class SanitaryIncidentListCreateView(generics.ListCreateAPIView):
    queryset = SanitaryIncident.objects.all()
    serializer_class = SanitaryIncidentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = {
        'incident_type': ['exact'],
        'city': ['exact'],
        'outcome': ['exact'],
        'event': ['exact'],
        'date_time': ['gte', 'lte', 'exact'],
    }

    search_fields = ['description', 'source']
    ordering_fields = ['date_time', 'number_of_people_involved']
    ordering = ['-date_time']


class SanitaryIncidentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SanitaryIncident.objects.all()
    serializer_class = SanitaryIncidentSerializer
    permission_classes = [permissions.IsAuthenticated]