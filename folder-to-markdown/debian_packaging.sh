#!/bin/bash
# Script to create a Debian package for the Folder-to-Markdown application

# Exit on error
set -e

# Configuration
APP_NAME="folder-to-markdown"
APP_VERSION="1.0.0"
MAINTAINER="yadnyeshkolte"
DESCRIPTION="Application to create markdown document from project folder"
DEPENDS="python3, python3-pip, python3-tk, python3-pil, python3-pil.imagetk"

# Create temporary directory structure
BUILD_DIR="$(mktemp -d)"
PACKAGE_DIR="${BUILD_DIR}/${APP_NAME}_${APP_VERSION}"
mkdir -p "${PACKAGE_DIR}/DEBIAN"
mkdir -p "${PACKAGE_DIR}/usr/bin"
mkdir -p "${PACKAGE_DIR}/usr/share/${APP_NAME}"
mkdir -p "${PACKAGE_DIR}/usr/share/applications"
mkdir -p "${PACKAGE_DIR}/usr/share/pixmaps"

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

# Create postinst script to install Python dependencies
cat > "${PACKAGE_DIR}/DEBIAN/postinst" << EOF
#!/bin/bash
set -e
pip3 install markdown
chmod +x /usr/bin/${APP_NAME}
update-desktop-database
EOF
chmod 755 "${PACKAGE_DIR}/DEBIAN/postinst"

# Create the launcher script
cat > "${PACKAGE_DIR}/usr/bin/${APP_NAME}" << EOF
#!/bin/bash
python3 /usr/share/${APP_NAME}/folder_to_markdown.py "\$@"
EOF
chmod 755 "${PACKAGE_DIR}/usr/bin/${APP_NAME}"

# Copy the main application
cp folder_to_markdown.py "${PACKAGE_DIR}/usr/share/${APP_NAME}/"

# Create a simple icon for the application
cat > "${PACKAGE_DIR}/usr/share/pixmaps/${APP_NAME}.svg" << EOF
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <rect width="128" height="128" fill="#f0f0f0" rx="14" ry="14" />
  <g fill="#4a86e8">
    <rect x="20" y="30" width="40" height="10" rx="2" ry="2" />
    <rect x="30" y="50" width="70" height="10" rx="2" ry="2" />
    <rect x="30" y="70" width="60" height="10" rx="2" ry="2" />
    <rect x="30" y="90" width="50" height="10" rx="2" ry="2" />
  </g>
  <path d="M20,30 L25,20 L65,20 L70,30 Z" fill="#ffcc33" />
</svg>
EOF

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
EOF

# Build the package
dpkg-deb --build "${PACKAGE_DIR}"

# Move the package to the current directory
cp "${PACKAGE_DIR}.deb" ./
echo "Package created: ${APP_NAME}_${APP_VERSION}.deb"

# Clean up
rm -rf "${BUILD_DIR}"
