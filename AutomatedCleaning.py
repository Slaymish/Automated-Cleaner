import os
import shutil
import subprocess
import tempfile
import tkinter as tk
from tkinter import filedialog
from rich import print
from rich.panel import Panel
from rich.table import Table
from openai import OpenAI
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

tree_depth = "2"

# Set up OpenAI API key

def organize_file_system(directory):
    global tree_depth
    # Get the file system tree of the specified directory
    file_system_tree = execute_command("tree", directory)

    tree_footer = file_system_tree.split("\n")[-2]

    # If files > 1000, ask user to confirm
    if len(file_system_tree) > 10000:
        if not get_user_confirmation("The file system is very large. Do you want to continue?"):
            return

    # Store the current state of the file system tree
    old_state = file_system_tree

    # Show options to user: print tree, create cleaning script, execute script, undo changes
    while True:
        os.system("clear")
        file_system_tree = execute_command("tree", directory)
        tree_footer = file_system_tree.split("\n")[-2]
        print(Panel.fit("Automated Cleaning Tool", style="bold blue on white"))
        print(f"\nCurrent directory: {directory}")
        print(f"Script made? {'Yes' if 'script' in locals() else 'No'}")
        print(f"Old state stored? {'Yes' if 'old_state' in locals() else 'No'}")
        print(f"{tree_footer}")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Option")
        table.add_column("Description")
        table.add_row('1) [p]', 'Print file system tree')
        table.add_row("2) [c]", "Create cleaning script")
        table.add_row("3) [e]", "Execute cleaning script")
        table.add_row("4) [d]", "Change tree depth (default: 2)")
        table.add_row("5) [u]", "Undo changes")
        table.add_row("6) [q]", "Exit")
        print(table)

        choice = input("Enter your choice (1-5): ")

        if choice == "1" or choice == "p":
            display_file_system_tree(file_system_tree)
            input("Press Enter to continue...")
        elif choice == "2" or choice == "c":
            if "script" in locals():
                print(script)
            script = create_cleaning_script(file_system_tree)
            print(f"\n==================\nCleaning script:\n{script}\n==================\n")
            input("Press Enter to continue...")
        elif choice == "3" or choice == "e":
            if "script" in locals():
                execute_script(script, directory)
                print("Cleaning script executed.")
                input("Press Enter to continue...")
            else:
                print("No cleaning script available. Please create a script first.")
                input("Press Enter to continue...")
        elif choice == "4" or choice == "d":
            tree_depth = input("Enter the tree depth (default: 2): ")
            file_system_tree = execute_command("tree", directory)
        elif choice == "5" or choice == "u":
            restore_old_state(old_state, directory)
            print("Changes undone.")
        elif choice == "6" or choice == "q":
            break
        else:
            print("Invalid choice. Please try again.")

def create_cleaning_script(file_system_tree):
    script = ""
    satisfied = False
    first_run = True
    users_requests = []
    user_input = get_user_input("\nHow would you like to organize the file system? ", script)
    users_requests.append(user_input)
    while not satisfied:
        if not first_run:
            user_input = get_user_input("How would you like to modify the script? ", script)
            users_requests.append(user_input)
        possible_script = generate_script_part(file_system_tree, user_input, script, users_requests)
        if script_is_valid(possible_script):
            script = possible_script

        print(f"\n==================\nCurrent script:\n{script}\n==================\n")
        satisfied = not get_user_confirmation("Any more changes?")
        first_run = False

    return script


def get_user_input(prompt, script):
    # Display the prompt to the user and get their input
    if script != "":
        print(f"Current script:\n{script}")

    print("\nExamples of valid inputs:")
    print("- Organize files by file type (e.g., .jpg, .pdf, .txt)")
    print("- Create folders for each programming language (e.g., Python, Java, C++)")
    print("- Move all files with 'report' in the name to a 'Reports' folder")
    print("- Delete temporary files with the extension .tmp")
    print("- Rename files to follow a specific naming convention (e.g., YYYY-MM-DD_filename)")

    user_input = input(prompt)

    return user_input

