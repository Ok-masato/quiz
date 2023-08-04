import tkinter as tk
import cv2
from PIL import Image, ImageTk
from data import questions_and_answers
import random
import os
import torch

next_button_clicked = False
correct_choice_detected = False
flag = True

#表示した質問を配列に追加していく，因みにチュートリアルは一度のみの表示にするため，あらかじめ追加．
questions_shown = [0]

def on_close():
    global cap
    cap.release()
    cv2.destroyAllWindows()
    root.destroy()

def on_next_button_click():
    global next_button, next_button_clicked
    next_button.config(state=tk.DISABLED)
    next_button_clicked = True

    # 次の質問を表示する前に、ランダムな遅延（5秒から15秒）を追加します。
    root.after(random.randint(5000, 15000), show_next_question)
    next_button_clicked = False

def show_next_question():
    global current_question_index, current_question, next_button, flag, cap, questions_shown

    current_question_index = int(current_question_index) + 1

    if current_question_index <= len(questions_and_answers):
        # 質問をシャッフルし重複がないようにする
        remaining_questions = [i for i in range(len(questions_and_answers)) if i not in questions_shown]
        if len(remaining_questions) == 0:
            # 全ての質問が表示された場合
            question_label.config(text='全ての問題が終了しました！')
            next_button.config(state=tk.DISABLED)
            return

        current_question_index = random.choice(remaining_questions)
        questions_shown.append(current_question_index)

        current_question = questions_and_answers[current_question_index]
        update_question_display()
        next_button.config(state=tk.NORMAL)

        # 問題遷移時の結果を表示
        show_result(current_question_index)
    else:
        # 全て質問が表示されている
        question_label.config(text='全ての問題が終了しました！')
         # 全ての質問が終了した場合に「次へ」ボタンを無効にする
        next_button.config(state=tk.DISABLED)
        #表示されている質問リストをリセットして最初からやり直す
        questions_shown = [] 



def update_question_display():
    question_label.config(text=current_question["question"])

    choices_text = "\n".join([f"{key} : {value['answer']}" for key, value in current_question["choices"].items()])
    answer_label.config(text=choices_text)

def create_frames(root):
    global next_button
    top_frame = tk.Frame(root, height=150, bg='white')
    top_frame.pack(side=tk.TOP, fill=tk.X)

    bottom_frame = tk.Frame(root)
    bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    next_button = tk.Button(top_frame, text='次の問題', command=on_next_button_click, font=('Helvetica', 16))
    next_button.pack()

    return bottom_frame

def update_frame():
    global flag, cap, next_button_clicked

    ret, frame = cap.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        img = img.resize((bottom_frame.winfo_width(), bottom_frame.winfo_height()), Image.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)

        results = detect_objects(frame)

        if process_detected_objects(frame, results) and not flag:
            return
        
        if next_button_clicked:
            next_button_clicked = False
            show_next_question()

    root.after(10, update_frame)

def detect_objects(frame):
    results = model(frame)
    return results

def process_detected_objects(frame, results, threshold=0.91):
    global cap, flag, correct_choice_detected

    objects = results.pandas().xyxy[0]
    for i in range(len(objects)):
        confidence = objects.confidence[i]

        if confidence > threshold:
            name = objects.name[i]
            print(f"{i}, {confidence}, 種類: {name}")

            for choice_key, choice_value in current_question["choices"].items():
                if choice_value["is_correct"] and choice_key == name:
                    cap.release()
                    cv2.imwrite(f'{choice_key}_detected.jpg', frame)
                    detected_bgr_image = cv2.imread(f'{choice_key}_detected.jpg')
                    detected_rgb_image = cv2.cvtColor(detected_bgr_image, cv2.COLOR_BGR2RGB)

                    # 検出されたオブジェクトの周囲にバウンディングボックスを描画する．
                    x1, y1, x2, y2 = int(objects.xmin[i]), int(objects.ymin[i]), int(objects.xmax[i]), int(objects.ymax[i])
                    line_thickness = 5  # バウンディングボックスの線の太さを変更
                    bounding_box_color = (0,0,255)  #バウンディングボックスの色
                    cv2.rectangle(detected_rgb_image, (x1, y1), (x2, y2), bounding_box_color, line_thickness)

                    #バウンディングボックスの上部に名前と閾値を追加する．
                    text = f"{name}: {confidence:.2f}"
                    font_scale = 0.8  # フォントの大きさ
                    text_thickness = 1  # 文字の太さを変更する
                    text_color = (255,255,0)  # 色の変更
                    text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_thickness)
                    text_x = x1
                    text_y = max(y1 - 10, text_size[1] + 5)
                    cv2.putText(detected_rgb_image, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, text_thickness)

                    cv2.imshow(f"Detected '{choice_key}'", detected_rgb_image)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
                    restart_camera(choice_key)
                    flag = True
                    correct_choice_detected = True
                    return True

    correct_choice_detected = False
    return False


def restart_camera(choice_key=None):
    global cap, current_question_index
    cap.release()
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    next_button.config(state=tk.NORMAL)
    if choice_key is not None:
        show_result(current_question_index)

def show_result(current_question_index):
    current_question_index = int(current_question_index)
    if current_question_index >= 0 and current_question_index < len(questions_and_answers):
        current_question = questions_and_answers[current_question_index]
        for choice_key, choice_value in current_question["choices"].items():
            if choice_value["is_correct"]:
                print(f"Correct choice_key: {choice_key}, Answer: {choice_value['answer']}")
                return

if __name__ == "__main__":
    root = tk.Tk()
    root.state('zoomed')

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    current_question_index = 0
    current_question = questions_and_answers[current_question_index]

    for choice_key, choice_value in current_question["choices"].items():
        if choice_value["is_correct"]:
            print("正解:", choice_key)

    bottom_frame = create_frames(root)
    question_label = tk.Label(bottom_frame, text='', bg='white', font=('Helvetica', 30), anchor='w')
    question_label.pack()
    answer_label = tk.Label(bottom_frame, text='', bg='white', font=('Helvetica', 20))
    answer_label.pack()

    model_path = './yolov5/best_goochokipar.pt'
    if os.path.isfile(model_path):
        model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
        print("モデルが読み込まれました")
    else:
        print("指定したモデルが見つかりません")
        exit()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) 
    video_label = tk.Label(bottom_frame)
    video_label.pack()
    
    update_frame()
    update_question_display()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
