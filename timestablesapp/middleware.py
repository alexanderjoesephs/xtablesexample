from .models import Teacher,Student,Admin


def checkstatus(request):
    if request.user.is_authenticated:
        if Teacher.objects.filter(user=request.user).exists():
            return 'teacher'
        elif Student.objects.filter(user=request.user).exists():
            return 'student'
        elif Admin.objects.filter(user=request.user).exists():
            return 'admin'
        else:
            return 'unassigned'
    else:
        return 'logged_out'

class CheckUserRoleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_status = checkstatus(request)

        # Store the user_status in the request object for easy access in views
        request.user_status = user_status

        response = self.get_response(request)

        return response
