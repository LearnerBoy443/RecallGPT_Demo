from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
from .models import User, ChatSession, Message
from .serializers import ChatSessionSerializer, MessageSerializer
from .services import get_keybert_model, fix_broken_prompt, generate_image_pollinations, extract_text_from_image
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage

@api_view(['GET'])
def get_me(request):
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    if user_id:
        return Response({'logged_in': True, 'username': username, 'user_id': user_id})
    return Response({'logged_in': False})

@api_view(['POST'])
def login(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()
    if not username or not password:
        return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.filter(username=username).first()
    if user:
        if user.password and user.password != password:
            return Response({'error': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)
        elif not user.password:
            user.password = password
            user.save()
    else:
        user = User.objects.create(username=username, password=password)
        
    request.session['user_id'] = user.id
    request.session['username'] = user.username
    return Response({'success': True, 'username': user.username, 'user_id': user.id})

@api_view(['POST'])
def logout(request):
    request.session.flush()
    return Response({'success': True})

@api_view(['GET', 'POST'])
def handle_sessions(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
    user = User.objects.get(id=user_id)

    if request.method == 'GET':
        sessions = ChatSession.objects.filter(user=user).order_by('-created_at')
        serializer = ChatSessionSerializer(sessions, many=True)
        return Response(serializer.data)
        
    elif request.method == 'POST':
        title = "New Chat"
        new_session = ChatSession.objects.create(user=user, title=title)
        serializer = ChatSessionSerializer(new_session)
        return Response(serializer.data)

@api_view(['GET'])
def get_messages(request, session_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
    try:
        chat_session = ChatSession.objects.get(id=session_id, user_id=user_id)
    except ChatSession.DoesNotExist:
        return Response({'error': 'Not found or unauthorized'}, status=status.HTTP_404_NOT_FOUND)
        
    messages = Message.objects.filter(session=chat_session).order_by('id')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def chat(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
    prompt = request.data.get('prompt')
    session_id = request.data.get('session_id')
    image_file = request.FILES.get('image')
    
    if not prompt or not session_id:
        return Response({'error': 'Missing prompt or session_id'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        chat_session = ChatSession.objects.get(id=session_id, user_id=user_id)
    except ChatSession.DoesNotExist:
        return Response({'error': 'Invalid session'}, status=status.HTTP_403_FORBIDDEN)
        
    # Handle Image Upload and OCR
    uploaded_image_url = None
    ocr_text = ""
    if image_file:
        fs = FileSystemStorage(location=os.path.join(settings.BASE_DIR, 'static', 'uploads'))
        filename = fs.save(image_file.name, image_file)
        uploaded_image_url = f"/static/uploads/{filename}"
        
        # Run OCR
        filepath = os.path.join(settings.BASE_DIR, 'static', 'uploads', filename)
        ocr_text = extract_text_from_image(filepath)
        
    # Save user message
    Message.objects.create(session=chat_session, role='user', content=prompt, uploaded_image_path=uploaded_image_url)
    
    # Update Session Title
    if chat_session.title == 'New Chat':
        chat_session.title = prompt[:30] + '...' if len(prompt) > 30 else prompt
        chat_session.save()
        
    # Combine user prompt with OCR text if any
    combined_prompt = prompt
    if ocr_text:
        combined_prompt += f". Found in attached image: {ocr_text}"
        
    # Process structured prompt
    structured_prompt = fix_broken_prompt(combined_prompt)
    
    # Extract keywords
    try:
        keywords_list = []
        keywords_str = ""
        keywords_list = [res.keyword for res in extracted]
        keywords_str = ", ".join(keywords_list)
    except Exception as e:
        print(f"Keyword Extraction Failed: {e}")
        keywords_list = []
        keywords_str = ""
        
    # Generate image
    try:
        gen_prompt = f"{structured_prompt}, {keywords_str}"
        image_filename = generate_image_pollinations(gen_prompt, seed=hash(prompt) % 1000000)
        image_url = f"/static/images/{image_filename}"
    except Exception as e:
        print(f"Image gen failed: {e}")
        image_url = None
        
    bot_content = "Here is the masterpiece based on your concept!"
    if structured_prompt != prompt:
        bot_content = "I've structured your concept into a cohesive prompt. Here's what we envisioned:"

    # Save bot message
    bot_msg = Message.objects.create(
        session=chat_session,
        role='bot',
        content=bot_content,
        image_path=image_url,
        uploaded_image_path=None,
        keywords=keywords_str,
        structured_prompt=structured_prompt
    )
    
    return Response({
        'id': bot_msg.id,
        'role': 'bot',
        'content': bot_content,
        'structured_prompt': structured_prompt,
        'keywords': keywords_list,
        'image_path': image_url
    })

def render_index(request):
    return render(request, 'index.html')
