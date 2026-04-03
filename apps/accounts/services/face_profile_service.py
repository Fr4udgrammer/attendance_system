import base64
import os
import uuid
import math
from statistics import mean
from typing import Any, Dict, List, Tuple

from django.conf import settings
from django.core.files.base import ContentFile

def _get_detection_model() -> str:
    return getattr(settings, 'FACE_RECOGNITION_MODEL', 'hog')

def _calculate_ear(eye_points: List[Tuple[int, int]]) -> float:
    if not eye_points or len(eye_points) < 6:
        return 0.0
    def distance(p1, p2):
        return math.hypot(p2[0]-p1[0], p2[1]-p1[1])
    
    A = distance(eye_points[1], eye_points[5])
    B = distance(eye_points[2], eye_points[4])
    C = distance(eye_points[0], eye_points[3])
    return (A + B) / (2.0 * C) if C != 0 else 0.0


class FaceRecognitionDependencyError(Exception):
    """Raised when face-recognition dependencies are unavailable."""


QUALITY_LIMITS = {
    'min_brightness': 45,
    'max_brightness': 220,
    'min_contrast': 20,
    'min_blur_score': 80,
    'min_face_ratio': 0.10,
    'min_registration_quality': 0.55,
    'min_verification_quality': 0.45,
}


def _import_ml_dependencies() -> Tuple[Any, Any, Any]:
    try:
        import cv2  # type: ignore
        import face_recognition  # type: ignore
        import numpy as np  # type: ignore

        return cv2, face_recognition, np
    except ImportError as exc:
        raise FaceRecognitionDependencyError(
            'Face recognition dependencies are missing. Install requirements before using this feature.'
        ) from exc


def _decode_data_url(image_data: str) -> Tuple[Any, Any]:
    cv2, _, np = _import_ml_dependencies()

    if ';base64,' not in image_data:
        raise ValueError('Invalid image payload format.')

    _, encoded_image = image_data.split(';base64,', 1)
    image_bytes = base64.b64decode(encoded_image)
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image_bgr = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image_bgr is None:
        raise ValueError('Unable to decode captured image.')

    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    return image_bgr, image_rgb


def _enhance_lighting(image_bgr: Any) -> Tuple[Any, Any]:
    cv2, _, _ = _import_ml_dependencies()

    ycrcb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2YCrCb)
    y_channel, cr_channel, cb_channel = cv2.split(ycrcb)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    y_channel = clahe.apply(y_channel)

    enhanced_bgr = cv2.cvtColor(
        cv2.merge((y_channel, cr_channel, cb_channel)),
        cv2.COLOR_YCrCb2BGR,
    )
    enhanced_rgb = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2RGB)
    return enhanced_bgr, enhanced_rgb


def _extract_single_face_encoding(image_bgr: Any, image_rgb: Any, num_jitters: int) -> Dict[str, Any]:
    _, face_recognition, _ = _import_ml_dependencies()

    enhanced_bgr, enhanced_rgb = _enhance_lighting(image_bgr)
    variants = [
        (image_bgr, image_rgb, False),
        (enhanced_bgr, enhanced_rgb, True),
    ]

    multiple_faces_detected = False

    for _, rgb_variant, used_enhancement in variants:
        face_locations = face_recognition.face_locations(rgb_variant, model=_get_detection_model())

        if len(face_locations) > 1:
            multiple_faces_detected = True
            continue
        if len(face_locations) == 0:
            continue

        encodings = face_recognition.face_encodings(
            rgb_variant,
            known_face_locations=face_locations,
            num_jitters=num_jitters,
        )
        if encodings:
            ear = 0.0
            landmarks_list = face_recognition.face_landmarks(rgb_variant, known_face_locations=[face_locations[0]])
            if landmarks_list:
                landmarks = landmarks_list[0]
                left_eye_ear = _calculate_ear(landmarks.get('left_eye', []))
                right_eye_ear = _calculate_ear(landmarks.get('right_eye', []))
                if left_eye_ear and right_eye_ear:
                    ear = (left_eye_ear + right_eye_ear) / 2.0

            return {
                'encoding': encodings[0],
                'face_location': face_locations[0],
                'used_enhancement': used_enhancement,
                'ear': ear,
            }

    if multiple_faces_detected:
        raise ValueError('exactly one face must be visible per sample')
    raise ValueError('unable to extract facial features')


