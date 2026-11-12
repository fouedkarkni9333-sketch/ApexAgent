import os
import json
import subprocess
import google.generativeai as genai

# إعداد مفتاح Gemini من متغيرات البيئة الآمنة في GitHub
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-3.8-flash")

def load_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def save_file(filepath, content):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def test_code_in_sandbox(code_content):
    """اختبار الكود الجديد في ملف مؤقت للتأكد من خلوه من الأخطاء البرمجية"""
    sandbox_file = "sandbox_test.py"
    save_file(sandbox_file, code_content)
    try:
        result = subprocess.run(
            ["python", sandbox_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        os.remove(sandbox_file)
        return result.returncode == 0, result.stderr
    except Exception as e:
        if os.path.exists(sandbox_file):
            os.remove(sandbox_file)
        return False, str(e)

def evolve():
    current_code = load_file("target_app.py")
    memory = json.loads(load_file("memory.json"))
    
    # قراءة آخر 5 تطورات فقط لتوفير استهلاك التوكنز (Sliding Window)
    recent_history = memory["evolution_history"][-5:]
    
    prompt = f"""
    أنت وكيل برمجي مستقل ذاتي التطور (Autonomous Self-Evolving Code Agent).
    مهمتك: تطوير وتحسين الكود التالي في ملف target_app.py لجعله أذكى، أسرع، وأكثر فائدة (مثلاً: إضافة معالجة أخطاء متقدمة، دوال تحليل ذكية، تحسين الأداء، أو ميزات جديدة مفيدة لمعالجة البيانات).
    
    تاريخ التطورات السابقة (لا تكرر نفس الفكرة):
    {json.dumps(recent_history, ensure_ascii=False)}
    
    الكود الحالي:
    ```python
    {current_code}
    ```
    
    الشروط الصارمة:
    1. أرجع الكود البرمجي الكامل الجديد فقط بدون أي شرح أو علامات markdown (لا تكتب ```python في البداية أو النهاية).
    2. يجب أن يكون الكود قابلاً للتشغيل مباشرة وبدون أي مكتبات خارجية غير مثبتة في بايثون القياسي.
    3. حافظ على قسم if __name__ == "__main__": لاختبار الدوال الجديدة تلقائياً عند التشغيل.
    """
    
    response = model.generate_content(prompt)
    new_code = response.text.strip()
    
    # تنظيف أي علامات markdown قد يضيفها النموذج بالخطأ
    if new_code.startswith("```python"):
        new_code = new_code[9:]
    if new_code.startswith("```"):
        new_code = new_code[3:]
    if new_code.endswith("```"):
        new_code = new_code[:-3]
    new_code = new_code.strip()

    # اختبار الكود الجديد قبل اعتماده
    is_valid, error_msg = test_code_in_sandbox(new_code)
    
    new_cycle = memory["version"] + 1
    if is_valid:
        save_file("target_app.py", new_code)
        memory["version"] = new_cycle
        memory["evolution_history"].append({
            "cycle": new_cycle,
            "action": "Successfully evolved and upgraded target_app.py",
            "status": "success"
        })
        print(f"نجح التطور! تم الانتقال إلى الإصدار {new_cycle}")
    else:
        memory["evolution_history"].append({
            "cycle": new_cycle,
            "action": f"Failed evolution attempt: {error_msg[:100]}",
            "status": "reverted"
        })
        print(f"فشل الاختبار وتم رفض التعديل لحماية النظام: {error_msg}")

    save_file("memory.json", json.dumps(memory, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    evolve()
