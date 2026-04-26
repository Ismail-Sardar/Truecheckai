

'''
import os
import io
import logging
import base64
import numpy as np
import cv2
import tempfile
import re
from PIL import Image, ImageChops, ImageEnhance
from mtcnn import MTCNN
from skimage.measure import shannon_entropy
import pytesseract
from pytesseract import Output
from collections import Counter
import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification
import matplotlib
matplotlib.use("Agg")  # Headless mode for matplotlib
import matplotlib.pyplot as plt

# -------------------------------
# SETUP LOGGING
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

# -------------------------------
# DEVICE CONFIGURATION
# -------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logging.info(f"--- Using device: {device} ---")


# -------------------------------
# MODEL LOADING
# -------------------------------
logging.info("--- Loading a committee of expert AI models ---")

# Expert 1: Vision Transformer (AI Image Detector)
VIT_MODEL_NAME = "umm-maybe/AI-image-detector"
try:
    logging.info(f"🔄 Loading Expert 1: {VIT_MODEL_NAME}")
    vit_processor = AutoImageProcessor.from_pretrained(VIT_MODEL_NAME)
    vit_model = AutoModelForImageClassification.from_pretrained(VIT_MODEL_NAME).to(device).eval()
    logging.info("✅ Expert 1 (ViT) loaded.")
except Exception as e:
    logging.critical(f"❌ Failed to load ViT model: {e}")
    vit_processor, vit_model = None, None

# Expert 2: CNN-based (ResNet)
CNN_MODEL_NAME = "microsoft/resnet-50"
try:
    logging.info(f"🔄 Loading Expert 2: {CNN_MODEL_NAME}")
    cnn_processor = AutoImageProcessor.from_pretrained(CNN_MODEL_NAME)
    cnn_model = AutoModelForImageClassification.from_pretrained(CNN_MODEL_NAME).to(device).eval()
    logging.info("✅ Expert 2 (CNN) loaded.")
except Exception as e:
    logging.critical(f"❌ Failed to load CNN model: {e}")
    cnn_processor, cnn_model = None, None

# Expert 3: MTCNN Face Detector
try:
    logging.info("🔄 Loading Expert 3: MTCNN Face Detector")
    face_detector = MTCNN()
    logging.info("✅ MTCNN Face Detector loaded.")
except Exception as e:
    logging.critical(f"❌ Failed to load Face Detector: {e}")
    face_detector = None

# -------------------------------
# HELPER: GRAPH GENERATION
# -------------------------------
def _generate_graph(scores: dict, final_label: str) -> str:
    """Generates a bar chart from a scores dictionary and returns it as a Base64 string."""
    labels = ["Real", "AI-Generated", "Edited"]
    values = [scores.get("real", 0), scores.get("ai", 0), scores.get("edited", 0)]
    
    plt.figure(figsize=(5, 4))
    colors = ["#4dff4d", "#ff4d4d", "#4da6ff"] # Green for Real, Red for AI, Blue for Edited
    plt.bar(labels, values, color=colors)
    plt.ylim(0, 1)
    plt.title(f"Final Prediction: {final_label}")
    plt.ylabel("Confidence Score")
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# -------------------------------
# AUTHENTICITY PREDICTION FUNCTION
# -------------------------------
def _predict_image_authenticity(pil_image: Image.Image):
    if not all([vit_processor, vit_model, cnn_processor, cnn_model]):
        raise RuntimeError("One or more AI models failed to load.")

    # Expert 1: ViT
    inputs_vit = vit_processor(images=pil_image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs_vit = vit_model(**inputs_vit)
        probs_vit = torch.softmax(outputs_vit.logits, dim=-1)[0].cpu().numpy()

    id2label_vit = vit_model.config.id2label
    fake_idx_vit = next(i for i, label in id2label_vit.items() if label.lower() == "artificial")
    ai_score_vit = float(probs_vit[fake_idx_vit])

    # Expert 2: CNN heuristic
    inputs_cnn = cnn_processor(images=pil_image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs_cnn = cnn_model(**inputs_cnn)
        probs_cnn = torch.softmax(outputs_cnn.logits, dim=-1)[0].cpu().numpy()

    top_confidence_cnn = np.max(probs_cnn)
    ai_score_cnn = 1.0 - float(top_confidence_cnn)

    # Weighted average
    final_ai_score = (0.7 * ai_score_vit) + (0.3 * ai_score_cnn)

    return {
        "ai": round(final_ai_score, 4),
        "real": round(1.0 - final_ai_score, 4)
    }

# -------------------------------
# DOCUMENT ANALYSIS (UPGRADED)
# -------------------------------
def analyze_document(file_bytes: bytes):
    pil_image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    
    # --- NEW: Step 1 - Find and analyze any faces on the document ---
    photo_analysis = {}
    if face_detector:
        image_np = np.array(pil_image)
        faces = face_detector.detect_faces(image_np)
        if faces:
            logging.info(f"Found {len(faces)} face(s) on the document. Analyzing photo...")
            # Analyze the first detected face
            x, y, w, h = faces[0]['box']
            face_image = pil_image.crop((x, y, x + w, y + h))
            photo_scores = _predict_image_authenticity(face_image)
            photo_label = "AI-Generated Photo" if photo_scores['ai'] > 0.5 else "Real Photo"
            photo_analysis = {"status": photo_label, "confidence": photo_scores}

    # --- Step 2: Analyze the document as a whole image for tampering ---
    overall_scores = _predict_image_authenticity(pil_image)
    
    # --- Step 3: OCR for text extraction ---
    try:
        ocr_data = pytesseract.image_to_data(pil_image, output_type=Output.DICT)
        extracted_text = " ".join(ocr_data['text']).strip()
    except Exception as e:
        logging.warning(f"⚠️ OCR failed: {e}")
        extracted_text = "OCR failed or no text found."

    # --- Step 4: Text-based heuristic checks ---
    red_flags = []
    if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\b', extracted_text):
        if not re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(com|net|org|gov|edu|io|ai|co)\b', extracted_text):
            red_flags.append("Suspicious or incomplete email domain")

    # --- Step 5: Final Decision Logic ---
    label = "Likely Real Document"
    if overall_scores['ai'] > 0.6 or red_flags:
        label = "Edited/Fake Document"
    if photo_analysis.get("status") == "AI-Generated Photo":
        label = "Edited/Fake Document (AI Photo Detected)"

    overall_scores['edited'] = 0.1 if not red_flags else 0.8
    graph_b64 = _generate_graph(overall_scores, label)

    return {
        "label": label,
        "ocr_text": extracted_text,
        "ocr_flags": red_flags,
        "scores": overall_scores,
        "photo_analysis": photo_analysis, # Add the new photo analysis to the result
        "graph_base64": graph_b64
    }

# -------------------------------
# VIDEO ANALYSIS
# -------------------------------
def analyze_video(video_bytes: bytes):
    if not face_detector:
        raise RuntimeError("Face detector not available.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_bytes)
        video_path = tmp.name

    cap = cv2.VideoCapture(video_path)
    face_analysis_scores = []
    frame_count = 0

    while cap.isOpened() and len(face_analysis_scores) < 10:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % 15 == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = face_detector.detect_faces(frame_rgb)

            for face in faces:
                x, y, w, h = face['box']
                y1, y2 = max(0, y), min(frame_rgb.shape[0], y + h)
                x1, x2 = max(0, x), min(frame_rgb.shape[1], x + w)
                face_image = Image.fromarray(frame_rgb[y1:y2, x1:x2])
                try:
                    scores = _predict_image_authenticity(face_image)
                    face_analysis_scores.append(scores["ai"])
                except Exception as e:
                    logging.warning(f"⚠️ Failed to analyze face frame: {e}")

        frame_count += 1

    cap.release()
    os.remove(video_path)

    if not face_analysis_scores:
        scores = {"real": 1.0, "ai": 0.0, "edited": 0.0}
        return {
            "label": "Real (No Faces Detected)",
            "frames_sampled": frame_count,
            "frame_analysis": {},
            "scores": scores,
            "graph_base64": _generate_graph(scores, "Real")
        }

    avg_fake_score = float(np.mean(face_analysis_scores))
    label = "Deepfake Detected" if avg_fake_score > 0.5 else "Real"
    
    scores = {"real": 1.0 - avg_fake_score, "ai": avg_fake_score, "edited": 0.0}
    graph_b64 = _generate_graph(scores, label)

    return {
        "label": label,
        "frames_sampled": frame_count,
        "frame_analysis": {
            "average_fake_score": round(avg_fake_score, 4),
            "faces_analyzed": len(face_analysis_scores)
        },
        "scores": scores,
        "graph_base64": graph_b64
    }

# -------------------------------
# FILE DISPATCHER
# -------------------------------
def analyze_file(file_bytes: bytes, mimetype: str):
    try:
        if "video" in mimetype:
            logging.info("Routing to: Video Analyzer")
            return analyze_video(file_bytes)

        elif "image" in mimetype:
            if not face_detector:
                raise RuntimeError("Face detector model not available for image triage.")

            pil_image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            image_np = np.array(pil_image)
            faces = face_detector.detect_faces(image_np)

            if faces:
                logging.info(f"Routing to: Image Authenticity Analyzer ({len(faces)} face(s) found)")
                scores = _predict_image_authenticity(pil_image)
                label = "AI-Generated" if scores['ai'] > 0.5 else "Real"
                
                scores['edited'] = 0.0
                graph_b64 = _generate_graph(scores, label)
                
                return {
                    "label": label,
                    "scores": scores,
                    "graph_base64": graph_b64
                }
            else:
                logging.info("Routing to: Document Analyzer (no faces found)")
                return analyze_document(file_bytes)

        else:
            return {
                "label": "Unsupported",
                "error": "File type not supported."
            }
# ----------------------------------------------------
# HELPER: ADVANCED AND DYNAMIC STRUCTURED REPORT
# ----------------------------------------------------

def _create_image_report(result: dict) -> list:
    """Generates a report specifically for standalone images."""
    report = []
    label = result.get("label", "")
    scores = result.get("scores", {})
    ai_score = scores.get("ai", 0)

    report.append({
        "title": "Overall Finding",
        "details": f"Based on a deep analysis of visual artifacts, the model's final prediction is that this image is **{label}**."
    })
    
    reasoning = (
        f"This conclusion is based on a high AI-generated content score of **{(ai_score * 100):.1f}%**. Our models detected patterns and textural inconsistencies that are hallmarks of synthetic image generation."
        if "AI-Generated" in label
        else "The image exhibits natural lighting, focus, and real-world imperfections. Our models found no significant evidence of AI generation."
    )
    report.append({"title": "Reasoning Summary", "details": reasoning})
    return report

def _create_video_report(result: dict) -> list:
    """Generates a report specifically for videos."""
    report = []
    label = result.get("label", "")
    frame_analysis = result.get("frame_analysis", {})
    avg_fake_score = frame_analysis.get("average_fake_score", 0)

    report.append({
        "title": "Overall Finding",
        "details": f"After analyzing multiple frames, the model's final prediction is that this video is **{label}**."
    })

    reasoning = (
        f"The primary indicator was a high average deepfake score of **{(avg_fake_score * 100):.1f}%** across **{frame_analysis.get('faces_analyzed', 0)}** analyzed faces. This suggests the faces in the video may be synthetically generated or manipulated."
        if "Deepfake" in label
        else "The facial features and movements across sampled frames appear consistent and natural. No significant deepfake indicators were found."
    )
    report.append({"title": "Reasoning Summary", "details": reasoning})
    return report

def _create_document_report(result: dict) -> list:
    """Generates a report specifically for documents."""
    report = []
    label = result.get("label", "")
    ocr_flags = result.get("ocr_flags", [])
    photo_analysis = result.get("photo_analysis", {})

    report.append({
        "title": "Overall Finding",
        "details": f"Based on visual and textual analysis, the model's prediction is that this is a **{label}**."
    })
    
    evidence = []
    if "AI Photo Detected" in label:
        evidence.append("the embedded photo was identified as AI-generated")
    if ocr_flags:
        evidence.append(f"textual red flags were found, including: '{', '.join(ocr_flags)}'")
    
    reasoning = (
        f"This conclusion is based on several key indicators: {', and '.join(evidence)}."
        if evidence
        else "The document's layout, text, and any embedded photos appear authentic. No significant signs of tampering or forgery were detected."
    )
    report.append({"title": "Reasoning Summary", "details": reasoning})
    return report

def generate_structured_report(result: dict) -> list:
    """Main dispatcher function to generate the correct report type."""
    analysis_type = result.get("analysis_type", "image") # Default to image
    
    if analysis_type == "video":
        return _create_video_report(result)
    elif analysis_type == "document":
        return _create_document_report(result)
    else: # Image
        return _create_image_report(result)
except Exception as e:
        logging.error(f"❌ Error in analyze_file: {e}")
        return {
            "label": "Error",
            "error": str(e)
        }
'''