def _compute_quality_metrics(image_bgr: Any, face_location: Tuple[int, int, int, int]) -> Dict[str, float]:
    cv2, _, _ = _import_ml_dependencies()

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean())
    contrast = float(gray.std())
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    top, right, bottom, left = face_location
    height, width = gray.shape
    face_area = max(bottom - top, 1) * max(right - left, 1)
    frame_area = max(height * width, 1)
    face_ratio = float(face_area / frame_area)

    return {
        'brightness': round(brightness, 2),
        'contrast': round(contrast, 2),
        'blur_score': round(blur_score, 2),
        'face_ratio': round(face_ratio, 4),
    }


def _score_quality(metrics: Dict[str, float]) -> Tuple[float, List[str]]:
    score = 0.0
    issues: List[str] = []

    if QUALITY_LIMITS['min_brightness'] <= metrics['brightness'] <= QUALITY_LIMITS['max_brightness']:
        score += 0.25
    elif metrics['brightness'] < QUALITY_LIMITS['min_brightness']:
        issues.append('frame is too dark')
    else:
        issues.append('frame is too bright')

    if metrics['contrast'] >= QUALITY_LIMITS['min_contrast']:
        score += 0.25
    else:
        issues.append('low contrast')

    if metrics['blur_score'] >= QUALITY_LIMITS['min_blur_score']:
        score += 0.25
    else:
        issues.append('image is blurry')

    if metrics['face_ratio'] >= QUALITY_LIMITS['min_face_ratio']:
        score += 0.25
    else:
        issues.append('face is too far from camera')

    return round(score, 2), issues


def save_avatar_from_data_url(user: Any, image_data: str, filename_prefix: str) -> None:
    if ';base64,' not in image_data:
        raise ValueError('Invalid image payload format.')

    mime_part, encoded_image = image_data.split(';base64,', 1)
    extension = mime_part.split('/')[-1] if '/' in mime_part else 'jpg'
    filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.{extension}"

    image_bytes = base64.b64decode(encoded_image)
    content = ContentFile(image_bytes, name=filename)
    user.avatar.save(filename, content, save=False)

def validate_single_sample(image_data: str) -> Dict[str, Any]:
    _import_ml_dependencies()
    
    if not image_data:
        return {'valid': False, 'guidance': 'No image data provided.'}
        
    try:
        image_bgr, image_rgb = _decode_data_url(image_data)
        extracted = _extract_single_face_encoding(image_bgr, image_rgb, num_jitters=1)
        
        metrics = _compute_quality_metrics(image_bgr, extracted['face_location'])
        quality_score, quality_issues = _score_quality(metrics)
        
        if quality_score < QUALITY_LIMITS['min_registration_quality']:
            return {
                'valid': False,
                'face_detected': True,
                'quality_score': quality_score,
                'quality_metrics': metrics,
                'issues': quality_issues,
                'guidance': ', '.join(quality_issues) or 'Quality too low. Please improve lighting or face position.'
            }
            
        return {
            'valid': True,
            'face_detected': True,
            'quality_score': quality_score,
            'quality_metrics': metrics,
            'issues': [],
            'guidance': 'Sample looks great!'
        }
    except ValueError as e:
        return {
            'valid': False,
            'face_detected': False,
            'guidance': str(e)
        }
    except Exception as e:
        return {
            'valid': False,
            'face_detected': False,
            'guidance': f'Error validating sample: {str(e)}'
        }


def analyze_registration_samples(sample_images: List[str], min_valid_samples: int = 3) -> Dict[str, Any]:
    _import_ml_dependencies()

    if not sample_images:
        return {
            'success': False,
            'error': 'No face samples were provided.',
        }

    valid_samples: List[Dict[str, Any]] = []
    rejected_reasons: List[str] = []

    for sample in sample_images:
        try:
            image_bgr, image_rgb = _decode_data_url(sample)
            extracted = _extract_single_face_encoding(image_bgr, image_rgb, num_jitters=2)

            metrics = _compute_quality_metrics(image_bgr, extracted['face_location'])
            quality_score, quality_issues = _score_quality(metrics)

            if quality_score < QUALITY_LIMITS['min_registration_quality']:
                rejected_reasons.append(', '.join(quality_issues) or 'quality too low')
                continue

            valid_samples.append({
                'encoding': extracted['encoding'].tolist(),
                'metrics': metrics,
                'quality_score': quality_score,
                'image': sample,
                'used_enhancement': extracted['used_enhancement'],
            })
        except Exception as exc:
            rejected_reasons.append(str(exc))

    if len(valid_samples) < min_valid_samples:
        return {
            'success': False,
            'error': (
                f'Only {len(valid_samples)} valid face samples were accepted. '
                f'Capture at least {min_valid_samples} clear samples in different angles.'
            ),
            'analysis': {
                'captured_samples': len(sample_images),
                'valid_samples': len(valid_samples),
                'rejected_samples': max(len(sample_images) - len(valid_samples), 0),
                'rejected_reasons': rejected_reasons[:5],
            },
        }

    primary_sample = max(valid_samples, key=lambda item: item['quality_score'])

    analysis = {
        'captured_samples': len(sample_images),
        'valid_samples': len(valid_samples),
        'rejected_samples': max(len(sample_images) - len(valid_samples), 0),
        'enhanced_frames': sum(1 for item in valid_samples if item['used_enhancement']),
        'average_brightness': round(mean(item['metrics']['brightness'] for item in valid_samples), 2),
        'average_contrast': round(mean(item['metrics']['contrast'] for item in valid_samples), 2),
        'average_blur_score': round(mean(item['metrics']['blur_score'] for item in valid_samples), 2),
        'average_face_ratio': round(mean(item['metrics']['face_ratio'] for item in valid_samples), 4),
        'average_quality_score': round(mean(item['quality_score'] for item in valid_samples), 2),
    }

    return {
        'success': True,
        'encodings': [item['encoding'] for item in valid_samples],
        'primary_image': primary_sample['image'],
        'analysis': analysis,
    }


