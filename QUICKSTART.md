# Quick Start Guide

## Prerequisites Check

Before starting, ensure you have:

1. **Python 3.9+** installed
   ```bash
   python3 --version
   ```

2. **Docker** installed (for Qdrant)
   ```bash
   docker --version
   ```

3. **System build tools** (for llama.cpp compilation)
   - macOS: `brew install cmake`
   - Linux: `sudo apt-get install cmake build-essential`
   - Windows: Visual Studio Build Tools

## Installation Steps

### 1. Run Setup Script

```bash
./setup.sh
```

This will:
- Create virtual environment
- Install all dependencies
- Create necessary directories
- Start Qdrant container

### 2. Manual Setup (Alternative)

If the setup script doesn't work:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Qdrant
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
```

### 3. Verify Qdrant is Running

```bash
docker ps | grep qdrant
```

You should see the Qdrant container running on port 6333.

### 4. Run the Application

```bash
python main.py
```

The first run will:
- Download the LLM model (this may take several minutes)
- Initialize the vector store
- Launch the desktop UI

## First Question

Try asking:
- "What were the main causes of World War I?"
- "Who was involved in the Battle of Gettysburg?"

## Troubleshooting

### Model Download Issues

If model download fails:
1. Check internet connection
2. Manually download a GGUF model from Hugging Face
3. Place it in `models/` directory
4. Update `config.yaml` with the correct path

### Qdrant Connection Error

```bash
# Check if Qdrant is running
docker ps | grep qdrant

# If not running, start it
docker start qdrant

# Or create a new container
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
```

### Import Errors

If you see import errors:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Memory Issues

If you encounter memory errors:
1. Edit `config.yaml`
2. Reduce `n_ctx` (context window size)
3. Use a smaller quantized model (Q4_0 instead of Q4_K_M)

## Testing the System

Run the test script to verify everything works:

```bash
python test_system.py
```

This will test the complete workflow with sample questions.

## Next Steps

- Customize `config.yaml` for your needs
- Add more test questions
- Review the evaluation metrics
- Explore the codebase structure

