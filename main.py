import tkinter as tk
from tkinter import ttk
import json
import random
import os
import hashlib
from tkinter import messagebox
import time
import pyttsx3
from ttkthemes import ThemedStyle
from tkinter import filedialog
import shutil
from datetime import datetime


# 全局变量
current_user = None
words = []
current_word_index = 0
current_wordbook = "KaoYan_2.json"  # 默认词库
start_time = None  # 添加学习开始时间变量

# 初始化语音引擎
engine = pyttsx3.init()

# 设置语音属性
engine.setProperty('rate', 150)  # 语速
engine.setProperty('volume', 0.9)  # 音量

# 记录学习开始时间
def start_learning():
    if not current_user:
        messagebox.showinfo("提示", "请先登录以开始学习！")
        return
    global start_time
    start_time = time.time()
    messagebox.showinfo("提示", "开始记录学习时间！")

# 记录学习结束时间并统计时长
def end_learning():
    if not current_user:
        messagebox.showinfo("提示", "请先登录以结束学习！")
        return
    global start_time
    if start_time is not None:
        end_time = time.time()
        duration = end_time - start_time
        # 保存学习时长到文件
        save_learning_duration(duration)
        messagebox.showinfo("学习结束", f"本次学习时长: {duration/60:.1f} 分钟")
        start_time = None
    else:
        messagebox.showinfo("提示", "还未开始学习！")

# 显示总学习时长
def show_total_learning_time():
    if not current_user:
        messagebox.showinfo("提示", "请先登录以查看学习时长！")
        return
    
    learning_record_file = f'learning_record_{current_user}.json'
    if not os.path.exists(learning_record_file):
        messagebox.showinfo("提示", "暂无学习记录！")
        return
    
    try:
        with open(learning_record_file, 'r', encoding='utf-8') as file:
            records = json.load(file)
            total_duration = sum(record["duration"] for record in records)
            total_minutes = total_duration / 60
            total_hours = total_minutes / 60
            
            # 获取最近一次学习时间
            if records:
                last_record = records[-1]
                last_time = last_record["time"]
                messagebox.showinfo("学习统计", 
                    f"总学习时长：{total_hours:.1f} 小时\n"
                    f"最近学习时间：{last_time}")
            else:
                messagebox.showinfo("学习统计", "暂无学习记录！")
    except Exception as e:
        messagebox.showerror("错误", f"读取学习记录时出错：{str(e)}")

# 保存学习时长
def save_learning_duration(duration):
    if current_user:
        learning_record_file = f'learning_record_{current_user}.json'
        records = []
        if os.path.exists(learning_record_file):
            try:
                with open(learning_record_file, 'r', encoding='utf-8') as file:
                    records = json.load(file)
            except json.JSONDecodeError:
                records = []
        records.append({"duration": duration, "time": time.strftime("%Y-%m-%d %H:%M:%S")})
        with open(learning_record_file, 'w', encoding='utf-8') as file:
            json.dump(records, file, ensure_ascii=False, indent=4)

# 用户数据管理
def get_user_memory_file(username):
    return f'memory_{username}.json'


def get_user_wrong_words_file(username):
    return f'wrong_words_{username}.json'


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# 加载单词数据
def load_words():
    try:
        with open(current_wordbook, 'r', encoding='utf-8') as file:
            words = json.load(file)
            # 加载记忆数据
            if current_user and os.path.exists(get_user_memory_file(current_user)):
                try:
                    with open(get_user_memory_file(current_user), 'r', encoding='utf-8') as mem_file:
                        memory = json.load(mem_file)
                        for word in words:
                            if word["headWord"] in memory:
                                word["count"] = memory[word["headWord"]]["count"]
                                if memory[word["headWord"]]["marked"]:
                                    word["marked"] = True
                            else:
                                word["count"] = 0
                except FileNotFoundError:
                    for word in words:
                        word["count"] = 0
            else:
                for word in words:
                    word["count"] = 0
            return words
    except FileNotFoundError:
        print("文件未找到，请检查文件路径。")
        return []


# 保存记忆数据
def save_memory():
    if current_user:
        memory = {word["headWord"]: {"count": word["count"], "marked": "marked" in word} for word in words}
        with open(get_user_memory_file(current_user), 'w', encoding='utf-8') as file:
            json.dump(memory, file, ensure_ascii=False, indent=4)


# 显示当前单词信息
def show_current_word():
    global current_word_index
    if not current_user:
        word_label.config(text="请先登录以使用单词背诵功能")
        trans_label.config(text="")
        sentence_text_widget.delete('1.0', tk.END)
        phrase_text_widget.delete('1.0', tk.END)
        count_label.config(text="")
        return

    if 0 <= current_word_index < len(words):
        word = words[current_word_index]
        word_label.config(text=word["headWord"])
        trans_text = "\n".join([f"{trans['pos']}. {trans['tranCn']}" for trans in word["content"]["word"]["content"]["trans"]])
        trans_label.config(text=trans_text)

        # 显示例句
        sentences = word["content"]["word"]["content"]["sentence"]["sentences"]
        sentence_text = "\n\n".join([f"{sent['sContent']}\n{sent['sCn']}" for sent in sentences])
        sentence_text_widget.delete('1.0', tk.END)
        sentence_text_widget.insert(tk.END, sentence_text)

        # 显示短语
        if "phrase" in word["content"]["word"]["content"]:
            phrases = word["content"]["word"]["content"]["phrase"]["phrases"]
            phrase_text = "\n\n".join([f"{phrase['pContent']}\n{phrase['pCn']}" for phrase in phrases])
            phrase_text_widget.delete('1.0', tk.END)
            phrase_text_widget.insert(tk.END, phrase_text)
        else:
            phrase_text_widget.delete('1.0', tk.END)
            phrase_text_widget.insert(tk.END, "无短语信息")

        # 增加单词出现次数
        word["count"] = word.get("count", 0) + 1
        save_memory()

        # 显示出现次数
        count_label.config(text=f"出现次数: {word['count']}")

        # 根据当前单词是否被标记来更新mark_button的文本
        if 'marked' in word:
            mark_button.config(text="已标记")
        else:
            mark_button.config(text="标记单词")
    else:
        word_label.config(text="所有单词已背完！")
        trans_label.config(text="")
        sentence_text_widget.delete('1.0', tk.END)
        phrase_text_widget.delete('1.0', tk.END)
        count_label.config(text="")
        next_button.config(state=tk.DISABLED)
        prev_button.config(state=tk.DISABLED)
        random_button.config(state=tk.DISABLED)