def get_user_known_encodings(user: Any) -> List[List[float]]:
    _, face_recognition, _ = _import_ml_dependencies()

    if isinstance(user.face_encodings, list) and user.face_encodings:
        return user.face_encodings

    if not user.avatar:
        return []

    avatar_path = user.avatar.path
    if not avatar_path or not os.path.exists(avatar_path):
        return []

    registered_image = face_recognition.load_image_file(avatar_path)
    face_locations = face_recognition.face_locations(registered_image, model=_get_detection_model())
    encodings = face_recognition.face_encodings(
        registered_image,
        known_face_locations=face_locations,
        num_jitters=2,
    )

    if not encodings:
        return []

    return [encodings[0].tolist()]


def verify_face_frames(
    frame_images: List[str],
    known_encodings: List[List[float]],
    tolerance: float = 0.55,
) -> Dict[str, Any]:
    _, face_recognition, np = _import_ml_dependencies()

    if not known_encodings:
        return {
            'success': False,
            'error': 'No enrolled face profile found. Register face profile again.',
        }

    if not frame_images:
        return {
            'success': False,
            'error': 'No verification frames were provided.',
        }

    known_vectors = np.array(known_encodings, dtype=np.float64)
    required_matches = 1 if len(frame_images) == 1 else 2

    matched_frames = 0
    best_distance = 1.0
    rejected_reasons: List[str] = []
    ear_values: List[float] = []

    for frame in frame_images:
        try:
            image_bgr, image_rgb = _decode_data_url(frame)
            extracted = _extract_single_face_encoding(image_bgr, image_rgb, num_jitters=1)
            
            if extracted.get('ear'):
                ear_values.append(extracted['ear'])

            metrics = _compute_quality_metrics(image_bgr, extracted['face_location'])
            quality_score, quality_issues = _score_quality(metrics)
            if quality_score < QUALITY_LIMITS['min_verification_quality']:
                rejected_reasons.append(', '.join(quality_issues) or 'frame quality too low')
                continue

            distances = face_recognition.face_distance(known_vectors, extracted['encoding'])
            distance = float(np.min(distances))
            best_distance = min(best_distance, distance)

            if distance <= tolerance:
                matched_frames += 1
            else:
                rejected_reasons.append('face does not match enrolled profile')
        except Exception as exc:
            rejected_reasons.append(str(exc))

    liveness_verified = False
    if ear_values and max(ear_values) > 0.0:
        if (max(ear_values) - min(ear_values)) >= 0.035 and min(ear_values) < 0.245:
            liveness_verified = True

    if matched_frames >= required_matches:
        if not liveness_verified:
            return {
                'success': False,
                'error': 'Liveness check failed. Please blink while scanning.',
                'matched_frames': matched_frames,
                'required_matches': required_matches,
                'best_distance': round(best_distance, 4),
                'liveness_verified': False,
            }

        return {
            'success': True,
            'matched_frames': matched_frames,
            'required_matches': required_matches,
            'best_distance': round(best_distance, 4),
            'liveness_verified': True,
        }

    top_reason = rejected_reasons[0] if rejected_reasons else 'unable to verify face identity'
    return {
        'success': False,
        'error': top_reason,
        'matched_frames': matched_frames,
        'required_matches': required_matches,
        'best_distance': round(best_distance, 4),
        'liveness_verified': liveness_verified,
    }
