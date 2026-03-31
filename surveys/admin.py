from django.contrib import admin
from django.db.models import Count

from .models import Survey, Question, Answer, SurveySession, UserAnswer


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 3
    ordering = ('order',)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    ordering = ('order',)


class SurveyStatusFilter(admin.SimpleListFilter):
    title = 'Статус прохождений'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('has_finished', 'Завершённые'),
            ('none_finished', 'Незавершённые'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'has_finished':
            return queryset.filter(sessions__finished_at__isnull=False).distinct()
        if self.value() == 'none_finished':
            return queryset.exclude(sessions__finished_at__isnull=False).distinct()


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'questions_count', 'sessions_count')
    list_filter = ('author', SurveyStatusFilter)
    search_fields = ('title', 'author__username')
    inlines = (QuestionInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _questions_count=Count('questions'),
            _sessions_count=Count('sessions'),
        )

    @admin.display(description='Кол-во вопросов')
    def questions_count(self, survey):
        return survey._questions_count

    @admin.display(description='Кол-во прохождений')
    def sessions_count(self, survey):
        return survey._sessions_count


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'survey', 'order', 'allow_custom_answer')
    list_filter = ('survey',)
    search_fields = ('text',)
    inlines = (AnswerInline,)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'order')
    search_fields = ('text',)
    list_filter = ('question__survey',)


@admin.register(SurveySession)
class SurveySessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'survey', 'started_at', 'finished_at')
    list_filter = ('survey', 'user')
    readonly_fields = ('started_at', 'finished_at')


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('session', 'question', 'chosen_answer', 'custom_text', 'answered_at')
    search_fields = ('session__user__username',)