def generate_script_part(file_system_tree, user_input, existing_script, users_requests):
    # Formulating the prompt for the LLM with additional instructions and existing script as context
    prompt_text = (
        "Here's the current file system tree:\n"
        f"{file_system_tree}\n\n"
        "Existing script that organizes the file system based on previous instructions:\n"
        f"{existing_script}\n\n"
        "Think carefully and review the existing script and file system structure. "
        "Generate ONLY the additional bash script snippet needed to fulfill the new user request. Do not use code blocks. "
        "This snippet should strictly follow the logical structure and style of the existing script. "
        "Do not include explanations or comments outside the script logic."
    )

    messages = [
        {"role": "system", "content": "You are a bash script generator. You only write bash script snippets."},
    ]   

    # adding the user's previous requests to the messages (excluding the first one which is the current request)
    for request in users_requests:
        messages.append({"role": "user", "content": request})

    messages.append({"role": "system", "content": prompt_text})

    
    response = client.chat.completions.create(
        model="gpt-4-turbo",  # Or another suitable model
        messages=messages,
        max_tokens=150,  # Adjust based on expected script length
        temperature=0.5  # Adjust creativity level; lower is more deterministic
    )
    
    # Extracting the script part generated by the model
    generated_script_part = response.choices[0].message.content

    # check if it has a codeblock around it, if so, remove it and bash
    if generated_script_part.startswith("```") and generated_script_part.endswith("```"):
        generated_script_part = generated_script_part[3:-3]
    if generated_script_part.startswith("bash"):
        generated_script_part = generated_script_part[4:]

    return generated_script_part


def script_is_valid(script):
    # Implement your validation logic here
    # This could include checking for potentially dangerous commands, syntax errors, etc.
    return True  # Placeholder


def execute_script(script, directory):
    # Execute the generated script in the specified directory
    script_file = os.path.join(directory, "organize_script.sh")
    
    # Check if the script file exists
    if not os.path.exists(script_file):
        # Create the script file
        with open(script_file, "w") as file:
            file.write(script)
        print(f"Script file '{script_file}' created.")
    else:
        print(f"Script file '{script_file}' already exists. Overwriting...")
        with open(script_file, "w") as file:
            file.write(script)
    
    try:
        subprocess.run(["bash", script_file], cwd=directory, check=True)
        print("Cleaning script executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing script: {e}")
    finally:
        os.remove(script_file)


def create_temp_folder():
    # Create a temporary folder to store deleted items
    return tempfile.mkdtemp()

def move_deleted_items(directory, temp_folder):
    # Move deleted items from the specified directory to the temporary folder
    deleted_items = get_deleted_items(directory)
    for item in deleted_items:
        shutil.move(item, temp_folder)

def get_deleted_items(directory):
    # Get the list of deleted items in the specified directory
    # Replace this with your actual implementation to identify deleted items
    return []

def restore_old_state(old_state, directory):
    # Restore the file system to its previous state
    # Replace this with your actual implementation to restore the old state
    pass

def delete_folder(folder):
    # Delete the specified folder
    shutil.rmtree(folder)

def display_file_system_tree(file_system_tree):
    # Display the file system tree to the user (except the last line)
    file_system_tree = file_system_tree.split("\n")[:-2]
    print("\nFile system tree:")
    for line in file_system_tree:
        print(line)

def execute_command(command, directory):
    # Execute the specified command and return the output
    result = subprocess.run([command,"-L",tree_depth, directory], capture_output=True, text=True)
    return result.stdout

def get_user_confirmation(prompt):
    # Display the prompt to the user and get their confirmation (y/n)
    while True:
        response = input(f"{prompt} (y/n): ").lower()
        if response == "y":
            return True
        elif response == "n":
            return False
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

def get_directory():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    directory = filedialog.askdirectory()  # Open the file dialog
    return directory

# Main program
directory = get_directory()
organize_file_system(directory)
