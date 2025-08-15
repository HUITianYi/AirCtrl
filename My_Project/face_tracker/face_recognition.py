import cv2
import numpy as np
import os
import shutil
import threading
import tkinter as tk
from PIL import Image, ImageTk

# 获取当前脚本所在的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 构建所有文件的绝对路径
CONFIG_PATH = os.path.join(BASE_DIR, 'config.txt')
HAARCASCADE_PATH = os.path.join(BASE_DIR, 'haarcascade_frontalface_default.xml')
DATA_DIR = os.path.join(BASE_DIR, 'data')

# 首先读取config文件，第一行代表当前已经储存的人名个数，接下来每一行是（id，name）标签和对应的人名
id_dict = {}  # 字典里存的是id——name键值对
Total_face_num = 999  # 已经被识别有用户名的人脸个数

def init():  # 将config文件内的信息读入到字典中
    global Total_face_num
    try:
        with open(CONFIG_PATH, 'r') as f:
            Total_face_num = int(f.readline().strip())
            
            for i in range(Total_face_num):
                line = f.readline().strip()
                if line:
                    id_name = line.split(' ')
                    if len(id_name) >= 2:
                        id_dict[int(id_name[0])] = ' '.join(id_name[1:])
    except Exception as e:
        print(f"初始化错误: {e}")
        Total_face_num = 0

init()

# 加载OpenCV人脸检测分类器Haar
face_cascade = cv2.CascadeClassifier(HAARCASCADE_PATH)

# 准备好识别方法LBPH方法
recognizer = cv2.face.LBPHFaceRecognizer_create()

# 打开标号为0的摄像头
camera = cv2.VideoCapture(0)  # 摄像头
success, img = camera.read()  # 从摄像头读取照片
if camera.isOpened():
    W_size = 0.1 * camera.get(3)
    H_size = 0.1 * camera.get(4)
else:
    W_size, H_size = 50, 50  # 默认值

system_state_lock = 0  # 标志系统状态的量 0表示无子线程在运行 1表示正在刷脸 2表示正在录入新面孔。

def Get_new_face():
    print("正在从摄像头录入新人脸信息 \n")

    if not os.path.exists(DATA_DIR):
        os.mkdir(DATA_DIR)
    else:
        # 清空目录但保留目录本身
        for filename in os.listdir(DATA_DIR):
            file_path = os.path.join(DATA_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f'删除文件失败: {file_path}. 原因: {e}')

    sample_num = 0  # 已经获得的样本数
    pictur_num = 30  # 控制拍摄的图片数量

    while sample_num < pictur_num:
        global success
        global img
        success, img = camera.read()

        if success:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                sample_num += 1
                img_path = os.path.join(DATA_DIR, f"User.{Total_face_num}.{sample_num}.jpg")
                cv2.imwrite(img_path, gray[y:y + h, x:x + w])

        l = int(sample_num / pictur_num * 50)
        r = int((pictur_num - sample_num) / pictur_num * 50)
        print(f"\r{sample_num / pictur_num * 100:.1f}% ={'=' * l}->{'_' * r}", end="")
        var.set(f"采集进度: {sample_num / pictur_num * 100:.1f}%")
        window.update()  # 实时更新进度条

    print("采集完毕，开始训练")
    Train_new_face()

def Train_new_face():
    print("\n正在训练")
    recog = cv2.face.LBPHFaceRecognizer_create()

    faces, ids = get_images_and_labels(DATA_DIR)
    print('本次用于训练的识别码为:')
    print(ids)

    if len(ids) > 0:
        recog.train(faces, np.array(ids))
        yml_path = os.path.join(BASE_DIR, f"{Total_face_num}.yml")
        recog.save(yml_path)

        # 更新配置文件
        write_config()
    else:
        print("错误: 未找到训练数据")

def get_images_and_labels(path):
    face_samples = []
    ids = []
    
    if not os.path.exists(path):
        return face_samples, ids
        
    image_paths = [os.path.join(path, f) for f in os.listdir(path) if f.endswith('.jpg')]
    
    for image_path in image_paths:
        try:
            img = Image.open(image_path).convert('L')
            img_np = np.array(img, 'uint8')

            filename = os.path.split(image_path)[-1]
            parts = filename.split(".")
            if len(parts) >= 3 and parts[0] == "User":
                id = int(parts[1])
                
                detector = cv2.CascadeClassifier(HAARCASCADE_PATH)
                faces = detector.detectMultiScale(img_np)

                for (x, y, w, h) in faces:
                    face_samples.append(img_np[y:y + h, x:x + w])
                    ids.append(id)
        except Exception as e:
            print(f"处理图像 {image_path} 时出错: {e}")
            
    return face_samples, ids

def write_config():
    print("新人脸训练结束")
    # 更新第一行的总人数
    try:
        with open(CONFIG_PATH, 'r') as f:
            lines = f.readlines()
            
        if len(lines) > 0:
            lines[0] = f"{int(lines[0].strip()) + 1}\n"
        else:
            lines.append("1\n")
            
        # 添加新用户
        new_user = f"{Total_face_num} User{Total_face_num}\n"
        lines.append(new_user)
        
        with open(CONFIG_PATH, 'w') as f:
            f.writelines(lines)
            
        id_dict[Total_face_num] = f"User{Total_face_num}"
        print(f"已添加新用户: User{Total_face_num}")
    except Exception as e:
        print(f"更新配置文件失败: {e}")

