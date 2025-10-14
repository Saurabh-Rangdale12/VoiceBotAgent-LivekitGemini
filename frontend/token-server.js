import express from 'express';
import cors from 'cors';
import { AccessToken } from 'livekit-server-sdk';
import 'dotenv/config';

const app = express();
const port = 3001;

// Aapke React app ka URL (Vite default)
app.use(cors({ origin: 'http://localhost:5173' }));

app.get('/token', (req, res) => {
  const roomName = 'gemini-test-room';
  const participantName = `react-user-${Math.floor(Math.random() * 1000)}`;

  // THE FIX IS HERE: Use variable names WITHOUT the VITE_ prefix
  const at = new AccessToken(
    process.env.LIVEKIT_API_KEY,
    process.env.LIVEKIT_API_SECRET,
    {
      identity: participantName,
      name: 'React User',
    }
  );

  at.addGrant({ room: roomName, roomJoin: true, canPublish: true, canSubscribe: true });

  res.json({ token: at.toJwt() });
});

app.listen(port, () => {
  console.log(`Token server listening on http://localhost:${port}`);
});