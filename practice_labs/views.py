from django.shortcuts import render, get_object_or_404, redirect
from .models import Lab, LabStep, UserLabProgress
from .forms import CodeSubmissionForm

def lab_list(request):
    labs = Lab.objects.all()
    return render(request, 'practice_labs/lab_list.html', {'labs': labs})

def lab_detail(request, lab_id, step_order=0):
    lab = get_object_or_404(Lab, pk=lab_id)
    step = lab.steps.order_by('order')[step_order]
    form = CodeSubmissionForm()
    feedback = None

    if request.method == 'POST':
        form = CodeSubmissionForm(request.POST)
        if form.is_valid():
            user_code = form.cleaned_data['code']
            # Add code checking and AI feedback logic here
            feedback = "Code checked. (Integrate AI here.)"

    return render(request, 'practice_labs/lab_detail.html', {
        'lab': lab,
        'step': step,
        'form': form,
        'feedback': feedback
    })
