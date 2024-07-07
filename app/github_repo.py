
import os
from github import Github
from github.GithubException import GithubException

class GitHubRepo:
    def __init__(self, url: str):
        owner, repo_name = self.extract_github_owner_repo(url)
        self.owner = owner
        self.repo_name = repo_name
        self.access_token = os.getenv("GITHUB_TOKEN")
        self.github = Github(self.access_token)
        try:
            self.repo = self.github.get_repo(f"{owner}/{repo_name}")
        except GithubException as e:
            print(f"Failed to access repository: {e.data['message']}")
            raise e

    def get_file_structure(self, path=""):
        try:
            contents = self.repo.get_contents(path)
            file_structure = []
            for content in contents:
                if "package-lock" in content.path or "png" in content.path or "pdf" in content.path or "ico" in content.path:
                    continue
                if content.type == "dir":
                    file_structure.extend(self.get_file_structure(content.path))
                else: 
                    file_structure.append(content.path)
            return file_structure
        except GithubException as e:
            print(f"Failed to get file structure: {e.data['message']}")
            return []

    def get_file_content(self, file_path: str):
        try:
            print(f"Getting content for file: {file_path}")
            file_content = self.repo.get_contents(file_path)
            return file_content.decoded_content.decode()
        except GithubException as e:
            print(f"Failed to get file content: {e.data['message']}")
            return None

    def extract_github_owner_repo(self, url):
        """
        Extracts the owner and repository name from a GitHub URL.
        
        Parameters:
        url (str): The GitHub URL.
        
        Returns:
        tuple: A tuple containing the owner and repository name.
        """
        if url.startswith("https://github.com/"):
            parts = url[len("https://github.com/"):].strip('/').split('/')
            if len(parts) >= 2:
                owner = parts[0]
                repo = parts[1]
                return owner, repo
        return None, None