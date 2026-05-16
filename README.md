Hey team — I built a DFM Inspector tool that analyzes CAD files against our manufacturing design rules. It covers CNC, sheet metal, welding, die casting, injection molding, and more.

Repo: https://github.com/aatala22/dfm-inspector

To run it:
git clone https://github.com/aatala22/dfm-inspector.git
cd dfm-inspector
pip install -r requirements.txt
python run.py

Then open http://localhost:5000 — upload a STEP file, pick a process and material, and it gives you a rule-by-rule DFM evaluation with scores and cost impact.