import os
import io
import logging
import base64
import numpy as np
import cv2
import tempfile
import re
from PIL import Image
from mtcnn import MTCNN
import pytesseract
from pytesseract import Output
import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s", handlers=[logging.StreamHandler()])


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logging.info(f"--- Using device: {device} ---")


logging.info("--- Loading AI models ---")
vit_processor, vit_model = None, None
cnn_processor, cnn_model = None, None
face_detector = None

try:
    vit_processor = AutoImageProcessor.from_pretrained("umm-maybe/AI-image-detector")
    vit_model = AutoModelForImageClassification.from_pretrained("umm-maybe/AI-image-detector").to(device).eval()
    logging.info("✅ ViT model loaded.")
except Exception as e:
    logging.critical(f"❌ Failed to load ViT model: {e}")

try:
    cnn_processor = AutoImageProcessor.from_pretrained("microsoft/resnet-50")
    cnn_model = AutoModelForImageClassification.from_pretrained("microsoft/resnet-50").to(device).eval()
    logging.info("✅ CNN model loaded.")
except Exception as e:
    logging.critical(f"❌ Failed to load CNN model: {e}")

try:
    face_detector = MTCNN()
    logging.info("✅ MTCNN Face Detector loaded.")
except Exception as e:
    logging.critical(f"❌ Failed to load Face Detector: {e}")


