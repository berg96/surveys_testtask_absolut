from rest_framework import serializers

from .models import Answer, Question, Survey


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ("id", "text", "order")


class QuestionReadSerializer(serializers.ModelSerializer):
    choices = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ("id", "text", "order", "allow_custom_answer", "choices")


class SurveySerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()

    class Meta:
        model = Survey
        fields = ("id", "title", "author", "created_at")


class SurveyStatsSerializer(serializers.Serializer):
    total_sessions = serializers.IntegerField()
    finished_sessions = serializers.IntegerField()
    avg_completion_seconds = serializers.FloatField(allow_null=True)
