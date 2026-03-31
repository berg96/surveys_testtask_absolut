from rest_framework.exceptions import APIException


class SurveyCompleted(APIException):
    status_code = 409
    default_detail = "Опрос уже завершён."
    default_code = "survey_completed"
