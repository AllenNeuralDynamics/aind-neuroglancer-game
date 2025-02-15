FROM node:23.8.0-slim

# Install the app here
WORKDIR /app

# A wildcard is used to ensure both package.json AND package-lock.json are copied
COPY package*.json ./

# Bundle app source
COPY . ./

# Install Node.js dependencies
RUN npm install

# Expose the default port Neuroglancer uses
EXPOSE 8080

# Start the Neuroglancer server
CMD [ "npx", "tsx", "./build_tools/cli.ts", "serve", "--host=0.0.0.0" ]
