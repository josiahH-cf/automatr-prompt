#!/usr/bin/env bash
#
# Automatr Unified Installer
#
# This script installs Automatr and all its dependencies on:
# - Ubuntu/Debian Linux
# - WSL2 (Windows Subsystem for Linux)
# - macOS (experimental)
#
# Usage:
#   ./install.sh          # Interactive installation
#   ./install.sh --quick  # Quick install with defaults
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

# Platform-specific paths (set after detect_platform)
DATA_DIR=""
CONFIG_DIR=""
LLAMA_CPP_DIR=""

set_platform_paths() {
    if [[ "$PLATFORM" == "macos" ]]; then
        DATA_DIR="$HOME/Library/Application Support/automatr"
        CONFIG_DIR="$DATA_DIR"
    else
        DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/automatr"
        CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/automatr"
    fi
    LLAMA_CPP_DIR="${DATA_DIR}/llama.cpp"
}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect platform
detect_platform() {
    OS="$(uname -s)"
    ARCH="$(uname -m)"
    IS_WSL2=false
    
    # Check for native Windows (Git Bash, MSYS2, etc.)
    if [[ "$OS" == MINGW* ]] || [[ "$OS" == MSYS* ]] || [[ "$OS" == CYGWIN* ]]; then
        echo ""
        log_warn "Native Windows detected!"
        echo ""
        echo "  This bash installer is for Linux/WSL2/macOS."
        echo "  For Windows, run the PowerShell installer instead:"
        echo ""
        echo "  Use Linux, WSL2, or macOS to run the bash installer."
        echo ""
        exit 0
    fi
    
    if [[ -f /proc/version ]] && grep -qi "microsoft\|wsl" /proc/version 2>/dev/null; then
        IS_WSL2=true
    fi
    
    case "$OS" in
        Linux*)
            if $IS_WSL2; then
                PLATFORM="wsl2"
            else
                PLATFORM="linux"
            fi
            ;;
        Darwin*)
            PLATFORM="macos"
            ;;
        *)
            log_error "Unsupported operating system: $OS"
            exit 1
            ;;
    esac
    
    log_info "Detected platform: $PLATFORM ($ARCH)"
}

# Install system dependencies
install_system_deps() {
    log_info "Installing system dependencies..."
    
    case "$PLATFORM" in
        linux|wsl2)
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y \
                    python3 python3-pip python3-venv \
                    build-essential cmake git \
                    libgl1-mesa-dev libxcb-xinerama0 \
                    qt6-base-dev libqt6widgets6 \
                    2>/dev/null || {
                        # Fallback for older Ubuntu
                        sudo apt-get install -y \
                            python3 python3-pip python3-venv \
                            build-essential cmake git \
                            libgl1-mesa-glx
                    }
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y \
                    python3 python3-pip \
                    gcc-c++ cmake git \
                    qt6-qtbase-devel
            else
                log_warn "Package manager not recognized. Please install manually:"
                log_warn "  - Python 3.10+"
                log_warn "  - build-essential/gcc, cmake, git"
                log_warn "  - Qt6 base libraries"
            fi
            ;;
        macos)
            if ! command -v brew &> /dev/null; then
                log_error "Homebrew is required. Install it from https://brew.sh"
                exit 1
            fi
            # Ensure Xcode Command Line Tools are installed
            if ! xcode-select -p &> /dev/null; then
                log_info "Installing Xcode Command Line Tools..."
                xcode-select --install
                log_warn "Please wait for Xcode CLI tools to finish installing, then re-run this script."
                exit 0
            fi
            brew install python@3.11 cmake qt@6 git
            ;;
    esac
    
    log_success "System dependencies installed"
}

# Create Python virtual environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."
    
    if [[ ! -d "$VENV_DIR" ]]; then
        python3 -m venv "$VENV_DIR"
    fi
    
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip wheel setuptools
    
    # Install automatr
    pip install -e "$SCRIPT_DIR"
    
    log_success "Python environment ready: $VENV_DIR"
}