# 下一个单词
def next_word():
    global current_word_index
    current_word_index += 1
    show_current_word()


# 上一个单词
def prev_word():
    global current_word_index
    current_word_index -= 1
    show_current_word()


# 随机单词
def random_word():
    global current_word_index
    current_word_index = random.randint(0, len(words) - 1)
    show_current_word()


# 标记单词
def mark_word():
    global current_word_index
    if 0 <= current_word_index < len(words):
        word = words[current_word_index]
        if 'marked' not in word:
            word['marked'] = True
            mark_button.config(text="已标记")
        else:
            del word['marked']
            mark_button.config(text="标记单词")


# 修改show_marked_words函数，当没有标记单词时，显示提示信息并返回主界面
def show_marked_words():
    marked = [i for i, word in enumerate(words) if 'marked' in word]
    if marked:
        # 创建新窗口
        marked_window = tk.Toplevel(root)
        marked_window.title("已标记单词列表")
        marked_window.geometry("400x300")

        # 创建列表框
        listbox = tk.Listbox(marked_window, font=("Arial", 12))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 添加已标记单词到列表框
        for idx in marked:
            word = words[idx]
            listbox.insert(tk.END, word["headWord"])

        # 绑定双击事件，切换到选中的单词
        def on_select(event):
            selection = listbox.curselection()
            if selection:
                global current_word_index
                current_word_index = marked[selection[0]]
                show_current_word()
                marked_window.destroy()

        listbox.bind('<Double-Button-1>', on_select)
    else:
        tk.messagebox.showinfo("提示", "没有标记的单词！")


# 显示学习进度
def show_learning_progress():
    if current_user:
        learned_count = sum(1 for word in words if word["count"] > 0)
        total_count = len(words)
        progress = (learned_count / total_count) * 100 if total_count > 0 else 0
        messagebox.showinfo("学习进度", f"已学习单词数量: {learned_count}\n剩余单词数量: {total_count - learned_count}\n学习完成百分比: {progress:.2f}%")
    else:
        messagebox.showinfo("提示", "请先登录以查看学习进度！")


# 单词测试
def start_test():
    if not current_user:
        messagebox.showinfo("提示", "请先登录以进行单词测试！")
        return
    
    test_size = 10  # 测试单词数量
    test_words = random.sample(words, min(test_size, len(words)))
    correct_count = 0
    current_test_index = 0

    test_window = tk.Toplevel(root)
    test_window.title("单词测试")
    test_window.geometry("600x400")
    
    # 创建主框架
    main_frame = ttk.Frame(test_window)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # 创建进度标签
    progress_label = ttk.Label(main_frame, text=f"第 1/{test_size} 题", font=("宋体", 14))
    progress_label.pack(pady=10)
    
    # 创建单词显示标签
    word_label = ttk.Label(main_frame, text="", font=("Times New Roman", 24))
    word_label.pack(pady=20)
    
    # 创建输入框框架
    input_frame = ttk.Frame(main_frame)
    input_frame.pack(fill=tk.X, pady=10)
    
    ttk.Label(input_frame, text="请输入释义:", font=("宋体", 14)).pack(side=tk.LEFT, padx=5)
    answer_entry = ttk.Entry(input_frame, font=("宋体", 14))
    answer_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    # 创建按钮框架
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=20)
    
    def show_next_question():
        nonlocal current_test_index
        if current_test_index < test_size:
            word = test_words[current_test_index]
            word_label.config(text=word["headWord"])
            answer_entry.delete(0, tk.END)
            progress_label.config(text=f"第 {current_test_index + 1}/{test_size} 题")
        else:
            show_result()
    
    def check_answer():
        nonlocal correct_count, current_test_index
        if current_test_index < test_size:
            word = test_words[current_test_index]
            answer = answer_entry.get().strip()
            correct_answer = "\n".join([f"{trans['pos']}. {trans['tranCn']}" for trans in word["content"]["word"]["content"]["trans"]])
            
            if answer == correct_answer.strip():
                correct_count += 1
            else:
                save_wrong_word(word["headWord"])  # 记录错题
                messagebox.showinfo("正确答案", f"正确答案是：\n{correct_answer}")
            
            current_test_index += 1
            show_next_question()
    
    def show_result():
        score = (correct_count / test_size) * 100
        result_text = f"测试完成！\n\n答对题目数：{correct_count}/{test_size}\n得分：{score:.1f}分"
        messagebox.showinfo("测试结果", result_text)
        test_window.destroy()
    
    def skip_word():
        nonlocal current_test_index
        current_test_index += 1
        show_next_question()
    
    # 创建按钮
    submit_button = ttk.Button(button_frame, text="提交答案", command=check_answer)
    submit_button.pack(side=tk.LEFT, padx=10)
    
    skip_button = ttk.Button(button_frame, text="跳过", command=skip_word)
    skip_button.pack(side=tk.LEFT, padx=10)
    
    # 绑定回车键
    answer_entry.bind('<Return>', lambda e: check_answer())
    
    # 显示第一个问题
    show_next_question()
    answer_entry.focus()


