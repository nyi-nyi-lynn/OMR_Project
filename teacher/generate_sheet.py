# teacher/generate_sheet.py
from PIL import Image, ImageDraw, ImageFont
import json, random, os

os.makedirs("assets", exist_ok=True)
os.makedirs("data", exist_ok=True)

def generate_omr_sheet(output_file="assets/omr_sheet.png", num_columns=1):
    """
    Generate a printable OMR sheet (PNG). Also creates data/layout.json:
    layout.json has structure:
    [
      {"printed_index": 1, "original_q_no": 5, "options": {"A": [x,y,w,h], ...}},
      ...
    ]
    Coordinates are pixel rectangles (x, y, w, h) for each bubble.
    """
    # load saved questions
    with open("data/questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)

    # if too many questions, use first 10 or whatever length
    n = len(questions)
    if n == 0:
        raise ValueError("No questions found in data/questions.json")

    # We'll layout for up to 20 questions comfortably on the page; adapt to n
    width, height = 800, 1100
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    draw.text((40, 30), "Student ID: ____________________", fill="black", font=font)

    start_y = 80
    line_height = 80
    bubble_radius = 10  # circle radius
    left_x = 60
    option_gap_x = 170  # horizontal distance between options
    text_gap = 30

    layout = []
    printed_index = 0

    # We'll place questions sequentially top->down
    for i, q in enumerate(questions, start=1):
        y = start_y + (i - 1) * line_height
        if y + 60 > height - 40:
            # page overflow - stop placing further questions
            break
        printed_index += 1
        draw.text((left_x, y), f"Q{printed_index}: {q['text']}", fill="black", font=font)

        options_coords = {}
        # place 4 options horizontally
        opt_x = left_x + 20
        for opt_idx, opt in enumerate(["A", "B", "C", "D"]):
            cx = opt_x + opt_idx * option_gap_x  # bubble center x
            cy = y + 30  # bubble center y
            # draw circle (ellipse)
            bx1 = cx - bubble_radius
            by1 = cy - bubble_radius
            bx2 = cx + bubble_radius
            by2 = cy + bubble_radius
            draw.ellipse((bx1, by1, bx2, by2), outline="black", width=2)
            # draw option text to the right
            draw.text((bx2 + 8, by1 - 2), f"{opt}: {q['choices'].get(opt,'')}", fill="black", font=font)

            # Save ROI as rectangle (x, y, w, h)
            options_coords[opt] = [int(bx1), int(by1), int(bx2 - bx1), int(by2 - by1)]

        layout.append({
            "printed_index": printed_index,
            "original_q_no": q.get("q_no", i),
            "options": options_coords
        })

    # Save image
    img.save(output_file)

    # Save layout mapping
    with open("data/layout.json", "w", encoding="utf-8") as f:
        json.dump(layout, f, indent=2)

    # Also save a copy of the printed order mapping (printed_index -> original q no)
    with open("data/printed_order.json", "w", encoding="utf-8") as f:
        printed_map = {entry["printed_index"]: entry["original_q_no"] for entry in layout}
        json.dump(printed_map, f, indent=2)

    print("OMR sheet generated:", output_file)
    print("Layout mapping saved to data/layout.json")
