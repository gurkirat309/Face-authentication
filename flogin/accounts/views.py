import face_recognition
import base64
import pickle
import tempfile

from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt

from .models import UserImages, User


@csrf_exempt
def register_page(request):
    if request.method == 'POST':
        try:
            username = request.POST['username']
            face_image_data = request.POST['face_image']

            # Decode base64 image
            face_image_data = face_image_data.split(",")[1]
            face_bytes = base64.b64decode(face_image_data)

            # Save user
            user = User(username=username)
            user.save()

            # Save image to model
            face_file = ContentFile(face_bytes, name=f'{username}_face.jpg')
            user_image = UserImages.objects.create(user=user, face_image=face_file)

            # Save encoding
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_file.write(face_bytes)
                temp_path = temp_file.name

            face_image_loaded = face_recognition.load_image_file(temp_path)
            face_encodings = face_recognition.face_encodings(face_image_loaded)

            if not face_encodings:
                return JsonResponse({'status': 'error', 'message': 'No face detected during registration.'})

            encoding = face_encodings[0]
            user_image.face_encoding = pickle.dumps(encoding)
            user_image.save()

            return JsonResponse({'status': 'success', 'message': 'User registered successfully!'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return render(request, 'register.html')


@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        try:
            username = request.POST['username']
            face_image_data = request.POST['face_image']

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'User not found.'})

            user_image = UserImages.objects.filter(user=user).first()
            if not user_image or not user_image.face_encoding:
                return JsonResponse({'status': 'error', 'message': 'Face data not found for this user.'})

            # Decode base64 image
            face_image_data = face_image_data.split(",")[1]
            face_bytes = base64.b64decode(face_image_data)

            # Temp file to process
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_file.write(face_bytes)
                temp_path = temp_file.name

            uploaded_face = face_recognition.load_image_file(temp_path)
            uploaded_encoding_list = face_recognition.face_encodings(uploaded_face)

            if not uploaded_encoding_list:
                return JsonResponse({'status': 'error', 'message': 'No face detected during login.'})

            uploaded_encoding = uploaded_encoding_list[0]
            stored_encoding = pickle.loads(user_image.face_encoding)

            # Use a stricter tolerance (0.4 instead of default 0.6)
            match = face_recognition.compare_faces([stored_encoding], uploaded_encoding, tolerance=0.4)
            
            # Also calculate face distance for better accuracy
            face_distance = face_recognition.face_distance([stored_encoding], uploaded_encoding)[0]
            
            # Combine both methods for better accuracy
            if match[0] and face_distance < 0.5:  # Lower distance means better match
                return JsonResponse({'status': 'success', 'message': 'Login successful!'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Face recognition failed.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return render(request, 'login.html')