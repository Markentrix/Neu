import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import p_index, p_preise, p_kinder_firmen, p_kartbahn, p_faq_kontakt, p_legal, p_misc

# JavaScript: main.js + motion.js werden zu einer Datei zusammengefasst, buchen.js bleibt separat.
# Minifiziert mit terser, wenn verfügbar, sonst 1:1 kopiert.
import subprocess, shutil, tempfile
from common import OUT
_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
_js = os.path.join(_root, "tools", "js")
os.makedirs(os.path.join(OUT, "assets", "js"), exist_ok=True)
_tmp = tempfile.mkdtemp()
with open(os.path.join(_tmp, "main.js"), "w", encoding="utf-8") as out:
    out.write(open(os.path.join(_js, "main.js"), encoding="utf-8").read() + "\n" + open(os.path.join(_js, "motion.js"), encoding="utf-8").read())
shutil.copy(os.path.join(_js, "buchen.js"), os.path.join(_tmp, "buchen.js"))
for name in ("main.js", "buchen.js"):
    src = os.path.join(_tmp, name); dst = os.path.join(OUT, "assets", "js", name)
    try:
        subprocess.run(["npx", "--yes", "terser@5.31.0", src, "-c", "-m", "-o", dst, "--comments", "false"], check=True, timeout=120, capture_output=True)
    except Exception:
        shutil.copy(src, dst)
    print("js", name, os.path.getsize(dst))
_old = os.path.join(OUT, "assets", "js", "motion.js")
if os.path.exists(_old): os.remove(_old)