def scan_face():
    for i in range(1, Total_face_num + 1):
        yml_path = os.path.join(BASE_DIR, f"{i}.yml")
        if not os.path.exists(yml_path):
            print(f"跳过缺失的模型文件: {yml_path}")
            continue
            
        print(f"\n使用模型: {yml_path}")
        recognizer.read(yml_path)

        ave_poss = 0
        for times in range(10):
            cur_poss = 0
            global success
            global img
            while system_state_lock == 2:
                pass
            success, img = camera.read()
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(int(W_size), int(H_size)))

            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                idnum, confidence = recognizer.predict(gray[y:y + h, x:x + w])
                if confidence < 100:
                    user_name = id_dict.get(idnum, f"Untagged user:{idnum}")
                    conf_value = round(100 - confidence)
                else:
                    user_name = "unknown"
                    conf_value = 0

                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(img, str(user_name), (x + 5, y - 5), font, 1, (0, 0, 255), 1)
                cv2.putText(img, f"{conf_value}%", (x + 5, y + h - 5), font, 1, (0, 0, 0), 1)

                if 15 < conf_value < 100:
                    cur_poss = 1
                else:
                    cur_poss = 0

            ave_poss += cur_poss

        if ave_poss >= 5:
            return i

    return 0

def f_scan_face_thread():
    var.set('正在刷脸...')
    ans = scan_face()
    if ans == 0:
        result = "最终结果：无法识别"
        print(result)
        var.set(result)
    else:
        ans_name = f"最终结果：{id_dict[ans]} (ID:{ans})"
        print(ans_name)
        var.set(ans_name)

    global system_state_lock
    system_state_lock = 0  # 释放锁
    print("刷脸完成，锁已释放")

def f_scan_face():
    global system_state_lock
    print("\n当前锁状态:", system_state_lock)
    if system_state_lock != 0:
        print("操作被阻塞 - 系统忙")
        var.set("系统忙，请稍后再试")
        return
        
    system_state_lock = 1
    print("开始刷脸，锁状态:", system_state_lock)
    threading.Thread(target=f_scan_face_thread, daemon=True).start()

def f_rec_face_thread():
    var.set('正在录入人脸...')
    global Total_face_num
    Total_face_num += 1
    Get_new_face()
    print("采集完毕，开始训练")
    Train_new_face()
    
    global system_state_lock
    system_state_lock = 0
    print("录入完成，锁已释放")
    var.set(f"新用户添加成功: User{Total_face_num}")

def f_rec_face():
    global system_state_lock
    print("当前锁状态:", system_state_lock)
    if system_state_lock != 0:
        print("操作被阻塞 - 系统忙")
        var.set("系统忙，请稍后再试")
        return
        
    system_state_lock = 2
    print("开始录入，锁状态:", system_state_lock)
    threading.Thread(target=f_rec_face_thread, daemon=True).start()

def f_exit():
    camera.release()
    cv2.destroyAllWindows()
    window.destroy()
    exit()

# 创建主窗口
window = tk.Tk()
window.title('人脸识别系统')
window.geometry('1000x500')

# 状态显示
var = tk.StringVar(value="就绪")
status_label = tk.Label(window, textvariable=var, bg='#4CAF50', fg='white', 
                      font=('Arial', 14), width=50, height=2, relief='ridge')
status_label.pack(pady=10)

# 视频显示区域
panel = tk.Label(window, width=640, height=480)
panel.place(x=20, y=60)

# 按钮区域
button_frame = tk.Frame(window)
button_frame.place(x=700, y=100)

tk.Button(button_frame, text='开始刷脸', font=('Arial', 12), width=15, height=2, 
         command=f_scan_face, bg='#2196F3', fg='white').pack(pady=10)

tk.Button(button_frame, text='录入人脸', font=('Arial', 12), width=15, height=2, 
         command=f_rec_face, bg='#FF9800', fg='white').pack(pady=10)

tk.Button(button_frame, text='退出系统', font=('Arial', 12), width=15, height=2, 
         command=f_exit, bg='#F44336', fg='white').pack(pady=10)

# 信息标签
info_label = tk.Label(window, text="操作说明: \n1. 点击'开始刷脸'进行人脸识别\n2. 点击'录入人脸'添加新用户\n3. 确保摄像头正常工作",
                    font=('Arial', 10), justify=tk.LEFT)
info_label.place(x=700, y=280)

# 视频流处理
def video_loop():
    global success
    global img
    if camera.isOpened():
        success, img = camera.read()
        if success:
            # 显示系统状态
            if system_state_lock == 1:
                cv2.putText(img, "状态: 识别中", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            elif system_state_lock == 2:
                cv2.putText(img, "状态: 录入中", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # 转换并显示图像
            cv2image = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
            current_image = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=current_image)
            panel.imgtk = imgtk
            panel.config(image=imgtk)
    
    window.after(10, video_loop)

# 启动视频流
video_loop()

# 启动主循环
window.mainloop()

# 释放摄像头资源
camera.release()
cv2.destroyAllWindows()