# Build llama.cpp from source
build_llama_cpp() {
    log_info "Setting up llama.cpp..."
    
    if [[ -f "$LLAMA_CPP_DIR/build/bin/llama-server" ]]; then
        log_success "llama-server already built"
        return
    fi
    
    # Ensure data directory exists
    mkdir -p "$DATA_DIR"
    
    # Clone if not present
    if [[ ! -d "$LLAMA_CPP_DIR" ]]; then
        log_info "Cloning llama.cpp to $LLAMA_CPP_DIR..."
        git clone --depth 1 https://github.com/ggerganov/llama.cpp.git "$LLAMA_CPP_DIR"
    fi
    
    cd "$LLAMA_CPP_DIR"
    
    # Build
    log_info "Building llama.cpp (this may take a few minutes)..."
    
    mkdir -p build
    cd build
    
    # Detect GPU support
    CMAKE_ARGS=""
    if command -v nvcc &> /dev/null; then
        log_info "CUDA detected, building with GPU support..."
        CMAKE_ARGS="-DGGML_CUDA=ON"
    elif [[ "$PLATFORM" == "macos" ]]; then
        log_info "Building with Metal support..."
        CMAKE_ARGS="-DGGML_METAL=ON"
    fi
    
    cmake .. $CMAKE_ARGS -DCMAKE_BUILD_TYPE=Release
    cmake --build . --config Release -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
    
    log_success "llama.cpp built successfully"
    cd "$SCRIPT_DIR"
}

# Setup configuration
setup_config() {
    log_info "Setting up configuration..."
    
    mkdir -p "$CONFIG_DIR/templates"
    mkdir -p "$DATA_DIR"
    
    # Copy example templates while respecting existing user placement (folders)
    # Rule: Templates in folders take precedence over root-level templates
    if [[ -d "$SCRIPT_DIR/templates" ]]; then
        python3 - <<PY
from pathlib import Path
import shutil
import os

src = Path(r"""$SCRIPT_DIR/templates""")
dst = Path(r"""$CONFIG_DIR/templates""")
dst.mkdir(parents=True, exist_ok=True)

# Build map of existing templates: filename -> list of paths
existing = {}
for p in dst.rglob("*.json"):
    existing.setdefault(p.name, []).append(p)

copied = 0
skipped = 0
updated = 0

for src_file in src.rglob("*.json"):
    locations = existing.get(src_file.name, [])
    
    # Check if template exists in a user folder (subdirectory)
    folder_versions = [p for p in locations if p.parent != dst]
    root_version = next((p for p in locations if p.parent == dst), None)
    
    if folder_versions:
        # Folder version exists - it takes precedence
        # If root version also exists, remove the duplicate
        if root_version and root_version.exists():
            root_version.unlink()
            print(f"  Removed duplicate: {src_file.name} (folder version in {folder_versions[0].parent.name}/ takes precedence)")
        skipped += 1
        continue
    
    target = dst / src_file.relative_to(src)
    
    if target.exists():
        # Check if repo version is newer
        if src_file.stat().st_mtime > target.stat().st_mtime:
            shutil.copy2(src_file, target)
            updated += 1
        else:
            skipped += 1
    else:
        # New template - copy it
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, target)
        copied += 1

print(f"Templates: {copied} new, {updated} updated, {skipped} skipped (folder precedence)")
PY
    fi
    
    # Create default config if it doesn't exist
    if [[ ! -f "$CONFIG_DIR/config.json" ]]; then
        cat > "$CONFIG_DIR/config.json" << EOF
{
  "llm": {
    "model_path": "",
    "model_dir": "$HOME/models",
    "server_port": 8080,
    "context_size": 4096,
    "gpu_layers": 0,
    "server_binary": ""
  },
  "ui": {
    "theme": "dark",
    "window_width": 900,
    "window_height": 700,
    "font_size": 11
  }
}
EOF
        log_info "Created default configuration"
    fi
    
    log_success "Configuration ready: $CONFIG_DIR"
}