# 用户管理函数
def register_user(username, password, window):
    if not username or not password:
        tk.messagebox.showerror("错误", "用户名和密码不能为空！")
        return

    users_file = 'users.json'
    users = {}
    if os.path.exists(users_file):
        with open(users_file, 'r', encoding='utf-8') as file:
            users = json.load(file)

    if username in users:
        tk.messagebox.showerror("错误", "用户名已存在！")
        return

    users[username] = hash_password(password)
    with open(users_file, 'w', encoding='utf-8') as file:
        json.dump(users, file, ensure_ascii=False, indent=4)

    tk.messagebox.showinfo("成功", "注册成功！")
    window.destroy()


def login_user(username, password, window):
    if not username or not password:
        tk.messagebox.showerror("错误", "用户名和密码不能为空！")
        return

    users_file = 'users.json'
    if not os.path.exists(users_file):
        tk.messagebox.showerror("错误", "用户不存在！")
        return

    with open(users_file, 'r', encoding='utf-8') as file:
        users = json.load(file)

    if username not in users or users[username] != hash_password(password):
        tk.messagebox.showerror("错误", "用户名或密码错误！")
        return

    global current_user, words
    current_user = username
    words = load_words()
    
    # 登录后显示随机单词
    global current_word_index
    current_word_index = random.randint(0, len(words) - 1)
    show_current_word()

    # 更新界面状态
    user_status_label.config(text=f"当前用户：{username}")
    login_button.config(state=tk.DISABLED)
    register_button.config(state=tk.DISABLED)
    logout_button.config(state=tk.NORMAL)

    tk.messagebox.showinfo("成功", f"欢迎回来，{username}！")
    window.destroy()


def logout_user():
    global current_user
    if current_user:
        save_memory()  # 保存当前用户的记忆数据
        current_user = None
        user_status_label.config(text="未登录")
        login_button.config(state=tk.NORMAL)
        register_button.config(state=tk.NORMAL)
        logout_button.config(state=tk.DISABLED)
        # 重新加载单词数据
        global words
        words = load_words()
        show_current_word()
        tk.messagebox.showinfo("成功", "已退出登录！")


# 窗口显示函数
def show_register_window():
    register_window = tk.Toplevel(root)
    register_window.title("注册")
    register_window.geometry("300x200")

    ttk.Label(register_window, text="用户名:").pack(pady=5)
    username_entry = ttk.Entry(register_window)
    username_entry.pack(pady=5)

    ttk.Label(register_window, text="密码:").pack(pady=5)
    password_entry = ttk.Entry(register_window, show="*")
    password_entry.pack(pady=5)

    ttk.Button(register_window, text="注册", command=lambda: register_user(username_entry.get(), password_entry.get(), register_window)).pack(pady=10)


def show_login_window():
    login_window = tk.Toplevel(root)
    login_window.title("登录")
    login_window.geometry("300x200")

    ttk.Label(login_window, text="用户名:").pack(pady=5)
    username_entry = ttk.Entry(login_window)
    username_entry.pack(pady=5)

    ttk.Label(login_window, text="密码:").pack(pady=5)
    password_entry = ttk.Entry(login_window, show="*")
    password_entry.pack(pady=5)

    ttk.Button(login_window, text="登录", command=lambda: login_user(username_entry.get(), password_entry.get(), login_window)).pack(pady=10)


def show_help_window():
    help_window = tk.Toplevel(root)
    help_window.title("帮助")
    help_window.geometry("500x500")

    help_text = """
    欢迎使用本软件！

    功能说明：
    1. 注册：创建新用户账号。
    2. 登录：使用已有账号登录。
    3. 帮助：查看帮助信息。

    使用方法：
    - 点击"上一个"或"下一个"按钮切换单词。
    - 点击"随机单词"按钮随机显示单词。
    - 点击"标记单词"按钮标记当前单词。
    - 点击"显示标记单词"按钮查看已标记的单词。

    快捷键：
    - 左方向键：上一个单词
    - 右方向键：下一个单词
    - 空格键：随机单词
    - M键：标记单词
    - S键：显示标记单词
    """
    ttk.Label(help_window, text=help_text, justify=tk.LEFT).pack(padx=10, pady=10)


# 添加单词搜索功能
def search_word():
    if not current_user:
        messagebox.showinfo("提示", "请先登录以使用搜索功能！")
        return

    search_window = tk.Toplevel(root)
    search_window.title("单词搜索")
    search_window.geometry("300x150")

    ttk.Label(search_window, text="请输入要搜索的单词:").pack(pady=10)
    search_entry = ttk.Entry(search_window)
    search_entry.pack(pady=5)

    def do_search():
        search_text = search_entry.get().strip().lower()
        if not search_text:
            messagebox.showinfo("提示", "请输入要搜索的单词！")
            return

        # 在单词列表中搜索
        for i, word in enumerate(words):
            if word["headWord"].lower() == search_text:
                global current_word_index
                current_word_index = i
                show_current_word()
                search_window.destroy()
                return

        messagebox.showinfo("提示", "未找到该单词！")

    ttk.Button(search_window, text="搜索", command=do_search).pack(pady=10)
    ttk.Button(search_window, text="取消", command=search_window.destroy).pack(pady=5)

    # 绑定回车键
    search_entry.bind('<Return>', lambda e: do_search())
    search_entry.focus()


