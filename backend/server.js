import fs from "fs";

import express from "express";
import cors from "cors";
import { spawn } from "child_process";

const app = express();
app.use(cors());
app.use(express.json());

const PORT = 5000;
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const audioLog = join(__dirname, "../audio/audio_log.json");


// only letters/numbers we care about
const INTERESTING_CHARS = ["a","b","c","d","1","2","3","4"];

// --- start python audio process ---
const audioProcess = spawn("python", ["../audio/audio.py"]);

audioProcess.stdout.on("data", (data) => {
  const str = data.toString().trim();
  try {
    const jsonData = JSON.parse(str);

    // filter: cheating detected OR faint audio contains interesting letters/numbers
    const hasCheating = jsonData.cheating_detected === true;
    const transcription = (jsonData.transcription || "").toLowerCase();
    const hasInteresting = INTERESTING_CHARS.some(c => transcription.includes(c));

    if (hasCheating || hasInteresting) {
      console.log("audio event (logged):", jsonData);
      fs.appendFileSync(audioLog, JSON.stringify(jsonData) + "\n");
    }

  } catch (e) {
    console.error("failed to parse audio json:", str);
  }
});

audioProcess.stderr.on("data", (data) => {
  console.error("audio process error:", data.toString());
});

audioProcess.on("close", (code) => {
  console.log(`audio process exited with code ${code}`);
});

// --- Express routes ---
app.get("/", (req, res) => res.send("Audio server running..."));

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
