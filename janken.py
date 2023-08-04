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
    """
    ウィンドウを閉じる際の処理を行うコールバック関数。

    カメラを解放し、OpenCVで開いたウィンドウをすべて閉じ、
    そしてGUIのルートウィンドウを破棄します。
    """
    global cap
    cap.release()             # カメラを解放
    cv2.destroyAllWindows()  # OpenCVで開いたウィンドウをすべて閉じる
    root.destroy()          # GUIのルートウィンドウを破棄


def on_next_button_click():
    """
    「次へ」ボタンをクリックした際の処理を行うコールバック関数。

    1. 「次へ」ボタンを無効化（DISABLED）します。
    2. next_button_clicked変数をTrueに設定します。
    3. ランダムな遅延（5秒から15秒）を追加してから、show_next_question()関数を呼び出します。
    4. next_button_clicked変数をFalseに戻します。
    """
    global next_button, next_button_clicked
    next_button.config(state=tk.DISABLED)  # 「次へ」ボタンを無効化（クリック不可）にする
    next_button_clicked = True  # next_button_clicked変数をTrueに設定

    # 次の質問を表示する前に、ランダムな遅延（5秒から15秒）を追加します。
    root.after(random.randint(5000, 15000), show_next_question)

    next_button_clicked = False  # next_button_clicked変数をFalseに戻す


def show_next_question():
    """
    次の質問を表示する関数。

    1. 現在の質問インデックスを1つ進めます。
    2. まだ表示されていない質問が残っている場合、質問リストをシャッフルし、重複がないように質問を表示します。
    3. 全ての質問が表示されている場合、問題終了メッセージを表示し、「次へ」ボタンを無効化します。
    4. 問題遷移時の結果を表示します。
    """
    global current_question_index, current_question, next_button, flag, cap, questions_shown

    current_question_index = int(current_question_index) + 1  # 現在の質問インデックスを1つ進める

    if current_question_index <= len(questions_and_answers):
        # 質問をシャッフルし重複がないようにする
        remaining_questions = [i for i in range(len(questions_and_answers)) if i not in questions_shown]
        if len(remaining_questions) == 0:
            # 全ての質問が表示された場合
            question_label.config(text='全ての問題が終了しました！')
            next_button.config(state=tk.DISABLED)  # 「次へ」ボタンを無効化（クリック不可）にする
            return

        current_question_index = random.choice(remaining_questions)  # 残りの質問からランダムに選択
        questions_shown.append(current_question_index)  # 表示した質問リストに追加

        current_question = questions_and_answers[current_question_index]  # 選択した質問を取得
        update_question_display()  # GUI上の質問表示を更新
        next_button.config(state=tk.NORMAL)  # 「次へ」ボタンを有効化（クリック可能）にする

        # 問題遷移時の結果を表示
        show_result(current_question_index)  # 問題遷移時の結果を表示するための関数を呼び出す
    else:
        # 全ての質問が表示されている場合
        question_label.config(text='全ての問題が終了しました！')
        next_button.config(state=tk.DISABLED)  # 「次へ」ボタンを無効化（クリック不可）にする
        questions_shown = []  # 表示された質問リストをリセットして最初からやり直すために空にする


def update_question_display():
    """
    GUI上の質問と選択肢を更新する関数。

    現在の質問を取得し、GUIのラベルに設定します。
    選択肢を適切なフォーマットで取得し、GUIのラベルに設定します。
    """
    question_label.config(text=current_question["question"])  # 現在の質問をGUIのラベルに設定

    # 選択肢を適切なフォーマットで取得し、GUIのラベルに設定
    choices_text = "\n".join([f"{key} : {value['answer']}" for key, value in current_question["choices"].items()])
    answer_label.config(text=choices_text)


def create_frames(root):
    """
    GUIのフレームを作成する関数。

    1. ルートウィンドウに上部フレーム（高さ150ピクセル、背景色は白）を作成し配置します。
    2. ルートウィンドウに下部フレームを作成し配置します。
    3. 上部フレーム内に「次の問題」を表すボタンを作成し配置します。
    4. 下部フレームオブジェクトを返します。

    Args:
        root (tk.Tk): Tkinterのルートウィンドウオブジェクト。

    Returns:
        tk.Frame: 作成された下部フレームオブジェクト。
    """
    global next_button
    top_frame = tk.Frame(root, height=150, bg='white')  # 上部フレーム（高さ150ピクセル、背景色は白）を作成
    top_frame.pack(side=tk.TOP, fill=tk.X)  # ルートウィンドウの上部に配置

    bottom_frame = tk.Frame(root)  # 下部フレームを作成
    bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)  # ルートウィンドウの上部に配置

    next_button = tk.Button(top_frame, text='次の問題', command=on_next_button_click, font=('Helvetica', 16))
    next_button.pack()  # 「次の問題」を表すボタンを上部フレームに配置

    return bottom_frame  # 作成した下部フレームオブジェクトを返す