# 保存错题函数
def save_wrong_word(word):
    if current_user:
        wrong_words_file = get_user_wrong_words_file(current_user)
        wrong_words = []
        if os.path.exists(wrong_words_file):
            try:
                with open(wrong_words_file, 'r', encoding='utf-8') as file:
                    wrong_words = json.load(file)
            except json.JSONDecodeError:
                wrong_words = []
        # 查找单词是否已存在于错题列表中
        for item in wrong_words:
            if item["word"] == word:
                item["count"] = item.get("count", 1) + 1
                item["time"] = time.time()
                break
        else:
            # 如果单词不存在，则添加新的错题记录
            wrong_words.append({"word": word, "time": time.time(), "count": 1})
        with open(wrong_words_file, 'w', encoding='utf-8') as file:
            json.dump(wrong_words, file, ensure_ascii=False, indent=4)


# 删除错题函数
def delete_wrong_word(word):
    if current_user:
        wrong_words_file = get_user_wrong_words_file(current_user)
        if os.path.exists(wrong_words_file):
            try:
                with open(wrong_words_file, 'r', encoding='utf-8') as file:
                    wrong_words = json.load(file)
                # 过滤掉要删除的单词
                wrong_words = [item for item in wrong_words if item["word"] != word]
                with open(wrong_words_file, 'w', encoding='utf-8') as file:
                    json.dump(wrong_words, file, ensure_ascii=False, indent=4)
                messagebox.showinfo("成功", f"已删除错题: {word}")
            except json.JSONDecodeError:
                messagebox.showinfo("提示", "错题记录文件损坏！")


# 显示错题列表
def show_wrong_words(sort_by='time'):
    if current_user:
        wrong_words_file = get_user_wrong_words_file(current_user)
        if os.path.exists(wrong_words_file):
            try:
                with open(wrong_words_file, 'r', encoding='utf-8') as file:
                    wrong_words = json.load(file)
                if wrong_words:
                    # 根据排序条件排序
                    if sort_by == 'time':
                        wrong_words.sort(key=lambda x: x["time"])
                    elif sort_by == 'count':
                        wrong_words.sort(key=lambda x: x["count"], reverse=True)

                    wrong_window = tk.Toplevel(root)
                    wrong_window.title(f"错题列表（按{'时间' if sort_by == 'time' else '错误次数'}排序）")
                    wrong_window.geometry("400x300")

                    listbox = tk.Listbox(wrong_window, font=("Arial", 12))
                    listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                    for item in wrong_words:
                        word = item["word"]
                        count = item["count"]
                        listbox.insert(tk.END, f"{word} (错误次数: {count})")

                    def on_select(event):
                        selection = listbox.curselection()
                        if selection:
                            selected_item = listbox.get(selection)
                            selected_word = selected_item.split(' (错误次数:')[0]
                            for idx, word in enumerate(words):
                                if word["headWord"] == selected_word:
                                    global current_word_index
                                    current_word_index = idx
                                    show_current_word()
                                    wrong_window.destroy()
                                    break

                    listbox.bind('<Double-Button-1>', on_select)

                    def delete_selected_word():
                        selection = listbox.curselection()
                        if selection:
                            selected_item = listbox.get(selection)
                            selected_word = selected_item.split(' (错误次数:')[0]
                            delete_wrong_word(selected_word)
                            # 刷新错题列表
                            show_wrong_words(sort_by)

                    delete_button = ttk.Button(wrong_window, text="删除选中错题", command=delete_selected_word)
                    delete_button.pack(pady=10)

                    sort_time_button = ttk.Button(wrong_window, text="按时间排序", command=lambda: show_wrong_words('time'))
                    sort_time_button.pack(side=tk.LEFT, padx=10)

                    sort_count_button = ttk.Button(wrong_window, text="按错误次数排序", command=lambda: show_wrong_words('count'))
                    sort_count_button.pack(side=tk.LEFT, padx=10)

                else:
                    messagebox.showinfo("提示", "没有错题记录！")
            except json.JSONDecodeError:
                messagebox.showinfo("提示", "错题记录文件损坏！")
        else:
            messagebox.showinfo("提示", "没有错题记录！")
    else:
        messagebox.showinfo("提示", "请先登录以查看错题记录！")


