"""
Setup script for Local AI Assistant.
Downloads required models and verifies dependencies.
"""
import os
import sys
import subprocess
import zipfile
import urllib.request

def install_packages():
    """Install required Python packages."""
    print("Installing required packages...")
    packages = [
        "openai-whisper",
        "ollama",
        "vosk",
        "pyaudio",
        "pyttsx3",
        "numpy"
    ]
    for package in packages:
        print(f"  Installing {package}...")
        subprocess.run([sys.executable, "-m", "pip", "install", package, "--quiet"], check=True)
    print("All packages installed!\n")

def download_vosk_model():
    """Download VOSK model for wake-word detection."""
    model_dir = "vosk_model"
    if os.path.exists(model_dir):
        print(f"VOSK model already exists at '{model_dir}'")
        return True
    
    print("Downloading VOSK model (this may take a few minutes)...")
    model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    zip_path = "vosk_model.zip"
    
    try:
        # Download
        print(f"  Downloading from {model_url}...")
        urllib.request.urlretrieve(model_url, zip_path)
        
        # Extract
        print("  Extracting model...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # Rename to vosk_model
        extracted_name = "vosk-model-small-en-us-0.15"
        if os.path.exists(extracted_name):
            os.rename(extracted_name, model_dir)
        
        # Clean up
        os.remove(zip_path)
        print(f"VOSK model downloaded to '{model_dir}'!\n")
        return True
    except Exception as e:
        print(f"Error downloading VOSK model: {e}")
        print("Please download manually from: https://alphacephei.com/vosk/models")
        return False

def check_ollama():
    """Check if Ollama is installed and running."""
    print("Checking Ollama installation...")
    try:
        import ollama
        models = ollama.list()
        print(f"  Ollama is running. Available models: {[m['name'] for m in models.get('models', [])]}")
        
        # Check if llama2 is available
        model_names = [m['name'] for m in models.get('models', [])]
        if not any('llama' in name.lower() for name in model_names):
            print("\n  WARNING: No LLaMA model found!")
            print("  Please run: ollama pull llama2")
        return True
    except Exception as e:
        print(f"  WARNING: Could not connect to Ollama: {e}")
        print("  Please ensure Ollama is installed and running.")
        print("  Download from: https://ollama.ai")
        print("  Then run: ollama serve")
        return False

def test_tts():
    """Test text-to-speech."""
    print("Testing text-to-speech...")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say("Hello, I am your local AI assistant.")
        engine.runAndWait()
        print("  TTS working!\n")
        return True
    except Exception as e:
        print(f"  WARNING: TTS error: {e}\n")
        return False

def main():
    print("="*60)
    print("Local AI Assistant Setup")
    print("="*60 + "\n")
    
    # Install packages
    install_packages()
    
    # Download VOSK model
    download_vosk_model()
    
    # Check Ollama
    check_ollama()
    
    # Test TTS
    test_tts()
    
    print("="*60)
    print("Setup complete!")
    print("="*60)
    print("\nTo start the assistant, run:")
    print("  python orchestrator.py")
    print("\nNote: Make sure Ollama is running with a model:")
    print("  1. Start Ollama: ollama serve")
    print("  2. Pull a model: ollama pull llama2")

if __name__ == "__main__":
    main()
