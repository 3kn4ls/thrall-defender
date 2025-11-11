# Multi-stage build para reducir tamaño de imagen
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependencias del sistema necesarias para scapy
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# Stage final
FROM python:3.11-slim

WORKDIR /app

# Instalar solo runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpcap0.8 \
    iptables \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias Python desde builder
COPY --from=builder /root/.local /root/.local

# Copiar código de la aplicación
COPY ./app ./app

# Asegurar que los scripts en .local están en el PATH
ENV PATH=/root/.local/bin:$PATH

# Exponer puerto
EXPOSE 8000

# Crear directorio para la base de datos
RUN mkdir -p /data
ENV DATABASE_URL=sqlite+aiosqlite:////data/thrall_defender.db

# Usuario root necesario para captura de paquetes
# En producción con Kubernetes, se usan capabilities en vez de root

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