# 错题复习功能
def review_wrong_words():
    if current_user:
        wrong_words_file = get_user_wrong_words_file(current_user)
        if os.path.exists(wrong_words_file):
            try:
                with open(wrong_words_file, 'r', encoding='utf-8') as file:
                    wrong_words = json.load(file)
                if wrong_words:
                    # 按时间排序
                    wrong_words.sort(key=lambda x: x["time"])
                    review_window = tk.Toplevel(root)
                    review_window.title("错题复习")
                    review_window.geometry("600x400")
                    
                    # 创建主框架
                    main_frame = ttk.Frame(review_window)
                    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
                    
                    # 创建进度标签
                    progress_label = ttk.Label(main_frame, text="", font=("宋体", 14))
                    progress_label.pack(pady=10)
                    
                    # 创建单词显示标签
                    word_label = ttk.Label(main_frame, text="", font=("Times New Roman", 24))
                    word_label.pack(pady=20)
                    
                    # 创建输入框框架
                    input_frame = ttk.Frame(main_frame)
                    input_frame.pack(fill=tk.X, pady=10)
                    
                    ttk.Label(input_frame, text="请输入释义:", font=("宋体", 14)).pack(side=tk.LEFT, padx=5)
                    answer_entry = ttk.Entry(input_frame, font=("宋体", 14))
                    answer_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                    
                    # 创建按钮框架
                    button_frame = ttk.Frame(main_frame)
                    button_frame.pack(pady=20)
                    
                    # 获取错题对应的单词
                    test_words = [word for word in words if word["headWord"] in [item["word"] for item in wrong_words]]
                    test_size = len(test_words)
                    correct_count = 0
                    current_test_index = 0
                    
                    def show_next_question():
                        nonlocal current_test_index
                        if current_test_index < test_size:
                            word = test_words[current_test_index]
                            word_label.config(text=word["headWord"])
                            answer_entry.delete(0, tk.END)
                            progress_label.config(text=f"第 {current_test_index + 1}/{test_size} 题")
                        else:
                            show_result()
                    
                    def check_answer():
                        nonlocal correct_count, current_test_index
                        if current_test_index < test_size:
                            word = test_words[current_test_index]
                            answer = answer_entry.get().strip()
                            correct_answer = "\n".join([f"{trans['pos']}. {trans['tranCn']}" for trans in word["content"]["word"]["content"]["trans"]])
                            
                            if answer == correct_answer.strip():
                                correct_count += 1
                            else:
                                messagebox.showinfo("正确答案", f"正确答案是：\n{correct_answer}")
                            
                            current_test_index += 1
                            show_next_question()
                    
                    def show_result():
                        score = (correct_count / test_size) * 100
                        result_text = f"复习完成！\n\n答对题目数：{correct_count}/{test_size}\n得分：{score:.1f}分"
                        messagebox.showinfo("复习结果", result_text)
                        review_window.destroy()
                    
                    # 创建按钮
                    submit_button = ttk.Button(button_frame, text="提交答案", command=check_answer)
                    submit_button.pack(side=tk.LEFT, padx=10)
                    
                    skip_button = ttk.Button(button_frame, text="跳过", command=lambda: [setattr(current_test_index, 'current_test_index', current_test_index + 1), show_next_question()])
                    skip_button.pack(side=tk.LEFT, padx=10)
                    
                    # 绑定回车键
                    answer_entry.bind('<Return>', lambda e: check_answer())
                    
                    # 显示第一个问题
                    show_next_question()
                    answer_entry.focus()
                else:
                    messagebox.showinfo("提示", "没有错题记录！")
            except json.JSONDecodeError:
                messagebox.showinfo("提示", "错题记录文件损坏！")
        else:
            messagebox.showinfo("提示", "没有错题记录！")
    else:
        messagebox.showinfo("提示", "请先登录以进行错题复习！")


# 单词排序功能
def sort_words_by_count():
    global words
    words.sort(key=lambda x: x["count"], reverse=True)
    global current_word_index
    current_word_index = 0
    show_current_word()

# 保存学习计划
def save_learning_plan(plan):
    if current_user:
        plan_file = f'plan_{current_user}.json'
        with open(plan_file, 'w', encoding='utf-8') as file:
            json.dump(plan, file, ensure_ascii=False, indent=4)

