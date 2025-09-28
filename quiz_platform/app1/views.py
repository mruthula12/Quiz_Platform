from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import *
from django.http import JsonResponse
from django.contrib.auth import authenticate,get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework.decorators import authentication_classes
import json




User = get_user_model() 

@csrf_exempt
def register_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            username = data.get("username")
            password = data.get("password")
            role = data.get("role", "user")


            if not username or not password:
                return JsonResponse({"error": "Username and password are required"})

            if User.objects.filter(username=username).exists():
                return JsonResponse({"error": "Username already exists"})

            user = User.objects.create(
                username=username,
                password=make_password(password),
                role=role
            )

            return JsonResponse({
                "message": "User registered successfully",
                "username": user.username,
                "role": user.role
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"})
        except Exception as e:
            return JsonResponse({"error": str(e)})

    return JsonResponse({"message": "Only POST allowed"})



@csrf_exempt
def register_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"error": "Invalid JSON"})
        username = data.get("username")
        password = data.get("password")
        role = data.get("role", "user")
        if not username or not password:
            return JsonResponse({"error": "Missing username or password"})
        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Username already exists"})
        user = User.objects.create(
            username=username,
            password=make_password(password),
            role=role
        )
        return JsonResponse({
            "message": f"User {username} registered successfully",
            "username": username,
            "role": role
        }, status=201)

    return JsonResponse({"error": "Only POST allowed"})


@csrf_exempt
def quiz_list_for_user(request):
    if request.method == "GET":
        quizzes = Quiz.objects.filter(active=True)
        quiz_list = []

        for quiz in quizzes:
            quiz_list.append({
                "id": quiz.id,
                "quiz_title": quiz.quiz_title,
                "question_text": quiz.question_text,
                "options": {
                    "A": quiz.option_a,
                    "B": quiz.option_b,
                    "C": quiz.option_c,
                    "D": quiz.option_d,
                },
                "category": {
                    "id": quiz.category.id if quiz.category else None,
                    "name": quiz.category.name if quiz.category else None
                }
            })

        return JsonResponse({"quizzes": quiz_list})

    return JsonResponse({"error": "Only GET allowed"})


