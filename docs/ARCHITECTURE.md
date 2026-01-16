# Architecture Documentation

## Overview

AI Stock Bestie is a real-time stock analysis application built with Streamlit, providing AI-powered insights and advanced technical indicators.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                    │
│  (app.py, ui_components.py)                             │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│                 Business Logic Layer                      │
│  (indicators.py, llm_insights.py, charts.py)             │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│                  Data Access Layer                       │
│  (data_fetcher.py)                                       │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              External Services Layer                     │
│  (yfinance, Ollama)                                      │
└──────────────────────────────────────────────────────────┘
```

## Component Overview

### Core Modules

#### `app.py`
- Main application entry point
- Streamlit UI orchestration
- Session state management
- User interaction handling

#### `data_fetcher.py`
- Stock data fetching from yfinance
- Market data (SPY) fetching
- Data validation and cleaning

#### `indicators.py`
- Technical indicator calculations
- RSI, MACD, Bollinger Bands
- Support/Resistance levels
- Volume analysis

#### `llm_insights.py`
- AI-powered analysis generation
- Ollama integration
- Response caching

#### `charts.py`
- Plotly chart generation
- Price visualization
- Volume visualization

#### `ui_components.py`
- UI component rendering
- CSS styling
- Layout components

#### `config.py`
- Application configuration
- Constants and settings

## Data Flow

1. **User Input**: User enters ticker symbol
2. **Data Fetching**: `data_fetcher.py` fetches stock and market data
3. **Data Processing**: Data is validated and cleaned
4. **Indicator Calculation**: `indicators.py` calculates technical indicators
5. **Visualization**: `charts.py` generates interactive charts
6. **AI Analysis**: `llm_insights.py` generates insights (periodically)
7. **UI Rendering**: `ui_components.py` renders all components

## Design Patterns

### Singleton Pattern
- Configuration is accessed via `config.py` module

### Strategy Pattern
- Different indicator calculation strategies in `indicators.py`

### Observer Pattern
- Streamlit's reactive UI updates based on state changes

## Performance Considerations

- **Caching**: LLM responses are cached for 60 seconds
- **Vectorization**: NumPy operations for performance
- **Lazy Loading**: Data fetched only when needed
- **Efficient Data Structures**: List-based rolling windows

## Error Handling

- Input validation at multiple layers
- Graceful degradation for missing data
- User-friendly error messages

## Security Considerations

- Input sanitization for ticker symbols
- No sensitive data storage
- Disclaimer for financial advice

## Future Enhancements

- Database integration for historical data
- Real-time WebSocket connections
- Multi-user support
- Advanced caching strategies
- Performance monitoring
