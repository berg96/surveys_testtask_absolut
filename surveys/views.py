from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import SurveyCompleted
from .models import Survey, SurveySession
from .serializers import QuestionReadSerializer, SurveyStatsSerializer


class NextQuestionAPIView(APIView):
    def _get_or_create_session(self, survey, user):
        session, _ = SurveySession.objects.get_or_create(user=user, survey=survey)
        return session

    def get(self, request, pk):
        survey = get_object_or_404(Survey, pk=pk)
        session, _ = SurveySession.objects.get_or_create(user=request.user, survey=survey)
        if session.finished_at:
            raise SurveyCompleted()

        answered_ids = session.answers.values_list("question_id", flat=True)
        next_question = survey.questions.exclude(id__in=answered_ids).prefetch_related("choices").first()
        if not next_question:
            session.finished_at = timezone.now()
            session.save()
            raise SurveyCompleted()

        serializer = QuestionReadSerializer(next_question)
        return Response(serializer.data)


class SurveyStatsAPIView(APIView):
    def get(self, request, pk):
        survey = get_object_or_404(Survey, pk=pk)
        if survey.author != request.user:
            return Response(
                {"detail": "Статистику может посмотреть только автор опроса."},
                status=status.HTTP_403_FORBIDDEN,
            )

        agg = survey.sessions.aggregate(
            total_sessions=Count("id"),
            finished_sessions=Count("id", filter=Q(finished_at__isnull=False)),
            avg_completion=Avg(
                ExpressionWrapper(F("finished_at") - F("started_at"), output_field=DurationField()),
                filter=Q(finished_at__isnull=False),
            ),
        )
        data = {
            "total_sessions": agg["total_sessions"],
            "finished_sessions": agg["finished_sessions"],
            "avg_completion_seconds": agg["avg_completion"].total_seconds() if agg["avg_completion"] else None,
        }
        return Response(SurveyStatsSerializer(data).data)