@csrf_exempt
@permission_classes([IsAuthenticated])
def quiz_list_create(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Authorization token missing"})

    token_str = auth_header.split(" ")[1]
    try:
        access_token = AccessToken(token_str) 
        user_id = access_token["user_id"]
        user = User.objects.get(id=user_id)
    except Exception as e:
        return JsonResponse({"error": f"Invalid or expired token: {str(e)}"})

    if request.method == "GET":
        quizzes = Quiz.objects.filter(active=True).values()
        return JsonResponse(list(quizzes), safe=False)

    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            quiz_id = data.get("id") 
            category_id = data.get("category_id")
            category = Category.objects.get(id=category_id) if category_id else None

            if quiz_id: 
                quiz = Quiz.objects.get(id=quiz_id)
                quiz.quiz_title = data.get("quiz_title", quiz.quiz_title)
                quiz.question_text = data.get("question_text", quiz.question_text)
                quiz.option_a = data.get("option_a", quiz.option_a)
                quiz.option_b = data.get("option_b", quiz.option_b)
                quiz.option_c = data.get("option_c", quiz.option_c)
                quiz.option_d = data.get("option_d", quiz.option_d)
                quiz.correct_answer = data.get("correct_answer", quiz.correct_answer)
                quiz.category = category if category else quiz.category
                quiz.save()
            else: 
                quiz = Quiz.objects.create(
                    quiz_title=data.get("quiz_title"),
                    question_text=data.get("question_text"),
                    option_a=data.get("option_a"),
                    option_b=data.get("option_b"),
                    option_c=data.get("option_c"),
                    option_d=data.get("option_d"),
                    correct_answer=data.get("correct_answer"),
                    created_by=user,
                    category=category,
                    active=True
                )

            return JsonResponse({
                "id": quiz.id,
                "quiz_title": quiz.quiz_title,
                "question_text": quiz.question_text,
                "options": {
                    "A": quiz.option_a,
                    "B": quiz.option_b,
                    "C": quiz.option_c,
                    "D": quiz.option_d,
                },
                "correct_answer": quiz.correct_answer,
                "category": quiz.category.name if quiz.category else None,
                "created_by": quiz.created_by.username
            })

        except Exception as e:
            return JsonResponse({"error": str(e)})

    if request.method == "DELETE":
        try:
            data = json.loads(request.body.decode("utf-8"))
            quiz_id = data.get("id")

            if not quiz_id:
                return JsonResponse({"error": "Quiz ID required for delete"})

            quiz = Quiz.objects.get(id=quiz_id)
            quiz.delete()
            return JsonResponse({"message": f"Quiz {quiz_id} deleted successfully"})

        except Quiz.DoesNotExist:
            return JsonResponse({"error": "Quiz not found"})
        except Exception as e:
            return JsonResponse({"error": str(e)})

    return JsonResponse({"message": "Only GET/POST/DELETE allowed"})



@csrf_exempt
def submit_quiz(request):
    if request.method == "POST":
        try:
           
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JsonResponse({"error": "Authorization header missing or invalid"})

            token_str = auth_header.split(" ")[1]

            try:
                
                access_token = AccessToken(token_str)
                user_id = access_token["user_id"]   
                user = User.objects.get(id=user_id)
            except Exception as e:
                return JsonResponse({"error": f"Invalid or expired token: {str(e)}"})

        
            data = json.loads(request.body.decode("utf-8"))
            category_id = data.get("category_id")
            answers = data.get("answers")

            if not all([category_id, answers]):
                return JsonResponse({"message": "Something is missing"})

            category = Category.objects.get(id=category_id)
            quizzes = Quiz.objects.filter(category=category, active=True)

            correct_count = 0
            total_questions = quizzes.count()

            for quiz in quizzes:
                user_answer = answers.get(str(quiz.id))
                if user_answer and user_answer.upper() == quiz.correct_answer.upper():
                    correct_count += 1

            mark = Mark.objects.create(
                category=category,
                user=user,
                quiz=None,  
                score=correct_count,
                total=total_questions
            )

            return JsonResponse({
                "category": category.name,
                "score": mark.score,
                "total": mark.total,
                "percentage": int((mark.score / mark.total) * 100) if mark.total > 0 else 0
            })

        except Exception as e:
            return JsonResponse({"error": str(e)})

    return JsonResponse({"error": "Only POST allowed"})


@csrf_exempt
def login_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return JsonResponse({"error": "Username and password required"})

            user = authenticate(username=username, password=password)
            if user is not None:
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                quizzes = Quiz.objects.filter(active=True)
                quiz_list = []
                for quiz in quizzes:
                    quiz_list.append({
                        "id": quiz.id,
                        "quiz_title": quiz.quiz_title,
                        "question_text": quiz.question_text,
                        "options": {
                            "A": quiz.option_a,
                            "B": quiz.option_b,
                            "C": quiz.option_c,
                            "D": quiz.option_d,
                        },
                        "score": getattr(quiz, "score", 0)
                    })

                return JsonResponse({
                    "message": "Login successful",
                    "user_id": user.id,
                    "username": user.username,
                    "role": getattr(user, "role", "user"),
                    "active_questions": quiz_list,
                    "tokens": {
                        "access": access_token,
                        "refresh": str(refresh)
                    }
                }, status=200)
            else:
                return JsonResponse({"error": "Login Failed"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"})

    return JsonResponse({"error": "Only POST allowed"})


@csrf_exempt
def create_category(request):
    """
    API to create a new category.
    POST JSON body: { "name": "Science", "description": "Science related quizzes" }
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            name = data.get("name")
            description = data.get("description", "")

            if not name:
                return JsonResponse({"error": "Category name is required"})

            if Category.objects.filter(name=name).exists():
                return JsonResponse({"error": "Category already exists"})

            category = Category.objects.create(
                name=name,
                description=description
            )

            return JsonResponse({
                "id": category.id,
                "name": category.name,
                "description": category.description
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"})

    return JsonResponse({"error": "Only POST allowed"})

@csrf_exempt
def create_or_update_category(request):
    
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            name = data.get("name")
            description = data.get("description", "")

            if not name:
                return JsonResponse({"error": "Category name is required"})

        
            category, created = Category.objects.update_or_create(
                name=name,
                defaults={"description": description}
            )

            return JsonResponse({
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "created": created  
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"})

    return JsonResponse({"error": "Only POST allowed"})



@api_view(["GET"])
@authentication_classes([JWTAuthentication])   
@permission_classes([IsAuthenticated])         
def user_mark_history(request):
    try:
        user = request.user   

        marks = Mark.objects.filter(user=user).select_related("quiz", "category").order_by("-created_at")

        data = []
        for m in marks:
            data.append({
                "quiz": m.quiz.quiz_title if m.quiz else None,
                "category": m.category.name if m.category else None,
                "score": m.score,
                "total": m.total,
                "created_at": m.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return JsonResponse({"user": user.username, "marks": data}, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)})
