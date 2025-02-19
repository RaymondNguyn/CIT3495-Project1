# Use a Node.js base image
FROM node:16

# Set working directory inside the container
WORKDIR /usr/src/app

# Copy the package.json first to optimize caching
COPY package.json ./

# Install dependencies
RUN npm install

# Copy the rest of your project files
COPY . .

# Expose the port that the application will run on
EXPOSE 4000

# Start the application
CMD ["npm", "start"]
