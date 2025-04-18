import express from 'express';
import VoiceService from './services/voiceService.js';

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static('public'));

app.post('/voice', (req, res) => {
  const { text } = req.body;
  VoiceService.speak(text);
  res.sendStatus(200);
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