# 加载学习计划
def load_learning_plan():
    if current_user:
        plan_file = f'plan_{current_user}.json'
        if os.path.exists(plan_file):
            try:
                with open(plan_file, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except json.JSONDecodeError:
                return None
    return None

# 设置学习计划
def set_learning_plan():
    plan_window = tk.Toplevel(root)
    plan_window.title("设置学习计划")
    plan_window.geometry("300x200")

    ttk.Label(plan_window, text="请输入每天学习的单词数量:").pack(pady=10)
    plan_entry = ttk.Entry(plan_window)
    plan_entry.pack(pady=5)

    def save_plan():
        try:
            daily_count = int(plan_entry.get())
            plan = {
                "daily_count": daily_count,
                "last_learned_date": time.strftime("%Y-%m-%d")
            }
            save_learning_plan(plan)
            messagebox.showinfo("成功", "学习计划设置成功！")
            plan_window.destroy()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字！")

    ttk.Button(plan_window, text="保存", command=save_plan).pack(pady=10)

# 检查学习计划进度
def check_learning_plan():
    plan = load_learning_plan()
    if plan:
        today = time.strftime("%Y-%m-%d")
        if today != plan["last_learned_date"]:
            learned_count = 0
            plan["last_learned_date"] = today
            save_learning_plan(plan)
        else:
            learned_count = sum(1 for word in words if word["count"] > 0 and word["count"] == int(time.strftime("%d")))
        remaining_count = plan["daily_count"] - learned_count
        if remaining_count > 0:
            messagebox.showinfo("学习提醒", f"你今天还需要学习 {remaining_count} 个单词！")
    else:
        messagebox.showinfo("提示", "你还没有设置学习计划，请先设置。")

# 统计不同难度单词的掌握情况
def analyze_word_difficulty():
    if current_user:
        easy_count = 0
        medium_count = 0
        hard_count = 0
        total_words = len(words)
        
        # 统计各难度单词数量
        for word in words:
            if word["count"] >= 5:
                easy_count += 1
            elif word["count"] >= 2:
                medium_count += 1
            else:
                hard_count += 1
        
        # 计算百分比
        easy_percent = (easy_count / total_words * 100) if total_words > 0 else 0
        medium_percent = (medium_count / total_words * 100) if total_words > 0 else 0
        hard_percent = (hard_count / total_words * 100) if total_words > 0 else 0
        
        # 生成分析报告
        report = f"""单词难度分析报告：

总单词数：{total_words}

难度分布：
- 简单单词：{easy_count}个 ({easy_percent:.1f}%)
- 中等单词：{medium_count}个 ({medium_percent:.1f}%)
- 困难单词：{hard_count}个 ({hard_percent:.1f}%)

学习建议：
1. 建议优先复习困难单词
2. 保持中等单词的练习频率
3. 定期复习简单单词以巩固记忆"""
        
        messagebox.showinfo("单词难度分析", report)
    else:
        messagebox.showinfo("提示", "请先登录以进行统计分析！")

# 播放单词发音
def play_word_pronunciation():
    if 0 <= current_word_index < len(words):
        word = words[current_word_index]["headWord"]
        engine.say(word)
        engine.runAndWait()
    else:
        messagebox.showinfo("提示", "没有可播放的单词！")


# 主题列表
THEMES = {
    "简约风格 (arc)": "arc",
    "清爽风格 (breeze)": "breeze",
    "深色主题 (equilux)": "equilux",
    "塑料质感 (plastik)": "plastik",
    "明亮风格 (radiance)": "radiance",
    "Ubuntu风格 (yaru)": "yaru"
}

# 切换主题
def change_theme(theme_name):
    style.set_theme(THEMES[theme_name])
    messagebox.showinfo("主题切换", f"已切换到 {theme_name}")

# 创建主题切换窗口
def show_theme_window():
    theme_window = tk.Toplevel(root)
    theme_window.title("切换主题")
    theme_window.geometry("250x350")
    
    # 创建标题标签
    title_label = ttk.Label(theme_window, text="请选择主题", font=("宋体", 14))
    title_label.pack(pady=10)
    
    # 创建主题按钮
    for theme_display in THEMES.keys():
        ttk.Button(theme_window, text=theme_display, 
                  command=lambda t=theme_display: change_theme(t)).pack(pady=5, padx=10, fill=tk.X)


# 选择词库
def select_wordbook():
    global current_wordbook, words, current_word_index
    file_path = filedialog.askopenfilename(
        title="选择词库文件",
        filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
    )
    if file_path:
        current_wordbook = file_path
        words = load_words()
        current_word_index = 0
        show_current_word()
        messagebox.showinfo("提示", f"已加载词库：{os.path.basename(current_wordbook)}")

# 数据备份与恢复功能
def backup_user_data():
    if not current_user:
        messagebox.showinfo("提示", "请先登录以备份数据！")
        return
    
    # 创建备份目录
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # 创建用户备份目录
    user_backup_dir = os.path.join(backup_dir, current_user)
    if not os.path.exists(user_backup_dir):
        os.makedirs(user_backup_dir)
    
    # 创建时间戳目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(user_backup_dir, timestamp)
    os.makedirs(backup_path)
    
    try:
        # 备份记忆数据
        memory_file = get_user_memory_file(current_user)
        if os.path.exists(memory_file):
            shutil.copy2(memory_file, os.path.join(backup_path, "memory.json"))
        
        # 备份错题记录
        wrong_words_file = get_user_wrong_words_file(current_user)
        if os.path.exists(wrong_words_file):
            shutil.copy2(wrong_words_file, os.path.join(backup_path, "wrong_words.json"))
        
        # 备份学习计划
        plan_file = f'plan_{current_user}.json'
        if os.path.exists(plan_file):
            shutil.copy2(plan_file, os.path.join(backup_path, "plan.json"))
        
        # 备份学习记录
        learning_record_file = f'learning_record_{current_user}.json'
        if os.path.exists(learning_record_file):
            shutil.copy2(learning_record_file, os.path.join(backup_path, "learning_record.json"))
        
        messagebox.showinfo("成功", "数据备份完成！")
    except Exception as e:
        messagebox.showerror("错误", f"备份数据时出错：{str(e)}")

def restore_user_data():
    if not current_user:
        messagebox.showinfo("提示", "请先登录以恢复数据！")
        return
    
    # 获取用户备份目录
    backup_dir = os.path.join("backups", current_user)
    if not os.path.exists(backup_dir):
        messagebox.showinfo("提示", "没有找到备份数据！")
        return
    
    # 获取所有备份
    backups = sorted([d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d))], reverse=True)
    if not backups:
        messagebox.showinfo("提示", "没有找到备份数据！")
        return
    
    # 创建选择窗口
    restore_window = tk.Toplevel(root)
    restore_window.title("选择要恢复的备份")
    restore_window.geometry("400x300")
    
    # 创建列表框
    listbox = tk.Listbox(restore_window, font=("宋体", 12))
    listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # 添加备份到列表框
    for backup in backups:
        date_str = backup.split("_")[0]
        time_str = backup.split("_")[1]
        display_text = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]} {time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"
        listbox.insert(tk.END, display_text)
    
    def restore_selected():
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请选择一个备份！")
            return
        
        selected_backup = backups[selection[0]]
        backup_path = os.path.join(backup_dir, selected_backup)
        
        try:
            # 恢复记忆数据
            memory_backup = os.path.join(backup_path, "memory.json")
            if os.path.exists(memory_backup):
                shutil.copy2(memory_backup, get_user_memory_file(current_user))
            
            # 恢复错题记录
            wrong_words_backup = os.path.join(backup_path, "wrong_words.json")
            if os.path.exists(wrong_words_backup):
                shutil.copy2(wrong_words_backup, get_user_wrong_words_file(current_user))
            
            # 恢复学习计划
            plan_backup = os.path.join(backup_path, "plan.json")
            if os.path.exists(plan_backup):
                shutil.copy2(plan_backup, f'plan_{current_user}.json')
            
            # 恢复学习记录
            learning_record_backup = os.path.join(backup_path, "learning_record.json")
            if os.path.exists(learning_record_backup):
                shutil.copy2(learning_record_backup, f'learning_record_{current_user}.json')
            
            messagebox.showinfo("成功", "数据恢复完成！")
            restore_window.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"恢复数据时出错：{str(e)}")
    
    # 创建恢复按钮
    restore_button = ttk.Button(restore_window, text="恢复选中备份", command=restore_selected)
    restore_button.pack(pady=10)