def update_frame():
    """
    GUIのフレームを更新する関数。

    1. グローバル変数からカメラからフレームを読み取ります。
    2. 読み取ったフレームをRGB形式に変換し、イメージオブジェクトに変換します。
    3. イメージをウィンドウのサイズにリサイズします。
    4. フレームをGUI上のラベルに表示します。
    5. オブジェクト検出を実行し、必要な処理を行います。
    6. 「次の問題」ボタンがクリックされた場合、次の質問を表示します。

    Note:
        この関数は、10ミリ秒後に再度自身を呼び出します（ループ）。
    """
    global flag, cap, next_button_clicked

    ret, frame = cap.read()  # カメラからフレームを読み取る
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # フレームをRGB形式に変換
        img = Image.fromarray(frame)  # イメージオブジェクトに変換
        img = img.resize((bottom_frame.winfo_width(), bottom_frame.winfo_height()), Image.LANCZOS)  # イメージをウィンドウサイズにリサイズ
        imgtk = ImageTk.PhotoImage(image=img)  # イメージをTkinter PhotoImageに変換
        video_label.imgtk = imgtk  # ラベルにイメージを保持
        video_label.configure(image=imgtk)  # ラベルにイメージを表示

        results = detect_objects(frame)  # オブジェクト検出を実行

        if process_detected_objects(frame, results) and not flag:
            return

        if next_button_clicked:
            next_button_clicked = False
            show_next_question()  # 「次の問題」ボタンがクリックされた場合、次の質問を表示

    root.after(10, update_frame)  # 10ミリ秒後に再度自身を呼び出す（ループ）


def detect_objects(frame):
    """
    モデルを使用してフレーム内のオブジェクトを検出する関数。

    Args:
        frame: オブジェクト検出を行うための画像フレーム。

    Returns:
        results: オブジェクト検出結果を保持するオブジェクト。
    """
    results = model(frame)  # モデルを使用してフレーム内のオブジェクトを検出
    return results  # オブジェクト検出結果を返す


def process_detected_objects(frame, results, threshold=0.91):
    """
    検出されたオブジェクトを処理する関数。

    Args:
        frame: カメラ画像フレーム。
        results: オブジェクト検出結果を保持するオブジェクト。
        threshold (float, optional): 検出結果を処理するための確信度のしきい値。デフォルトは0.91。

    Returns:
        bool: 正解の選択肢が検出された場合はTrue、それ以外はFalse。
    """
    global cap, flag, correct_choice_detected

    objects = results.pandas().xyxy[0]  # 検出されたオブジェクトの情報を取得

    for i in range(len(objects)):
        confidence = objects.confidence[i]

        if confidence > threshold:  # 確信度がしきい値以上の検出結果を処理
            name = objects.name[i]  # 検出されたオブジェクトのクラス名を取得
            print(f"{i}, {confidence}, 種類: {name}")

            # オブジェクトが正解の選択肢に含まれる場合の処理
            for choice_key, choice_value in current_question["choices"].items():
                if choice_value["is_correct"] and choice_key == name:
                    # カメラを解放し、検出されたオブジェクトを画像として保存
                    cap.release()
                    cv2.imwrite(f'{choice_key}_detected.jpg', frame)
                    detected_bgr_image = cv2.imread(f'{choice_key}_detected.jpg')
                    detected_rgb_image = cv2.cvtColor(detected_bgr_image, cv2.COLOR_BGR2RGB)

                    # 検出されたオブジェクトの周囲にバウンディングボックスを描画する．
                    x1, y1, x2, y2 = int(objects.xmin[i]), int(objects.ymin[i]), int(objects.xmax[i]), int(objects.ymax[i])
                    line_thickness = 5  # バウンディングボックスの線の太さを変更
                    bounding_box_color = (0,0,255)  # バウンディングボックスの色
                    cv2.rectangle(detected_rgb_image, (x1, y1), (x2, y2), bounding_box_color, line_thickness)

                    # バウンディングボックスの上部に名前と確信度を追加する．
                    text = f"{name}: {confidence:.2f}"
                    font_scale = 0.8  # フォントの大きさ
                    text_thickness = 1  # 文字の太さを変更する
                    text_color = (255,255,0)  # 色の変更
                    text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_thickness)
                    text_x = x1
                    text_y = max(y1 - 10, text_size[1] + 5)
                    cv2.putText(detected_rgb_image, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, text_thickness)

                    # ウィンドウに検出結果を表示し、カメラを再開する
                    cv2.imshow(f"Detected '{choice_key}'", detected_rgb_image)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
                    restart_camera(choice_key)

                    # フラグを設定して、正解が検出されたことを示す
                    flag = True
                    correct_choice_detected = True
                    return True

    # フラグを設定して、正解が検出されなかったことを示す
    correct_choice_detected = False
    return False


