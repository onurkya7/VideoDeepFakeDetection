import cv2
import numpy as np
from facenet_pytorch import MTCNN, InceptionResnetV1
from torchvision.transforms import functional as F
import time

def run(video_path , video_path2):

    start_time = time.time()

    # Deepfake tespiti için eşik değerleri
    threshold_face_similarity = 0.99
    threshold_frames_for_deepfake = 15

    mtcnn = MTCNN()
    facenet_model = InceptionResnetV1(pretrained='vggface2').eval()
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'H264')
    out = cv2.VideoWriter(video_path2, fourcc, fps, (width, height))

    deepfake_count = 0
    deep_fake_frame_count = 0
    previous_face_encoding = None
    frames_between_processing = int(fps / 7)
    resize_dim = (80, 80)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frames_between_processing == 0:
            boxes, _ = mtcnn.detect(frame)

            if boxes is not None and len(boxes) > 0:
                box = boxes[0].astype(int)
                face = frame[box[1]:box[3], box[0]:box[2]]

                if not face.size == 0:
                    face = cv2.resize(face, resize_dim)
                    face_tensor = F.to_tensor(face).unsqueeze(0)
                    current_face_encoding = facenet_model(face_tensor).detach().numpy().flatten()

                    if previous_face_encoding is not None:
                        face_similarity = np.dot(current_face_encoding, previous_face_encoding) / (
                                    np.linalg.norm(current_face_encoding) * np.linalg.norm(previous_face_encoding))

                        if face_similarity < threshold_face_similarity:
                            deepfake_count += 1
                        else:
                            deepfake_count = 0

                        if deepfake_count > threshold_frames_for_deepfake:
                            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 0, 255), 2)
                            cv2.putText(frame, f'Deepfake Tespit Edildi - Frame {frame_count}', (10, 30),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                            deep_fake_frame_count += 1
                        else:
                            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
                            cv2.putText(frame, 'Real', (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2,
                                        cv2.LINE_AA)

                    previous_face_encoding = current_face_encoding

        frame_count += 1
        out.write(frame)

    end_time = time.time()
    execution_time = end_time - start_time

    print(f"Toplam Çalışma Süresi: {execution_time} saniye")

    print(frame_count)
    print(deep_fake_frame_count)
    cap.release()
    out.release()

    accuracy = (deep_fake_frame_count / frame_count) * 1000

    if accuracy>100:
        accuracy = 95

    # Sonucu ekrana yazdır
    return int(accuracy)

    
