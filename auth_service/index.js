// auth_service/index.js
const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const mysql = require('mysql2/promise');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

// Add basic HTML form handling
app.use(express.urlencoded({ extended: true }));

const pool = mysql.createPool({
    host: process.env.MYSQL_HOST || 'mysql',
    user: process.env.MYSQL_USER || 'user',
    password: process.env.MYSQL_PASSWORD || 'password',
    database: process.env.MYSQL_DATABASE || 'datadb'
});

// Initialize users table
async function initDB() {
    const connection = await pool.getConnection();
    await connection.execute(`
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    `);
    connection.release();
}

initDB();

// Root route - Basic HTML form
// Root route - Basic HTML form
app.get('/', (req, res) => {
  res.send(`
      <html>
      <head>
          <title>Authentication Service</title>
          <style>
              body {
                  font-family: Arial, sans-serif;
                  max-width: 800px;
                  margin: 0 auto;
                  padding: 20px;
              }
              .form-container {
                  margin-bottom: 30px;
                  padding: 20px;
                  border: 1px solid #ccc;
                  border-radius: 5px;
              }
              input {
                  margin: 10px 0;
                  padding: 5px;
              }
              button {
                  padding: 10px;
                  background-color: #007bff;
                  color: white;
                  border: none;
                  border-radius: 5px;
                  cursor: pointer;
              }
              button:hover {
                  background-color: #0056b3;
              }
              #response {
                  margin-top: 20px;
                  padding: 10px;
                  border: 1px solid #ccc;
                  border-radius: 5px;
              }
          </style>
      </head>
      <body>
          <h1>Authentication Service</h1>
          
          <div class="form-container">
              <h2>Register</h2>
              <form id="registerForm">
                  <div>
                      <input type="text" name="username" placeholder="Username" required>
                  </div>
                  <div>
                      <input type="password" name="password" placeholder="Password" required>
                  </div>
                  <button type="submit">Register</button>
              </form>
          </div>

          <div class="form-container">
              <h2>Login</h2>
              <form id="loginForm">
                  <div>
                      <input type="text" name="username" placeholder="Username" required>
                  </div>
                  <div>
                      <input type="password" name="password" placeholder="Password" required>
                  </div>
                  <button type="submit">Login</button>
              </form>
          </div>

          <div id="response"></div>

          <script>
              const responseDiv = document.getElementById('response');

              document.getElementById('registerForm').addEventListener('submit', async (e) => {
                  e.preventDefault();
                  const formData = new FormData(e.target);
                  try {
                      const response = await fetch('/register', {
                          method: 'POST',
                          headers: {
                              'Content-Type': 'application/json',
                          },
                          body: JSON.stringify({
                              username: formData.get('username'),
                              password: formData.get('password')
                          }),
                      });
                      const data = await response.json();
                      responseDiv.innerText = JSON.stringify(data, null, 2);
                  } catch (error) {
                      responseDiv.innerText = 'Error: ' + error.message;
                  }
              });

              document.getElementById('loginForm').addEventListener('submit', async (e) => {
                  e.preventDefault();
                  const formData = new FormData(e.target);
                  try {
                      const response = await fetch('/login', {
                          method: 'POST',
                          headers: {
                              'Content-Type': 'application/json',
                          },
                          body: JSON.stringify({
                              username: formData.get('username'),
                              password: formData.get('password')
                          }),
                      });
                      const data = await response.json();
                      
                      if (response.ok && data.token) {
                          // Redirect to localhost:8000 with token
                          window.location.href = \`http://localhost:8000/data?token=\${data.token}\`;
                      } else {
                          responseDiv.innerText = JSON.stringify(data, null, 2);
                      }
                  } catch (error) {
                      responseDiv.innerText = 'Error: ' + error.message;
                  }
              });
          </script>
      </body>
      </html>
  `);
});


// Existing routes remain the same
app.post('/register', async (req, res) => {
    const { username, password } = req.body;
    try {
        const hashedPassword = await bcrypt.hash(password, 10);
        await pool.execute(
            'INSERT INTO users (username, password) VALUES (?, ?)',
            [username, hashedPassword]
        );
        res.status(201).json({ message: 'User registered successfully' });
    } catch (error) {
        res.status(500).json({ error: 'Error registering user' });
    }
});

app.post('/login', async (req, res) => {
  const { username, password } = req.body;
  try {
      const [rows] = await pool.execute(
          'SELECT * FROM users WHERE username = ?',
          [username]
      );

      if (rows.length === 0) {
          return res.status(401).json({ error: 'Invalid credentials' });
      }

      const valid = await bcrypt.compare(password, rows[0].password);
      if (!valid) {
          return res.status(401).json({ error: 'Invalid credentials' });
      }

      const token = jwt.sign(
          { userId: rows[0].id, username },
          process.env.JWT_SECRET || 'your_jwt_secret',
          { expiresIn: '1h' }
      );

      // Check if request comes from a browser
      if (req.headers.accept?.includes("text/html")) {
          return res.redirect(`http://localhost:8000/data?token=${token}`);
      }

      // If request is from API, return JSON response
      res.json({ token });
  } catch (error) {
      res.status(500).json({ error: 'Error logging in' });
  }
});

app.post('/verify', async (req, res) => {
    const token = req.headers.authorization?.split(' ')[1];
    
    if (!token) {
        return res.status(401).json({ error: 'No token provided' });
    }

    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your_jwt_secret');
        res.json({ valid: true, user: decoded });
    } catch (error) {
        res.status(401).json({ valid: false, error: 'Invalid token' });
    }
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
    console.log(`Auth service running on port ${port}`);
});