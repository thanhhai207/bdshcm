"""
Deploy dashboard to GitHub Pages (free hosting).

Setup (one time):
  1. Create a GitHub repo (e.g. hcmc-realestate-dashboard)
  2. Run: python deploy.py --setup <your-github-username> <repo-name>

Update & deploy:
  python deploy.py           # Crawl fresh data + deploy
  python deploy.py --demo    # Deploy with demo data
"""
import os
import sys
import subprocess
import shutil

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True

DOCS_DIR = os.path.join(os.getcwd(), "docs")


def setup_github(username, repo):
    """Initialize git repo and configure for GitHub Pages."""
    os.makedirs(DOCS_DIR, exist_ok=True)

    if not os.path.exists(".git"):
        subprocess.run(["git", "init"], check=True)

    # Create .gitignore
    with open(".gitignore", "w") as f:
        f.write("__pycache__/\n*.pyc\ndata/listings_*.csv\n.env\n")

    subprocess.run(["git", "remote", "add", "origin",
                     f"https://github.com/{username}/{repo}.git"], check=False)

    print(f"""
Setup complete! Next steps:
  1. Go to https://github.com/new and create repo: {repo}
  2. Run: python deploy.py --demo   (to do first deploy)
  3. Go to repo Settings > Pages > Source: "Deploy from branch" > Branch: main, folder: /docs
  4. Your dashboard will be live at: https://{username}.github.io/{repo}/
""")


def deploy(mode="full"):
    """Build dashboard and deploy to GitHub Pages."""
    # Step 1: Generate fresh data + dashboard
    if mode == "demo":
        subprocess.run([sys.executable, "-B", "run.py", "--demo"], check=True)
    elif mode == "quick":
        subprocess.run([sys.executable, "-B", "run.py", "--quick"], check=True)
    else:
        subprocess.run([sys.executable, "-B", "run.py"], check=True)

    # Step 2: Copy dashboard to docs/ for GitHub Pages
    os.makedirs(DOCS_DIR, exist_ok=True)
    shutil.copy2("dashboard.html", os.path.join(DOCS_DIR, "index.html"))

    print(f"Dashboard copied to docs/index.html")

    # Step 3: Git commit and push
    subprocess.run(["git", "add", "docs/"], check=True)
    subprocess.run(["git", "add", ".gitignore"], check=False)

    from datetime import datetime
    msg = f"Update dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    result = subprocess.run(["git", "commit", "-m", msg], capture_output=True, text=True)
    if "nothing to commit" in result.stdout:
        print("No changes to deploy.")
        return

    result = subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True, text=True)
    if result.returncode != 0:
        # Try master branch
        subprocess.run(["git", "branch", "-M", "main"], check=False)
        subprocess.run(["git", "push", "-u", "origin", "main"], check=True)

    print("\nDeployed! Your dashboard will be live in ~1 minute.")


def main():
    args = sys.argv[1:]

    if "--setup" in args:
        idx = args.index("--setup")
        if len(args) < idx + 3:
            print("Usage: python deploy.py --setup <github-username> <repo-name>")
            return
        setup_github(args[idx + 1], args[idx + 2])
    elif "--demo" in args:
        deploy("demo")
    elif "--quick" in args:
        deploy("quick")
    else:
        deploy("full")


if __name__ == "__main__":
    main()
