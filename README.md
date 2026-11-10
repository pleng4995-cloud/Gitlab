DC Circuit Calculator

วัตถุประสงค์: โปรแกรมคำนวณและวิเคราะห์วงจรไฟฟ้ากระแสตรง (DC) แบบอนุกรม ขนาน และผสม โดยผู้ใช้เพียงระบุค่าความต่างศักย์และแรงต้านทาน ระบบจะคำนวณหาค่ากระแสไฟฟ้ารวม (Current) และกำลังไฟฟ้า (Power) ของแต่ละอุปกรณ์ให้อัตโนมัติ เพื่อช่วยให้ผู้เรียนเข้าใจกฎของโอมห์และวิเคราะห์วงจรได้อย่างแม่นยำ

## BJT DC Bias Web App (ENG29 2121)

เว็บแอป Flask สำหรับคำนวณจุดทำงาน DC (Q-point) ของทรานซิสเตอร์แบบ common-emitter ที่ไบแอสด้วย voltage divider

- อินพุต: `VCC`, `R1`, `R2`, `RC`, `RE`, `β`, `VBE`
- เอาต์พุต: `VB`, `VC`, `VE`, `IB`, `IC`, `IE`, `VCE` พร้อมหน่วย
- ตรวจสอบค่าอินพุตทีละช่อง และแจ้งเตือนเมื่ออยู่ในช่วง cutoff / saturation
- แสดงผลการคำนวณสองวิธีเทียบกัน: สูตรมาตรฐาน และ nodal analysis ที่คำนวณแยกกันจริง

ขอบเขต: DC bias เท่านั้น ไม่มี AC, Bode plot, transient, function generator หรือ circuit editor

### วิธีติดตั้งและรัน

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

เปิดเบราว์เซอร์ที่ <http://127.0.0.1:5000>

### วิธีทดสอบ

```powershell
.venv\Scripts\python -m unittest discover -s tests -t . -v
.venv\Scripts\python -m unittest test_electrical -v
```
