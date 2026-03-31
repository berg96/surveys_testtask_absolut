from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class Survey(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название опроса")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="surveys", verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        db_table = "surveys"
        verbose_name = "Опрос"
        verbose_name_plural = "Опросы"

    def __str__(self):
        return f"{self.title} от {self.author} ({self.created_at})"


class Question(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="questions", verbose_name="Опрос")
    text = models.TextField(verbose_name="Текст вопроса")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    allow_custom_answer = models.BooleanField(default=False, verbose_name="Разрешить свой ответ")

    class Meta:
        db_table = "questions"
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ("order",)
        indexes = [
            models.Index(fields=["survey", "order"]),
        ]

    def __str__(self):
        return f"{self.survey.title} - {self.text[:50]} ({self.order}, {self.allow_custom_answer})"


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices", verbose_name="Вопрос")
    text = models.CharField(max_length=255, verbose_name="Текст ответа")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        db_table = "answers"
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"
        ordering = ("order",)
        indexes = [
            models.Index(fields=["question", "order"]),
        ]

    def __str__(self):
        return f"{self.question.text[:50]} - {self.text} ({self.order})"


class SurveySession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions", verbose_name="Пользователь")
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="sessions", verbose_name="Опрос")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Время начала")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Время завершения")

    class Meta:
        db_table = "survey_sessions"
        verbose_name = "Сессия прохождения"
        verbose_name_plural = "Сессии прохождения"
        constraints = [
            models.UniqueConstraint(fields=["user", "survey"], name="unique_user_survey"),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.survey.title} ({self.started_at} - {self.finished_at or "none_finished"})'


class UserAnswer(models.Model):
    session = models.ForeignKey(SurveySession, on_delete=models.CASCADE, related_name="answers", verbose_name="Сессия")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="user_answers", verbose_name="Вопрос")
    chosen_answer = models.ForeignKey(
        Answer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_answers",
        verbose_name="Выбранный вариант",
    )
    custom_text = models.TextField(null=True, blank=True, verbose_name="Свой ответ")
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name="Время ответа")

    class Meta:
        db_table = "user_answers"
        verbose_name = "Ответ пользователя"
        verbose_name_plural = "Ответы пользователей"
        constraints = [models.UniqueConstraint(fields=["session", "question"], name="unique_session_question")]

    def clean(self):
        if not self.chosen_answer and not self.custom_text:
            raise ValidationError("Необходимо выбрать ответ или ввести свой.")

    def __str__(self):
        answer_text = self.chosen_answer.text if self.chosen_answer else self.custom_text
        return f"{self.session.user.username} - {self.question.text[:50]} - {answer_text[:50]} ({self.answered_at})"