def restart_camera(choice_key=None):
    """
    カメラを再起動する関数。

    Args:
        choice_key (str or None, optional): 選択肢のキー。デフォルトはNone。

    Note:
        - グローバル変数の `cap` を解放（release）してカメラを停止します。
        - カメラを再起動するために `cv2.VideoCapture` を再度設定します。
        - `next_button` の状態を有効化（クリック可能）に戻します。
        - `choice_key` が与えられた場合は、関数 `show_result(current_question_index)` を呼び出します。
    """
    global cap, current_question_index

    cap.release()  # カメラを停止
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)  # カメラを再起動
    next_button.config(state=tk.NORMAL)  # 「次の問題」ボタンの状態を有効化（クリック可能）に戻す

    if choice_key is not None:
        show_result(current_question_index)  # `choice_key` が与えられた場合は結果表示を呼び出す


def show_result(current_question_index):
    """
    質問に対する結果表示を行う関数。

    Args:
        current_question_index (int): 現在の質問のインデックス。

    Note:
        - 現在の質問のインデックスが範囲内にある場合、正解の選択肢を探し、それを表示します。
        - 正解の選択肢が見つかった場合、選択肢のキーと回答を表示します。
    """
    current_question_index = int(current_question_index)

    if current_question_index >= 0 and current_question_index < len(questions_and_answers):
        current_question = questions_and_answers[current_question_index]

        for choice_key, choice_value in current_question["choices"].items():
            if choice_value["is_correct"]:
                print(f"Correct choice_key: {choice_key}, Answer: {choice_value['answer']}")
                return


if __name__ == "__main__":
    # Tkinterウィンドウのルートを作成
    root = tk.Tk()

    # ウィンドウを最大化
    root.state('zoomed')

    # スクリーンの幅と高さを取得
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # 現在の質問のインデックスを初期化
    current_question_index = 0

    # 現在の質問を質問と回答のリストから取得
    current_question = questions_and_answers[current_question_index]


    # 正解の選択肢を探し、表示する
    for choice_key, choice_value in current_question["choices"].items():
        if choice_value["is_correct"]:
            print("正解:", choice_key)

    # Tkinterウィンドウの下部フレームを作成
    bottom_frame = create_frames(root)

    # 質問を表示するラベルを作成してパック（配置）
    question_label = tk.Label(bottom_frame, text='', bg='white', font=('Helvetica', 30), anchor='w')
    question_label.pack()

    # 回答を表示するラベルを作成してパック（配置）
    answer_label = tk.Label(bottom_frame, text='', bg='white', font=('Helvetica', 20))
    answer_label.pack()

    # モデルを読み込む
    model_path = './yolov5/best_goochokipar.pt'
    if os.path.isfile(model_path):
        model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
        print("モデルが読み込まれました")
    else:
        print("指定したモデルが見つかりません")
        exit()

    # カメラをキャプチャするためにOpenCVを使用
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    # ビデオラベルを作成してパック（配置）
    video_label = tk.Label(bottom_frame)
    video_label.pack()

    # カメラからのフレーム更新を行う関数
    update_frame()

    # 質問の表示を更新する関数
    update_question_display()

    # ウィンドウが閉じられたときに実行する処理を設定
    root.protocol("WM_DELETE_WINDOW", on_close)

    # Tkinterウィンドウのメインループを開始
    root.mainloop()
