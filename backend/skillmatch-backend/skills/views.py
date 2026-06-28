from rest_framework import viewsets, permissions

from .models import Skill
from .serializers import SkillSerializer


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    search_fields = ("name", "category")
    filterset_fields = ("category",)
    ordering_fields = ("name",)
