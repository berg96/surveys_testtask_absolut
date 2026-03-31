from django.urls import path

from surveys.views import NextQuestionAPIView, SurveyStatsAPIView

urlpatterns = [
    path("surveys/<int:pk>/next-question/", NextQuestionAPIView.as_view(), name="survey-next-question"),
    path("surveys/<int:pk>/stats/", SurveyStatsAPIView.as_view(), name="survey-stats"),
]
