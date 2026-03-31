from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import SurveyCompleted
from .models import Survey, SurveySession
from .serializers import ErrorSerializer, QuestionReadSerializer, SurveyStatsSerializer


class NextQuestionAPIView(APIView):
    @extend_schema(
        responses={
            200: QuestionReadSerializer,
            403: OpenApiResponse(description="Доступ запрещён", response=ErrorSerializer),
            404: OpenApiResponse(description="Опрос не найден", response=ErrorSerializer),
            409: OpenApiResponse(description="Конфликт данных (например, опрос завершён)", response=ErrorSerializer),
        },
        description="Получить следующий вопрос",
    )
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

        return Response(QuestionReadSerializer(next_question).data)


class SurveyStatsAPIView(APIView):
    @extend_schema(
        responses={
            200: SurveyStatsSerializer,
            403: OpenApiResponse(description="Доступ запрещён", response=ErrorSerializer),
            404: OpenApiResponse(description="Опрос не найден", response=ErrorSerializer),
        },
        description="Статистика по опросу",
    )
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