# Create shell alias
setup_alias() {
    log_info "Setting up shell alias..."
    
    SHELL_RC=""
    if [[ -f "$HOME/.zshrc" ]]; then
        SHELL_RC="$HOME/.zshrc"
    elif [[ -f "$HOME/.bashrc" ]]; then
        SHELL_RC="$HOME/.bashrc"
    fi
    
    if [[ -n "$SHELL_RC" ]]; then
        ALIAS_LINE="alias automatr='source $VENV_DIR/bin/activate && automatr'"
        
        if ! grep -q "alias automatr=" "$SHELL_RC" 2>/dev/null; then
            echo "" >> "$SHELL_RC"
            echo "# Automatr" >> "$SHELL_RC"
            echo "$ALIAS_LINE" >> "$SHELL_RC"
            log_success "Added alias to $SHELL_RC"
        fi
    fi
}

# Run smoke test
smoke_test() {
    log_info "Running smoke test..."
    
    source "$VENV_DIR/bin/activate"
    
    # Test import
    if python3 -c "import automatr; print(f'Version: {automatr.__version__}')" 2>/dev/null; then
        log_success "Import test passed"
    else
        log_error "Import test failed"
        return 1
    fi
    
    # Test config
    if python3 -c "from automatr.core.config import get_config; get_config()" 2>/dev/null; then
        log_success "Config test passed"
    else
        log_error "Config test failed"
        return 1
    fi
    
    # Test templates
    if python3 -c "from automatr.core.templates import get_template_manager; print(f'Templates: {len(get_template_manager().list_all())}')" 2>/dev/null; then
        log_success "Template test passed"
    else
        log_error "Template test failed"
        return 1
    fi
    
    # Check llama-server
    if [[ -f "$LLAMA_CPP_DIR/build/bin/llama-server" ]]; then
        log_success "llama-server binary found"
    else
        log_warn "llama-server not found - LLM features will be unavailable"
    fi
    
    log_success "Smoke test complete!"
}

# Print summary
print_summary() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                  Automatr Installation Complete             ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${BLUE}Virtual environment:${NC} $VENV_DIR"
    echo -e "  ${BLUE}Configuration:${NC}       $CONFIG_DIR"
    echo -e "  ${BLUE}Data directory:${NC}      $DATA_DIR"
    echo -e "  ${BLUE}llama.cpp:${NC}           $LLAMA_CPP_DIR"
    echo ""
    echo -e "  ${YELLOW}To start Automatr:${NC}"
    echo -e "    source $VENV_DIR/bin/activate"
    echo -e "    automatr"
    echo ""
    echo -e "  ${YELLOW}Or restart your shell and run:${NC}"
    echo -e "    automatr"
    echo ""
    echo -e "  ${YELLOW}Next steps:${NC}"
    echo -e "    1. Download a GGUF model to ~/models/"
    echo -e "    2. Select model in LLM menu or edit $CONFIG_DIR/config.json"
    echo -e "    3. Run 'automatr' to start the GUI"
    echo ""
}

# Main installation
main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    Automatr Installer                       ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    detect_platform
    set_platform_paths
    
    if [[ "$1" != "--quick" ]]; then
        echo ""
        log_info "This will install:"
        echo "  - System dependencies (Python, Qt6, cmake, etc.)"
        echo "  - Python virtual environment with PyQt6"
        echo "  - llama.cpp (built from source)"
        echo "  - Example templates"
        echo ""
        read -p "Continue? [Y/n] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            log_info "Installation cancelled"
            exit 0
        fi
    fi
    
    install_system_deps
    setup_python_env
    build_llama_cpp
    setup_config
    setup_alias
    smoke_test
    print_summary
}

# Run main
main "$@"
