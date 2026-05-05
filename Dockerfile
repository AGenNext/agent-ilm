FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install -e .

# Create state directory
RUN mkdir -p /root/.agent-ilm

# Default command
CMD ["agent-ilm", "--help"]