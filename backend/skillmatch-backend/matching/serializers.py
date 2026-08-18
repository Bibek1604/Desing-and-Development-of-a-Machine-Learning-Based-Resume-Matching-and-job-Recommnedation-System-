from rest_framework import serializers

from jobs.serializers import JobSerializer


class JobMatchSerializer(serializers.Serializer):
    job = JobSerializer()
    score = serializers.IntegerField()
    similarity = serializers.IntegerField()
    matched_skills = serializers.ListField(child=serializers.CharField())
    # Classifier output, exposed separately so no client can mistake it for the
    # "% match" figure. Null when no trained artifact is loaded.
    shortlist_probability = serializers.FloatField(allow_null=True, required=False)


class CandidateMatchSerializer(serializers.Serializer):
    # Flat fields (backwards compatible with earlier clients).
    candidate_id = serializers.IntegerField(source="candidate.id")
    candidate_email = serializers.EmailField(source="candidate.email")
    candidate_name = serializers.CharField(source="candidate.full_name")
    # Nested object consumed by the frontend employer page.
    candidate = serializers.SerializerMethodField()
    score = serializers.IntegerField()
    similarity = serializers.IntegerField()
    matched_skills = serializers.ListField(child=serializers.CharField())
    # Classifier output, exposed separately so no client can mistake it for the
    # "% match" figure. Null when no trained artifact is loaded.
    shortlist_probability = serializers.FloatField(allow_null=True, required=False)

    def get_candidate(self, obj):
        user = obj["candidate"]
        profile = getattr(user, "candidate_profile", None)
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "degree": getattr(profile, "degree", "") or "",
            "university": getattr(profile, "university", "") or "",
            "cgpa": getattr(profile, "cgpa", None),
        }
