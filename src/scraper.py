import os
import ast
import requests
import csv
from bs4 import BeautifulSoup
import urllib.parse
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

def get_soup(url):
    response = requests.get(url)
    return BeautifulSoup(response.content, 'html.parser')

def get_items_in_directory(url):
    soup = get_soup(url)
    items = []

    for item in soup.find_all('a', class_='js-navigation-open Link--primary'):
        items.append('https://github.com' + item.get('href'))

    return items

def get_file_content(file_url):
    soup = get_soup(file_url)
    file_name = soup.find('strong', class_='final-path').text

    # A set of file extensions to ignore
    ignored_extensions = {'.png', '.jpg', '.jpeg', '.gif'}

    # Check the file extension
    _, extension = os.path.splitext(file_name)
    if extension in ignored_extensions:
        return None, None

    files_to_ignore = set(ast.literal_eval(os.getenv('FILES_TO_IGNORE')))

    if file_name in files_to_ignore:
        return None, None

    raw_btn = soup.find('a', attrs={'id': 'raw-url'})

    if raw_btn:
        raw_url = 'https://github.com' + raw_btn['href']
        response = requests.get(raw_url)
        file_content = response.text
    else:
        print(f"Could not find raw content for {file_name}.")
        return None, None

    return file_name, file_content


def process_repository(url, output_dir_path, current_dir="", file_paths=[]):
    items = get_items_in_directory(url)

    # Parse the URL to extract the user and repo names
    parsed_url = urllib.parse.urlparse(url)
    user_name, repo_name = parsed_url.path.strip("/").split("/")[:2]

    for item_url in items:
        if "/tree/" in item_url:
            item_name = item_url.split('/')[-1]
            new_current_dir = os.path.join(current_dir, item_name)
            process_repository(item_url, output_dir_path, new_current_dir, file_paths)
        elif "/blob/" in item_url:
            file_name, file_content = get_file_content(item_url)
            if file_name is not None:
                file_path = os.path.join(current_dir, file_name)
                file_paths.append(file_path)
                safe_file_path = file_path.replace("/", "_")  # Replace / with _ in file path
                output_file_path = os.path.join(output_dir_path, f"{file_name}.txt")

                # Create the directory if it doesn't exist
                os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

                with open(output_file_path, 'w') as output_file:
                    output_file.write(f"The following is the content of a file named {file_name} from a GitHub repository named {repo_name} by {user_name}. The content starts after ------ and ends before --END--.\n")  # Custom sentence
                    output_file.write("------\n")
                    output_file.write(f"{file_path}\n")
                    output_file.write(f"{file_content}\n")
                    output_file.write("--END--\n")
    return file_paths

def main(repo_url):
    # Parse the repository URL to extract the user and repo names
    parsed_url = urllib.parse.urlparse(repo_url)
    user_name, repo_name = parsed_url.path.strip("/").split("/")

    # Form the output directory path
    output_dir_path = os.path.join(os.getenv('SAVE_PATH'), f"{user_name}_{repo_name}")

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir_path, exist_ok=True)

    # Form the output filenames
    txt_filename = f"{user_name}_{repo_name}_file_paths.txt"

    # Form the full paths for the output files
    txt_file_path = os.path.join(output_dir_path, txt_filename)

    file_paths = process_repository(repo_url, output_dir_path)
    print("=" * 100)
    print(f"Repository contents written to {output_dir_path}.")

    # Write the list of file paths to a TXT file
    with open(txt_file_path, 'w') as txtfile:
        txtfile.write(f"This is a list of file paths from the GitHub repository named {repo_name} by {user_name}:\n")
        for file_path in file_paths:
            txtfile.write(file_path + "\n")
    print("=" * 100)
    print(f"List of file paths written to {txt_file_path}.\n")



# This asks for URL input if the file is randirectly for testing purposes.
if __name__ == "__main__":
    repo_url = input("Enter the GitHub repository URL: ")
    main(repo_url)