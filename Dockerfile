FROM openfabric/tee-python-cpu:dev

# Copy only necessary files for Poetry installation
COPY pyproject.toml poetry.lock* ./

# Install dependencies using Poetry
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --upgrade poetry && \
    poetry env acitvate && \
    poetry install --no-root

# Copy the rest of the source code into the container
COPY . .

# Expose ports for both services
EXPOSE 8888 8501

# Start both services
CMD ["/start.sh"]