# 自动备份功能
def auto_backup():
    if current_user:
        backup_user_data()
    root.after(3600000, auto_backup)  # 每小时自动备份一次

# 语音设置窗口
def show_voice_settings():
    voice_window = tk.Toplevel(root)
    voice_window.title("语音设置")
    voice_window.geometry("300x200")
    
    # 创建语速滑块
    ttk.Label(voice_window, text="语速", font=("宋体", 12)).pack(pady=5)
    rate_scale = ttk.Scale(voice_window, from_=50, to=300, orient=tk.HORIZONTAL)
    rate_scale.set(engine.getProperty('rate'))
    rate_scale.pack(fill=tk.X, padx=20, pady=5)
    
    # 创建音量滑块
    ttk.Label(voice_window, text="音量", font=("宋体", 12)).pack(pady=5)
    volume_scale = ttk.Scale(voice_window, from_=0, to=1, orient=tk.HORIZONTAL)
    volume_scale.set(engine.getProperty('volume'))
    volume_scale.pack(fill=tk.X, padx=20, pady=5)
    
    def apply_settings():
        engine.setProperty('rate', rate_scale.get())
        engine.setProperty('volume', volume_scale.get())
        messagebox.showinfo("成功", "语音设置已保存！")
        voice_window.destroy()
    
    # 创建应用按钮
    ttk.Button(voice_window, text="应用设置", command=apply_settings).pack(pady=20)

# 创建主窗口
root = tk.Tk()
root.title("简易的单词学习软件")
root.geometry("1200x750")  # 固定窗口大小

# 设置程序图标
try:
    icon = tk.PhotoImage(file="软件图标.png")
    root.iconphoto(True, icon)
except Exception as e:
    print("加载图标失败:", e)

# 应用主题
style = ThemedStyle(root)
style.set_theme("arc")  # 默认主题

# 样式优化
style.configure("TButton", font=("Times New Roman", 12), padding=5)
style.configure("TLabel", font=("宋体", 14))

# 创建用户管理框架
user_frame = ttk.Frame(root)
user_frame.pack(pady=10)

# 创建用户状态标签
user_status_label = ttk.Label(user_frame, text="未登录", font=("宋体", 14))
user_status_label.pack(side=tk.LEFT, padx=10)

# 创建用户管理按钮
register_button = ttk.Button(user_frame, text="注册", command=lambda: show_register_window())
register_button.pack(side=tk.LEFT, padx=10)

login_button = ttk.Button(user_frame, text="登录", command=lambda: show_login_window())
login_button.pack(side=tk.LEFT, padx=10)

logout_button = ttk.Button(user_frame, text="退出登录", command=lambda: logout_user(), state=tk.DISABLED)
logout_button.pack(side=tk.LEFT, padx=10)

help_button = ttk.Button(user_frame, text="帮助", command=lambda: show_help_window())
help_button.pack(side=tk.LEFT, padx=10)

theme_button = ttk.Button(user_frame, text="切换主题", command=show_theme_window)
theme_button.pack(side=tk.LEFT, padx=10)

wordbook_button = ttk.Button(user_frame, text="选择词库", command=select_wordbook)
wordbook_button.pack(side=tk.LEFT, padx=10)

# 在用户管理框架中添加语音设置按钮
voice_button = ttk.Button(user_frame, text="语音设置", command=show_voice_settings)
voice_button.pack(side=tk.LEFT, padx=10)

# 创建单词和释义标签
word_label = tk.Label(root, text="", font=("Times New Roman", 24))
word_label.pack(pady=10)

trans_label = tk.Label(root, text="", font=("宋体", 18))
trans_label.pack(pady=10)

# 创建显示出现次数的标签
count_label = tk.Label(root, text="", font=("Times New Roman", 14))
count_label.pack(pady=5)

# 创建滚动区域
scroll_frame = ttk.Frame(root)
scroll_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

