import os
import requests
import re
from datetime import datetime

USERNAME = "LuisHenriqueDaSilv"
README_PATH = "README.md"
START_MARKER_REPOS = "<!-- START_LATEST_REPOS -->"
END_MARKER_REPOS = "<!-- END_LATEST_REPOS -->"
START_MARKER_STATS = "<!-- START_PROFILE_STATS -->"
END_MARKER_STATS = "<!-- END_PROFILE_STATS -->"

# Mapeamento manual para ícones do devicon
LANGUAGE_ICON_MAP = {
    "C++": "cplusplus",
    "C#": "csharp",
    "Jupyter Notebook": "jupyter",
    "HTML": "html5",
    "CSS": "css3",
    "Shell": "bash",
}

def get_headers():
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers

def fetch_all_repos():
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{USERNAME}/repos?sort=updated&per_page=100&page={page}"
        response = requests.get(url, headers=get_headers())
        if response.status_code != 200:
            raise Exception(f"Failed to fetch repos: {response.status_code} {response.text}")
        
        page_repos = response.json()
        if not page_repos:
            break
            
        repos.extend(page_repos)
        page += 1
        
    return repos

def get_commit_count(repo_name):
    try:
        url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/commits?per_page=1"
        response = requests.get(url, headers=get_headers())
        
        if response.status_code != 200:
            return 0
        
        if "Link" in response.headers:
            links = response.headers["Link"]
            match = re.search(r'[&?]page=(\d+)>; rel="last"', links)
            if match:
                return int(match.group(1))
        
        # If no pagination, count items (0 or 1)
        return len(response.json())
    except:
        return 0

def get_last_commit(repo_name):
    try:
        url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/commits?per_page=1"
        response = requests.get(url, headers=get_headers())
        
        if response.status_code == 200 and len(response.json()) > 0:
            commit = response.json()[0]
            message = commit["commit"]["message"].split("\n")[0]
            html_url = commit["html_url"]
            return message, html_url
    except:
        pass
    return "Sem commits", "#"

def get_pr_count():
    try:
        # Search API to count PRs created by the user
        url = f"https://api.github.com/search/issues?q=author:{USERNAME}+type:pr"
        response = requests.get(url, headers=get_headers())
        if response.status_code == 200:
            return response.json().get("total_count", 0)
    except:
        pass
    return 0

def get_language_icon_url(language):
    if not language:
        return ""
    icon_name = LANGUAGE_ICON_MAP.get(language, language.lower())
    return f"https://cdn.jsdelivr.net/gh/devicons/devicon/icons/{icon_name}/{icon_name}-original.svg"

def calculate_stats(repos):
    total_commits = 0
    languages_count = {}
    
    print(f"Calculating stats for {len(repos)} repositories...")
    
    for repo in repos:
        if repo["fork"]:
            continue
            
        # Total commits
        count = get_commit_count(repo["name"])
        total_commits += count
        
        # Languages
        lang = repo["language"]
        if lang:
            languages_count[lang] = languages_count.get(lang, 0) + 1

    return total_commits, languages_count

def format_stats_section(total_repos, total_commits, total_prs, languages_count):
    # Sort languages by usage
    sorted_langs = sorted(languages_count.items(), key=lambda x: x[1], reverse=True)[:5]
    
    langs_html = ""
    for lang, count in sorted_langs:
        icon = get_language_icon_url(lang)
        langs_html += f'<img src="{icon}" alt="{lang}" width="30" height="30" style="margin-right: 10px;" /> '

    html = f"""
<div align="center">
    <h2>📊 Estatísticas Gerais</h2>
    <table width="100%" align="center">
        <tr>
            <td width="25%" align="center" style="text-align: center;">
                <h3>📦 Repositórios</h3>
                <p style="font-size: 24px;"><strong>{total_repos}</strong></p>
            </td>
            <td width="25%" align="center" style="text-align: center;">
                <h3>💾 Total de Commits</h3>
                <p style="font-size: 24px;"><strong>{total_commits}</strong></p>
            </td>
            <td width="25%" align="center" style="text-align: center;">
                <h3>🔄 Pull Requests</h3>
                <p style="font-size: 24px;"><strong>{total_prs}</strong></p>
            </td>
            <td width="25%" align="center" style="text-align: center;">
                <h3>🛠️ Principais Linguagens</h3>
                <div align="center">{langs_html}</div>
            </td>
        </tr>
    </table>
</div>
"""
    return html

def format_repo_card(repo):
    name = repo["name"]
    url = repo["html_url"]
    description = repo["description"] or "Sem descrição"
    if len(description) > 60:
        description = description[:57] + "..."
        
    language = repo["language"]
    icon_url = get_language_icon_url(language)
    
    commit_count = get_commit_count(name)
    last_msg, last_url = get_last_commit(name)
    if len(last_msg) > 40:
        last_msg = last_msg[:37] + "..."

    card = f"""
<td width="33%">
<div align="center">
    <a href="{url}">
        <img src="{icon_url}" width="40" height="40" alt="{language}" />
    </a>
    <br/>
    <strong><a href="{url}">{name}</a></strong>
    <br/>
    <p align="center" style="font-size: 12px; height: 40px; overflow: hidden;">{description}</p>
    <p align="left" style="font-size: 11px;">
        📄 <strong>Commits:</strong> {commit_count}<br/>
        📝 <strong>Último:</strong> <a href="{last_url}" title="{last_msg}">{last_msg}</a>
    </p>
</div>
</td>
"""
    return card

def format_repo_grid(repos):
    html = '<table width="100%">\n'
    for i in range(0, len(repos), 3):
        html += '  <tr>\n'
        chunk = repos[i:i+3]
        for repo in chunk:
            html += format_repo_card(repo)
        while len(chunk) < 3:
            html += '    <td width="33%"></td>\n'
            chunk.append(None)
        html += '  </tr>\n'
    html += '</table>'
    return html

def update_readme_section(content, start_marker, end_marker):
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme_content = f.read()
        
    pattern = f"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
    replacement = f"{start_marker}\n{content}\n{end_marker}"
    
    new_content = re.sub(pattern, replacement, readme_content, flags=re.DOTALL)
    
    if new_content != readme_content:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False

if __name__ == "__main__":
    try:
        print("Fetching all repositories...")
        all_repos = fetch_all_repos()
        print(f"Total repositories found: {len(all_repos)}")
        
        # 1. Update Latest Repos Section
        all_repos.sort(key=lambda x: x['updated_at'], reverse=True)
        latest_repos = all_repos[:6]
        
        print("Generating latest repos grid...")
        latest_content = format_repo_grid(latest_repos)
        if update_readme_section(latest_content, START_MARKER_REPOS, END_MARKER_REPOS):
            print("Updated Latest Repos section.")
            
        # 2. Update Profile Stats Section
        print("Calculating profile stats...")
        total_commits, languages_count = calculate_stats(all_repos)
        
        print("Fetching PR count...")
        total_prs = get_pr_count()
        
        stats_content = format_stats_section(len(all_repos), total_commits, total_prs, languages_count)
        
        if update_readme_section(stats_content, START_MARKER_STATS, END_MARKER_STATS):
            print("Updated Profile Stats section.")
            
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
