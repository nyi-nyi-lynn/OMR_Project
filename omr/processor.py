from tkinter import messagebox

import cv2
import numpy as np

from omr import utlis


def detect_bubbles(img, answer_key):
    widthImg = 600
    heightImg = 400
    questions = len(answer_key)
    choices = len(answer_key)
    myIndex = []
    score =0
    ans = []

    try:
        img = cv2.resize(img, (widthImg, heightImg))  # RESIZE IMAGE
        imgFinal = img.copy()
        imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)
        imgCanny = cv2.Canny(imgBlur, 10, 70)

        # find all contours
        imgContours = img.copy()  # COPY IMAGE FOR DISPLAY PURPOSES
        imgBigContour = img.copy()  # COPY IMAGE FOR DISPLAY PURPOSES
        contours, _ = cv2.findContours(imgCanny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        rectCon = utlis.rectContour(contours)  # FILTER FOR RECTANGLE CONTOURS
        if len(rectCon) < 1:
            print("⚠️ No OMR Sheet detected!")
            cv2.putText(img, "! No OMR Sheet detected!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return img,score,myIndex

        biggestPoints = utlis.getCornerPoints(rectCon[0])
        gradePoints = utlis.getCornerPoints(rectCon[1]) if len(rectCon) > 1 else None

        if biggestPoints.size != 0 and gradePoints is not None and gradePoints.size != 0:
            # WARP MAIN OMR
            biggestPoints = utlis.reorder(biggestPoints)
            pts1 = np.float32(biggestPoints)
            pts2 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]])
            matrix = cv2.getPerspectiveTransform(pts1, pts2)
            imgWarpColored = cv2.warpPerspective(img, matrix, (widthImg, heightImg))

            # SECOND BIGGEST RECTANGLE WARPING
            cv2.drawContours(imgBigContour, gradePoints, -1, (255, 0, 0), 20)  # DRAW THE BIGGEST CONTOUR
            gradePoints = utlis.reorder(gradePoints)  # REORDER FOR WARPING
            ptsG1 = np.float32(gradePoints)  # PREPARE POINTS FOR WARP
            ptsG2 = np.float32([[0, 0], [325, 0], [0, 150], [325, 150]])  # PREPARE POINTS FOR WARP
            matrixG = cv2.getPerspectiveTransform(ptsG1, ptsG2)  # GET TRANSFORMATION MATRIX
            imgGradeDisplay = cv2.warpPerspective(img, matrixG, (325, 150))  # APPLY WARP PERSPECTIVE

            # APPLY THRESHOLD
            imgWarpGray = cv2.cvtColor(imgWarpColored, cv2.COLOR_BGR2GRAY)
            imgThresh = cv2.threshold(imgWarpGray, 170, 255, cv2.THRESH_BINARY_INV)[1]
            # cv2.imshow("Thredshow",imgThresh)
            boxes = utlis.splitBoxes(imgThresh)  # GET INDIVIDUAL BOXES
            myPixelVal = np.zeros((questions, choices))  # TO STORE THE NON ZERO VALUES OF EACH BOX

            countR = 0
            countC = 0
            for image in boxes:
                totalPixels = cv2.countNonZero(image)
                myPixelVal[countR][countC] = totalPixels
                countC += 1
                if countC == choices:
                    countC = 0
                    countR += 1

            # FIND THE USER ANSWERS
            for x in range(0, questions):
                arr = myPixelVal[x]
                myIndexVal = np.where(arr == np.amax(arr))
                myIndex.append(int(myIndexVal[0][0]))  # save student answer index

            print("Student Answers:", myIndex)

            # COMPARE WITH ANSWER KEY
            grading = []
            for i in range(questions):
                student_answer = myIndex[i]
                correct_answer = answer_key.get(i + 1, -1) # dict starts at 1
                ans.append(correct_answer)
                if student_answer == correct_answer:
                    grading.append(1)
                else:
                    grading.append(0)
            score = (sum(grading) / questions) * 100
            print("SCORE:", score)


            # DISPLAYING ANSWERS
            utlis.showAnswers(imgWarpColored, myIndex, grading, ans,questions,choices)  # DRAW DETECTED ANSWERS
            utlis.drawGrid(imgWarpColored)  # DRAW GRID
            imgRawDrawings = np.zeros_like(imgWarpColored)  # NEW BLANK IMAGE WITH WARP IMAGE SIZE
            utlis.showAnswers(imgRawDrawings, myIndex, grading, myIndex)  # DRAW ON NEW IMAGE
            invMatrix = cv2.getPerspectiveTransform(pts2, pts1)  # INVERSE TRANSFORMATION MATRIX
            imgInvWarp = cv2.warpPerspective(imgRawDrawings, invMatrix, (widthImg, heightImg))  # INV IMAGE WARP

            # DISPLAY GRADE
            imgRawGrade = np.zeros_like(imgGradeDisplay, np.uint8)  # NEW BLANK IMAGE WITH GRADE AREA SIZE
            cv2.putText(imgRawGrade, str(int(score)) + "%", (70, 100)
                        , cv2.FONT_HERSHEY_COMPLEX, 3, (0, 255, 255), 3)  # ADD THE GRADE TO NEW IMAGE
            invMatrixG = cv2.getPerspectiveTransform(ptsG2, ptsG1)  # INVERSE TRANSFORMATION MATRIX
            imgInvGradeDisplay = cv2.warpPerspective(imgRawGrade, invMatrixG, (widthImg, heightImg))  # INV IMAGE WARP

            # SHOW ANSWERS AND GRADE ON FINAL IMAGE
            imgFinal = cv2.addWeighted(imgFinal, 1, imgInvWarp, 1, 0)
            imgFinal = cv2.addWeighted(imgFinal, 1, imgInvGradeDisplay, 1, 0)



    except Exception as e:
        print("Error in detect_bubbles:", e)

    return imgFinal,score,myIndex

def realtime_scan(student_id, answer_key):
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

        frame, score, myIndex = detect_bubbles(frame, answer_key)

        # Convert list to dict with question numbers starting from 1
        answers = {i + 1: ans for i, ans in enumerate(myIndex)}

        # Map numeric index to letters
        index_to_letter = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E"}

        # Apply mapping
        answers = {q_no: index_to_letter.get(ans, "-") for q_no, ans in answers.items()}

        # Show frame
        cv2.imshow("OMR Realtime Scan - Press 'q' to finish", frame)

        # Store detected answers
        student_answers.update(answers)

        # Stop when 'q' pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    score = (score/100) * len(answer_key)
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


