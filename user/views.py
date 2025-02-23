from typing import Iterable
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import TaskSerializer, UserPasswordResetSerializer, PassResetEmailSerializer, RegisterSerializer, ProjectSerializer, LoginSerializer , UserSerializer , ChangePassSerializer
from .models import User, Project, Task
from django.contrib.auth import authenticate
from .permissions import IsActive
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = get_tokens_for_user(user)
            return Response({'msg':'registration successful','data':serializer.data,'token':token},status=201)
        return Response({'error':serializer.errors},status=400)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.data.get('email')
            password = serializer.data.get('password')
            user = authenticate(username=email,password=password)
            if user:
                token = get_tokens_for_user(user)
                return Response({'msg':'login success','data':{'email':user.email,'name':user.name,'role':user.role,'is_active':user.is_active,'job':user.job,'created_at':user.created_at,'updated_at':user.updated_at,'token':token}},status=200)
            return Response({'error':'Email or Password is not valid'}, status=404)
        return Response({'error':serializer.errors}, status=400)
           
class UserView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        user = User.objects.get(email=request.user)
        serializer = UserSerializer(instance=user)
        if serializer.data:
            return Response(serializer.data, status=200)
        return Response({'msg':'no data found'}, status=404)
        

class ChangePassView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = ChangePassSerializer(data=request.data, context={'user':request.user} )
        if serializer.is_valid():
            return Response({'msg':'password changed successfuly'},status=201)
        return Response({'error':serializer.errors},status=400)

class PassResetEmailView(APIView):
        def post(self, request):
            serializer = PassResetEmailSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                return Response({'msg':'Password reset email send, please check your email', 'link':serializer.validated_data}, status=200)
            return Response(serializer.errors, status=400)   

class UserPasswordResetView(APIView):
    def post(self, request,uid,token):
        serializer=UserPasswordResetSerializer(data=request.data,context={'uid':uid,'token':token})
        if serializer.is_valid(raise_exception=True):
            return Response({'msg':'password reset successfully'},status=200)
        return Response(serializer.errors,status=400)

class ProjectView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        search = request.query_params.get('search')
        user = User.objects.get(email=request.user)
        serializer = UserSerializer(instance=user)
        role = serializer.data.get('role')
        name = serializer.data.get('name')
        email = serializer.data.get('email')
        print(email)
        if role == 'developer':
            projects = Project.objects.filter(assigned_to = request.user)
            if search is not None:
                filteredProjects = projects.filter(name = search)
                serializer = ProjectSerializer(instance=filteredProjects, many=True)
                return Response({'user_email':email,'user_name':name,'user_role':role,'data':serializer.data},status=200)
            serializer = ProjectSerializer(instance=projects, many=True)
            return Response({'user_email':email,'user_name':name,'user_role':role,'data':serializer.data}, status=200)
        if role == 'lead':
            projects = Project.objects.filter(assigned_by = request.user)
            if search is not None:
                filteredProjects = projects.filter(name = search)
                serializer = ProjectSerializer(instance=filteredProjects, many=True)
                return Response({'user_email':email,'user_name':name,'user_role':role,'data':serializer.data},status=200)
            serializer = ProjectSerializer(instance=projects, many=True)
            return Response({'user_email':email,'user_name':name,'user_role':role,'data':serializer.data}, status=200)
        return Response({'msg':'something went wrong','error':serializer.errors}, status=400)
    def post(self,request):
        user = User.objects.get(email=request.user)
        serializer = UserSerializer(instance=user)
        role = serializer.data.get('role')
        if role == 'lead':
            serializer = ProjectSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'msg':'Project Created!','project':serializer.data},status=201)
            return Response({'error':serializer.errors},status=400)
        return Response({'error':'only lead can create project'}, status=400)

class TaskView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        project = request.query_params.get('project')
        user = User.objects.get(email=request.user)
        serializer = UserSerializer(instance=user)
        role = serializer.data.get('role')
        if role == 'developer':
            tasks = Task.objects.filter(user = request.user)
            if project is not None:
                filteredTasks = tasks.filter(project_name=project)
                serializer = TaskSerializer(instance=filteredTasks, many=True)
                return Response(serializer.data, status=200)
            serializer = TaskSerializer(instance=tasks, many=True)
            return Response(serializer.data,status=200)
        return Response({'msg':'only developer can view tasks'},status=400)
    
    def post(self,request):
        user = User.objects.get(email=request.user)
        serializer = UserSerializer(instance=user)
        role = serializer.data.get('role')
        if role == 'developer':
            serializer = TaskSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'msg':'Task created','data':serializer.data},status=201)
            return Response(serializer.errors, status=400)
        return Response({'msg':'lead cannot add tasks'},status=400)

    def patch(self,request):
        user = User.objects.get(email=request.user)
        serializer = UserSerializer(instance=user)
        role = serializer.data.get('role')
        if role == 'developer':
            param = request.query_params.get('id')
            if not param:
                return Response({"message": "Please provide a task ID."}, status=400)
            task = Task.objects.get(id=param)
            serializer = TaskSerializer(instance=task,data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,status=200)
            return Response({'error':'data is not in valid format','details':serializer.errors},status=400)
        return Response({'msg':'only developer can update task'},status=403)
    
    def delete(self, request):
        param = request.query_params.get("id")
        if not param:
            return Response({"message": "Please provide a task id."}, status=400)
        task = Task.objects.get(id=param)
        task.delete()
        return Response({"message": "Task deleted successfully."}, status=204)
    