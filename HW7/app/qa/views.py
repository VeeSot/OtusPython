from django.shortcuts import render_to_response


def questions(request, idx=None):
    return render_to_response('questions.html')
