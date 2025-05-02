#!/bin/bash
# Script to create a Debian package for the Folder-to-Markdown application
# This package will handle virtual environment creation automatically

# Exit on error
set -e

# Configuration
APP_NAME="folder-to-markdown"
APP_VERSION="1.0.0"
MAINTAINER="yadnyeshkolte"
DESCRIPTION="Application to create markdown document from project folder"
DEPENDS="python3-venv, python3-tk, python3-pil, python3-pil.imagetk"

# Create temporary directory structure
BUILD_DIR="$(mktemp -d)"
PACKAGE_DIR="${BUILD_DIR}/${APP_NAME}_${APP_VERSION}"
mkdir -p "${PACKAGE_DIR}/DEBIAN"
mkdir -p "${PACKAGE_DIR}/usr/bin"
mkdir -p "${PACKAGE_DIR}/usr/share/${APP_NAME}"
mkdir -p "${PACKAGE_DIR}/usr/share/applications"
mkdir -p "${PACKAGE_DIR}/usr/share/pixmaps"
mkdir -p "${PACKAGE_DIR}/var/lib/${APP_NAME}/venv"

# Create control file
cat > "${PACKAGE_DIR}/DEBIAN/control" << EOF
Package: ${APP_NAME}
Version: ${APP_VERSION}
Section: utils
Priority: optional
Architecture: all
Depends: ${DEPENDS}
Maintainer: ${MAINTAINER}
Description: ${DESCRIPTION}
 Creates a markdown representation of a folder structure.
 Features:
  * Generate a tree view of the folder structure
  * Include file contents in the markdown output
  * Exclude specific files, folders, and extensions
  * Real-time monitoring of file changes
  * Save markdown to the Documents folder
EOF

# Create postinst script to setup virtual environment
cat > "${PACKAGE_DIR}/DEBIAN/postinst" << EOF
#!/bin/bash
set -e

# Create virtual environment
if [ ! -d "/var/lib/${APP_NAME}/venv/bin" ]; then
    echo "Setting up Python virtual environment for ${APP_NAME}..."
    python3 -m venv /var/lib/${APP_NAME}/venv
    
    # Install dependencies in the virtual environment
    /var/lib/${APP_NAME}/venv/bin/pip install --no-cache-dir markdown Pillow
fi

# Set proper permissions
chmod 755 /usr/bin/${APP_NAME}
chmod -R 755 /usr/share/${APP_NAME}
chmod -R 755 /var/lib/${APP_NAME}

# Update desktop database
update-desktop-database
echo "${APP_NAME} installation completed successfully."
EOF
chmod 755 "${PACKAGE_DIR}/DEBIAN/postinst"

# Create postrm script to clean up
cat > "${PACKAGE_DIR}/DEBIAN/postrm" << EOF
#!/bin/bash
set -e

if [ "\$1" = "purge" ]; then
    echo "Removing ${APP_NAME} data..."
    rm -rf /var/lib/${APP_NAME}
fi
EOF
chmod 755 "${PACKAGE_DIR}/DEBIAN/postrm"

# Create the launcher script
cat > "${PACKAGE_DIR}/usr/bin/${APP_NAME}" << EOF
#!/bin/bash
# Launcher script for folder-to-markdown application

# Check if virtual environment exists and is functional
if [ ! -f "/var/lib/${APP_NAME}/venv/bin/python" ]; then
    # Virtual environment doesn't exist, recreate it
    echo "Recreating Python virtual environment..."
    python3 -m venv /var/lib/${APP_NAME}/venv
    /var/lib/${APP_NAME}/venv/bin/pip install --no-cache-dir markdown Pillow
fi

# Run the application using the virtual environment's Python
exec /var/lib/${APP_NAME}/venv/bin/python /usr/share/${APP_NAME}/folder_to_markdown.py "\$@"
EOF
chmod 755 "${PACKAGE_DIR}/usr/bin/${APP_NAME}"

# Copy the main application
cp folder_to_markdown.py "${PACKAGE_DIR}/usr/share/${APP_NAME}/"

# Copy icon file or create a new one
if [ -f "icon.svg" ]; then
    cp icon.svg "${PACKAGE_DIR}/usr/share/pixmaps/${APP_NAME}.svg"
else
    # Create a simple icon for the application
    cat > "${PACKAGE_DIR}/usr/share/pixmaps/${APP_NAME}.svg" << EOF
<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 124 124" fill="none">
<rect width="124" height="124" rx="24" fill="#fbbc05"/>
<path d="M19.375 36.7818V100.625C19.375 102.834 21.1659 104.625 23.375 104.625H87.2181C90.7818 104.625 92.5664 100.316 90.0466 97.7966L26.2034 33.9534C23.6836 31.4336 19.375 33.2182 19.375 36.7818Z" fill="white"/>
<circle cx="63.2109" cy="37.5391" r="18.1641" fill="black"/>
<rect opacity="0.4" x="81.1328" y="80.7198" width="17.5687" height="17.3876" rx="4" transform="rotate(-45 81.1328 80.7198)" fill="#FDBA74"/>
</svg>
EOF
fi

# Create desktop entry
cat > "${PACKAGE_DIR}/usr/share/applications/${APP_NAME}.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Folder to Markdown
Comment=${DESCRIPTION}
Exec=${APP_NAME}
Icon=${APP_NAME}
Terminal=false
Categories=Utility;Development;
Keywords=markdown;documentation;folder;project;
EOF

# Build the package
dpkg-deb --build "${PACKAGE_DIR}"

# Move the package to the current directory
cp "${PACKAGE_DIR}.deb" ./
echo "Package created: ${APP_NAME}_${APP_VERSION}.deb"

# Clean up
rm -rf "${BUILD_DIR}"

echo ""
echo "Installation instructions:"
echo "sudo apt install ./folder-to-markdown_1.0.0.deb"
echo ""
echo "If dependencies are missing, run:"
echo "sudo apt install -f"
