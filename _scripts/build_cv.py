import json
import os
import shutil
import subprocess
from jinja2 import Environment, FileSystemLoader

def tex_escape(text):
    if not isinstance(text, str):
        return text
    chars = {
        '\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
        '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}',
        '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
    }
    for key, val in chars.items():
        text = text.replace(key, val)
    return text

def build_cv():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cv_dir = os.path.join(project_root, "_cv")
    template_dir = os.path.join(cv_dir, "templates")
    json_path = os.path.join(project_root, "_data", "cv.json")
    files_dir = os.path.join(project_root, "files")
    
    pdf_path = os.path.join(cv_dir, "cv.pdf")
    dest_pdf_path = os.path.join(files_dir, "cv.pdf")

    # Ensure output directory exists
    os.makedirs(files_dir, exist_ok=True)

    # Remove old PDF before building
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    with open(json_path, "r", encoding="utf-8") as f:
        cv_data = json.load(f)

    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["tex_escape"] = tex_escape

    # 1. Render rubric section templates into _cv/
    for filename in os.listdir(template_dir):
        if filename.endswith(".j2") and filename != "cv.tex.j2":
            out_filename = filename.replace(".j2", "")
            tpl = env.get_template(filename)
            rendered = tpl.render(cv=cv_data)
            with open(os.path.join(cv_dir, out_filename), "w", encoding="utf-8") as f:
                f.write(rendered)
            print(f"[✓] Rendered rubric: {out_filename}")

    # 2. Render main cv.tex template into _cv/
    main_tpl = env.get_template("cv.tex.j2")
    rendered_main = main_tpl.render(cv=cv_data)
    with open(os.path.join(cv_dir, "cv.tex"), "w", encoding="utf-8") as f:
        f.write(rendered_main)
    print(f"[✓] Rendered main file: cv.tex")

    # 3. Compilation passes (running inside _cv/)
    print("[...] Running 1st pdflatex pass...")
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "cv.tex"], cwd=cv_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("[...] Running biber pass (bibliography processing)...")
    subprocess.run(["biber", "cv"], cwd=cv_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("[...] Running 2nd pdflatex pass (linking references)...")
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "cv.tex"], cwd=cv_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("[...] Running 3rd pdflatex pass (resolving final layout)...")
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "cv.tex"], cwd=cv_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 4. Verify success, copy output, and clean up intermediate files
    if os.path.exists(pdf_path):
        print(f"[✓] Success! PDF compiled at: _cv/cv.pdf")
        
        # Copy compiled PDF to ./files/cv.pdf
        shutil.copy2(pdf_path, dest_pdf_path)
        print(f"[✓] Copied PDF to: files/cv.pdf")

        # Clean auxiliary build artifacts
        aux_extensions = (".aux", ".bcf", ".log", ".out", ".run.xml", ".bbl", ".blg", ".toc")
        for fname in os.listdir(cv_dir):
            if fname.endswith(aux_extensions):
                os.remove(os.path.join(cv_dir, fname))
        print("[✓] Cleaned up LaTeX auxiliary files.")
    else:
        print("[X] LaTeX compilation failed! Check _cv/cv.log for details.")

if __name__ == "__main__":
    build_cv()