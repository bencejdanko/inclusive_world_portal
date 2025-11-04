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
    
    # Communication style checkboxes stored as JSON
    uses_words = forms.BooleanField(label="Uses words in English/Other Language", required=False)
    can_initiate_conversations = forms.BooleanField(label="Can initiate conversations", required=False)
    communicates_nonverbal = forms.BooleanField(label="Communicates without using words", required=False)
    can_articulate_needs = forms.BooleanField(label="Can clearly articulate needs/desires", required=False)
    uses_sign_language = forms.BooleanField(label="Uses American Sign Language/Other Sign Language", required=False)
    needs_electronic_device = forms.BooleanField(label="Electronic device needed", required=False)
    uses_pictures = forms.BooleanField(label="Uses pictures/picture board", required=False)
    uses_augmented_system = forms.BooleanField(label="Uses augmented communication system", required=False)
    uses_pointing_gesturing = forms.BooleanField(label="Uses pointing and gesturing", required=False)
    other_language = forms.CharField(label="Other language other than English", required=False, widget=forms.TextInput(attrs={'placeholder': 'Specify language...'}))
    communication_other = forms.CharField(label="Other communication methods", required=False, widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Describe any other communication methods...'}))
    
    class Meta:
        model = DiscoverySurvey
        fields = [
            'how_communicate_needs',
            'what_makes_you_happy',
            'how_communicate_happy',
            'what_makes_you_sad',
            'how_communicate_sad',
        ]
        widgets = {
            'how_communicate_needs': forms.Textarea(attrs={'rows': 3}),
            'what_makes_you_happy': forms.Textarea(attrs={'rows': 3}),
            'how_communicate_happy': forms.Textarea(attrs={'rows': 2}),
            'what_makes_you_sad': forms.Textarea(attrs={'rows': 3}),
            'how_communicate_sad': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load communication style from JSON if exists
        if self.instance and self.instance.pk and self.instance.communication_style:
            comm_style = self.instance.communication_style
            if isinstance(comm_style, dict):
                self.fields['uses_words'].initial = comm_style.get('uses_words', False)
                self.fields['can_initiate_conversations'].initial = comm_style.get('can_initiate_conversations', False)
                self.fields['communicates_nonverbal'].initial = comm_style.get('communicates_nonverbal', False)
                self.fields['can_articulate_needs'].initial = comm_style.get('can_articulate_needs', False)
                self.fields['uses_sign_language'].initial = comm_style.get('uses_sign_language', False)
                self.fields['needs_electronic_device'].initial = comm_style.get('needs_electronic_device', False)
                self.fields['uses_pictures'].initial = comm_style.get('uses_pictures', False)
                self.fields['uses_augmented_system'].initial = comm_style.get('uses_augmented_system', False)
                self.fields['uses_pointing_gesturing'].initial = comm_style.get('uses_pointing_gesturing', False)
                self.fields['other_language'].initial = comm_style.get('other_language', '')
                self.fields['communication_other'].initial = comm_style.get('communication_other', '')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Save communication style as JSON
        instance.communication_style = {
            'uses_words': self.cleaned_data.get('uses_words', False),
            'can_initiate_conversations': self.cleaned_data.get('can_initiate_conversations', False),
            'communicates_nonverbal': self.cleaned_data.get('communicates_nonverbal', False),
            'can_articulate_needs': self.cleaned_data.get('can_articulate_needs', False),
            'uses_sign_language': self.cleaned_data.get('uses_sign_language', False),
            'needs_electronic_device': self.cleaned_data.get('needs_electronic_device', False),
            'uses_pictures': self.cleaned_data.get('uses_pictures', False),
            'uses_augmented_system': self.cleaned_data.get('uses_augmented_system', False),
            'uses_pointing_gesturing': self.cleaned_data.get('uses_pointing_gesturing', False),
            'other_language': self.cleaned_data.get('other_language', ''),
            'communication_other': self.cleaned_data.get('communication_other', ''),
        }
        if commit:
            instance.save()
        return instance


class SurveySection8Form(forms.ModelForm):
    """Section 8: Learning Preferences"""
    
    # Learning style checkboxes stored as JSON
    learning_visual = forms.BooleanField(label="Visual learner (pictures, diagrams, charts)", required=False)
    learning_auditory = forms.BooleanField(label="Auditory learner (listening, discussions)", required=False)
    learning_kinesthetic = forms.BooleanField(label="Kinesthetic learner (hands-on, movement)", required=False)
    learning_reading = forms.BooleanField(label="Reading/Writing learner", required=False)
    learning_social = forms.BooleanField(label="Social learner (group work)", required=False)
    learning_solitary = forms.BooleanField(label="Solitary learner (working alone)", required=False)
    learning_other = forms.CharField(label="Other learning preferences", required=False, widget=forms.TextInput(attrs={'placeholder': 'Describe other learning styles...'}))
    
    class Meta:
        model = DiscoverySurvey
        fields = [
            'working_environment_preferences',
            'virtual_learning_help',
            'supportive_devices',
        ]
        widgets = {
            'working_environment_preferences': forms.Textarea(attrs={'rows': 3}),
            'virtual_learning_help': forms.Textarea(attrs={'rows': 3}),
            'supportive_devices': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load learning style from JSON if exists
        if self.instance and self.instance.pk and self.instance.learning_style:
            learn_style = self.instance.learning_style
            if isinstance(learn_style, dict):
                self.fields['learning_visual'].initial = learn_style.get('visual', False)
                self.fields['learning_auditory'].initial = learn_style.get('auditory', False)
                self.fields['learning_kinesthetic'].initial = learn_style.get('kinesthetic', False)
                self.fields['learning_reading'].initial = learn_style.get('reading', False)
                self.fields['learning_social'].initial = learn_style.get('social', False)
                self.fields['learning_solitary'].initial = learn_style.get('solitary', False)
                self.fields['learning_other'].initial = learn_style.get('other', '')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Save learning style as JSON
        styles = []
        if self.cleaned_data.get('learning_visual'):
            styles.append('visual')
        if self.cleaned_data.get('learning_auditory'):
            styles.append('auditory')
        if self.cleaned_data.get('learning_kinesthetic'):
            styles.append('kinesthetic')
        if self.cleaned_data.get('learning_reading'):
            styles.append('reading/writing')
        if self.cleaned_data.get('learning_social'):
            styles.append('social')
        if self.cleaned_data.get('learning_solitary'):
            styles.append('solitary')
        
        other = self.cleaned_data.get('learning_other', '')
        
        instance.learning_style = {
            'visual': self.cleaned_data.get('learning_visual', False),
            'auditory': self.cleaned_data.get('learning_auditory', False),
            'kinesthetic': self.cleaned_data.get('learning_kinesthetic', False),
            'reading': self.cleaned_data.get('learning_reading', False),
            'social': self.cleaned_data.get('learning_social', False),
            'solitary': self.cleaned_data.get('learning_solitary', False),
            'other': other,
            'summary': ', '.join(styles) + (f', {other}' if other else ''),
        }
        if commit:
            instance.save()
        return instance


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
    
    # Availability checkboxes
    available_weekdays = forms.BooleanField(label="Weekdays", required=False)
    available_weekends = forms.BooleanField(label="Weekends", required=False)
    available_mornings = forms.BooleanField(label="Mornings", required=False)
    available_afternoons = forms.BooleanField(label="Afternoons", required=False)
    available_evenings = forms.BooleanField(label="Evenings", required=False)
    available_other = forms.CharField(label="Other availability", required=False, widget=forms.TextInput(attrs={'placeholder': 'Specify other times...'}))
    
    class Meta:
        model = DiscoverySurvey
        fields = [
            'prior_jobs',
            'jobs_interested_in',
            'dream_job',
            'employment_goals',
            'hours_per_week_working',
        ]
        widgets = {
            'prior_jobs': forms.Textarea(attrs={'rows': 3}),
            'jobs_interested_in': forms.Textarea(attrs={'rows': 3}),
            'dream_job': forms.Textarea(attrs={'rows': 4}),
            'employment_goals': forms.Textarea(attrs={'rows': 4}),
            'hours_per_week_working': forms.TextInput(attrs={'placeholder': 'e.g., 10-15 hours'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load availability from JSON if exists
        if self.instance and self.instance.pk and self.instance.available_to_work_on:
            availability = self.instance.available_to_work_on
            if isinstance(availability, dict):
                self.fields['available_weekdays'].initial = availability.get('weekdays', False)
                self.fields['available_weekends'].initial = availability.get('weekends', False)
                self.fields['available_mornings'].initial = availability.get('mornings', False)
                self.fields['available_afternoons'].initial = availability.get('afternoons', False)
                self.fields['available_evenings'].initial = availability.get('evenings', False)
                self.fields['available_other'].initial = availability.get('other', '')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Save availability as JSON
        times = []
        if self.cleaned_data.get('available_weekdays'):
            times.append('Weekdays')
        if self.cleaned_data.get('available_weekends'):
            times.append('Weekends')
        if self.cleaned_data.get('available_mornings'):
            times.append('Mornings')
        if self.cleaned_data.get('available_afternoons'):
            times.append('Afternoons')
        if self.cleaned_data.get('available_evenings'):
            times.append('Evenings')
        
        other = self.cleaned_data.get('available_other', '')
        
        instance.available_to_work_on = {
            'weekdays': self.cleaned_data.get('available_weekdays', False),
            'weekends': self.cleaned_data.get('available_weekends', False),
            'mornings': self.cleaned_data.get('available_mornings', False),
            'afternoons': self.cleaned_data.get('available_afternoons', False),
            'evenings': self.cleaned_data.get('available_evenings', False),
            'other': other,
            'summary': ', '.join(times) + (f', {other}' if other else ''),
        }
        if commit:
            instance.save()
        return instance


class SurveySection11Form(forms.ModelForm):
    """Section 11: Why Inclusive World & Additional Info"""
    
    # How heard about us checkboxes
    heard_family_friends = forms.BooleanField(label="Family/Friends", required=False)
    heard_social_media = forms.BooleanField(label="Social Media", required=False)
    heard_internet_search = forms.BooleanField(label="Internet Search", required=False)
    heard_event = forms.BooleanField(label="Event/Community Activity", required=False)
    heard_school = forms.BooleanField(label="School/Educational Institution", required=False)
    heard_other = forms.CharField(label="Other source", required=False, widget=forms.TextInput(attrs={'placeholder': 'How else did you hear about us...'}))
    
    class Meta:
        model = DiscoverySurvey
        fields = [
            'why_interested_in_iw',
            'goals_and_expectations',
            'community_activities_interest',
            'has_ged_or_diploma',
            'training_courses_completed',
        ]
        widgets = {
            'why_interested_in_iw': forms.Textarea(attrs={'rows': 4}),
            'goals_and_expectations': forms.Textarea(attrs={'rows': 4}),
            'community_activities_interest': forms.Textarea(attrs={'rows': 3}),
            'training_courses_completed': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load how_heard_about_us from JSON if exists
        if self.instance and self.instance.pk and self.instance.how_heard_about_us:
            sources = self.instance.how_heard_about_us
            if isinstance(sources, dict):
                self.fields['heard_family_friends'].initial = sources.get('family_friends', False)
                self.fields['heard_social_media'].initial = sources.get('social_media', False)
                self.fields['heard_internet_search'].initial = sources.get('internet_search', False)
                self.fields['heard_event'].initial = sources.get('event', False)
                self.fields['heard_school'].initial = sources.get('school', False)
                self.fields['heard_other'].initial = sources.get('other', '')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Save how_heard_about_us as JSON
        sources = []
        if self.cleaned_data.get('heard_family_friends'):
            sources.append('Family/Friends')
        if self.cleaned_data.get('heard_social_media'):
            sources.append('Social Media')
        if self.cleaned_data.get('heard_internet_search'):
            sources.append('Internet Search')
        if self.cleaned_data.get('heard_event'):
            sources.append('Event')
        if self.cleaned_data.get('heard_school'):
            sources.append('School')
        
        other = self.cleaned_data.get('heard_other', '')
        
        instance.how_heard_about_us = {
            'family_friends': self.cleaned_data.get('heard_family_friends', False),
            'social_media': self.cleaned_data.get('heard_social_media', False),
            'internet_search': self.cleaned_data.get('heard_internet_search', False),
            'event': self.cleaned_data.get('heard_event', False),
            'school': self.cleaned_data.get('heard_school', False),
            'other': other,
            'summary': ', '.join(sources) + (f', {other}' if other else ''),
        }
        if commit:
            instance.save()
        return instance


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
