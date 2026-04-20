from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from .models import User, ChatSession, Message
from .serializers import ChatSessionSerializer, MessageSerializer
from .services import fix_broken_prompt, generate_image_pollinations

# Root test
def render_index(request):
    return JsonResponse({"status": "ok"})

# Health check
@api_view(['GET'])
def test(request):
    return Response({"status": "ok"})

@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    user, _ = User.objects.get_or_create(username=username)
    return Response({"user_id": user.id})

@api_view(['POST'])
def chat(request):
    user_id = request.data.get('user_id')
    prompt = request.data.get('prompt')

    user = User.objects.get(id=user_id)
    session = ChatSession.objects.create(user=user)

    structured_prompt = fix_broken_prompt(prompt)
    image_url = generate_image_pollinations(structured_prompt)

    msg = Message.objects.create(
        session=session,
        role='bot',
        content=structured_prompt
    )

    return Response({
        "message": msg.content,
        "image": image_url
    })
