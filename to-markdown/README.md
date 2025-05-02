# Folder to Markdown

A Python application that create markdown document from a folder structure. This tool analyzes your project's directory structure and creates a markdown file that includes both the tree structure and the content of each file.

## Features

- **Tree Structure Visualization**: Shows the folder hierarchy in a tree view
- **File Content Inclusion**: Includes the content of each file in the document
- **Customizable Exclusions**: Exclude specific file types, folders, and files
- **Change Detection**: Monitors files for changes and displays them in the UI
- **Live Preview**: Renders the markdown in real-time
- **Auto-Save**: Automatically saves the markdown file to your Documents folder
- **Custom Naming**: Specify a custom name for the generated markdown file

## Installation on Ubuntu

### Method 1: Using the Debian Package (.deb)

1. Download the `.deb` package
2. Install the package:
    
    ```
    sudo dpkg -i folder-to-markdown_1.0.0.deb
    ```
    
3. If there are dependency issues, run:
    
    ```
    sudo apt-get install -f
    ```
    

### Method 2: Manual Installation

1. Clone or download this repository
2. Install the required dependencies:
    
    ```
    sudo apt-get updatesudo apt-get install python3 python3-pip python3-tk python3-pil python3-pil.imagetkpip3 install markdown
    ```
    
3. Make the application executable:
    
    ```
    chmod +x folder_to_markdown.py
    ```
    
4. Run the application:
    
    ```
    ./folder_to_markdown.py
    ```
    

## Building the Debian Package

If you want to build the Debian package yourself:

1. Make sure the required packages are installed:
    
    ```
    sudo apt-get install dpkg-dev
    ```
    
2. Run the packaging script:
    
    ```
    chmod +x debian_packaging.sh./debian_packaging.sh
    ```
    
3. This will create a .deb package in the current directory

## Usage

1. Launch the application
2. Click "Browse" to select a folder
3. The application will display the folder structure in the left panel and the markdown preview in the right panel
4. Use the "Exclusion Settings" button to customize what files and folders to exclude
5. Click "Refresh" to regenerate the documentation if needed
6. The application auto-saves to your Documents folder, but you can also click "Save" to save manually
7. You can change the output filename in the "Output" text field

## Customizing

You can customize the excluded directories, files, and extensions using the "Exclusion Settings" button in the application. Your settings will be saved for future use.