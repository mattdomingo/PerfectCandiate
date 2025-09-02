FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code (excluding node_modules if it exists locally)
COPY . .

# Reinstall dependencies to ensure they're properly linked
RUN npm install

# Create next.js config if it doesn't exist
RUN touch next.config.js

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "run", "dev"]
