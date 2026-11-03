# Imagem da tela do Rangô, em duas fases:
# 1) usa o Node para gerar os arquivos finais (npm run build)
# 2) entrega esses arquivos com o nginx, um servidor web leve
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Endereço da API, gravado nos arquivos na hora do build
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
