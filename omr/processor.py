import cv2
import numpy as np


def detect_bubbles(frame):
    """
    Detect bubbles on OMR sheet and mark filled ones with green,
    unfilled with red. Returns modified frame and list of filled bubbles.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 150, 255, cv2.THRESH_BINARY_INV)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    filled_bubbles = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 500 < area < 2000:  # filter bubble size
            (x, y, w, h) = cv2.boundingRect(cnt)
            aspect_ratio = w / float(h)

            if 0.8 < aspect_ratio < 1.2:  # roughly circular
                roi = thresh[y:y+h, x:x+w]
                non_zero = cv2.countNonZero(roi)
                fill_ratio = non_zero / (w * h)

                if fill_ratio > 0.3:  # threshold for "filled"
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)  # GREEN
                    filled_bubbles.append((x, y))
                else:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 1)  # RED

    return frame, filled_bubbles


def realtime_scan(student_id, answer_key):
    """
    Open camera, detect bubbles in realtime, mark filled with green.
    Press 'q' to stop scanning and calculate dummy score.
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot access camera!")
        return {}, 0

    print(f"📷 Camera started for Student ID: {student_id}")
    student_answers = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Detect & mark bubbles
        frame, filled_bubbles = detect_bubbles(frame)

        # Show frame
        cv2.imshow("OMR Realtime Scan - Press 'q' to finish", frame)

        # Stop when 'q' pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # # Dummy mapping: assume all answers "A"
    for q in answer_key.keys():
        student_answers[q] = "A"

    score = sum(1 for q in answer_key if student_answers.get(q) == answer_key[q])
    print(f"✅ Scan complete for Student {student_id}: Score {score}/{len(answer_key)}")
    return student_answers, score


def scan_image(file_path):
    """
    Detect bubbles on a saved OMR sheet image (instead of realtime camera).
    """
    img = cv2.imread(file_path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {file_path}")

    frame, filled_bubbles = detect_bubbles(img)

    cv2.imshow("OMR Image Scan - Press any key to close", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Dummy answers (extend later with mapping)
    student_answers = {i+1: "A" for i in range(10)}
    score = sum(1 for v in student_answers.values() if v == "A")

    print(f"✅ Image scan complete. Score: {score}/10")
    return student_answers, score
