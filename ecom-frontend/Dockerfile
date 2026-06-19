FROM node:20-alpine
WORKDIR /app

# Install dependencies first for better caching
COPY package.json package-lock.json ./
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the default Vite port
EXPOSE 3000

# Run vite with host set to 0.0.0.0 to be accessible from outside the container
CMD ["npm", "run", "dev", "--", "--host"]
