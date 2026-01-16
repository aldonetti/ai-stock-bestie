# AI Stock Bestie

[![CI Status](https://img.shields.io/badge/CI-Passing-success?style=flat-square&logo=github)](https://github.com/nouraellm/qtrade/actions)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000?style=flat-square)](https://github.com/psf/black)

Real-time stock analysis application with AI-powered insights.

<img width="1438" height="721" alt="Screenshot 2026-01-16 at 18 28 08" src="https://github.com/user-attachments/assets/82a928a8-ae0e-4f96-8aff-b3576f544460" />

<img width="1433" height="727" alt="Screenshot 2026-01-16 at 18 31 30" src="https://github.com/user-attachments/assets/20a9e314-9432-42eb-8e1a-089a43e16a86" />

## Features

- **Real-Time Analysis**: Live price tracking with advanced technical indicators
- **AI-Powered Insights**: Intelligent analysis using Ollama LLM
- **Interactive Charts**: Professional Plotly visualizations

## Requirements

- Python 3.9 or higher
- Internet connection (for fetching stock data)
- Ollama installed and running (for AI insights)

## Installation

### Quick Start (One-Click)

**macOS/Linux:**
```bash
chmod +x run.sh
./run.sh
```

**Windows:**
```cmd
run.bat
```

### Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/nouraellm/ai-stock-bestie.git
cd ai-stock-bestie
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install pre-commit hooks (optional):
```bash
pre-commit install
```

5. Run the application:
```bash
streamlit run src/app.py
```

## Project Structure

```
ai-stock-bestie/
├── src/                    # Source code
│   ├── app.py             # Main application
│   ├── config.py          # Configuration
│   ├── data_fetcher.py    # Data fetching
│   ├── indicators.py      # Technical indicators
│   ├── llm_insights.py    # AI insights
│   ├── ui_components.py  # UI components
│   └── charts.py          # Chart generation
├── tests/                  # Test suite
│   ├── test_validators.py
│   └── test_formatters.py
├── utils/                  # Utility functions
│   ├── logger.py          # Logging utilities
│   ├── validators.py      # Validation functions
│   └── formatters.py      # Formatting utilities
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md    # Architecture docs
│   └── API.md             # API documentation
├── .github/               # GitHub workflows
│   └── workflows/
│       └── ci.yml         # CI/CD configuration
├── run.sh                 # Unix/Linux run script
├── run.bat                # Windows run script
├── requirements.txt        # Python dependencies
├── pytest.ini             # Pytest configuration
├── Makefile               # Make commands
└── README.md              # This file
```

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ -v --cov=src --cov-report=html
```

## Development

### Code Quality

Format code:
```bash
make format
# or
black src/ tests/ utils/
isort src/ tests/ utils/
```

Run linters:
```bash
make lint
# or
black --check src/ tests/ utils/
isort --check-only src/ tests/ utils/
flake8 src/ tests/ utils/
mypy src/ --ignore-missing-imports
```

### Available Make Commands

- `make install` - Install dependencies
- `make test` - Run tests
- `make lint` - Run linters
- `make format` - Format code
- `make clean` - Clean cache files
- `make run` - Run the application

## Technical Indicators

- **Moving Averages**: Enhanced rolling averages
- **EMA Indicators**: Short (9) and Long (21) period EMAs
- **Bollinger Bands**: 20-period calculation
- **RSI**: Wilder's smoothing method
- **MACD**: Full MACD, Signal, and Histogram
- **Support/Resistance**: 30-period lookback
- **Volume Analysis**: VWAP and volume ratio
- **Price Momentum**: Buying vs selling pressure

## Documentation

- [Architecture Documentation](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature-name`)
3. Commit your changes (`git commit -m 'Add feature description'`)
4. Push to the branch (`git push origin feature/your-feature-name`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This is an educational project for demonstration purposes only. The analysis and insights provided should not be considered as financial advice. Always consult with a qualified financial advisor before making any investment decisions. Past performance does not guarantee future results.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Stock data from [yfinance](https://github.com/ranaroussi/yfinance)
- Charts powered by [Plotly](https://plotly.com/)
- AI insights via [Ollama](https://ollama.ai/)
