# Stage 1: Build
FROM node:20-alpine as build

WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm install --legacy-peer-deps --ignore-scripts

# Copiar código fuente
COPY . .

# Build para producción
RUN npm run build:prod

# Stage 2: Serve
FROM nginx:alpine

# Copiar archivos compilados desde stage de build
COPY --from=build /app/dist/thrall-defender-frontend/browser /usr/share/nginx/html

# Copiar configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