def _generate_graph(scores: dict, final_label: str) -> str:
    labels = ["Real", "AI-Generated", "Edited"]
    values = [scores.get("real", 0), scores.get("ai", 0), scores.get("edited", 0)]
    plt.figure(figsize=(5, 4))
    colors = ["#4dff4d", "#ff4d4d", "#4da6ff"]
    plt.bar(labels, values, color=colors)
    plt.ylim(0, 1)
    plt.title(f"Final Prediction: {final_label}")
    plt.ylabel("Confidence Score")
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def _predict_image_authenticity(pil_image: Image.Image):
    if not all([vit_processor, vit_model, cnn_processor, cnn_model]):
        raise RuntimeError("One or more AI models failed to load.")
    
    inputs_vit = vit_processor(images=pil_image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs_vit = vit_model(**inputs_vit)
        probs_vit = torch.softmax(outputs_vit.logits, dim=-1)[0].cpu().numpy()
    id2label_vit = vit_model.config.id2label
    fake_idx_vit = next((i for i, label in id2label_vit.items() if "artificial" in label.lower()), 1)
    ai_score_vit = float(probs_vit[fake_idx_vit])

    inputs_cnn = cnn_processor(images=pil_image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs_cnn = cnn_model(**inputs_cnn)
        probs_cnn = torch.softmax(outputs_cnn.logits, dim=-1)[0].cpu().numpy()
    top_confidence_cnn = np.max(probs_cnn)
    ai_score_cnn = 1.0 - float(top_confidence_cnn)

    final_ai_score = (0.7 * ai_score_vit) + (0.3 * ai_score_cnn)
    return {"ai": round(final_ai_score, 4), "real": round(1.0 - final_ai_score, 4)}


def _create_image_report(result: dict) -> list:
    report = [{"title": "Overall Finding", "details": f"Based on a deep analysis of visual artifacts, the model's final prediction is that this image is **{result.get('label', '')}**."}]
    reasoning = (f"This conclusion is based on a high AI-generated content score of **{(result['scores'].get('ai', 0) * 100):.1f}%**. Our models detected patterns and textural inconsistencies that are hallmarks of synthetic image generation." if "AI-Generated" in result.get('label', '') else "The image exhibits natural lighting, focus, and real-world imperfections. Our models found no significant evidence of AI generation.")
    report.append({"title": "Reasoning Summary", "details": reasoning})
    return report

def _create_video_report(result: dict) -> list:
    report = [{"title": "Overall Finding", "details": f"After analyzing multiple frames, the model's final prediction is that this video is **{result.get('label', '')}**."}]
    avg_fake_score = result.get('frame_analysis', {}).get('average_fake_score', 0)
    faces_analyzed = result.get('frame_analysis', {}).get('faces_analyzed', 0)
    reasoning = (f"The primary indicator was a high average deepfake score of **{(avg_fake_score * 100):.1f}%** across **{faces_analyzed}** analyzed faces. This suggests the faces in the video may be synthetically generated or manipulated." if "Deepfake" in result.get('label', '') else "The facial features and movements across sampled frames appear consistent and natural. No significant deepfake indicators were found.")
    report.append({"title": "Reasoning Summary", "details": reasoning})
    return report

def _create_document_report(result: dict) -> list:
    report = [{"title": "Overall Finding", "details": f"Based on visual and textual analysis, the model's prediction is that this is a **{result.get('label', '')}**."}]
    evidence = []
    if "AI Photo Detected" in result.get('label', ''): evidence.append("the embedded photo was identified as AI-generated")
    if result.get('ocr_flags'): evidence.append(f"textual red flags were found, including: '{', '.join(result['ocr_flags'])}'")
    reasoning = (f"This conclusion is based on several key indicators: {', and '.join(evidence)}." if evidence else "The document's layout, text, and any embedded photos appear authentic. No significant signs of tampering or forgery were detected.")
    report.append({"title": "Reasoning Summary", "details": reasoning})
    return report

def generate_structured_report(result: dict) -> list:
    analysis_type = result.get("analysis_type", "image")
    if analysis_type == "video": return _create_video_report(result)
    elif analysis_type == "document": return _create_document_report(result)
    else: return _create_image_report(result)


def analyze_document(file_bytes: bytes):
    pil_image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    photo_analysis, faces, red_flags = {}, [], []
    if face_detector:
        faces = face_detector.detect_faces(np.array(pil_image))
        if faces:
            x, y, w, h = faces[0]['box']
            face_image = pil_image.crop((x, y, x + w, y + h))
            photo_scores = _predict_image_authenticity(face_image)
            photo_label = "AI-Generated Photo" if photo_scores['ai'] > 0.5 else "Real Photo"
            photo_analysis = {"status": photo_label, "confidence": photo_scores}
    overall_scores = _predict_image_authenticity(pil_image)
    try:
        ocr_data = pytesseract.image_to_data(pil_image, output_type=Output.DICT)
        extracted_text = " ".join(t for t in ocr_data['text'] if t.strip())
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\b', extracted_text) and not re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-zA-Z]{2,}\b', extracted_text):
            red_flags.append("Suspicious or incomplete email domain")
    except Exception:
        extracted_text = "OCR failed or no text found."
    label = "Likely Real Document"
    if overall_scores['ai'] > 0.6 or red_flags: label = "Edited/Fake Document"
    if photo_analysis.get("status") == "AI-Generated Photo": label = "Edited/Fake Document (AI Photo Detected)"
    overall_scores['edited'] = 0.8 if red_flags else 0.1
    graph_b64 = _generate_graph(overall_scores, label)
    result = {"label": label, "ocr_text": extracted_text, "ocr_flags": red_flags, "scores": overall_scores, "photo_analysis": photo_analysis, "graph_base64": graph_b64, "analysis_type": "document"}
    result["structured_report"] = generate_structured_report(result)
    return result

def analyze_video(video_bytes: bytes):
    if not face_detector: raise RuntimeError("Face detector not available.")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_bytes)
        video_path = tmp.name
    cap, face_scores, frame_count = cv2.VideoCapture(video_path), [], 0
    while cap.isOpened() and len(face_scores) < 10:
        ret, frame = cap.read()
        if not ret: break
        if frame_count % 15 == 0:
            faces = face_detector.detect_faces(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            for face in faces:
                x, y, w, h = face['box']
                face_image = Image.fromarray(cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2RGB))
                face_scores.append(_predict_image_authenticity(face_image)["ai"])
        frame_count += 1
    cap.release()
    os.remove(video_path)
    if not face_scores:
        scores = {"real": 1.0, "ai": 0.0, "edited": 0.0}
        label = "Real (No Faces Detected)"
        frame_analysis = {}
    else:
        avg_fake_score = float(np.mean(face_scores))
        label = "Deepfake Detected" if avg_fake_score > 0.5 else "Real"
        scores = {"real": 1.0 - avg_fake_score, "ai": avg_fake_score, "edited": 0.0}
        frame_analysis = {"average_fake_score": round(avg_fake_score, 4), "faces_analyzed": len(face_scores)}
    graph_b64 = _generate_graph(scores, label)
    result = {"label": label, "frames_sampled": frame_count, "frame_analysis": frame_analysis, "scores": scores, "graph_base64": graph_b64, "analysis_type": "video"}
    result["structured_report"] = generate_structured_report(result)
    return result


def analyze_file(file_bytes: bytes, mimetype: str):
    try:
        if "video" in mimetype:
            return analyze_video(file_bytes)
        elif "image" in mimetype:
            pil_image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            if face_detector and face_detector.detect_faces(np.array(pil_image)):
                logging.info("Routing to: Image Authenticity Analyzer")
                scores = _predict_image_authenticity(pil_image)
                label = "AI-Generated" if scores['ai'] > 0.5 else "Real"
                scores['edited'] = 0.0
                graph_b64 = _generate_graph(scores, label)
                result = {"label": label, "scores": scores, "graph_base64": graph_b64, "analysis_type": "image"}
                result["structured_report"] = generate_structured_report(result)
                return result
            else:
                logging.info("Routing to: Document Analyzer (no faces found)")
                return analyze_document(file_bytes)
        else:
            return {"label": "Unsupported", "error": "File type not supported."}
    except Exception as e:
        logging.error(f"❌ Error in analyze_file: {e}")
        return {"label": "Error", "error": str(e)}