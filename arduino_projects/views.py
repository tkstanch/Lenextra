from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import ArduinoProject
from django.contrib.auth.decorators import login_required

@login_required
def share_project(request, pk):
    project = get_object_or_404(ArduinoProject, pk=pk, user=request.user)
    if request.method == 'POST':
        recipient = request.POST.get('recipient')
        # Implement email sending logic here
        # send_mail(subject, message, from_email, [recipient])
        return render(request, 'arduino_projects/share_project.html', {
            'project': project,
            'shared': True,
            'recipient': recipient
        })
    return render(request, 'arduino_projects/share_project.html', {'project': project})

@login_required
def download_file(request, pk):
    project = get_object_or_404(ArduinoProject, pk=pk, user=request.user)
    response = HttpResponse(project.code, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{project.name}.ino"'
    return response

@login_required
def upload_to_device(request, pk):
    project = get_object_or_404(ArduinoProject, pk=pk, user=request.user)
    upload_output = None
    if request.method == 'POST':
        port = request.POST.get('port')
        # Save code to temp file and call arduino-cli upload
        import tempfile, os, subprocess
        tmp = tempfile.TemporaryDirectory()
        ino_path = os.path.join(tmp.name, f"{project.name}.ino")
        with open(ino_path, "w") as f:
            f.write(project.code)
        cmd = [
            "arduino-cli", "upload", "-p", port,
            "--fqbn", project.board_fqbn, ino_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        upload_output = result.stdout + result.stderr
        tmp.cleanup()
    return render(request, 'arduino_projects/upload_to_device.html', {
        'project': project,
        'upload_output': upload_output
    })
