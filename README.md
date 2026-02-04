# History Helper - Local History Assistant

A production-ready desktop application that serves as an intelligent history assistant, running entirely locally using CPU-based inference with local LLM models. The system autonomously gathers relevant information from the web and synthesizes accurate, context-rich answers to historical questions.

## Features

- **Local LLM Inference**: CPU-optimized inference using llama.cpp with GGUF quantized models
- **Multi-Agent System**: LangGraph-based workflow with three specialized agents:
  - Query Analyzer: Extracts optimal search keywords from historical questions
  - Information Gatherer: Performs web searches and crawls content using Crawl4AI
  - Answer Synthesizer: Generates comprehensive answers using RAG architecture
- **Vector Store**: Qdrant-based similarity search for efficient information retrieval
- **Web Crawling**: Intelligent content extraction with caching and error handling
- **Evaluation Framework**: Metrics for retrieval quality, keyword relevance, and answer quality
- **Desktop UI**: Modern PyQt6 interface for seamless user interaction

## Architecture

```
User Question
    ↓
Query Analyzer Agent → Extract Keywords
    ↓
Information Gatherer Agent → Web Search → Crawl URLs → Store in Vector DB
    ↓
Answer Synthesizer Agent → RAG Retrieval → Generate Answer
    ↓
Display Answer with Sources
```

## Installation

### Prerequisites

1. **Python 3.9+**
2. **Qdrant Server** (for vector storage):
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

3. **System Dependencies** (for llama.cpp):
   - macOS: `brew install cmake`
   - Linux: `sudo apt-get install cmake build-essential`
   - Windows: Install Visual Studio Build Tools

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd R-helper-pet
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Download LLM model (optional - will auto-download on first run):
   - The application will automatically download a quantized model from Hugging Face on first run
   - Or manually download a GGUF model and place it in `models/` directory
   - Recommended: Mistral-7B-Instruct or similar 7B-13B parameter models optimized for CPU

5. Configure the application:
   - Edit `config.yaml` to customize settings
   - Adjust model paths, agent parameters, and UI preferences

## Usage

### Running the Application

1. Ensure Qdrant is running:
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

2. Start the application:
   ```bash
   python main.py
   ```

3. Enter a historical question in the UI and click "Ask"

### Example Questions

- "What were the main causes of World War I?"
- "Who was involved in the Battle of Gettysburg?"
- "What happened during the French Revolution?"
- "When did the Renaissance begin and what were its key characteristics?"

## Configuration

Edit `config.yaml` to customize:

- **LLM Settings**: Model path, context window, temperature
- **Embedding Model**: Choose different sentence transformer models
- **Vector Store**: Qdrant connection settings
- **Agent Parameters**: Keyword limits, crawl timeouts, retrieval settings
- **UI Preferences**: Window size, theme

## Project Structure

```
R-helper-pet/
├── src/
│   ├── agents/          # Multi-agent workflow
│   │   ├── query_analyzer.py
│   │   ├── information_gatherer.py
│   │   ├── answer_synthesizer.py
│   │   └── workflow.py
│   ├── llm/             # LLM inference
│   │   └── inference.py
│   ├── embeddings/      # Embedding generation
│   │   └── encoder.py
│   ├── vector_store/    # Vector database
│   │   └── qdrant_store.py
│   ├── crawler/         # Web crawling
│   │   └── web_crawler.py
│   ├── search/          # Web search
│   │   └── web_search.py
│   ├── evaluation/      # Evaluation metrics
│   │   └── metrics.py
│   ├── ui/              # Desktop UI
│   │   └── main_window.py
│   └── config.py        # Configuration management
├── config.yaml          # Application configuration
├── requirements.txt     # Python dependencies
├── main.py             # Application entry point
└── README.md           # This file
```

## Evaluation

The system includes comprehensive evaluation metrics:

- **ROUGE Scores**: Answer quality assessment (ROUGE-1, ROUGE-2, ROUGE-L)
- **Precision@K**: Retrieval quality metrics
- **Keyword Relevance**: Assessment of keyword extraction accuracy

Use the evaluation framework to assess system performance on test questions.

## Edge Cases Handled

- Historical questions requiring temporal reasoning
- Ambiguous historical events with multiple interpretations
- Limited or contradictory information from web sources
- Crawling failures (paywalls, JavaScript-heavy sites, rate limiting)
- CPU memory constraints during inference
- Non-English historical sources
- Questions spanning multiple historical periods or regions

## Performance Optimization

- **Caching**: Crawled content is cached to avoid re-fetching
- **Concurrent Crawling**: Multiple URLs crawled in parallel
- **Quantized Models**: GGUF models optimized for CPU inference
- **Batch Embedding**: Efficient batch processing of embeddings
- **Async Operations**: Non-blocking I/O for web operations

## Troubleshooting

### Qdrant Connection Error
- Ensure Qdrant Docker container is running: `docker ps | grep qdrant`
- Check port 6333 is not blocked by firewall

### Model Download Issues
- Manually download GGUF model from Hugging Face
- Place in `models/` directory with correct filename
- Update `config.yaml` with correct model path

### Memory Issues
- Reduce `n_ctx` in config.yaml (context window)
- Use smaller quantized models (Q4_K_M or Q4_0)
- Reduce `max_concurrent_crawls` in config

### Crawling Failures
- Some sites may block automated access
- Check network connectivity
- Increase timeout in config.yaml

## License

[Specify your license here]

## Contributing

[Contributing guidelines]

## Acknowledgments

- llama.cpp for CPU-optimized inference
- LangGraph for agentic workflows
- Qdrant for vector storage
- Crawl4AI for web content extraction
- Sentence Transformers for embeddings

