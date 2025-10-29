"""
Forms for the Discovery Survey - broken into logical sections for a multi-step form.
"""
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import DiscoverySurvey


class SurveySection1Form(forms.ModelForm):
    """Section 1: About You - Great Things"""
    
    class Meta:
        model = DiscoverySurvey
        fields = ['great_things_about_you']
        widgets = {
            'great_things_about_you': forms.Textarea(attrs={'rows': 5, 'placeholder': 'What do people appreciate about you? What do people like and admire about you?'}),
        }


class SurveySection2Form(forms.ModelForm):
    """Section 2: Your Team & Important People"""
    
    class Meta:
        model = DiscoverySurvey
        fields = ['people_closest_to_you']
        widgets = {
            'people_closest_to_you': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Who are the people on your team? At home, at school, friends...'}),
        }


class SurveySection3Form(forms.ModelForm):
    """Section 3: Things You Like To Do"""
    
    class Meta:
        model = DiscoverySurvey
        fields = [
            'hobbies',
            'activities', 
            'entertainment',
            'favorite_food',
            'favorite_people',
            'favorite_outings',
            'routines_and_rituals',
            'good_day_description',
            'bad_day_description',
            'perfect_day_description',
        ]
        widgets = {
            'hobbies': forms.Textarea(attrs={'rows': 3}),
            'activities': forms.Textarea(attrs={'rows': 3}),
            'entertainment': forms.Textarea(attrs={'rows': 3}),
            'favorite_food': forms.Textarea(attrs={'rows': 2}),
            'favorite_people': forms.Textarea(attrs={'rows': 3}),
            'favorite_outings': forms.Textarea(attrs={'rows': 3}),
            'routines_and_rituals': forms.Textarea(attrs={'rows': 3}),
            'good_day_description': forms.Textarea(attrs={'rows': 3}),
            'bad_day_description': forms.Textarea(attrs={'rows': 3}),
            'perfect_day_description': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Describe your perfect day from when you wake up until you go to bed...'}),
        }


class SurveySection4Form(forms.ModelForm):
    """Section 4: Hopes, Dreams & What's Important"""
    
    class Meta:
        model = DiscoverySurvey
        fields = [
            'hopes_and_dreams',
            'important_to_you',
            'important_for_you',
        ]
        widgets = {
            'hopes_and_dreams': forms.Textarea(attrs={'rows': 4}),
            'important_to_you': forms.Textarea(attrs={'rows': 4}),
            'important_for_you': forms.Textarea(attrs={'rows': 4}),
        }


class SurveySection5Form(forms.ModelForm):
    """Section 5: Learning & Growth"""
    
    class Meta:
        model = DiscoverySurvey
        fields = [
            'desired_growth_areas',
            'skills_to_develop',
            'things_want_to_learn',
        ]
        widgets = {
            'desired_growth_areas': forms.Textarea(attrs={'rows': 4}),
            'skills_to_develop': forms.Textarea(attrs={'rows': 4}),
            'things_want_to_learn': forms.Textarea(attrs={'rows': 4}),
        }


class SurveySection6Form(forms.ModelForm):
    """Section 6: School & IEP Experience"""
    
    class Meta:
        model = DiscoverySurvey
        fields = [
            'learned_at_school_liked',
            'learned_at_school_disliked',
            'iep_working',
            'iep_not_working',
        ]
        widgets = {
            'learned_at_school_liked': forms.Textarea(attrs={'rows': 4}),
            'learned_at_school_disliked': forms.Textarea(attrs={'rows': 4}),
            'iep_working': forms.Textarea(attrs={'rows': 4, 'placeholder': 'List 3 ways your IEP is working for you...'}),
            'iep_not_working': forms.Textarea(attrs={'rows': 4, 'placeholder': 'List 3 ways your IEP isn\'t working... How can we support you?'}),
        }


