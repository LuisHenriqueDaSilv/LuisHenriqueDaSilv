import os
import requests
import re
from datetime import datetime

USERNAME = "LuisHenriqueDaSilv"
README_PATH = "README.md"
START_MARKER = "<!-- START_LATEST_REPOS -->"
END_MARKER = "<!-- END_LATEST_REPOS -->"

# Mapeamento manual para ícones do devicon, caso o nome da linguagem não bata direto
LANGUAGE_ICON_MAP = {
    "C++": "cplusplus",
    "C#": "csharp",
    "Jupyter Notebook": "jupyter",
    "HTML": "html5",
    "CSS": "css3",
    "Shell": "bash",
    # Adicione outros conforme necessário. Se não estiver aqui, tenta usar o nome em lowercase.
}

def get_headers():
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers

def fetch_latest_repos():
    url = f"https://api.github.com/users/{USERNAME}/repos?sort=updated&per_page=6"
    response = requests.get(url, headers=get_headers())
    if response.status_code != 200:
        raise Exception(f"Failed to fetch repos: {response.status_code} {response.text}")
    return response.json()

def get_commit_count(repo_name):
    # Usa per_page=1 e pega o link do header para saber o total de páginas (commits)
    url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/commits?per_page=1"
    response = requests.get(url, headers=get_headers())
    
    if response.status_code != 200:
        return 0
    
    if "Link" in response.headers:
        links = response.headers["Link"]
        # Ex: <...page=42>; rel="last"
        match = re.search(r'[&?]page=(\d+)>; rel="last"', links)
        if match:
            return int(match.group(1))
    
    # Se não tem paginação, conta os itens retornados (0 ou 1 aqui)
    return len(response.json())

def get_last_commit(repo_name):
    url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/commits?per_page=1"
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200 and len(response.json()) > 0:
        commit = response.json()[0]
        message = commit["commit"]["message"].split("\n")[0] # Pega só a primeira linha
        html_url = commit["html_url"]
        return message, html_url
    return "Sem commits", "#"

def get_language_icon_url(language):
    if not language:
        return ""
    
    icon_name = LANGUAGE_ICON_MAP.get(language, language.lower())
    # URL do devicon
    return f"https://cdn.jsdelivr.net/gh/devicons/devicon/icons/{icon_name}/{icon_name}-original.svg"

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

    # Layout do card em HTML
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
    # Cria uma tabela 2x3 (2 linhas, 3 colunas) ou ajusta conforme # de repos
    html = '<table width="100%">\n'
    
    for i in range(0, len(repos), 3):
        html += '  <tr>\n'
        chunk = repos[i:i+3]
        for repo in chunk:
            html += format_repo_card(repo)
        
        # Preenche celulas vazias se não tiver 3
        while len(chunk) < 3:
            html += '    <td width="33%"></td>\n'
            chunk.append(None)
            
        html += '  </tr>\n'
        
    html += '</table>'
    return html

def update_readme(content):
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme_content = f.read()
        
    pattern = f"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}"
    replacement = f"{START_MARKER}\n{content}\n{END_MARKER}"
    
    new_content = re.sub(pattern, replacement, readme_content, flags=re.DOTALL)
    
    if new_content != readme_content:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("README.md updated successfully.")
    else:
        print("No changes needed in README.md.")

if __name__ == "__main__":
    try:
        print("Fetching repositories...")
        repos = fetch_latest_repos()
        print(f"Found {len(repos)} repositories.")
        
        print("Generating grid...")
        content = format_repo_grid(repos)
        
        print("Updating README...")
        update_readme(content)
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
