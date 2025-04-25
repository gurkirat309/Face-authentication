import face_recognition
import base64
import pickle
import tempfile
import cv2
import numpy as np
import os

from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt

from .models import UserImages, User
@csrf_exempt
def helloworld(response):
    return JsonResponse({ 'message':'HIII'})


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
                os.unlink(temp_path)  # Clean up temp file
                return JsonResponse({'status': 'error', 'message': 'No face detected during registration.'})

            encoding = face_encodings[0]
            user_image.face_encoding = pickle.dumps(encoding)
            user_image.save()
            
            os.unlink(temp_path)  # Clean up temp file
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

            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_file.write(face_bytes)
                temp_path = temp_file.name

            # Basic liveness detection - check for photo-of-photo
            img = cv2.imread(temp_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 1. Check image quality (blurry images might be photos of photos)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian_var < 100:  # Threshold for blurriness
                os.unlink(temp_path)  # Clean up
                return JsonResponse({'status': 'error', 'message': 'Low quality image detected. Please try again with better lighting.'})
            
            # 2. Check for reflection patterns often seen in screen photos
            # This is a simplified version - more advanced methods would use ML models
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            saturation = hsv[:,:,1]
            sat_mean = np.mean(saturation)
            if sat_mean < 30:  # Very low saturation might indicate a screen photo
                os.unlink(temp_path)  # Clean up
                return JsonResponse({'status': 'error', 'message': 'Screen reflection detected. Please use your real face.'})

            # Process for face recognition
            uploaded_face = face_recognition.load_image_file(temp_path)
            uploaded_encoding_list = face_recognition.face_encodings(uploaded_face)

            if not uploaded_encoding_list:
                os.unlink(temp_path)  # Clean up
                return JsonResponse({'status': 'error', 'message': 'No face detected during login.'})

            uploaded_encoding = uploaded_encoding_list[0]
            stored_encoding = pickle.loads(user_image.face_encoding)

            # Use a stricter tolerance (0.4 instead of default 0.6)
            match = face_recognition.compare_faces([stored_encoding], uploaded_encoding, tolerance=0.4)
            
            # Also calculate face distance for better accuracy
            face_distance = face_recognition.face_distance([stored_encoding], uploaded_encoding)[0]
            
            os.unlink(temp_path)  # Clean up temp file
            
            # Combine both methods for better accuracy
            if match[0] and face_distance < 0.5:  # Lower distance means better match
                return JsonResponse({'status': 'success', 'message': 'Login successful!'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Face recognition failed.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return render(request, 'login.html')