class SurveySection7Form(forms.ModelForm):
    """Section 7: Communication"""
    
    communication_style = forms.CharField(
        label="Communication Style",
        required=False,
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'e.g., Uses words, sign language, gestures, devices, pictures...'}),
        help_text="Stores communication preferences: words, sign language, gestures, devices, etc."
    )
    
    class Meta:
        model = DiscoverySurvey
        fields = [
            'how_communicate_needs',
            'what_makes_you_happy',
            'how_communicate_happy',
            'what_makes_you_sad',
            'how_communicate_sad',
            'communication_style',
        ]
        widgets = {
            'how_communicate_needs': forms.Textarea(attrs={'rows': 3}),
            'what_makes_you_happy': forms.Textarea(attrs={'rows': 3}),
            'how_communicate_happy': forms.Textarea(attrs={'rows': 2}),
            'what_makes_you_sad': forms.Textarea(attrs={'rows': 3}),
            'how_communicate_sad': forms.Textarea(attrs={'rows': 2}),
        }


class SurveySection8Form(forms.ModelForm):
    """Section 8: Learning Preferences"""
    
    learning_style = forms.CharField(
        label="How do you like to learn?",
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g., Visual, auditory, kinesthetic, hands-on...'}),
        help_text="How do you like to learn? Visual, auditory, kinesthetic, etc."
    )
    
    class Meta:
        model = DiscoverySurvey
        fields = [
            'learning_style',
            'working_environment_preferences',
            'virtual_learning_help',
            'supportive_devices',
        ]
        widgets = {
            'working_environment_preferences': forms.Textarea(attrs={'rows': 3}),
            'virtual_learning_help': forms.Textarea(attrs={'rows': 3}),
            'supportive_devices': forms.Textarea(attrs={'rows': 2}),
        }


class SurveySection9Form(forms.ModelForm):
    """Section 9: Staff Preferences"""
    
    class Meta:
        model = DiscoverySurvey
        fields = [
            'ideal_staff_characteristics',
            'disliked_staff_characteristics',
        ]
        widgets = {
            'ideal_staff_characteristics': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What would you like in a staff? Ideal person?'}),
            'disliked_staff_characteristics': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What would you not like to have in a staff?'}),
        }


class SurveySection10Form(forms.ModelForm):
    """Section 10: Employment & Career Goals"""
    
    available_to_work_on = forms.CharField(
        label="When are you available to work?",
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., Weekdays, weekends, mornings, afternoons...'}),
        help_text="Days/times available for work"
    )
    
    class Meta:
        model = DiscoverySurvey
        fields = [
            'prior_jobs',
            'jobs_interested_in',
            'dream_job',
            'employment_goals',
            'available_to_work_on',
            'hours_per_week_working',
        ]
        widgets = {
            'prior_jobs': forms.Textarea(attrs={'rows': 3}),
            'jobs_interested_in': forms.Textarea(attrs={'rows': 3}),
            'dream_job': forms.Textarea(attrs={'rows': 4}),
            'employment_goals': forms.Textarea(attrs={'rows': 4}),
            'hours_per_week_working': forms.TextInput(attrs={'placeholder': 'e.g., 10-15 hours'}),
        }


class SurveySection11Form(forms.ModelForm):
    """Section 11: Why Inclusive World & Additional Info"""
    
    how_heard_about_us = forms.CharField(
        label="How did you hear about us?",
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., Family/Friends, Social Media, Internet Search, Events...'}),
        help_text="Sources: Family/Friends, Social Media, etc."
    )
    
    class Meta:
        model = DiscoverySurvey
        fields = [
            'why_interested_in_iw',
            'goals_and_expectations',
            'community_activities_interest',
            'has_ged_or_diploma',
            'training_courses_completed',
            'how_heard_about_us',
        ]
        widgets = {
            'why_interested_in_iw': forms.Textarea(attrs={'rows': 4}),
            'goals_and_expectations': forms.Textarea(attrs={'rows': 4}),
            'community_activities_interest': forms.Textarea(attrs={'rows': 3}),
            'training_courses_completed': forms.Textarea(attrs={'rows': 2}),
        }


class SurveySection12Form(forms.ModelForm):
    """Section 12: Support Needs & Final Info"""
    
    class Meta:
        model = DiscoverySurvey
        fields = [
            'risk_factors',
            'day_program_recommendations',
            'form_helper',
        ]
        widgets = {
            'risk_factors': forms.Textarea(attrs={'rows': 3}),
            'day_program_recommendations': forms.Textarea(attrs={'rows': 4}),
            'form_helper': forms.TextInput(attrs={'placeholder': 'Who helped you complete this survey?'}),
        }
