// results_service/index.js
const express = require('express');
const { MongoClient } = require('mongodb');
const axios = require('axios');

const app = express();
app.use(express.json());

const mongoUri = process.env.MONGO_URI || 'mongodb://root:rootpassword@mongodb:27017/';
const authServiceUrl = process.env.AUTH_SERVICE_URL || 'http://auth_service:3000';

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
async function verifyToken(req, res, next) {
  const token = req.headers.authorization;

  if (!token) {
    return res.status(401).json({ error: 'No token provided' });
  }

  try {
    const response = await axios.post(
      `${authServiceUrl}/verify`,
      {},
      { headers: { Authorization: token } }
    );
    
    req.user = response.data.user;
    next();
  } catch (error) {
    res.status(401).json({ error: 'Invalid token' });
  }
}

// Get latest analytics
app.get('/analytics/latest', verifyToken, async (req, res) => {
  try {
    const db = mongoClient.db('analytics');
    const stats = await db.collection('statistics')
      .find()
      .sort({ timestamp: -1 })
      .limit(1)
      .toArray();

    if (stats.length === 0) {
      return res.status(404).json({ error: 'No analytics data available' });
    }

    res.json(stats[0]);
  } catch (error) {
    res.status(500).json({ error: 'Error fetching analytics' });
  }
});

// Get historical analytics
app.get('/analytics/history', verifyToken, async (req, res) => {
  try {
    const db = mongoClient.db('analytics');
    const stats = await db.collection('statistics')
      .find()
      .sort({ timestamp: -1 })
      .limit(100)
      .toArray();

    res.json(stats);
  } catch (error) {
    res.status(500).json({ error: 'Error fetching analytics history' });
  }
});

const port = process.env.PORT || 4000;
app.listen(port, () => {
  console.log(`Results service running on port ${port}`);
});