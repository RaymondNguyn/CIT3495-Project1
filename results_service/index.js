const express = require('express');
const { MongoClient } = require('mongodb');
const axios = require('axios');

const app = express();
app.use(express.json());

const mongoUri = process.env.MONGO_URI || 'mongodb://root:rootpassword@mongodb:27017/';
const authServiceUrl = process.env.AUTH_SERVICE_URL || 'http://localhost:3000';

let mongoClient;

async function connectToMongo() {
  try {
    mongoClient = new MongoClient(mongoUri);
    await mongoClient.connect();
    console.log('Connected to MongoDB');
  } catch (error) {
    console.error('MongoDB connection error:', error);
    process.exit(1);
  }
}

connectToMongo();

// Middleware to verify JWT

// Render homepage and display MongoDB data
app.get('/', async (req, res) => {
  try {
    const db = mongoClient.db('datadb');
    const stats = await db.collection('float_statistics')
      .find()
      .sort({ timestamp: -1 })
      .limit(1)
      .toArray();

    if (stats.length === 0) {
      return res.status(404).send('No analytics data available');
    }

    // Render the HTML with MongoDB data
    res.send(`
      <html>
        <head>
          <title>Analytics Results</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .data-container { margin-bottom: 20px; }
            .data-item { margin: 10px 0; }
          </style>
        </head>
        <body>
          <h1>Latest Analytics</h1>
          <div class="data-container">
            <div class="data-item"><strong>Min:</strong> ${stats[0].min || 'N/A'}</div>
            <div class="data-item"><strong>Max:</strong> ${stats[0].max || 'N/A'}</div>
            <div class="data-item"><strong>Average:</strong> ${stats[0].average || 'N/A'}</div>
            <div class="data-item"><strong>Median:</strong> ${stats[0].median || 'N/A'}</div>
            <div class="data-item"><strong>Count:</strong> ${stats[0].count || 'N/A'}</div>
            <div class="data-item"><strong>Timestamp:</strong> ${new Date(stats[0].timestamp * 1000).toLocaleString()}</div>
          </div>
        </body>
      </html>
    `);
  } catch (error) {
    res.status(500).send('Error fetching analytics data');
  }
});

const port = process.env.PORT || 4000;
app.listen(port, () => {
  console.log(`Results service running on port ${port}`);
});