# 创建画布
canvas = tk.Canvas(scroll_frame)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 创建滚动条
scrollbar = ttk.Scrollbar(scroll_frame, orient=tk.VERTICAL, command=canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
canvas.configure(yscrollcommand=scrollbar.set)

# 创建内部框架
inner_frame = ttk.Frame(canvas)
canvas.create_window((0, 0), window=inner_frame, anchor="nw")

# 设置显示框大小
sentence_width = 60
sentence_height = 10
phrase_width = 60
phrase_height = 10

# 创建内容框架
content_frame = ttk.Frame(inner_frame)
content_frame.pack(fill=tk.BOTH, expand=True, pady=5)

# 创建例句框架
sentence_frame = ttk.Frame(content_frame)
sentence_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

# 创建例句标签
sentence_label = ttk.Label(sentence_frame, text="例句", font=("宋体", 14))
sentence_label.pack(pady=5)

# 创建例句文本框
sentence_text_widget = tk.Text(sentence_frame, font=("Times New Roman", 14), wrap=tk.WORD, 
                              width=sentence_width, height=sentence_height,
                              padx=10, pady=5)
sentence_text_widget.pack(fill=tk.BOTH, expand=True)

# 创建短语框架
phrase_frame = ttk.Frame(content_frame)
phrase_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

# 创建短语标签
phrase_label = ttk.Label(phrase_frame, text="短语", font=("宋体", 14))
phrase_label.pack(pady=5)

# 创建短语文本框
phrase_text_widget = tk.Text(phrase_frame, font=("Times New Roman", 14), wrap=tk.WORD, 
                            width=phrase_width, height=phrase_height,
                            padx=10, pady=5)
phrase_text_widget.pack(fill=tk.BOTH, expand=True)

# 更新画布滚动区域
def update_scroll_region(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

inner_frame.bind('<Configure>', update_scroll_region)

# 绑定鼠标滚轮事件
def on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

canvas.bind_all("<MouseWheel>", on_mousewheel)

# 创建按钮框架
button_frame = ttk.Frame(root)
button_frame.pack(pady=10)

prev_button = ttk.Button(button_frame, text="上一个", command=prev_word)
prev_button.pack(side=tk.LEFT, padx=10)

next_button = ttk.Button(button_frame, text="下一个", command=next_word)
next_button.pack(side=tk.LEFT, padx=10)

random_button = ttk.Button(button_frame, text="随机单词", command=random_word)
random_button.pack(side=tk.LEFT, padx=10)

mark_button = ttk.Button(button_frame, text="标记单词", command=mark_word)
mark_button.pack(side=tk.LEFT, padx=10)

show_marked_button = ttk.Button(button_frame, text="显示标记单词", command=show_marked_words)
show_marked_button.pack(side=tk.LEFT, padx=10)

# 创建发音按钮
pronunciation_button = ttk.Button(button_frame, text="播放发音", command=play_word_pronunciation)
pronunciation_button.pack(side=tk.LEFT, padx=10)

# 创建第二个按钮框架
button_frame2 = ttk.Frame(root)
button_frame2.pack(pady=10)

progress_button = ttk.Button(button_frame2, text="学习进度", command=show_learning_progress)
progress_button.pack(side=tk.LEFT, padx=10)

test_button = ttk.Button(button_frame2, text="单词测试", command=start_test)
test_button.pack(side=tk.LEFT, padx=10)

search_button = ttk.Button(button_frame2, text="单词搜索", command=search_word)
search_button.pack(side=tk.LEFT, padx=10)

wrong_words_button = ttk.Button(button_frame2, text="显示错题", command=show_wrong_words)
wrong_words_button.pack(side=tk.LEFT, padx=10)

review_button = ttk.Button(button_frame2, text="错题复习", command=review_wrong_words)
review_button.pack(side=tk.LEFT, padx=10)

sort_button = ttk.Button(button_frame2, text="按出现次数排序", command=sort_words_by_count)
sort_button.pack(side=tk.LEFT, padx=10)


# 创建第三个按钮框架
button_frame3 = ttk.Frame(root)
button_frame3.pack(pady=10)

# 创建设置学习计划按钮
plan_button = ttk.Button(button_frame3, text="设置学习计划", command=set_learning_plan)
plan_button.pack(side=tk.LEFT, padx=10)

# 创建检查学习计划进度按钮
check_plan_button = ttk.Button(button_frame3, text="检查学习进度", command=check_learning_plan)
check_plan_button.pack(side=tk.LEFT, padx=10)

# 创建开始学习按钮
start_learning_button = ttk.Button(button_frame3, text="开始学习", command=start_learning)
start_learning_button.pack(side=tk.LEFT, padx=10)

# 创建结束学习按钮
end_learning_button = ttk.Button(button_frame3, text="结束学习", command=end_learning)
end_learning_button.pack(side=tk.LEFT, padx=10)

# 创建显示总学习时长按钮
total_learning_button = ttk.Button(button_frame3, text="学习统计", command=show_total_learning_time)
total_learning_button.pack(side=tk.LEFT, padx=10)

# 创建统计分析按钮
analyze_button = ttk.Button(button_frame2, text="单词难度分析", command=analyze_word_difficulty)
analyze_button.pack(side=tk.LEFT, padx=10)


# 创建第四个按钮框架
button_frame4 = ttk.Frame(root)
button_frame4.pack(pady=10)

# 创建备份按钮
backup_button = ttk.Button(button_frame4, text="备份数据", command=backup_user_data)
backup_button.pack(side=tk.LEFT, padx=10)

# 创建恢复按钮
restore_button = ttk.Button(button_frame4, text="恢复数据", command=restore_user_data)
restore_button.pack(side=tk.LEFT, padx=10)

# 绑定快捷键
root.bind('<Left>', lambda event: prev_word())
root.bind('<Right>', lambda event: next_word())
root.bind('<space>', lambda event: random_word())
root.bind('m', lambda event: mark_word())
root.bind('s', lambda event: show_marked_words())

# 显示第一个单词
if words:
    show_current_word()
else:
    word_label.config(text="没有加载到任何单词！")

# 在程序启动时开始自动备份
root.after(1800000, auto_backup)  # 每30分钟自动备份一次

# 运行主循环
root.mainloop()