FROM node:20
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Ensure node_modules remains in container for dev even with bind mount
VOLUME ["/app/node_modules"]
EXPOSE 3000
CMD ["npm","run","dev","--","-p","3000"]


