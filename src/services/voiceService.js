import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';

class VoiceService {
  constructor() {
    this.synth = window.speechSynthesis;
    this.voices = [];
    this.populateVoiceList();
  }

  populateVoiceList() {
    this.voices = this.synth.getVoices();
  }

  startListening() {
    return SpeechRecognition.startListening();
  }

  stopListening() {
    return SpeechRecognition.stopListening();
  }

  speak(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    const voice = this.voices.find(v => v.lang === 'en-US');
    if (voice) {
      utterance.voice = voice;
    }
    this.synth.speak(utterance);
  }
}

export default new VoiceService();
